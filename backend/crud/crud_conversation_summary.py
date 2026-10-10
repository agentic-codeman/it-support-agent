"""
会话摘要数据访问层（CRUD）
将会话摘要相关的数据库读写操作下沉到该模块，供 conversation_memory_summary_service 调用
符合 Google Python 编码规范
"""
from typing import Optional

from sqlalchemy.orm import Session

from backend.models.conversation_summary import ConversationSummaryModel


def get_latest(
    db: Session,
    conversation_id: str,
    user_id: str
) -> Optional[ConversationSummaryModel]:
    """查询最新未删除摘要记录

    Args:
        db: 数据库会话
        conversation_id: 会话ID
        user_id: 用户ID

    Returns:
        摘要对象或 None
    """
    return db.query(ConversationSummaryModel).filter(
        ConversationSummaryModel.conversation_id == conversation_id,
        ConversationSummaryModel.user_id == user_id,
        ConversationSummaryModel.deleted == 0
    ).order_by(ConversationSummaryModel.id.desc()).first()


def create(
    db: Session,
    conversation_id: str,
    user_id: str,
    content: str,
    last_message_id: str
) -> ConversationSummaryModel:
    """新增摘要记录（不提交，由调用方控制事务）

    Args:
        db: 数据库会话
        conversation_id: 会话ID
        user_id: 用户ID
        content: 摘要内容
        last_message_id: 摘要最后消息ID

    Returns:
        创建的摘要对象
    """
    from backend.utils.snowflake_id_utils import generate_snowflake_id_str

    record = ConversationSummaryModel(
        id=generate_snowflake_id_str(),
        conversation_id=conversation_id,
        user_id=user_id,
        content=content,
        last_message_id=last_message_id,
        deleted=0
    )
    db.add(record)
    return record


__all__ = [
    "get_latest",
    "create",
]
