"""
知识库 Pydantic Schemas
符合 Google Python 编码规范
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class KnowledgeBaseCreateRequest(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., min_length=1, max_length=128, description="知识库名称")
    collection_name: str = Field(..., min_length=1, max_length=64, description="Collection名称")
    embedding_model: str = Field(..., min_length=1, max_length=64, description="嵌入模型标识")


class KnowledgeBaseUpdateRequest(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=128, description="知识库名称")


class KnowledgeBaseVO(BaseModel):
    """知识库视图对象"""
    id: str = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    collection_name: str = Field(..., description="Collection名称")
    embedding_model: str = Field(..., description="嵌入模型标识")
    document_count: int = Field(0, description="文档数量")
    created_by: str = Field(..., description="创建人")
    updated_by: Optional[str] = Field(None, description="修改人")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="更新时间")


# ========== 分块管理相关 Schema ==========

class KnowledgeChunkVO(BaseModel):
    """分块视图对象"""
    id: str = Field(..., description="分块ID")
    kb_id: str = Field(..., description="知识库ID")
    doc_id: str = Field(..., description="文档ID")
    chunk_index: int = Field(..., description="分块索引")
    content: str = Field(..., description="分块内容")
    content_hash: Optional[str] = Field(None, description="内容哈希")
    char_count: Optional[int] = Field(None, description="字符数")
    token_count: Optional[int] = Field(None, description="Token数")
    enabled: int = Field(default=1, description="是否启用 0：禁用 1：启用")
    created_by: str = Field(..., description="创建人")
    updated_by: Optional[str] = Field(None, description="修改人")
    create_time: Optional[str] = Field(None, description="创建时间")
    update_time: Optional[str] = Field(None, description="更新时间")


class KnowledgeChunkPageRequest(BaseModel):
    """分块分页查询请求"""
    current: int = Field(default=1, ge=1, description="当前页码")
    size: int = Field(default=10, ge=1, le=500, description="每页数量")
    enabled: Optional[int] = Field(default=None, description="启用状态筛选 0：禁用 1：启用")


class KnowledgeChunkBatchRequest(BaseModel):
    """批量操作分块请求"""
    chunk_ids: Optional[list[str]] = Field(default=None, description="分块ID列表")
