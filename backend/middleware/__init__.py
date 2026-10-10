"""
中间件层
包含认证中间件和 JWT 工具
符合 Google Python 编码规范
"""
from backend.middleware.jwt_auth_middleware import JWTAuthMiddleware
from backend.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
)

__all__ = [
    "JWTAuthMiddleware",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
]
