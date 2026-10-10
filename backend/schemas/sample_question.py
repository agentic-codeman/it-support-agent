"""
示例问题相关的数据模型
对应数据库表 t_sample_question
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SampleQuestionVO(BaseModel):
    """示例问题视图对象"""
    id: str = Field(..., description="ID")
    title: Optional[str] = Field(None, description="展示标题")
    description: Optional[str] = Field(None, description="描述或提示")
    question: str = Field(..., description="示例问题内容")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class SampleQuestionCreateRequest(BaseModel):
    """创建示例问题请求"""
    title: Optional[str] = Field(None, description="展示标题", max_length=64)
    description: Optional[str] = Field(None, description="描述或提示", max_length=255)
    question: str = Field(..., description="示例问题内容", max_length=255)


class SampleQuestionUpdateRequest(BaseModel):
    """更新示例问题请求"""
    title: Optional[str] = Field(None, description="展示标题", max_length=64)
    description: Optional[str] = Field(None, description="描述或提示", max_length=255)
    question: Optional[str] = Field(None, description="示例问题内容", max_length=255)


class SampleQuestionPageRequest(BaseModel):
    """分页查询示例问题请求"""
    page_num: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="搜索关键词（标题/描述/问题）")


class SampleQuestionPageResponse(BaseModel):
    """分页查询示例问题响应"""
    list: List[SampleQuestionVO] = Field([], description="示例问题列表")
    total: int = Field(0, description="总数")
    page_num: int = Field(1, description="当前页码")
    page_size: int = Field(10, description="每页数量")
    total_pages: int = Field(0, description="总页数")
