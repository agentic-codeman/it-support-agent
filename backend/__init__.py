"""
后端模块包
提供用户认证、知识库管理等功能
符合 Google Python 编码规范
"""
from backend.db.database import engine, Base, SessionLocal, get_db
from backend.models.user import UserModel
from backend.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
)
from backend.controllers.auth import router as auth_router
from backend.middleware.jwt_auth_middleware import JWTAuthMiddleware
from backend.conf.app_config import AppSettings

__all__ = [
    # 数据库
    "engine",
    "Base",
    "SessionLocal",
    "get_db",
    # 模型
    "UserModel",
    # 工具
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
    # 路由
    "auth_router",
    # 中间件
    "JWTAuthMiddleware",
    # 配置
    "AppSettings",
]
