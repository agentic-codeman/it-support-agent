"""
消息反馈服务
提供消息投票查询等功能
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from backend.crud import crud_message_feedback

from backend.core.logger import logger


def submit_feedback(
    db: Session,
    message_id: str,
    conversation_id: str,
    user_id: str,
    vote: int,
    reason: Optional[str] = None,
    comment: Optional[str] = None
) -> bool:
    """提交消息反馈（点赞/点踩）

    Args:
        db: 数据库会话
        message_id: 消息ID
        conversation_id: 会话ID
        user_id: 用户ID
        vote: 投票值 1=点赞, -1=点踩
        reason: 反馈原因（可选）
        comment: 补充说明（可选）

    Returns:
        bool: 是否成功
    """
    if not message_id or not conversation_id or not user_id:
        logger.error(f"提交反馈失败：缺少必要参数")
        return False

    if vote not in [1, -1]:
        logger.error(f"提交反馈失败：无效的投票值 {vote}")
        return False

    try:
        # 检查是否已经存在反馈记录
        existing = crud_message_feedback.get_by_message_and_user(
            db, message_id, user_id
        )

        if existing:
            # 更新现有记录
            crud_message_feedback.update(db, existing, vote, reason, comment)
            logger.info(f"更新反馈记录 - messageId: {message_id}, userId: {user_id}, vote: {vote}")
        else:
            # 创建新记录
            crud_message_feedback.create(
                db, message_id, conversation_id, user_id, vote, reason, comment
            )
            logger.info(f"创建反馈记录 - messageId: {message_id}, userId: {user_id}, vote: {vote}")

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        logger.exception(f"提交反馈失败: {e}")
        return False


def get_user_votes(db: Session, user_id: str, message_ids: List[str]) -> Dict[str, int]:
    """获取用户对指定消息的投票信息

    Args:
        db: 数据库会话
        user_id: 用户ID
        message_ids: 消息ID列表

    Returns:
        Dict[str, int]: {messageId: vote} 映射，vote为1(赞)或-1(踩)
    """
    if not user_id or not message_ids:
        return {}

    try:
        records = crud_message_feedback.get_by_user_and_messages(
            db, user_id, message_ids
        )

        if not records:
            return {}

        # 构建 {messageId: vote} 映射
        votes_map = {
            record.message_id: record.vote
            for record in records
        }

        logger.debug(f"查询用户投票成功 - userId: {user_id}, count: {len(votes_map)}")
        return votes_map

    except Exception as e:
        logger.exception(f"查询用户投票失败: {e}")
        return {}


__all__ = [
    "submit_feedback",
    "get_user_votes",
]
