"""
对话消息服务
提供对话消息的查询功能，支持排序与数量限制
"""
from typing import List, Optional, Dict

from backend.db.database import get_db_session
from backend.schemas.enums.conversation_message_order import ConversationMessageOrder
from backend.schemas.chat import ConversationMessageVO
from backend.crud import crud_conversation, crud_conversation_message
from backend.services import message_feedback_service

from backend.core.logger import logger


def list_messages(conversation_id: str, user_id: str,
                 limit: Optional[int] = None,
                 order: ConversationMessageOrder = ConversationMessageOrder.DESC) -> List[ConversationMessageVO]:
    """获取对话消息列表（支持排序与数量限制）


    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        limit: 限制数量，None 表示不限制
        order: 排序方式，默认 DESC（降序）

    Returns:
        List[ConversationMessageVO]: 对话消息视图对象列表（已按指定顺序排列）
    """
    if not conversation_id or not user_id:
        return []

    try:
        with get_db_session() as session:
            conversation = crud_conversation.get_by_conversation_and_user(
                session, conversation_id, user_id
            )

            if not conversation:
                logger.warning(f"会话不存在 - conversationId: {conversation_id}, userId: {user_id}")
                return []

            asc = (order is None or order == ConversationMessageOrder.ASC)

            records = crud_conversation_message.list_by_conversation_and_user(
                session, conversation_id, user_id, asc=asc, limit=limit
            )

            if not records:
                return []

            #    原因：数据库按 DESC 查询是为了性能优化（配合 LIMIT），
            #    但业务上需要正序返回给调用者
            if not asc:
                records.reverse()

            assistant_message_ids = [
                record.id for record in records
                if record.role and record.role.lower() == "assistant"
            ]

            votes_by_message_id: Dict[str, int] = message_feedback_service.get_user_votes(
                session,
                user_id,
                assistant_message_ids
            )

            result = []
            for record in records:
                vo = ConversationMessageVO(
                    id=str(record.id),
                    conversation_id=record.conversation_id,
                    role=record.role,
                    content=record.content,
                    vote=votes_by_message_id.get(record.id),
                    create_time=record.create_time.strftime("%Y-%m-%d %H:%M:%S") if record.create_time else None
                )
                result.append(vo)

            logger.debug(
                f"查询消息列表成功 - conversationId: {conversation_id}, "
                f"userId: {user_id}, count: {len(result)}, order: {order.value}"
            )

            return result

    except Exception as e:
        logger.exception(f"查询消息列表失败: {e}")
        return []
