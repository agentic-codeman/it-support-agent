"""
会话消息数据访问层（CRUD）
将会话消息相关的数据库读写操作下沉到该模块，供 conversation_message_service 调用
符合 Google Python 编码规范
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models.conversation_message import ConversationMessageModel


def list_by_conversation_and_user(
    db: Session,
    conversation_id: str,
    user_id: str,
    asc: bool = True,
    limit: Optional[int] = None
) -> List[ConversationMessageModel]:
    """查询会话消息列表（支持排序与数量限制）

    Args:
        db: 数据库会话
        conversation_id: 会话ID
        user_id: 用户ID
        asc: True 按创建时间升序，False 按降序
        limit: 限制数量，None 表示不限制

    Returns:
        会话消息列表（已按指定顺序排列）
    """
    query = db.query(ConversationMessageModel).filter(
        ConversationMessageModel.conversation_id == conversation_id,
        ConversationMessageModel.user_id == user_id,
        ConversationMessageModel.deleted == 0
    )

    if asc:
        query = query.order_by(ConversationMessageModel.create_time.asc())
    else:
        query = query.order_by(ConversationMessageModel.create_time.desc())

    if limit is not None:
        query = query.limit(limit)

    return query.all()


def count_user_messages(db: Session, conversation_id: str, user_id: str) -> int:
    """统计会话中用户消息数量

    Args:
        db: 数据库会话
        conversation_id: 会话ID
        user_id: 用户ID

    Returns:
        用户消息数量
    """
    return db.query(ConversationMessageModel).filter(
        ConversationMessageModel.conversation_id == conversation_id,
        ConversationMessageModel.user_id == user_id,
        ConversationMessageModel.role == "user",
        ConversationMessageModel.deleted == 0
    ).count()


def list_latest_user_turns(
    db: Session,
    conversation_id: str,
    user_id: str,
    limit: int
) -> List[ConversationMessageModel]:
    """查询最近的用户消息轮次（按创建时间倒序，限制数量）

    Args:
        db: 数据库会话
        conversation_id: 会话ID
        user_id: 用户ID
        limit: 返回数量限制

    Returns:
        用户消息列表（按创建时间倒序）
    """
    return db.query(ConversationMessageModel).filter(
        ConversationMessageModel.conversation_id == conversation_id,
        ConversationMessageModel.user_id == user_id,
        ConversationMessageModel.role == "user",
        ConversationMessageModel.deleted == 0
    ).order_by(ConversationMessageModel.create_time.desc()).limit(limit).all()


def find_max_id_at_or_before(
    db: Session,
    conversation_id: str,
    user_id: str,
    before_time: datetime
) -> Optional[str]:
    """查找指定时间之前（含）的最大消息 ID

    Args:
        db: 数据库会话
        conversation_id: 会话ID
        user_id: 用户ID
        before_time: 截止时间

    Returns:
        最大消息 ID 或 None
    """
    message = db.query(ConversationMessageModel).filter(
        ConversationMessageModel.conversation_id == conversation_id,
        ConversationMessageModel.user_id == user_id,
        ConversationMessageModel.create_time <= before_time,
        ConversationMessageModel.deleted == 0
    ).order_by(ConversationMessageModel.id.desc()).first()

    return message.id if message else None


def list_between_ids(
    db: Session,
    conversation_id: str,
    user_id: str,
    after_id: Optional[str],
    cutoff_id: str
) -> List[ConversationMessageModel]:
    """查询两个 ID 之间的消息列表

    Args:
        db: 数据库会话
        conversation_id: 会话ID
        user_id: 用户ID
        after_id: 起始 ID（不包含），None 表示不限制下界
        cutoff_id: 截止 ID（包含）

    Returns:
        消息列表（按创建时间升序）
    """
    query = db.query(ConversationMessageModel).filter(
        ConversationMessageModel.conversation_id == conversation_id,
        ConversationMessageModel.user_id == user_id,
        ConversationMessageModel.deleted == 0
    )

    if after_id:
        query = query.filter(ConversationMessageModel.id > after_id)

    query = query.filter(ConversationMessageModel.id <= cutoff_id) \
        .order_by(ConversationMessageModel.create_time.asc())

    return query.all()


__all__ = [
    "list_by_conversation_and_user",
    "count_user_messages",
    "list_latest_user_turns",
    "find_max_id_at_or_before",
    "list_between_ids",
]
