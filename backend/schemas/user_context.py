"""
用户上下文管理
支持异步上下文（asyncio）
"""
from typing import Optional
from contextvars import ContextVar
from dataclasses import dataclass

from backend.core.logger import logger


@dataclass
class LoginUser:
    """当前登录用户的上下文快照"""
    
    user_id: str  # 用户 ID
    username: str  # 用户名
    role: Optional[str] = None  # 角色（如 admin/user）
    avatar: Optional[str] = None  # 用户头像


# 使用 ContextVar 实现异步安全的线程局部存储
_user_context: ContextVar[Optional[LoginUser]] = ContextVar('user_context', default=None)


class UserContext:
    """
    用户上下文容器
    
    参考 Java 项目的 UserContext 实现，使用 ContextVar 替代 TransmittableThreadLocal
    以支持 Python 的异步编程模型（asyncio）
    """
    
    @classmethod
    def set(cls, user: LoginUser):
        """
        设置当前协程的用户上下文
        
        Args:
            user: 登录用户对象
        """
        _user_context.set(user)
        logger.debug(f"设置用户上下文: user_id={user.user_id}, username={user.username}")
    
    @classmethod
    def get(cls) -> Optional[LoginUser]:
        """
        获取当前协程的用户上下文
        
        Returns:
            LoginUser 或 None（如果未设置）
        """
        return _user_context.get()
    
    @classmethod
    def require_user(cls) -> LoginUser:
        """
        获取当前用户，若不存在则抛异常
        
        Returns:
            LoginUser: 当前登录用户
            
        Raises:
            Exception: 如果用户未登录
        """
        user = _user_context.get()
        if user is None:
            raise Exception("未获取到当前登录用户")
        return user
    
    @classmethod
    def get_user_id(cls) -> Optional[str]:
        """
        获取当前用户 ID（未登录返回 None）
        
        Returns:
            str 或 None
        """
        user = _user_context.get()
        return user.user_id if user else None
    
    @classmethod
    def get_username(cls) -> Optional[str]:
        """
        获取当前用户名（未登录返回 None）
        
        Returns:
            str 或 None
        """
        user = _user_context.get()
        return user.username if user else None
    
    @classmethod
    def get_role(cls) -> Optional[str]:
        """
        获取当前角色（未登录返回 None）
        
        Returns:
            str 或 None
        """
        user = _user_context.get()
        return user.role if user else None
    
    @classmethod
    def get_avatar(cls) -> Optional[str]:
        """
        获取当前头像（未登录返回 None）
        
        Returns:
            str 或 None
        """
        user = _user_context.get()
        return user.avatar if user else None
    
    @classmethod
    def clear(cls):
        """清理当前协程的用户上下文"""
        _user_context.set(None)
        logger.debug("已清理用户上下文")
    
    @classmethod
    def has_user(cls) -> bool:
        """
        判断是否已存在用户上下文
        
        Returns:
            bool: 是否有用户上下文
        """
        return _user_context.get() is not None


# 便捷函数（模块级别）
def get_current_user_id() -> Optional[str]:
    """获取当前用户 ID"""
    return UserContext.get_user_id()


def get_current_username() -> Optional[str]:
    """获取当前用户名"""
    return UserContext.get_username()


def is_authenticated() -> bool:
    """检查用户是否已认证"""
    return UserContext.has_user()
