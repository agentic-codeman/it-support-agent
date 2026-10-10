import os
import re
import base64
import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple
from collections import deque

import requests

from backend.workflow.import_process.state import ImportGraphState

from backend.conf.rustfs_config import rustfs_config
from backend.client.rustfs_client import get_restfs_client
from backend.utils.path_util import PROJECT_ROOT

from backend.client.llm_factory import get_vl_model
from langchain.messages import HumanMessage
from langchain_core.exceptions import LangChainException
from backend.core.logger import logger
from backend.utils.rate_limit_utils import apply_api_rate_limit
from backend.services.prompt_loader import load_prompt

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

# 规则：![任意描述](http(s)://...)，URL 截取到首个空白或右括号为止
IMAGE_URL_PATTERN = re.compile(r"!\[[^\]]*\]\((?P<url>https?://[^)\s]+)\)")


def _ensure_md_local(state: ImportGraphState) -> str:
    file_url = state.get("file_url", "").strip()
    bucket_name = state.get("bucket_name", "").strip()
    if not file_url or not bucket_name:
        return ""

    restfs_client = get_restfs_client()
    if not restfs_client.object_exists(bucket_name, file_url):
        raise FileNotFoundError(f"RestFS 中 MD 对象不存在，bucket：{bucket_name}，key：{file_url}")

    local_path = Path(os.path.join(PROJECT_ROOT, file_url))
    local_path.parent.mkdir(parents=True, exist_ok=True)
    restfs_client.download_file(bucket_name, file_url, str(local_path))
    state["md_path"] = str(local_path.absolute())
    logger.info(f"MD 文件已从 RestFS 下载到本地：{local_path.absolute()}")
    return state["md_path"]


def step_1_get_content(state: ImportGraphState) -> Tuple[str, Path, Path]:
    md_file_path = state["md_path"]
    if not md_file_path:
        md_file_path = _ensure_md_local(state)
    if not md_file_path:
        raise FileNotFoundError(f"全局状态中无有效MD文件路径：{state['md_path']}")

    path_obj = Path(md_file_path)
    if not state["md_content"]:
        with open(path_obj, "r", encoding="utf-8") as f:
            md_content = f.read()
        logger.debug(f"从文件读取MD内容完成，文件大小：{len(md_content)} 字符")
    else:
        md_content = state["md_content"]
        logger.debug(f"从全局状态获取MD内容完成，内容大小：{len(md_content)} 字符")

    images_dir = path_obj.parent / "images"
    return md_content, path_obj, images_dir


def is_supported_image(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS


def find_image_in_md(md_content: str, image_filename: str, context_len: int = 100) -> List[Tuple[str, str]]:
    pattern = re.compile(r"!\[.*?\]\(.*?" + re.escape(image_filename) + r".*?\)")
    results = []

    for m in pattern.finditer(md_content):
        start, end = m.span()
        pre_text = md_content[max(0, start - context_len):start]
        post_text = md_content[end:min(len(md_content), end + context_len)]
        # 打印图片上下文，便于调试
        logger.debug(f"图片[{image_filename}]匹配到引用，上文：{pre_text.strip()}")
        logger.debug(f"图片[{image_filename}]匹配到引用，下文：{post_text.strip()}")
        results.append((pre_text, post_text))
    if not results:
        logger.debug(f"MD内容中未找到图片[{image_filename}]的引用")
    return results


def step_2_scan_images(md_content: str, images_dir: Path) -> List[Tuple[str, str, Tuple[str, str]]]:
    targets = []
    for image_file in os.listdir(images_dir):
        if not is_supported_image(image_file):
            logger.debug(f"图片格式不支持，跳过：{image_file}")
            continue
        img_path = str(images_dir / image_file)
        context_list = find_image_in_md(md_content, image_file)
        if not context_list:
            logger.warning(f"图片未在MD中引用，跳过处理：{image_file}")
            continue
        targets.append((image_file, img_path, context_list[0]))
        logger.info(f"图片加入待处理列表：{image_file}")
    logger.info(f"图片扫描完成，共筛选出待处理图片：{len(targets)} 张")
    return targets


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as img_file:
        base64_str = base64.b64encode(img_file.read()).decode("utf-8")
    logger.debug(f"图片Base64编码完成，文件：{image_path}，编码后长度：{len(base64_str)}")
    return base64_str


def summarize_image(image_path: str, root_folder: str, image_content: Tuple[str, str]) -> str:
    base64_image = encode_image_to_base64(image_path)
    try:
        lvm_client = get_vl_model()

        prompt_text = load_prompt(
            name="image_summary",
            root_folder=root_folder,
            image_content=image_content
        )

        messages = [
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            )
        ]

        response = lvm_client.invoke(messages)

        summary = response.content.strip().replace("\n", "")
        logger.info(f"图片摘要生成成功：{image_path}，摘要：{summary}")
        return summary

    except LangChainException as e:
        logger.error(f"图片摘要生成失败（LangChain框架异常）：{image_path}，错误信息：{str(e)}")
        return "图片描述"
    except Exception as e:
        logger.error(f"图片摘要生成失败（系统异常）：{image_path}，错误信息：{str(e)}")
        return "图片描述"


