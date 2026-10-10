"""
文档管理 Pydantic Schemas
符合 Google Python 编码规范
"""
from pydantic import BaseModel, Field
from typing import Optional
from backend.schemas.enums.document_status import DocumentStatus


class KnowledgeDocumentVO(BaseModel):
    """文档视图对象"""
    id: str
    kb_id: str
    file_name: str
    title: Optional[str] = None
    file_type: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    chunk_status: Optional[str] = DocumentStatus.PENDING.value
    chunk_count: Optional[int] = 0
    chunk_fail_reason: Optional[str] = None
    enabled: int = 1
    created_by: str
    updated_by: Optional[str] = None
    create_time: Optional[str] = None
    update_time: Optional[str] = None


class KnowledgeDocumentUpdateRequest(BaseModel):
    """文档更新请求"""
    doc_name: Optional[str] = Field(default=None, description="文档名称")
    title: Optional[str] = Field(default=None, description="文档标题")


class KnowledgeDocumentPageRequest(BaseModel):
    """文档分页查询请求"""
    current: int = Field(default=1, ge=1, description="当前页码")
    size: int = Field(default=10, ge=1, le=500, description="每页数量")
    keyword: Optional[str] = Field(default=None, description="文档名称关键字")
    chunk_status: Optional[str] = Field(default=None, description="分块状态筛选")
