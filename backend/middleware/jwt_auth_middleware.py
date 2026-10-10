"""
JWT 认证中间件
符合 Google Python 编码规范
"""
from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
import jwt

from backend.core.security import decode_token
from backend.models.user import UserModel
from backend.db.database import get_db
from backend.schemas.user_context import UserContext, LoginUser
from sqlalchemy.orm import Session


class JWTAuthMiddleware:
    """JWT 认证中间件"""

    def __init__(self, app, exclude_paths: list = None):
        """
        初始化中间件
        
        Args:
            app: FastAPI 应用实例
            exclude_paths: 需要排除的路径列表（不需要认证的路径）
        """
        self.app = app
        self.exclude_paths = exclude_paths or [
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/refresh",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/health"
        ]

    async def __call__(self, scope, receive, send):
        """处理请求"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        path = request.url.path
        method = request.method

        # OPTIONS 请求（CORS 预检）由外层 CORSMiddleware 处理，此处直接放行
        if method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        # 检查是否需要排除
        if self._should_exclude(path):
            await self.app(scope, receive, send)
            return

        # 验证 token
        try:
            token = self._extract_token(request)
            if not token:
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "code": "40100",
                        "message": "未提供认证令牌",
                        "data": None
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
                await response(scope, receive, send)
                return

            # 验证 token 有效性
            payload = decode_token(token)
            
            # 检查 token 是否在黑名单中
            from backend.db.database import SessionLocal
            from backend.services.token_blacklist_service import TokenBlacklistService
            
            db = SessionLocal()
            try:
                if TokenBlacklistService.is_blacklisted(db, token):
                    response = JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "code": "40102",
                            "message": "令牌已被撤销，请重新登录",
                            "data": None
                        },
                        headers={"WWW-Authenticate": "Bearer"}
                    )
                    await response(scope, receive, send)
                    return
            finally:
                db.close()
            
            # 检查 token 类型
            if payload.get("type") != "access":
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "code": "40100",
                        "message": "无效的令牌类型",
                        "data": None
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
                await response(scope, receive, send)
                return

            # 从数据库中查询用户信息
            username = payload.get("sub")
            user_id = payload.get("user_id")
            
            # 设置用户上下文
            if username:
                login_user = LoginUser(
                    user_id=user_id or username,
                    username=username,
                    role=payload.get("role", "user"),
                    avatar=payload.get("avatar")
                )
                UserContext.set(login_user)
            
            request.state.user = payload
            await self.app(scope, receive, send)

        except jwt.ExpiredSignatureError:
            UserContext.clear()
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "code": "40101",
                    "message": "认证令牌已过期，请重新登录",
                    "data": None
                }
            )
            await response(scope, receive, send)
        except Exception as e:
            UserContext.clear()
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "code": "40100",
                    "message": f"认证失败：{str(e)}",
                    "data": None
                }
            )
            await response(scope, receive, send)

    def _should_exclude(self, path: str) -> bool:
        """检查路径是否应该排除"""
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False

    def _extract_token(self, request: Request) -> Optional[str]:
        """从请求头中提取 token"""
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            return None

        return token


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> UserModel:
    """获取当前用户（依赖注入）"""
    user_payload = getattr(request.state, 'user', None)
    
    if not user_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    username = user_payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = db.query(UserModel).filter(
        UserModel.username == username,
        UserModel.deleted == 0
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_current_username(
    request: Request
) -> str:
    """获取当前用户名（依赖注入）"""
    user_payload = getattr(request.state, 'user', None)
    
    if not user_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    username = user_payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return username


async def require_admin(
    request: Request,
    db: Session = Depends(get_db)
) -> UserModel:
    """要求管理员权限（依赖注入）"""
    user = await get_current_user(request, db)
    
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user
