"""
JWT 工具函数
符合 Google Python 编码规范
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict

from passlib.context import CryptContext

from backend.conf.jwt_config import jwt_config

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    密码加密

    Args:
        password: 原始密码

    Returns:
        str: 加密后的密码
    """
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 原始密码
        hashed_password: 加密后的密码

    Returns:
        bool: 密码是否匹配
    """
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌

    Args:
        data: 载荷数据
        expires_delta: 过期时间增量

    Returns:
        str: JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=jwt_config.access_token_expire_minutes)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, jwt_config.secret_key, algorithm=jwt_config.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    创建刷新令牌

    Args:
        data: 载荷数据

    Returns:
        str: JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=jwt_config.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, jwt_config.secret_key, algorithm=jwt_config.algorithm)
    return encoded_jwt


def decode_token(token: str) -> Dict:
    """
    解码 JWT token

    Args:
        token: JWT token

    Returns:
        dict: 解码后的载荷数据

    Raises:
        jwt.ExpiredSignatureError: token 过期
        jwt.InvalidTokenError: token 无效
    """
    payload = jwt.decode(token, jwt_config.secret_key, algorithms=[jwt_config.algorithm])
    return payload


def verify_token(token: str) -> bool:
    """
    验证 token 是否有效

    Args:
        token: JWT token

    Returns:
        bool: 是否有效
    """
    try:
        decode_token(token)
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
]
