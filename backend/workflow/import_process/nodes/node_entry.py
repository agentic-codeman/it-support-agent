import sys

from backend.workflow.import_process.state import ImportGraphState, create_default_state
from backend.core.logger import logger
from backend.utils.format_utils import format_state

def node_entry(state: ImportGraphState) -> ImportGraphState:

    func_name = sys._getframe().f_code.co_name

    logger.debug(f"【{func_name}】节点启动，\n当前工作流状态：{format_state(state)}")

    file_url = state.get("file_url", "")
    file_name = state.get("file_name", "")
    if not file_url:
        logger.error(f"【{file_url}】核心参数缺失：工作流状态中未配置local_file_path，文件路径为空")
        return state

    if file_name.endswith(".pdf"):
        logger.info(f"【{func_name}】文件类型校验通过：{file_name} → PDF格式，开启PDF解析流程")
        state["is_pdf_read_enabled"] = True
    elif file_name.endswith(".md"):
        logger.info(f"【{func_name}】文件类型校验通过：{file_name} → MD格式，开启MD解析流程")
        state["is_md_read_enabled"] = True
    else:
        logger.warning(f"【{func_name}】文件类型校验失败：{file_name} → 不支持的格式，仅支持.pdf/.md")

    logger.debug(f"【{func_name}】节点执行完成，\n更新后工作流状态：{format_state(state)}")

    return state


if __name__ == '__main__':
    logger.remove()
    logger.add(sys.stdout, level="DEBUG")

    # 单元测试：覆盖不支持类型、MD、PDF三种场景
    logger.info("===== 开始node_entry节点单元测试 =====")

    # 测试1: 不支持的TXT文件
    test_state1 = create_default_state(
        task_id="test_task_001",
        file_name="联想海豚用户手册.txt",
        file_url="documents/17805447612368487.txt"
    )
    node_entry(test_state1)

    # 测试2: MD文件
    test_state2 = create_default_state(
        task_id="test_task_002",
        file_name="小米用户手册.md",
        file_url="documents/17805447612368487.md"
    )
    node_entry(test_state2)

    # 测试3: PDF文件
    test_state3 = create_default_state(
        task_id="test_task_003",
        file_name="万用表的使用.pdf",
        file_url="documents/17805447612368487.pdf"
    )
    node_entry(test_state3)

    logger.info("===== 结束node_entry节点单元测试 =====")