"""
消息反馈数据访问层（CRUD）
将消息反馈相关的数据库读写操作下沉到该模块，供 message_feedback_service 调用
符合 Google Python 编码规范
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models.message_feedback import MessageFeedbackModel


def get_by_message_and_user(
    db: Session,
    message_id: str,
    user_id: str
) -> Optional[MessageFeedbackModel]:
    """查询用户对某条消息的反馈记录（未删除）

    Args:
        db: 数据库会话
        message_id: 消息 ID
        user_id: 用户 ID

    Returns:
        反馈记录或 None
    """
    return db.query(MessageFeedbackModel).filter(
        MessageFeedbackModel.message_id == message_id,
        MessageFeedbackModel.user_id == user_id,
        MessageFeedbackModel.deleted == 0
    ).first()


def get_by_user_and_messages(
    db: Session,
    user_id: str,
    message_ids: List[str]
) -> List[MessageFeedbackModel]:
    """查询用户对多条消息的反馈记录（未删除）

    Args:
        db: 数据库会话
        user_id: 用户 ID
        message_ids: 消息 ID 列表

    Returns:
        反馈记录列表
    """
    return db.query(MessageFeedbackModel).filter(
        MessageFeedbackModel.user_id == user_id,
        MessageFeedbackModel.message_id.in_(message_ids),
        MessageFeedbackModel.deleted == 0
    ).all()


def create(
    db: Session,
    message_id: str,
    conversation_id: str,
    user_id: str,
    vote: int,
    reason: Optional[str] = None,
    comment: Optional[str] = None
) -> MessageFeedbackModel:
    """新增反馈记录（不提交，由调用方控制事务）

    Args:
        db: 数据库会话
        message_id: 消息 ID
        conversation_id: 会话 ID
        user_id: 用户 ID
        vote: 投票值 1=赞, -1=踩
        reason: 反馈原因
        comment: 补充说明

    Returns:
        创建的反馈记录
    """
    from datetime import datetime
    from backend.utils.snowflake_id_utils import generate_snowflake_id_str

    feedback = MessageFeedbackModel(
        id=generate_snowflake_id_str(),
        message_id=message_id,
        conversation_id=conversation_id,
        user_id=user_id,
        vote=vote,
        reason=reason,
        comment=comment,
        create_time=datetime.now(),
        update_time=datetime.now(),
        deleted=0
    )
    db.add(feedback)
    return feedback


def update(
    db: Session,
    feedback: MessageFeedbackModel,
    vote: int,
    reason: Optional[str],
    comment: Optional[str]
) -> None:
    """更新反馈记录（不提交，由调用方控制事务）

    Args:
        db: 数据库会话
        feedback: 待更新的反馈记录
        vote: 投票值
        reason: 反馈原因
        comment: 补充说明
    """
    feedback.vote = vote
    feedback.reason = reason
    feedback.comment = comment


__all__ = [
    "get_by_message_and_user",
    "get_by_user_and_messages",
    "create",
    "update",
]
