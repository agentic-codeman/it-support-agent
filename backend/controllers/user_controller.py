"""
用户管理控制器
提供用户 CRUD API 接口符合 Google Python 编码规范
"""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.models.user import UserModel
from backend.schemas.user import (
    UserVO, 
    UserPageRequest, 
    UserCreateRequestV2, 
    UserUpdateRequest
)
from backend.services import user_service
from backend.utils.results import Results
from backend.utils.result import Result
from backend.utils.exceptions import AbstractException
from backend.middleware.jwt_auth_middleware import require_admin, get_current_user

from backend.core.logger import logger

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=Result[UserVO])
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
):
    """获取当前登录用户信息"""
    return Results.success_with_data(UserVO.model_validate(current_user))


@router.get("", response_model=Result[dict])
async def page_query_users(
    page_num: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """分页查询用户列表（仅管理员）"""
    try:
        # 构建分页请求对象
        page_request = UserPageRequest(
            page_num=page_num,
            page_size=page_size,
            keyword=keyword
        )
        
        result = user_service.page_query(db, page_request)
        return Results.success_with_data(result)
    except AbstractException as e:
        logger.error(f"查询用户列表失败: {e.error_message}")
        return Results.failure_from_exception(e)
    except Exception as e:
        logger.exception(f"查询用户列表失败: {str(e)}")
        return Results.failure_with_code("50000", str(e))


@router.post("", response_model=Result[UserVO])
async def create_user(
    request: UserCreateRequestV2,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """创建用户（仅管理员）"""
    try:
        user = user_service.create_user(db, request)
        return Results.success_with_data(UserVO.model_validate(user))
    except AbstractException as e:
        logger.error(f"创建用户失败: {e.error_message}")
        return Results.failure_from_exception(e)
    except Exception as e:
        logger.exception(f"创建用户失败: {str(e)}")
        return Results.failure_with_code("50000", str(e))


@router.put("/{user_id}", response_model=Result[dict])
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """更新用户（仅管理员）"""
    try:
        user = user_service.update_user(db, user_id, request)
        return Results.success_with_data({
            "message": "用户更新成功",
            "user": UserVO.model_validate(user).model_dump()
        })
    except AbstractException as e:
        logger.error(f"更新用户失败: {e.error_message}")
        return Results.failure_from_exception(e)
    except Exception as e:
        logger.exception(f"更新用户失败: {str(e)}")
        return Results.failure_with_code("50000", str(e))


@router.delete("/{user_id}", response_model=Result[dict])
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """删除用户（仅管理员）"""
    try:
        user_service.delete_user(db, user_id)
        return Results.success_with_data({"message": "用户删除成功"})
    except AbstractException as e:
        logger.error(f"删除用户失败: {e.error_message}")
        return Results.failure_from_exception(e)
    except Exception as e:
        logger.exception(f"删除用户失败: {str(e)}")
        return Results.failure_with_code("50000", str(e))
