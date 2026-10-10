"""
会话服务
提供会话管理功能
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from backend.crud import crud_conversation
from backend.models.conversation import ConversationModel
from backend.utils.snowflake_id_utils import generate_snowflake_id_str

from backend.core.logger import logger


def list_by_user_id(db: Session, user_id: str) -> List[dict]:
    """获取用户的会话列表

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        List[dict]: 会话列表，按最后时间倒序排列
    """
    if not user_id:
        return []

    try:
        conversations = crud_conversation.list_by_user_id(db, user_id)

        # 转换为字典列表
        result = []
        for conv in conversations:
            result.append({
                "conversationId": conv.conversation_id,
                "title": conv.title,
                "lastTime": conv.last_time.isoformat() if conv.last_time else None
            })

        logger.debug(f"用户 {user_id} 的会话列表，共 {len(result)} 个")
        return result

    except Exception as e:
        logger.exception(f"获取会话列表失败: {e}")
        return []


def create_or_update(db: Session, conversation_id: str, user_id: str, title: str, last_time: Optional[datetime] = None):
    """创建或更新会话

    Args:
        db: 数据库会话
        conversation_id: 会话 ID
        user_id: 用户 ID
        title: 会话标题
        last_time: 最后消息时间
    """
    if not conversation_id or not user_id:
        logger.warning("创建/更新会话失败：缺少必要参数")
        return

    try:
        # 检查会话是否存在
        existing = crud_conversation.get_by_conversation_and_user(
            db, conversation_id, user_id
        )

        if existing:
            # 更新现有会话
            existing.title = title
            if last_time:
                existing.last_time = last_time
            logger.debug(f"更新会话 {conversation_id}")
        else:
            # 创建新会话
            now = datetime.now()
            conversation = ConversationModel(
                id=generate_snowflake_id_str(),
                conversation_id=conversation_id,
                user_id=user_id,
                title=title,
                last_time=last_time or now
            )
            crud_conversation.add(db, conversation)
            logger.debug(f"创建新会话 {conversation_id}")

        db.commit()

    except Exception as e:
        db.rollback()
        logger.exception(f"创建/更新会话失败: {e}")


def rename(db: Session, conversation_id: str, user_id: str, title: str):
    """重命名会话

    Args:
        db: 数据库会话
        conversation_id: 会话 ID
        user_id: 用户 ID
        title: 新标题
    """
    if not conversation_id or not user_id:
        raise ValueError("会话信息缺失")

    if not title or len(title.strip()) == 0:
        raise ValueError("会话名称不能为空")

    if len(title) > 128:
        raise ValueError("会话名称长度不能超过128个字符")

    try:
        # 查询会话
        conversation = crud_conversation.get_by_conversation_and_user(
            db, conversation_id, user_id
        )

        if not conversation:
            raise ValueError("会话不存在")

        # 更新标题
        conversation.title = title.strip()

        db.commit()

        logger.info(f"会话 {conversation_id} 重命名为 {title}")

    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"重命名会话失败: {e}")
        raise


def delete(db: Session, conversation_id: str, user_id: str):
    """删除会话（软删除）

    Args:
        db: 数据库会话
        conversation_id: 会话 ID
        user_id: 用户 ID
    """
    if not conversation_id or not user_id:
        raise ValueError("会话信息缺失")

    try:
        # 查询会话
        conversation = crud_conversation.get_by_conversation_and_user(
            db, conversation_id, user_id
        )

        if not conversation:
            raise ValueError("会话不存在")

        # 软删除
        crud_conversation.soft_delete(db, conversation)

        db.commit()

        logger.info(f"会话 {conversation_id} 已删除")

    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"删除会话失败: {e}")
        raise


__all__ = [
    "list_by_user_id",
    "create_or_update",
    "rename",
    "delete",
]
