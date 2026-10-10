import json
import os
import sys
from typing import List, Dict, Any, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

from backend.workflow.import_process.nodes.node_md_img import node_md_img

from backend.workflow.import_process.state import ImportGraphState
from backend.core.logger import logger

# 单个Chunk最大字符长度：超过则触发二次切分
DEFAULT_MAX_CONTENT_LENGTH = 2000
# 短Chunk合并阈值：同父标题的短Chunk会被合并，减少碎片化
MIN_CONTENT_LENGTH = 500
# Markdown 标题切分配置：按 1-6 级标题切分
HEADERS_TO_SPLIT_ON = [
    ("#", "一级标题"),
    ("##", "二级标题"),
    ("###", "三级标题"),
    ("####", "四级标题"),
    ("#####", "五级标题"),
    ("######", "六级标题"),
]


def step_1_get_inputs(state: ImportGraphState) -> Tuple[Any, str, int]:
    content = state["md_content"]
    if not content:
        logger.warning("状态字典中无有效MD内容，终止文档切分")
        return None, None, None

    content = content.replace("\r\n", "\n").replace("\r", "\n")
    file_title = os.path.splitext(state["file_name"])[0]
    max_len = DEFAULT_MAX_CONTENT_LENGTH

    logger.info(f"步骤1：输入数据加载完成，文件标题：{file_title}，最大Chunk长度：{max_len}")
    return content, file_title, max_len


def step_2_split_by_titles(content: str, file_title: str) -> Tuple[List[Dict[str, Any]], int, int]:
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=True,
    )
    docs = splitter.split_text(content)
    lines_count = len(content.split("\n"))

    sections = []
    title_count = 0
    for doc in docs:
        meta = doc.metadata or {}
        values = list(meta.values())
        leaf = values[-1] if values else ""
        ancestors = values[:-1]
        parent_title = " > ".join(ancestors) or None
        header = " > ".join(values) if values else ""
        body = doc.page_content
        title_count += len(meta)
        sections.append({
            "title": leaf,
            "content": f"{header}\n\n{body}" if header else body,
            "parent_title": parent_title,
            "file_title": file_title,
        })

    logger.info(f"步骤2：MD标题切分完成，识别到{title_count}个有效标题，原始文本共{lines_count}行")
    return sections, title_count, lines_count


def step_3_handle_no_title(content: str, sections: List[Dict[str, Any]], title_count: int, file_title: str) -> List[Dict[str, Any]]:
    if title_count == 0:
        logger.warning(f"步骤3：未识别到任何MD标题，将全文作为单个章节处理，文件：{file_title}")
        return [{"title": "无标题", "content": content, "parent_title": None, "file_title": file_title}]
    logger.debug(f"步骤3：检测到{title_count}个有效标题，无需兜底处理")
    return sections


def _split_long_section(section: Dict[str, Any], max_length: int = DEFAULT_MAX_CONTENT_LENGTH) -> List[Dict[str, Any]]:
    content = section.get("content", "") or ""
    if len(content) <= max_length:
        return [section]

    content = content.replace("\r\n", "\n").replace("\r", "\n")
    title = section.get("title", "") or ""
    parent_title = section.get("parent_title") or ""
    base_header = f"{parent_title} > {title}" if parent_title else title

    # 计算正文可用长度：预留头部（+2 为 "\n\n"）与序号空间（"-1"~"-999" 约 4 字符），保证最终 chunk <= max_length
    header_len = len(base_header) + 2 if base_header else 0
    available_len = max_length - header_len - 4
    if available_len <= 0:
        logger.warning(f"章节标题过长，无法切分：{title[:20]}...")
        return [section]

    body = content
    if base_header and body.lstrip().startswith(base_header):
        body = body[body.find(base_header) + len(base_header):].lstrip()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=available_len,
        chunk_overlap=0,           # 无重叠：按标题切分后语义完整，无需重叠
        # 分割符优先级：空行(段落)→换行→中文标点→英文标点→空格，最后硬拆
        separators=["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " "],
    )

    sub_sections = []
    for idx, chunk in enumerate(splitter.split_text(body), start=1):
        text = chunk.strip()
        if not text:
            continue
        sub_header = f"{base_header}-{idx}" if base_header else f"chunk-{idx}"
        full_text = (sub_header + "\n\n" + text).strip()
        sub_sections.append({
            "title": f"{title}-{idx}" if title else f"chunk-{idx}",
            "content": full_text,
            "parent_title": parent_title or None,
            "part": idx,
            "file_title": section.get("file_title"),
        })

    logger.debug(f"超长章节切分完成：{title} → 生成{len(sub_sections)}个子Chunk")
    return sub_sections


