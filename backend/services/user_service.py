"""
用户业务服务
符合 Google Python 编码规范
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.crud import crud_user
from backend.models.user import UserModel
from backend.schemas.user import UserCreateRequest, UserVO, UserPageRequest, UserCreateRequestV2, UserUpdateRequest
from backend.utils.exceptions import ServiceException, ClientException
from backend.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

from backend.core.logger import logger


def register(db: Session, request: UserCreateRequest) -> UserModel:
    """用户注册

    Args:
        db: 数据库会话
        request: 注册请求参数

    Returns:
        创建的用户对象

    Raises:
        ServiceException: 用户名已存在
    """
    try:
        # 检查用户名是否已存在
        if crud_user.exists_by_username(db, request.username):
            raise ServiceException("用户名已存在")

        # 密码加密
        hashed_password = hash_password(request.password)

        # 创建用户
        user = crud_user.create(
            db,
            username=request.username,
            password=hashed_password,
            role=request.role or "user"
        )

        db.commit()
        db.refresh(user)

        logger.info(f"用户注册成功: {request.username}")
        return user
    except Exception:
        db.rollback()
        raise


def login(db: Session, username: str, password: str) -> dict:
    """用户登录

    Args:
        db: 数据库会话
        username: 用户名
        password: 密码

    Returns:
        包含 token 和用户信息的字典

    Raises:
        ClientException: 用户名或密码错误
    """
    # 查询用户
    user = crud_user.get_by_username(db, username)

    if not user:
        raise ClientException("用户名或密码错误")

    # 验证密码
    if not verify_password(password, user.password):
        raise ClientException("用户名或密码错误")

    # 生成 JWT Token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role}
    )

    logger.info(f"用户登录成功: {username}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "avatar": user.avatar
        }
    }


def get_user_by_id(db: Session, user_id: int) -> Optional[UserModel]:
    """根据 ID 获取用户

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        用户对象或 None
    """
    return crud_user.get_by_id(db, user_id)


def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
    """根据用户名获取用户

    Args:
        db: 数据库会话
        username: 用户名

    Returns:
        用户对象或 None
    """
    return crud_user.get_by_username(db, username)


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    """使用 refresh token 刷新 access token

    Args:
        db: 数据库会话
        refresh_token: 刷新令牌

    Returns:
        包含新 access_token 的字典

    Raises:
        ClientException: token 无效或用户不存在
    """
    import jwt

    # 验证 refresh_token
    try:
        payload = decode_token(refresh_token)
    except jwt.ExpiredSignatureError:
        raise ClientException("刷新令牌已过期")
    except jwt.InvalidTokenError:
        raise ClientException("无效的刷新令牌")

    # 检查 token 类型
    if payload.get("type") != "refresh":
        raise ClientException("无效的令牌类型")

    # 检查 refresh_token 是否在黑名单中
    from backend.services.token_blacklist_service import TokenBlacklistService
    if TokenBlacklistService.is_blacklisted(db, refresh_token):
        raise ClientException("刷新令牌已被撤销")

    # 查询用户
    username = payload.get("sub")
    user_id = payload.get("user_id")

    if not username:
        raise ClientException("无效的令牌")

    user = crud_user.get_by_id(db, user_id)
    if not user or user.username != username:
        raise ClientException("用户不存在")

    # 生成新的 access_token
    new_access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role}
    )

    logger.info(f"Token 刷新成功: {username}")

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


def logout(db: Session, access_token: str, refresh_token: Optional[str] = None) -> dict:
    """用户登出，将 token 加入黑名单

    Args:
        db: 数据库会话
        access_token: 访问令牌
        refresh_token: 刷新令牌（可选）

    Returns:
        登出结果信息
    """
    from backend.services.token_blacklist_service import TokenBlacklistService

    revoked_count = 0

    # 将 access_token 加入黑名单
    if access_token:
        try:
            payload = decode_token(access_token)
            user_id = str(payload.get("user_id", ""))
            username = payload.get("sub", "")
            exp_timestamp = payload.get("exp")

            if exp_timestamp:
                expires_at = datetime.utcfromtimestamp(exp_timestamp)
            else:
                expires_at = datetime.utcnow() + timedelta(hours=24)

            success = TokenBlacklistService.add_to_blacklist(
                db=db,
                token=access_token,
                token_type="access",
                user_id=user_id,
                username=username,
                expires_at=expires_at,
                reason="logout"
            )

            if success:
                revoked_count += 1
                logger.info(f"Access token 已加入黑名单: {username}")

        except Exception as e:
            logger.error(f"处理 access_token 失败: {str(e)}")

    # 将 refresh_token 加入黑名单（如果提供）
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            user_id = str(payload.get("user_id", ""))
            username = payload.get("sub", "")
            exp_timestamp = payload.get("exp")

            if exp_timestamp:
                expires_at = datetime.utcfromtimestamp(exp_timestamp)
            else:
                expires_at = datetime.utcnow() + timedelta(days=7)

            success = TokenBlacklistService.add_to_blacklist(
                db=db,
                token=refresh_token,
                token_type="refresh",
                user_id=user_id,
                username=username,
                expires_at=expires_at,
                reason="logout"
            )

            if success:
                revoked_count += 1
                logger.info(f"Refresh token 已加入黑名单: {username}")

        except Exception as e:
            logger.error(f"处理 refresh_token 失败: {str(e)}")

    logger.info(f"用户登出成功，撤销了 {revoked_count} 个 token")

    return {
        "message": "登出成功",
        "revoked_tokens": revoked_count
    }


def page_query(db: Session, request: UserPageRequest) -> Dict[str, Any]:
    """分页查询用户列表

    Args:
        db: 数据库会话
        request: 分页请求参数

    Returns:
        包含用户列表和分页信息的字典
    """
    users, total = crud_user.page_query(
        db,
        page_num=request.page_num,
        page_size=request.page_size,
        keyword=request.keyword
    )

    # 转换为 VO
    user_list = [UserVO.model_validate(user) for user in users]

    return {
        "list": user_list,
        "total": total,
        "page_num": request.page_num,
        "page_size": request.page_size,
        "total_pages": (total + request.page_size - 1) // request.page_size
    }


def create_user(db: Session, request: UserCreateRequestV2) -> UserModel:
    """创建用户（管理端）

    Args:
        db: 数据库会话
        request: 用户创建请求

    Returns:
        创建的用户对象

    Raises:
        ServiceException: 用户名已存在
    """
    try:
        # 检查用户名是否已存在
        if crud_user.exists_by_username(db, request.username):
            raise ServiceException("用户名已存在")

        # 密码加密
        hashed_password = hash_password(request.password)

        # 创建用户
        user = crud_user.create(
            db,
            username=request.username,
            password=hashed_password,
            role=request.role or "user",
            avatar=request.avatar
        )

        db.commit()
        db.refresh(user)

        logger.info(f"管理员创建用户成功: {request.username}")
        return user
    except Exception:
        db.rollback()
        raise


def update_user(db: Session, user_id: str, request: UserUpdateRequest) -> UserModel:
    """更新用户

    Args:
        db: 数据库会话
        user_id: 用户ID
        request: 用户更新请求

    Returns:
        更新后的用户对象

    Raises:
        ClientException: 用户不存在或用户名冲突
    """
    try:
        # 查询用户
        user = crud_user.get_by_id(db, user_id)

        if not user:
            raise ClientException("用户不存在")

        # 如果修改了用户名，检查是否与其他用户冲突
        new_username = user.username
        if request.username and request.username != user.username:
            if crud_user.exists_by_username(db, request.username, exclude_id=user_id):
                raise ServiceException("用户名已被其他用户使用")
            new_username = request.username

        # 如果提供了新密码，进行加密
        new_password = hash_password(request.password) if request.password else None

        user = crud_user.update(
            db,
            user,
            username=new_username,
            password=new_password,
            role=request.role or None,
            avatar=request.avatar
        )

        db.commit()
        db.refresh(user)

        logger.info(f"用户更新成功: {user.username}")
        return user
    except Exception:
        db.rollback()
        raise


def delete_user(db: Session, user_id: str) -> None:
    """删除用户（逻辑删除）

    Args:
        db: 数据库会话
        user_id: 用户ID

    Raises:
        ClientException: 用户不存在
    """
    try:
        # 查询用户
        user = crud_user.get_by_id(db, user_id)

        if not user:
            raise ClientException("用户不存在")

        # 不允许删除自己
        # 这里可以根据实际需求添加检查逻辑

        # 逻辑删除
        crud_user.soft_delete(db, user)

        db.commit()

        logger.info(f"用户删除成功: {user.username}")
    except Exception:
        db.rollback()
        raise


__all__ = [
    "register",
    "login",
    "get_user_by_id",
    "get_user_by_username",
    "refresh_access_token",
    "logout",
    "page_query",
    "create_user",
    "update_user",
    "delete_user",
]
