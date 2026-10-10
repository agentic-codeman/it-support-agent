"""
用户上下文清理中间件
在请求结束后清理用户上下文，防止内存泄漏
"""
from backend.schemas.user_context import UserContext


class UserContextCleanupMiddleware:
    """
    用户上下文清理中间件
    
    在每个请求结束后清理 UserContext，确保不会泄露到其他请求
    """
    
    def __init__(self, app):
        """
        初始化中间件
        
        Args:
            app: FastAPI 应用实例
        """
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """处理请求"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        try:
            # 执行请求
            await self.app(scope, receive, send)
        finally:
            # 无论请求成功或失败，都清理用户上下文
            if UserContext.has_user():
                UserContext.clear()
