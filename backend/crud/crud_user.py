"""
用户数据访问层（CRUD）
将用户相关的数据库读写操作下沉到该模块，供 user_service 调用
符合 Google Python 编码规范
"""
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.models.user import UserModel


def get_by_id(db: Session, user_id: str) -> Optional[UserModel]:
    """按主键查询未删除用户

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        用户对象或 None
    """
    return db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.deleted == 0
    ).first()


def get_by_username(db: Session, username: str) -> Optional[UserModel]:
    """按用户名查询未删除用户

    Args:
        db: 数据库会话
        username: 用户名

    Returns:
        用户对象或 None
    """
    return db.query(UserModel).filter(
        UserModel.username == username,
        UserModel.deleted == 0
    ).first()


def exists_by_username(
    db: Session,
    username: str,
    exclude_id: Optional[str] = None
) -> bool:
    """判断用户名是否已被（其他）用户占用

    Args:
        db: 数据库会话
        username: 用户名
        exclude_id: 排除的用户 ID（用于更新时忽略自身）

    Returns:
        bool: 是否已存在
    """
    query = db.query(UserModel).filter(
        UserModel.username == username,
        UserModel.deleted == 0
    )
    if exclude_id is not None:
        query = query.filter(UserModel.id != exclude_id)
    return query.first() is not None


def create(
    db: Session,
    username: str,
    password: str,
    role: str = "user",
    avatar: Optional[str] = None
) -> UserModel:
    """创建用户

    Args:
        db: 数据库会话
        username: 用户名
        password: 已加密密码
        role: 角色，默认 user
        avatar: 头像 URL

    Returns:
        创建的用户对象
    """
    user = UserModel(
        username=username,
        password=password,
        role=role,
        avatar=avatar,
        deleted=0
    )
    db.add(user)
    return user


def page_query(
    db: Session,
    page_num: int,
    page_size: int,
    keyword: Optional[str] = None
) -> Tuple[List[UserModel], int]:
    """分页查询用户列表

    Args:
        db: 数据库会话
        page_num: 页码
        page_size: 每页数量
        keyword: 搜索关键词（用户名/角色）

    Returns:
        (用户列表, 总数) 元组
    """
    query = db.query(UserModel).filter(UserModel.deleted == 0)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (UserModel.username.like(like)) | (UserModel.role.like(like))
        )

    total = query.count()
    offset = (page_num - 1) * page_size
    users = query.offset(offset).limit(page_size).all()
    return users, total


def update(
    db: Session,
    user: UserModel,
    username: Optional[str] = None,
    password: Optional[str] = None,
    role: Optional[str] = None,
    avatar: Optional[str] = None
) -> UserModel:
    """更新用户字段

    参数为 None 表示跳过对应字段的更新。

    Args:
        db: 数据库会话
        user: 待更新的用户对象
        username: 新用户名
        password: 新密码（已加密）
        role: 新角色
        avatar: 新头像 URL

    Returns:
        更新后的用户对象
    """
    if username is not None:
        user.username = username
    if password is not None:
        user.password = password
    if role is not None:
        user.role = role
    if avatar is not None:
        user.avatar = avatar

    return user


def soft_delete(db: Session, user: UserModel) -> None:
    """逻辑删除用户

    Args:
        db: 数据库会话
        user: 待删除的用户对象
    """
    user.deleted = 1


__all__ = [
    "get_by_id",
    "get_by_username",
    "exists_by_username",
    "create",
    "page_query",
    "update",
    "soft_delete",
]
