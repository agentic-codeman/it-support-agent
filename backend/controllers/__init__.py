"""
API 控制器层
包含所有 FastAPI 路由定义
符合 Google Python 编码规范
"""
from backend.controllers.auth import router as auth_router

__all__ = [
    "auth_router",
]
