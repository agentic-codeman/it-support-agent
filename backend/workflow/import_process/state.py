from typing import TypedDict
import copy
from backend.core.logger import logger

class ImportGraphState(TypedDict):
    is_md_read_enabled: bool   # 是否启用 Markdown 读取路径
    is_pdf_read_enabled: bool  # 是否启用 PDF 读取路径
    local_dir: str        # 当前工作目录或输出目录
    md_path: str          # Markdown 文件路径 (转换后或直接输入的)
    file_url: str         # 文件存储路径
    file_name: str        # 文件名称
    doc_id: str           # 文档id
    kb_id: str            # 知识库ID
    collection_name: str  # 集合名称
    bucket_name: str      # RustFS桶名
    user_name:str         # 用户名
    md_content: str       # Markdown 的全文内容
    chunks: list          # 切片后的文本列表，包含 metadata

graph_default_state: ImportGraphState = {
    "is_pdf_read_enabled": False,
    "is_md_read_enabled": False,
    "local_dir": "",
    "md_path": "",
    "md_content": "",
    "chunks": []
}

def create_default_state(**overrides) -> ImportGraphState:
    state = copy.deepcopy(graph_default_state)
    state.update(overrides)
    return state

def get_default_state() -> ImportGraphState:
    return copy.deepcopy(graph_default_state)


if __name__ == "__main__":
    state = create_default_state(file_name="万用表RS-12的使用.pdf")
    logger.info(state)
