"""
对话记忆服务
管理会话历史和上下文，支持多轮对话
"""
from typing import List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from backend.schemas.chat import ChatMessage
from backend.db.database import get_db_session
from backend.services.conversation_memory_summary_service import (
    compress_if_needed,
    load_latest_summary,
    decorate_if_needed,
)
from backend.services.conversation_message_service import list_messages
from backend.schemas.enums.conversation_message_order import ConversationMessageOrder
from sqlalchemy.orm import Session
from langsmith import traceable

from backend.core.logger import logger

_max_history_per_session = 20
# 线程池用于并行加载
_executor = ThreadPoolExecutor(max_workers=4)


@traceable(name="load_and_append")
def load_and_append(conversation_id: str, user_id: str,
                    new_message: ChatMessage) -> List[ChatMessage]:
    """加载历史并追加新消息

    便捷方法：适用于需要同时获取历史和追加消息的场景
    避免重复调用 load() 和 append()

    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        new_message: 新的聊天消息

    Returns:
        List[ChatMessage]: 追加前的历史记录（不包含新消息）
    """
    try:
        # 第一步：加载历史记录（包含摘要）
        history = _load_with_summary(conversation_id, user_id)

        # 第二步：异步追加消息到数据库（不阻塞返回）
        _save_to_db_async(conversation_id, user_id, new_message)

        logger.debug(
            f"加载并追加消息成功 - conversationId: {conversation_id}, "
            f"userId: {user_id}, 历史消息数: {len(history)}"
        )

        return history

    except Exception as e:
        logger.exception(f"加载和追加消息失败: {e}")
        return []


def load_history(conversation_id: str, user_id: str,
                 limit: int = 20) -> List[ChatMessage]:
    """加载会话历史

    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        limit: 最大返回消息数

    Returns:
        List[ChatMessage]: 历史消息列表（包含摘要）
    """
    try:
        if not conversation_id or not user_id:
            return []

        # 加载带摘要的历史
        history = _load_with_summary(conversation_id, user_id)

        # 限制返回数量
        return history[-limit:] if len(history) > limit else history
    except Exception as e:
        logger.exception(f"加载历史失败: {e}")
        return []


def append(conversation_id: str, user_id: str, message: ChatMessage) -> Optional[str]:
    """追加消息到对话历史

    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        message: 要追加的消息

    Returns:
        Optional[str]: 消息ID
    """
    if not conversation_id or not user_id:
        return None

    # 保存消息
    message_id = _save_message_to_db(conversation_id, user_id, message)

    # 触发摘要压缩（如果是助手消息）
    if message.role == "assistant":
        compress_if_needed(conversation_id, user_id, message)

    return message_id


def _load_with_summary(conversation_id: str, user_id: str) -> List[ChatMessage]:
    """加载历史记录并附加摘要

    Args:
        conversation_id: 会话ID
        user_id: 用户ID

    Returns:
        List[ChatMessage]: 包含摘要的历史消息列表
    """
    try:
        # 并行加载摘要和历史记录
        summary_future = _executor.submit(
            _load_summary_with_fallback, conversation_id, user_id
        )
        history_future = _executor.submit(
            _load_history_with_fallback, conversation_id, user_id
        )

        # 等待两个任务完成
        summary = summary_future.result(timeout=5)
        history = history_future.result(timeout=5)

        # 附加摘要到历史前面
        return _attach_summary(summary, history)

    except Exception as e:
        logger.exception(f"加载带摘要的历史失败: {e}")
        # 降级：只返回历史记录
        return _load_history_with_fallback(conversation_id, user_id)


def _load_summary_with_fallback(conversation_id: str, user_id: str) -> Optional[ChatMessage]:
    """加载摘要，失败时返回 None

    Args:
        conversation_id: 会话ID
        user_id: 用户ID

    Returns:
        Optional[ChatMessage]: 摘要消息，失败时返回 None
    """
    try:
        return load_latest_summary(conversation_id, user_id)
    except Exception as e:
        logger.opt(exception=True).warning(f"加载摘要失败，将跳过摘要 - conversationId: {conversation_id}, userId: {user_id}")
        return None


def _load_history_with_fallback(conversation_id: str, user_id: str) -> List[ChatMessage]:
    """加载历史记录，失败时返回空列表

    Args:
        conversation_id: 会话ID
        user_id: 用户ID

    Returns:
        List[ChatMessage]: 历史消息列表
    """
    try:
        history = _load_from_db(conversation_id, user_id)
        return history if history else []
    except Exception as e:
        logger.exception(f"加载历史记录失败 - conversationId: {conversation_id}, userId: {user_id}")
        return []


def _attach_summary(summary: Optional[ChatMessage],
                    messages: List[ChatMessage]) -> List[ChatMessage]:
    """将摘要附加到历史消息前

    Args:
        summary: 摘要消息
        messages: 历史消息列表

    Returns:
        List[ChatMessage]: 包含摘要的完整历史
    """
    # 确保返回值不为空
    if not messages:
        return []

    # 如果没有摘要，直接返回历史
    if summary is None:
        return messages

    # 装饰摘要（添加前缀）- 使用摘要服务的装饰方法
    decorated_summary = decorate_if_needed(summary)

    # 将摘要放在最前面
    result = [decorated_summary] + messages
    return result


