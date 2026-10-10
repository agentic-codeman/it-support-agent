"""
Query Term Mapping (关键词映射) Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class QueryTermMappingCreateRequest(BaseModel):
    """创建关键词映射请求"""
    domain: Optional[str] = Field(default=None, max_length=100, description="业务域/系统标识")
    source_term: str = Field(..., min_length=1, max_length=500, description="用户原始短语")
    target_term: str = Field(..., min_length=1, max_length=500, description="归一化后的目标短语")
    match_type: int = Field(default=1, description="匹配类型：1-精确匹配, 2-前缀匹配, 3-正则匹配, 4-整词匹配")
    priority: int = Field(default=0, description="优先级，数值越大优先级越高")
    enabled: bool = Field(default=True, description="是否生效")
    remark: Optional[str] = Field(default=None, description="备注")


class QueryTermMappingUpdateRequest(BaseModel):
    """更新关键词映射请求"""
    domain: Optional[str] = Field(default=None, max_length=100, description="业务域/系统标识")
    source_term: Optional[str] = Field(default=None, min_length=1, max_length=500, description="用户原始短语")
    target_term: Optional[str] = Field(default=None, min_length=1, max_length=500, description="归一化后的目标短语")
    match_type: Optional[int] = Field(default=None, description="匹配类型：1-精确匹配, 2-前缀匹配, 3-正则匹配, 4-整词匹配")
    priority: Optional[int] = Field(default=None, description="优先级")
    enabled: Optional[bool] = Field(default=None, description="是否生效")
    remark: Optional[str] = Field(default=None, description="备注")


class QueryTermMappingVO(BaseModel):
    """关键词映射视图对象"""
    id: str = Field(..., description="主键ID")
    domain: Optional[str] = Field(None, description="业务域/系统标识")
    source_term: str = Field(..., description="用户原始短语")
    target_term: str = Field(..., description="归一化后的目标短语")
    match_type: int = Field(..., description="匹配类型")
    priority: int = Field(..., description="优先级")
    enabled: bool = Field(..., description="是否生效")
    remark: Optional[str] = Field(None, description="备注")
    create_by: Optional[str] = Field(None, description="创建人")
    update_by: Optional[str] = Field(None, description="更新人")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="更新时间")
