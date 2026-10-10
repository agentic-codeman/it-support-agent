import os
import sys
import time
import requests
import zipfile
import shutil
from pathlib import Path

from backend.workflow.import_process.state import ImportGraphState, create_default_state
from backend.utils.format_utils import format_state
from backend.utils.path_util import PROJECT_ROOT

from backend.core.logger import logger

from backend.client.rustfs_client import get_restfs_client
from backend.conf.mineru_config import mineru_config

MINERU_BASE_URL = mineru_config.base_url
MINERU_API_TOKEN = mineru_config.api_key
MINERU_MODEL_VERSION = mineru_config.model_version


def step_1_validate_paths(state):
    log_prefix = "[step_1_validate_paths]"
    object_key = state.get("file_url", "").strip()
    local_dir = state.get("local_dir", "").strip()
    bucket_name = state.get("bucket_name", "").strip()

    # 参数非空校验
    if not object_key:
        raise ValueError(f"{log_prefix}工作流状态缺失有效参数：file_url，当前值：{repr(object_key)}")
    if not local_dir:
        raise ValueError(f"{log_prefix}工作流状态缺失有效参数：local_dir，当前值：{repr(local_dir)}")

    output_dir_obj = Path(local_dir)

    # RestFS对象有效性校验：用object_exists检查对象是否存在
    rustfs_client = get_restfs_client()
    if not rustfs_client.object_exists(bucket_name, object_key):
        raise FileNotFoundError(
            f"{log_prefix}PDF对象不存在于RestFS，bucket：{bucket_name}，key：{object_key}"
        )
    pdf_path_obj = Path(os.path.join(PROJECT_ROOT, object_key))
    # download_file 要求父目录已存在，先递归创建（object_key 可能带 documents/ 等子目录前缀）
    pdf_path_obj.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"{log_prefix}开始从RestFS下载PDF：{bucket_name}/{object_key} -> {pdf_path_obj.absolute()}")
    try:
        rustfs_client.download_file(bucket_name, object_key, str(pdf_path_obj))
    except Exception as e:
        raise RuntimeError(f"{log_prefix}从RestFS下载PDF失败：{str(e)}")
    logger.info(f"{log_prefix}PDF已下载到本地：{pdf_path_obj.absolute()}")

    # 确保输出目录存在，不存在则递归创建
    if not output_dir_obj.exists():
        logger.info(f"{log_prefix}输出目录不存在，自动创建：{output_dir_obj.absolute()}")
        output_dir_obj.mkdir(parents=True, exist_ok=True)

    return pdf_path_obj, output_dir_obj


