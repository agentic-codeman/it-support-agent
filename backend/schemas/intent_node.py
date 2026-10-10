"""
意图节点 Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class IntentNodeTreeResponse(BaseModel):
    """意图树节点响应（用于树形展示）"""
    id: str = Field(..., description="节点ID")
    intent_code: str = Field(..., description="意图标识")
    name: str = Field(..., description="节点名称")
    level: int = Field(..., description="层级 0:DOMAIN 1:CATEGORY 2:TOPIC")
    parent_code: Optional[str] = Field(None, description="父节点标识")
    description: Optional[str] = Field(None, description="语义描述")
    examples: Optional[str] = Field(None, description="示例问题（JSON数组字符串）")
    collection_name: Optional[str] = Field(None, description="关联的Collection名称")
    kind: Optional[int] = Field(None, description="类型 0:KB 1:SYSTEM")
    children: Optional[List['IntentNodeTreeResponse']] = Field(None, description="子节点列表")


class IntentNodeCreateRequest(BaseModel):
    """创建意图节点请求"""
    kb_id: Optional[str] = Field(None, description="知识库ID")
    intent_code: str = Field(..., min_length=1, max_length=64, description="意图标识（字母、数字、-和_）")
    name: str = Field(..., min_length=1, max_length=64, description="节点名称")
    level: int = Field(..., ge=0, le=2, description="层级 0:DOMAIN 1:CATEGORY 2:TOPIC")
    parent_code: Optional[str] = Field(None, description="父节点标识")
    description: Optional[str] = Field(None, max_length=512, description="语义描述")
    examples: Optional[List[str]] = Field(None, description="示例问题列表")
    kind: Optional[int] = Field(0, ge=0, le=1, description="类型 0:KB 1:SYSTEM")


class IntentNodeUpdateRequest(BaseModel):
    """更新意图节点请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="节点名称")
    level: Optional[int] = Field(None, ge=0, le=2, description="层级")
    parent_code: Optional[str] = Field(None, description="父节点标识")
    description: Optional[str] = Field(None, max_length=512, description="语义描述")
    examples: Optional[List[str]] = Field(None, description="示例问题列表")
    collection_name: Optional[str] = Field(None, max_length=128, description="关联的Collection名称")
    kind: Optional[int] = Field(None, ge=0, le=1, description="类型")


class BatchOperationRequest(BaseModel):
    """批量操作请求"""
    ids: List[str] = Field(..., min_items=1, description="节点ID列表")


# 解决循环引用
IntentNodeTreeResponse.model_rebuild()