def _load_from_db(conversation_id: str, user_id: str,
                  order: ConversationMessageOrder = ConversationMessageOrder.DESC) -> List[ChatMessage]:
    """从数据库加载历史

    委托给 ConversationMessageService 处理排序和反转逻辑

    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        order: 排序方式，默认 DESC（降序查询后反转为正序）

    Returns:
        List[ChatMessage]: 历史消息列表（已规范化）
    """
    try:
        # 使用消息服务加载历史（Service 层处理排序和反转）
        max_messages = _max_history_per_session
        messages = list_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=max_messages,
            order=order
        )

        if not messages:
            return []

        # 将视图对象（ConversationMessageVO）转换为统一的 ChatMessage，
        # memory 服务对外约定为 List[ChatMessage]，避免 VO 泄漏到查询链路
        chat_messages = [
            ChatMessage(role=msg.role, content=msg.content)
            for msg in messages
        ]

        # 过滤有效消息并规范化
        valid_messages = [
            msg for msg in chat_messages
            if _is_valid_chat_message(msg)
        ]

        # 规范化历史：确保以 user 消息开头
        return _normalize_history(valid_messages)

    except Exception as e:
        logger.exception(f"从数据库加载历史失败: {e}")
        return []


def _is_valid_chat_message(message: ChatMessage) -> bool:
    """检查 ChatMessage 是否为有效的历史消息

    Args:
        message: 聊天消息对象

    Returns:
        bool: 是否为有效消息
    """
    return (message is not None
            and message.content
            and message.role in ["user", "assistant"])


def _normalize_history(messages: List[Optional[ChatMessage]]) -> List[ChatMessage]:
    """规范化历史消息

    规则：
    1. 过滤掉开头的 assistant 消息（确保以 user 开头）
    2. 过滤空内容消息

    Args:
        messages: 原始历史消息列表

    Returns:
        List[ChatMessage]: 规范化后的历史消息列表
    """
    if not messages:
        return []

    # 过滤有效消息
    cleaned = [
        msg for msg in messages
        if msg and msg.content and msg.role in ["user", "assistant"]
    ]

    if not cleaned:
        return []

    # 跳过开头的 assistant 消息
    start = 0
    while start < len(cleaned) and cleaned[start].role == "assistant":
        start += 1

    if start >= len(cleaned):
        return []

    return cleaned[start:]


def _save_to_db_async(conversation_id: str, user_id: str, message: ChatMessage):
    """异步保存消息到数据库

    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        message: 聊天消息
    """
    try:
        # 在线程池中异步执行
        _executor.submit(
            _save_message_to_db, conversation_id, user_id, message
        )
    except Exception as e:
        logger.exception(f"提交异步保存任务失败: {e}")


def _save_message_to_db(conversation_id: str, user_id: str, message: ChatMessage) -> Optional[str]:
    """保存消息到数据库（实际执行）

    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        message: 聊天消息

    Returns:
        Optional[str]: 消息ID
    """
    try:
        from backend.models.conversation_message import ConversationMessageModel
        from backend.models.conversation import ConversationModel
        from backend.utils.snowflake_id_utils import generate_snowflake_id_str

        # 生成唯一 ID
        message_id = generate_snowflake_id_str()

        with get_db_session() as session:
            # 1. 保存消息
            db_message = ConversationMessageModel(
                id=str(message_id),
                conversation_id=conversation_id,
                user_id=user_id,
                role=message.role,
                content=message.content
            )
            session.add(db_message)
            session.flush()

            # 2. 如果是用户消息，更新或创建会话
            if message.role == "user":
                _update_conversation(session, conversation_id, user_id, message.content)

            logger.debug(f"保存消息到数据库成功 - conversationId: {conversation_id}, role: {message.role}")
            return str(message_id)

    except Exception as e:
        logger.exception(f"保存消息到数据库失败: {e}")
        return None


def _update_conversation(session: Session, conversation_id: str,
                         user_id: str, question: str):
    """更新或创建会话记录

    Args:
        session: 数据库会话
        conversation_id: 会话ID
        user_id: 用户ID
        question: 用户问题（用于生成标题）
    """
    try:
        from backend.models.conversation import ConversationModel
        from backend.utils.snowflake_id_utils import generate_snowflake_id_str

        # 查询会话是否存在
        conversation = session.query(ConversationModel)\
            .filter(
                ConversationModel.conversation_id == conversation_id,
                ConversationModel.user_id == user_id,
                ConversationModel.deleted == 0
            )\
            .first()

        if conversation:
            # 更新最后时间
            conversation.last_time = datetime.now()
        else:
            # 创建新会话
            # 使用问题前 20 个字符作为标题
            title = question[:20] if len(question) > 20 else question

            # 生成会话 ID
            conv_id = generate_snowflake_id_str()

            new_conversation = ConversationModel(
                id=conv_id,
                conversation_id=conversation_id,
                user_id=user_id,
                title=title,
                last_time=datetime.now()
            )
            session.add(new_conversation)

    except Exception as e:
        logger.exception(f"更新会话记录失败: {e}")