def step_3_generate_summaries(doc_stem: str, targets: List[Tuple[str, str, Tuple[str, str]]],
                              requests_per_minute: int = 9) -> Dict[str, str]:
    summaries = {}
    request_times = deque()

    for img_file, image_path, context in targets:
        apply_api_rate_limit(request_times, requests_per_minute, window_seconds=60)
        logger.debug(f"开始生成图片摘要：{image_path}")
        summaries[img_file] = summarize_image(image_path, root_folder=doc_stem, image_content=context)

    logger.info(f"图片摘要批量生成完成，共处理{len(summaries)}张图片")
    return summaries


def clean_rustfs_directory(restfs_client, bucket_name: str, prefix: str) -> None:
    try:
        # S3 bucket 名称规范化
        safe_bucket = bucket_name.replace('_', '-').lower()
        # 列出指定前缀下的所有对象
        response = restfs_client.s3_client.list_objects_v2(
            Bucket=safe_bucket,
            Prefix=prefix,
        )
        objects_to_delete = response.get('Contents', [])
        # 构造删除对象列表
        delete_list = [{'Key': obj['Key']} for obj in objects_to_delete]

        if delete_list:
            logger.info(f"开始清理RestFS旧文件，待删除文件数：{len(delete_list)}，目录：{prefix}")
            # 批量删除对象
            restfs_client.s3_client.delete_objects(
                Bucket=safe_bucket,
                Delete={'Objects': delete_list},
            )
        else:
            logger.debug(f"RestFS目录无旧文件，无需清理：{prefix}")
    except Exception as e:
        logger.error(f"RestFS目录清理失败：{prefix}，错误信息：{str(e)}")


def upload_images_batch(restfs_client, bucket_name: str, upload_dir: str, targets: List[Tuple[str, str, Tuple[str, str]]]) -> Dict[
    str, str]:
    urls = {}
    for img_file, img_path, _ in targets:
        # 构造RestFS对象名称
        object_name = f"{upload_dir}/{img_file}"
        logger.debug(f"构造RestFS对象名称完成：{object_name}")
        # 上传单张图片并获取URL
        if img_url := upload_to_rustfs(restfs_client, bucket_name, img_path, object_name):
            urls[img_file] = img_url
    logger.info(f"图片批量上传完成，成功上传{len(urls)}/{len(targets)}张图片")
    return urls


def upload_to_rustfs(restfs_client, bucket_name: str, local_path: str, object_name: str) -> str | None:
    try:
        logger.info(f"开始上传图片至RestFS：本地路径={local_path}，对象名={object_name}")
        img_url = restfs_client.upload_file(bucket_name, local_path, object_name)
        logger.info(f"图片上传成功，访问URL：{img_url}")
        return img_url
    except Exception as e:
        logger.error(f"图片上传RestFS失败：{local_path}，错误信息：{str(e)}")
        return None


