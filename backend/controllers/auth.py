"""
认证控制器
处理用户注册、登录等认证相关 API
符合 Google Python 编码规范
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.models.user import UserModel
from backend.schemas.user import UserCreateRequest, UserLoginRequest, TokenRefreshRequest, UserVO
from backend.services import user_service
from backend.utils.results import Results
from backend.utils.result import Result
from backend.utils.exceptions import AbstractException

from backend.core.logger import logger

router = APIRouter(prefix="/auth", tags=["认证管理"])


@router.post("/register", response_model=Result[UserVO])
async def register(
    request: UserCreateRequest,
    db: Session = Depends(get_db)
):
    """用户注册"""
    try:
        user = user_service.register(db, request)
        return Results.success_with_data(UserVO.model_validate(user))
    except AbstractException as e:
        logger.error(f"用户注册失败: {e.error_message}")
        return Results.failure_from_exception(e)
    except Exception as e:
        logger.exception(f"用户注册失败: {str(e)}")
        return Results.failure_with_code("50000", str(e))


@router.post("/login", response_model=Result[dict])
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        result = user_service.login(db, request.username, request.password)
        return Results.success_with_data(result)
    except AbstractException as e:
        logger.error(f"用户登录失败: {e.error_message}")
        return Results.failure_from_exception(e)
    except Exception as e:
        logger.exception(f"用户登录失败: {str(e)}")
        return Results.failure_with_code("50000", str(e))


@router.get("/me", response_model=Result[UserVO])
async def get_current_user_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    # 从 Authorization header 中提取 token
    authorization = request.headers.get("Authorization")
    if not authorization:
        return Results.failure_with_code("40100", "未提供认证令牌")
    
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return Results.failure_with_code("40100", "无效的认证格式")
    
    # 验证 token
    try:
        from backend.core.security import decode_token
        payload = decode_token(token)
        
        if payload.get("type") != "access":
            return Results.failure_with_code("40100", "无效的令牌类型")
        
        # 从数据库中查询用户
        username = payload.get("sub")
        user = db.query(UserModel).filter(
            UserModel.username == username,
            UserModel.deleted == 0
        ).first()
        
        if not user:
            return Results.failure_with_code("40100", "用户不存在")
        
        return Results.success_with_data(UserVO.model_validate(user))
    except Exception as e:
        return Results.failure_with_code("40100", f"Token 验证失败: {str(e)}")


@router.post("/refresh", response_model=Result[dict])
async def refresh_token(
    request: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    try:
        result = user_service.refresh_access_token(db, request.refresh_token)
        return Results.success_with_data(result)
    except AbstractException as e:
        logger.error(f"刷新令牌失败: {e.error_message}")
        return Results.failure_from_exception(e)
    except Exception as e:
        logger.exception(f"刷新令牌失败: {str(e)}")
        return Results.failure_with_code("50000", str(e))


@router.post("/logout", response_model=Result[dict])
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """用户登出"""
    try:
        # 从 Authorization header 中提取 token
        authorization = request.headers.get("Authorization")
        if not authorization:
            return Results.failure_with_code("40100", "未提供认证令牌")
        
        scheme, _, access_token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not access_token:
            return Results.failure_with_code("40100", "无效的认证格式")
        
        # 尝试从请求体中获取 refresh_token（可选）
        refresh_token = None
        try:
            body = await request.json()
            refresh_token = body.get("refresh_token")
        except:
            pass
        
        # 调用登出服务
        result = user_service.logout(db, access_token, refresh_token)
        return Results.success_with_data(result)
        
    except AbstractException as e:
        logger.error(f"登出失败: {e.error_message}")
        return Results.failure_from_exception(e)
    except Exception as e:
        logger.exception(f"登出失败: {str(e)}")
        return Results.failure_with_code("50000", str(e))