def step_2_upload_and_poll(pdf_path_obj: Path, output_dir_obj: Path):

    if not MINERU_BASE_URL or not MINERU_API_TOKEN:
        raise ValueError("MinerU配置缺失：请在.env中正确配置MINERU_BASE_URL和MINERU_API_TOKEN")
    logger.info(f"[配置校验] MinerU基础配置加载成功，开始处理文件：{pdf_path_obj.name}")

    # 构造请求头（符合HTTP规范，Bearer鉴权）
    request_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MINERU_API_TOKEN}"
    }

    url_get_upload = f"{MINERU_BASE_URL}/file-urls/batch"
    req_data = {
        "files": [{"name": pdf_path_obj.name}],
        "model_version": MINERU_MODEL_VERSION  # 解析模型，.env可配置（pipeline/vlm）
    }
    logger.debug(f"[获取上传链接] 调用接口：{url_get_upload}，请求参数：{req_data}")
    resp = requests.post(url=url_get_upload, headers=request_headers, json=req_data, timeout=30)

    if resp.status_code != 200:
        raise RuntimeError(f"[获取上传链接] 网络请求失败，状态码：{resp.status_code}，响应内容：{resp.text}")

    resp_data = resp.json()
    if resp_data["code"] != 0:
        raise RuntimeError(f"[获取上传链接] API业务错误，返回数据：{resp_data}")

    signed_url = resp_data["data"]["file_urls"][0]
    batch_id = resp_data["data"]["batch_id"]
    logger.info(f"[获取上传链接] 成功，batch_id：{batch_id}，上传链接已生成")

    logger.info(f"[文件上传] 开始读取PDF文件：{pdf_path_obj.name}")
    with open(pdf_path_obj, "rb") as f:
        file_data = f.read()

    upload_session = requests.Session()
    upload_session.trust_env = False

    upload_timeout = 300
    max_attempts = 3

    try:
        last_error = None
        upload_ok = False
        for attempt in range(1, max_attempts + 1):
            # 首次自动识别类型，后续重试强制指定 PDF 的 Content-Type
            headers = None if attempt == 1 else {"Content-Type": "application/pdf"}
            try:
                put_resp = upload_session.put(
                    url=signed_url, data=file_data, headers=headers, timeout=upload_timeout
                )
            except requests.exceptions.RequestException as e:
                logger.warning(f"[文件上传] 第{attempt}次上传网络异常：{e}")
                last_error = e
                if attempt < max_attempts:
                    time.sleep(2 ** attempt)  # 2s、4s 指数退避
                continue

            if put_resp.status_code == 200:
                logger.info(f"[文件上传] 成功，文件{pdf_path_obj.name}已存入云存储")
                upload_ok = True
                break

            logger.warning(
                f"[文件上传] 第{attempt}次上传失败（状态码：{put_resp.status_code}），响应：{put_resp.text[:200]}"
            )
            last_error = RuntimeError(f"上传失败，状态码：{put_resp.status_code}，响应内容：{put_resp.text}")
            if attempt < max_attempts:
                time.sleep(2 ** attempt)

        if not upload_ok:
            raise RuntimeError(f"[文件上传] 重试{max_attempts}次后仍失败：{last_error}")
    finally:
        upload_session.close()

    poll_url = f"{MINERU_BASE_URL}/extract-results/batch/{batch_id}"
    start_time = time.time()
    timeout_seconds = 600
    poll_interval = 3
    logger.info(f"[任务轮询] 开始监控任务状态，batch_id：{batch_id}，最大超时：{timeout_seconds}s")

    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout_seconds:
            raise TimeoutError(f"[任务轮询] 超时！任务处理超{int(timeout_seconds)}秒，batch_id：{batch_id}")
        try:
            poll_resp = requests.get(url=poll_url, headers=request_headers, timeout=10)
        except Exception as e:
            logger.warning(f"[任务轮询] 网络请求异常，{poll_interval}秒后重试：{str(e)}")
            time.sleep(poll_interval)
            continue

        if poll_resp.status_code != 200:
            if 500 <= poll_resp.status_code < 600:
                logger.warning(f"[任务轮询] 服务端繁忙（状态码：{poll_resp.status_code}），{poll_interval}秒后重试")
                time.sleep(poll_interval)
                continue
            else:
                raise RuntimeError(f"[任务轮询] HTTP请求失败，状态码：{poll_resp.status_code}，响应内容：{poll_resp.text}")

        poll_data = poll_resp.json()
        if poll_data["code"] != 0:
            raise RuntimeError(f"[任务轮询] API业务错误，返回数据：{poll_data}")

        extract_results = poll_data["data"]["extract_result"]
        if not extract_results:
            logger.debug(f"[任务轮询] 结果暂为空，已耗时{int(elapsed_time)}s，继续等待")
            time.sleep(poll_interval)
            continue
        result_item = extract_results[0]
        state_status = result_item["state"]
        if state_status == "done":
            logger.info(f"[任务轮询] 解析任务完成！总耗时：{int(elapsed_time)}s，batch_id：{batch_id}")
            full_zip_url = result_item.get("full_zip_url")
            if not full_zip_url:
                raise RuntimeError("[任务轮询] 任务完成但未返回ZIP包下载链接，batch_id：{batch_id}")
            logger.info(f"[任务轮询] 结果ZIP包下载链接：{full_zip_url}...")
            return full_zip_url
        elif state_status == "failed":
            err_msg = result_item.get("err_msg", "未知错误，无具体信息")
            raise RuntimeError(f"[任务轮询] 解析任务失败，batch_id：{batch_id}，错误信息：{err_msg}")
        else:
            logger.debug(
                f"[任务轮询] 处理中（已耗时{int(elapsed_time)}s），状态：{state_status} | 刷新间隔{poll_interval}s",
                end="\r"
            )
            time.sleep(poll_interval)