def _merge_short_sections(sections: List[Dict[str, Any]], min_length: int = MIN_CONTENT_LENGTH) -> List[Dict[str, Any]]:
    if not sections:
        logger.debug("待合并Chunk列表为空，直接返回")
        return []

    merged_sections = []
    current_chunk = None

    for sec in sections:
        if current_chunk is None:
            current_chunk = sec
            continue

        is_current_short = len(current_chunk["content"]) < min_length
        is_same_parent = (
            current_chunk.get("parent_title") is not None
            and current_chunk.get("parent_title") == sec.get("parent_title")
        )

        if is_current_short and is_same_parent:
            current_chunk["content"] += "\n\n" + sec["content"]
            if "part" in sec:
                current_chunk["part"] = sec["part"]
            logger.debug(f"合并短Chunk：{current_chunk.get('parent_title')} → 累计长度{len(current_chunk['content'])}")
        else:
            merged_sections.append(current_chunk)
            current_chunk = sec

    if current_chunk is not None:
        merged_sections.append(current_chunk)

    logger.debug(f"短Chunk合并完成：原{len(sections)}个 → 合并后{len(merged_sections)}个")
    return merged_sections


def step_4_refine_chunks(sections: List[Dict[str, Any]], max_len: int) -> List[Dict[str, Any]]:
    if not max_len or max_len <= 0:
        logger.warning(f"步骤4：Chunk最大长度配置无效（{max_len}），跳过精细化处理")
        return sections

    refined_split = []
    for sec in sections:
        refined_split.extend(_split_long_section(sec, max_len))
    logger.info(f"步骤4-1：超长章节切分完成，共生成{len(refined_split)}个初始子Chunk")

    final_sections = _merge_short_sections(refined_split)
    logger.info(f"步骤4-2：过短章节合并完成，最终得到{len(final_sections)}个Chunk")

    for sec in final_sections:
        if not isinstance(sec, dict):
            continue
        if "part" not in sec:
            sec["part"] = 0
    logger.debug(f"步骤4-3：元信息兜底完成，所有Chunk均包含part字段")

    return final_sections


def step_5_print_stats(lines_count: int, sections: List[Dict[str, Any]]) -> None:
    chunk_num = len(sections)
    # 输出核心统计信息：原始行数/最终Chunk数/首个Chunk预览
    logger.info("-" * 50 + " 文档切分统计信息 " + "-" * 50)
    logger.info(f"MD原始文本总行数：{lines_count}")
    logger.info(f"最终生成Chunk数量：{chunk_num}")
    if sections:
        first_title = sections[0].get("title", "无标题")
        logger.info(f"首个Chunk标题预览：{first_title}")
    logger.info("-" * 110)


def node_document_split(state: ImportGraphState) -> ImportGraphState:
    node_name = sys._getframe().f_code.co_name
    logger.info(f">>> 开始执行核心节点：【文档切分】{node_name}")

    try:
        content, file_title, max_len = step_1_get_inputs(state)
        if content is None:
            logger.info(f">>> 节点执行终止：{node_name}（无有效MD内容）")
            return state

        sections, title_count, lines_count = step_2_split_by_titles(content, file_title)

        sections = step_3_handle_no_title(content, sections, title_count, file_title)

        sections = step_4_refine_chunks(sections, max_len)

        step_5_print_stats(lines_count, sections)

        state["chunks"] = sections

        logger.info(f">>> 核心节点执行完成：【文档切分】{node_name}，已生成{len(sections)}个有效Chunk，结果已写入状态字典")

    except Exception as e:
        logger.exception(f">>> 核心节点执行失败：【文档切分】{node_name}，错误信息：{str(e)}")

    return state

if __name__ == '__main__':
    """
    单元测试：联合node_md_img（图片处理节点）进行集成测试
    测试条件：1.已配置.env（MinIO/大模型环境） 2.存在测试MD文件 3.能导入node_md_img
    测试流程：先运行图片处理→再运行文档切分，验证端到端流程
    """

    """本地测试入口：单独运行该文件时，执行MD图片处理全流程测试"""
    from backend.utils.path_util import PROJECT_ROOT
    #from app.import_process.agent.nodes.node_md_img import node_md_img

    logger.info(f"本地测试 - 项目根目录：{PROJECT_ROOT}")

    # 测试MD文件路径（需手动将测试文件放入对应目录）
    test_md_name = os.path.join(r"documents\894868045225267200", "17_使用Kafka.md")
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
            "md_content": "",
            "file_name": "17805447902624130.md",
            "local_dir":os.path.join(PROJECT_ROOT, "output"),
        }
        logger.info("开始本地测试 - MD图片处理全流程")
        # 执行核心处理流程
        result_state = node_md_img(test_state)
        logger.info(f"本地测试完成 - 处理结果状态：{result_state}")
        logger.info("\n=== 开始执行文档切分节点集成测试 ===")

        logger.info(">> 开始运行当前节点：node_document_split（文档切分）")
        final_state = node_document_split(result_state)
        final_chunks = final_state.get("chunks", [])
        logger.info(f"✅ 测试成功：最终生成{len(final_chunks)}个有效Chunk{final_chunks}")