def merge_summary_and_url(summaries: Dict[str, str], urls: Dict[str, str]) -> Dict[str, Tuple[str, str]]:
    image_info = {}
    # 遍历摘要字典，仅保留有对应URL的图片
    for image_file, summary in summaries.items():
        if url := urls.get(image_file):
            image_info[image_file] = (summary, url)
    logger.info(f"图片摘要与URL合并完成，有效图片信息{len(image_info)}条")
    return image_info


def process_md_file(md_content: str, image_info: Dict[str, Tuple[str, str]]) -> str:
    for img_filename, (summary, new_url) in image_info.items():
        # 正则匹配MD图片标签，忽略大小写，兼容不同路径写法
        # 正则规则：![任意描述](任意路径+图片文件名+任意后缀)
        pattern = re.compile(
            r"!\[.*?\]\(.*?" + re.escape(img_filename) + r".*?\)",
            re.IGNORECASE
        )
        md_content = pattern.sub( f"![{summary}]({new_url})", md_content)
        logger.debug(f"完成MD图片引用替换：{img_filename} → {new_url}")

    logger.info(f"MD文件图片引用替换完成，共替换{len(image_info)}处图片引用")
    logger.debug(f"替换后MD内容：{md_content[:500]}..." if len(md_content) > 500 else f"替换后MD内容：{md_content}")
    return md_content


def step_4_upload_and_replace(restfs_client, bucket_name: str, doc_stem: str,
                              targets: List[Tuple[str, str, Tuple[str, str]]],
                              summaries: Dict[str, str], md_content: str) -> str:
    img_dir = rustfs_config.img_dir
    upload_dir = f"{img_dir}/{doc_stem}".replace(" ", "")

    clean_rustfs_directory(restfs_client, bucket_name, upload_dir)
    urls = upload_images_batch(restfs_client, bucket_name, upload_dir, targets)
    image_info = merge_summary_and_url(summaries, urls)
    if image_info:
        md_content = process_md_file(md_content, image_info)

    return md_content


def extract_image_urls(md_content: str, context_len: int = 100) -> List[Tuple[str, Tuple[str, str]]]:
    results = []
    for m in IMAGE_URL_PATTERN.finditer(md_content):
        url = m.group("url").strip()
        start, end = m.span()
        pre_text = md_content[max(0, start - context_len):start]
        post_text = md_content[end:min(len(md_content), end + context_len)]
        logger.debug(f"图片URL[{url}]匹配到引用，上文：{pre_text.strip()}")
        logger.debug(f"图片URL[{url}]匹配到引用，下文：{post_text.strip()}")
        results.append((url, (pre_text, post_text)))
    if not results:
        logger.debug("MD内容中未找到外部图片URL引用")
    return results


def guess_image_extension(url: str) -> str:
    path_part = url.split("?", 1)[0]
    ext = os.path.splitext(path_part)[1].lower()
    return ext if ext in IMAGE_EXTENSIONS else ".jpg"


def download_image_to_local(url: str, local_path: str) -> None:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(resp.content)
    logger.debug(f"远程图片下载完成：{url} → {local_path}")


def replace_image_url(md_content: str, url: str, summary: str, new_url: str) -> str:
    pattern = re.compile(r"!\[[^\]]*\]\(" + re.escape(url) + r"\)")
    return pattern.sub(f"![{summary}]({new_url})", md_content)