def step_3_download_and_extract(zip_url: str, output_dir_obj: Path, pdf_stem: str) -> str:

    logger.info(f"===== 开始处理[{pdf_stem}]的MinerU解析结果 =====")

    logger.info(f"[步骤1/4] 开始下载ZIP包，链接：{zip_url}...")
    resp = requests.get(zip_url, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"[步骤1/4] ZIP包下载失败，HTTP状态码：{resp.status_code}")

    zip_save_path = output_dir_obj / f"{pdf_stem}_result.zip"
    with open(zip_save_path, "wb") as f:
        f.write(resp.content)
    logger.info(f"[步骤1/4] ZIP包下载成功，保存路径：{zip_save_path}")

    logger.info(f"[步骤2/4] 开始解压ZIP包...")
    extract_target_dir = output_dir_obj / pdf_stem

    if extract_target_dir.exists():
        try:
            shutil.rmtree(extract_target_dir)
            logger.info(f"[步骤2/4] 已清理旧的解压目录：{extract_target_dir}")
        except Exception as e:
            logger.warning(f"[步骤2/4] 清理旧目录失败，可能不影响新文件解压：{str(e)}")

    extract_target_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_save_path, 'r') as zip_file_obj:
        zip_file_obj.extractall(extract_target_dir)
    logger.info(f"[步骤2/4] ZIP包解压完成，解压目录：{extract_target_dir}")

    logger.info(f"[步骤3/4] 开始查找解压目录中的MD文件...")
    md_file_list = list(extract_target_dir.rglob("*.md"))
    if not md_file_list:
        raise FileNotFoundError(f"[步骤3/4] 解压目录中未找到任何.md格式文件：{extract_target_dir}")
    logger.info(f"[步骤3/4] 共找到{len(md_file_list)}个MD文件，按优先级匹配目标文件")

    target_md_file = None
    for md_file in md_file_list:
        if md_file.stem == pdf_stem:
            target_md_file = md_file
            logger.info(f"[步骤4/4] 匹配到优先级1目标：与PDF同名的MD文件 {target_md_file.name}")
            break
    if not target_md_file:
        for md_file in md_file_list:
            if md_file.name.lower() == "full.md":
                target_md_file = md_file
                logger.info(f"[步骤4/4] 匹配到优先级2目标：MinerU默认文件 {target_md_file.name}")
                break
    if not target_md_file:
        target_md_file = md_file_list[0]
        logger.info(f"[步骤4/4] 未匹配到前两级目标，兜底取第一个MD文件 {target_md_file.name}")

    if target_md_file.stem != pdf_stem:
        logger.info(f"[步骤4/4] 开始重命名MD文件，统一为PDF同名：{pdf_stem}.md")
        new_md_path = target_md_file.with_name(f"{pdf_stem}.md")
        try:
            target_md_file.rename(new_md_path)
            target_md_file = new_md_path
            logger.info(f"[步骤4/4] MD文件重命名成功：{pdf_stem}.md")
        except OSError as e:
            logger.warning(f"[步骤4/4] MD文件重命名失败，将使用原文件名继续流程：{str(e)}")

    final_md_path = str(target_md_file.absolute())
    logger.info(f"===== [{pdf_stem}]解析结果处理完成，最终MD文件路径：{final_md_path} =====")
    return final_md_path


def node_pdf_to_md(state: ImportGraphState) -> ImportGraphState:
    """
    LangGraph工作流节点：PDF转MD核心处理节点
    核心流程：路径校验 → MinerU上传解析 → 结果下载解压 → 读取MD内容并更新工作流状态
    参数：state-工作流状态对象，需包含pdf_path/local_dir/task_id
    返回：更新后的工作流状态，新增md_path/md_content
    """

    func_name = sys._getframe().f_code.co_name

    logger.debug(f"【{func_name}】节点启动，\n当前工作流状态：{format_state(state)}")

    try:
        pdf_path_obj, output_dir_obj = step_1_validate_paths(state)

        zip_url = step_2_upload_and_poll(pdf_path_obj, output_dir_obj)

        md_path = step_3_download_and_extract(zip_url, output_dir_obj, pdf_path_obj.stem)

        state["md_path"] = md_path
        logger.info(f"【{func_name}】MD文件生成成功，路径：{md_path}")

        try:
            with open(md_path, "r", encoding="utf-8") as f:
                state["md_content"] = f.read()
            logger.debug(f"【{func_name}】MD文件内容读取成功，内容长度：{len(state['md_content'])}字符")
        except Exception as e:
            logger.error(f"【{func_name}】读取MD文件内容失败：{str(e)}")

        logger.info(f"【{func_name}】节点执行完成，更新后工作流状态键：{list(state.keys())}")

    except Exception as e:
        logger.exception(f"【{func_name}】PDF转MD流程执行失败：{str(e)}")
        raise
    finally:
        logger.debug(f"【{func_name}】节点执行完成，\n更新后工作流状态：{format_state(state)}")

    return state


if __name__ == "__main__":

    logger.info("===== 开始node_pdf_to_md节点单元测试 =====")

    logger.info(f"测试获取根地址：{PROJECT_ROOT}")

    test_pdf_name = os.path.join("doc", "17805447902624130.pdf")
    test_pdf_path = os.path.join(PROJECT_ROOT, test_pdf_name)

    # 构造测试状态
    test_state = create_default_state(
        task_id="test_pdf2md_task_001",
        file_url="documents/17805447902624130.pdf",
        # pdf_path=test_pdf_path,
        local_dir=os.path.join(PROJECT_ROOT, "output")
    )

    node_pdf_to_md(test_state)

    logger.info("===== 结束node_pdf_to_md节点单元测试 =====")