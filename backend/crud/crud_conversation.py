"""
会话数据访问层（CRUD）
将会话相关的数据库读写操作下沉到该模块，供 conversation_service 调用
符合 Google Python 编码规范
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models.conversation import ConversationModel


def list_by_user_id(db: Session, user_id: str) -> List[ConversationModel]:
    """查询用户所有未删除会话（按最后消息时间倒序）

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        会话列表
    """
    return db.query(ConversationModel).filter(
        ConversationModel.user_id == user_id,
        ConversationModel.deleted == 0
    ).order_by(ConversationModel.last_time.desc()).all()


def get_by_conversation_and_user(
    db: Session,
    conversation_id: str,
    user_id: str
) -> Optional[ConversationModel]:
    """按会话ID和用户ID查询未删除会话

    Args:
        db: 数据库会话
        conversation_id: 会话 ID
        user_id: 用户 ID

    Returns:
        会话对象或 None
    """
    return db.query(ConversationModel).filter(
        ConversationModel.conversation_id == conversation_id,
        ConversationModel.user_id == user_id,
        ConversationModel.deleted == 0
    ).first()


def add(db: Session, conversation: ConversationModel) -> None:
    """新增会话（不提交，由调用方控制事务）

    Args:
        db: 数据库会话
        conversation: 已构造好的会话对象
    """
    db.add(conversation)


def soft_delete(db: Session, conversation: ConversationModel) -> None:
    """逻辑删除会话（不提交，由调用方控制事务）

    Args:
        db: 数据库会话
        conversation: 待删除的会话对象
    """
    conversation.deleted = 1


__all__ = [
    "list_by_user_id",
    "get_by_conversation_and_user",
    "add",
    "soft_delete",
]