def process_remote_image_urls(restfs_client, bucket_name: str, doc_stem: str,
                              md_content: str, requests_per_minute: int = 9) -> str:
    image_urls = extract_image_urls(md_content)
    if not image_urls:
        logger.info("MD中未发现外部图片URL，无需处理")
        return md_content

    upload_dir = f"{rustfs_config.img_dir}/{doc_stem}".replace(" ", "")

    clean_rustfs_directory(restfs_client, bucket_name, upload_dir)

    tmp_dir = Path(tempfile.mkdtemp(prefix="md_img_"))
    request_times = deque()
    processed = 0

    try:
        for url, context in image_urls:
            local_name = hashlib.md5(url.encode("utf-8")).hexdigest() + guess_image_extension(url)
            local_path = str(tmp_dir / local_name)

            try:
                download_image_to_local(url, local_path)
            except Exception as e:
                logger.error(f"下载远程图片失败，跳过：{url}，错误信息：{str(e)}")
                continue

            apply_api_rate_limit(request_times, requests_per_minute, window_seconds=60)
            summary = summarize_image(local_path, root_folder=doc_stem, image_content=context)

            object_name = f"{upload_dir}/{local_name}"
            new_url = upload_to_rustfs(restfs_client, bucket_name, local_path, object_name)
            if not new_url:
                continue

            md_content = replace_image_url(md_content, url, summary, new_url)
            processed += 1
            logger.info(f"远程图片处理完成：{url} → {new_url}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    logger.info(f"远程图片处理结束，共替换 {processed}/{len(image_urls)} 张")
    return md_content


def step_5_backup_new_md_file(origin_md_path: str, md_content: str) -> str:
    new_md_file_name = os.path.splitext(origin_md_path)[0] + "_new.md"

    # 写入新MD内容（覆盖写入，若文件已存在则更新）
    with open(new_md_file_name, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"处理后MD文件已保存，新文件路径：{new_md_file_name}")
    return new_md_file_name


def node_md_img(state: ImportGraphState) -> ImportGraphState:

    md_content, path_obj, images_dir = step_1_get_content(state)
    state["md_content"] = md_content

    restfs_client = get_restfs_client()
    bucket_name = state.get("bucket_name", "")

    if images_dir.exists():
        targets = step_2_scan_images(md_content, images_dir)
        if not targets:
            logger.info("未检测到MD中引用的支持格式图片，跳过后续处理")
            return state
        summaries = step_3_generate_summaries(path_obj.stem, targets)
        new_md_content = step_4_upload_and_replace(
            restfs_client, bucket_name, path_obj.stem, targets, summaries, md_content
        )
    else:
        new_md_content = process_remote_image_urls(
            restfs_client, bucket_name, path_obj.stem, md_content
        )

    if new_md_content == md_content:
        logger.info("未检测到需要处理的图片，跳过后续处理")
        return state

    state["md_content"] = new_md_content
    new_md_file_name = step_5_backup_new_md_file(state['md_path'], new_md_content)
    state["md_path"] = new_md_file_name
    logger.info(f"MD图片处理完成，新文件已保存：{new_md_file_name}")

    return state

if __name__ == "__main__":
    """本地测试入口：单独运行该文件时，执行MD图片处理全流程测试"""
    from backend.utils.path_util import PROJECT_ROOT
    logger.info(f"本地测试 - 项目根目录：{PROJECT_ROOT}")

    # 测试MD文件路径（需手动将测试文件放入对应目录）
    test_md_name = os.path.join(r"output\17805447902624129", "17805447902624129.md")
    test_md_path = os.path.join(PROJECT_ROOT, test_md_name)

    # 校验测试文件是否存在
    if not os.path.exists(test_md_path):
        logger.error(f"本地测试 - 测试文件不存在：{test_md_path}")
        logger.info("请检查文件路径，或手动将测试MD文件放入项目根目录的output目录下")
    else:
        # 构造测试状态对象，模拟流程入参
        test_state = {
            "md_path": test_md_path,
            "task_id": "test_task_123456",
            "md_content": ""
        }
        logger.info("开始本地测试 - MD图片处理全流程")
        # 执行核心处理流程
        result_state = node_md_img(test_state)
        logger.info(f"本地测试完成 - 处理结果状态：{result_state}")