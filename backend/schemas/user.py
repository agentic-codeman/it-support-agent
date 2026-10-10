"""
用户数据验证模型
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime


class UserCreateRequest(BaseModel):
    """用户注册请求模型"""
    username: str = Field(..., min_length=3, max_length=64, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    role: Optional[str] = Field(default="user", description="角色：admin/user")


class UserLoginRequest(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenRefreshRequest(BaseModel):
    """Token 刷新请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class UserVO(BaseModel):
    """用户视图对象"""
    id: str
    username: str
    role: str
    avatar: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    
    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[datetime], _info):
        if value is None:
            return None
        return value.strftime("%Y-%m-%d %H:%M:%S")
    
    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[datetime], _info):
        if value is None:
            return None
        return value.strftime("%Y-%m-%d %H:%M:%S")
    
    model_config = {"from_attributes": True}


class UserPageRequest(BaseModel):
    """用户分页查询请求模型"""
    page_num: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(default=None, description="搜索关键词（用户名/角色）")


class UserCreateRequestV2(BaseModel):
    """用户创建请求模型（管理端）"""
    username: str = Field(..., min_length=3, max_length=64, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    role: str = Field(default="user", description="角色：admin/user")
    avatar: Optional[str] = Field(default=None, description="头像URL")


class UserUpdateRequest(BaseModel):
    """用户更新请求模型"""
    username: Optional[str] = Field(default=None, min_length=3, max_length=64, description="用户名")
    password: Optional[str] = Field(default=None, min_length=6, max_length=128, description="新密码")
    role: Optional[str] = Field(default=None, description="角色：admin/user")
    avatar: Optional[str] = Field(default=None, description="头像URL")
