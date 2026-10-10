"""
对话记忆摘要服务
负责在对话达到一定轮数时自动生成摘要，压缩历史上下文
"""
import time
from typing import Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from backend.schemas.chat import ChatMessage
from backend.db.database import get_db_session
from backend.services.prompt_loader import load_prompt
from backend.client.llm_factory import create_chat_model
from backend.utils.redislock_utils import try_lock, unlock
from backend.crud import crud_conversation_message, crud_conversation_summary

from backend.core.logger import logger

# 摘要前缀与锁配置
SUMMARY_PREFIX = "对话摘要："
SUMMARY_LOCK_PREFIX = "ragent:store:summary:lock:"
SUMMARY_LOCK_TTL = 300  # 5分钟（秒）

_SUMMARY_ENABLED = True              # 是否启用摘要
_SUMMARY_START_TURNS = 6             # 触发摘要的对话轮数
_HISTORY_KEEP_TURNS = 10             # 保留的历史轮数
_SUMMARY_MAX_CHARS = 200             # 摘要最大字符数

# 线程池用于异步执行摘要任务
_executor = ThreadPoolExecutor(max_workers=2)


def compress_if_needed(conversation_id: str, user_id: str, message: ChatMessage):
    """如果满足条件则压缩摘要

    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        message: 最新的聊天消息
    """
    if not _SUMMARY_ENABLED:
        logger.debug("摘要功能未启用")
        return

    # 只在助手回复后触发摘要
    if message.role != "assistant":
        logger.debug(f"消息角色为 {message.role}，不触发摘要")
        return

    # 异步执行摘要任务
    try:
        _executor.submit(
            _do_compress_if_needed,
            conversation_id,
            user_id
        )
    except Exception as e:
        logger.exception(f"提交摘要任务失败: {e}")


def load_latest_summary(conversation_id: str, user_id: str) -> Optional[ChatMessage]:
    """加载最新的摘要

    Args:
        conversation_id: 会话ID
        user_id: 用户ID

    Returns:
        Optional[ChatMessage]: 摘要消息，不存在则返回 None
    """
    try:
        with get_db_session() as session:
            summary = crud_conversation_summary.get_latest(
                session, conversation_id, user_id
            )

            if not summary or not summary.content:
                return None

            return _to_chat_message(summary)

    except Exception as e:
        logger.exception(f"加载摘要失败: {e}")
        return None


def decorate_if_needed(summary: Optional[ChatMessage]) -> Optional[ChatMessage]:
    """装饰摘要消息，添加前缀

    Args:
        summary: 原始摘要消息

    Returns:
        Optional[ChatMessage]: 装饰后的摘要消息
    """
    if not summary or not summary.content:
        return summary

    content = summary.content.strip()

    # 如果已经有前缀，直接返回
    if content.startswith(SUMMARY_PREFIX) or content.startswith("摘要："):
        return summary

    # 添加系统角色和前缀
    return ChatMessage(role="system", content=SUMMARY_PREFIX + content)


def _do_compress_if_needed(conversation_id: str, user_id: str):
    """执行摘要压缩逻辑

    Args:
        conversation_id: 会话ID
        user_id: 用户ID
    """
    start_time = time.time()

    lock_key = f"{SUMMARY_LOCK_PREFIX}{user_id.strip()}:{conversation_id.strip()}"

    if not try_lock(lock_key, SUMMARY_LOCK_TTL):
        logger.debug(f"获取摘要锁失败 - lockKey: {lock_key}")
        return

    try:
        total = _count_user_messages(conversation_id, user_id)
        if total < _SUMMARY_START_TURNS:
            logger.debug(f"对话轮数 {total} 未达到触发阈值 {_SUMMARY_START_TURNS}")
            return

        latest_summary = _get_latest_summary_record(conversation_id, user_id)

        latest_user_turns = _get_latest_user_turns(conversation_id, user_id)
        if not latest_user_turns:
            return

        cutoff_id = _resolve_cutoff_id(latest_user_turns)
        if not cutoff_id:
            return

        after_id = _resolve_summary_start_id(latest_summary)
        if after_id and int(after_id) >= int(cutoff_id):
            logger.debug(f"消息已摘要过 - after_id: {after_id}, cutoff_id: {cutoff_id}")
            return

        to_summarize = _get_messages_between_ids(
            conversation_id,
            user_id,
            after_id,
            cutoff_id
        )

        if not to_summarize:
            return

        last_message_id = _resolve_last_message_id(to_summarize)
        if not last_message_id:
            return

        existing_summary = latest_summary.get('content') if latest_summary else ""
        summary_content = _summarize_messages(to_summarize, existing_summary)

        if not summary_content:
            return

        _create_summary(
            conversation_id,
            user_id,
            summary_content,
            last_message_id
        )

        elapsed = (time.time() - start_time) * 1000
        logger.info(
            f"摘要成功 - conversationId: {conversation_id}, "
            f"userId: {user_id}, 消息数: {len(to_summarize)}, "
            f"耗时: {elapsed:.0f}ms"
        )

    except Exception as e:
        logger.exception(
            f"摘要失败 - conversationId: {conversation_id}, userId: {user_id}"
        )
    finally:
        unlock(lock_key)


def _count_user_messages(conversation_id: str, user_id: str) -> int:
    """统计用户消息数量

    Args:
        conversation_id: 会话ID
        user_id: 用户ID

    Returns:
        int: 用户消息数量
    """
    try:
        with get_db_session() as session:
            return crud_conversation_message.count_user_messages(
                session, conversation_id, user_id
            )
    except Exception as e:
        logger.exception(f"统计用户消息失败: {e}")
        return 0


def _get_latest_user_turns(conversation_id: str, user_id: str) -> List:
    """获取最近的用户消息轮次

    Args:
        conversation_id: 会话ID
        user_id: 用户ID

    Returns:
        List: 用户消息列表（按时间倒序），每个元素是包含 id 和其他属性的字典
    """
    try:
        with get_db_session() as session:
            messages = crud_conversation_message.list_latest_user_turns(
                session, conversation_id, user_id, _HISTORY_KEEP_TURNS
            )

            # 在会话内将所有需要的属性提取到字典中，避免 DetachedInstanceError
            return [
                {
                    'id': msg.id,
                    'content': msg.content,
                    'role': msg.role,
                    'create_time': msg.create_time,
                }
                for msg in messages
            ]
    except Exception as e:
        logger.exception(f"获取用户消息失败: {e}")
        return []


def _resolve_cutoff_id(latest_user_turns: List) -> Optional[str]:
    """解析截止消息 ID（最早的那条用户消息）

    Args:
        latest_user_turns: 用户消息列表（倒序）

    Returns:
        Optional[str]: 截止消息 ID
    """
    if not latest_user_turns:
        return None

    # 倒序列表的最后一个是时间最早的
    oldest = latest_user_turns[-1]
    return oldest.get('id') if oldest else None


def _get_latest_summary_record(conversation_id: str, user_id: str):
    """获取最新的摘要记录

    Args:
        conversation_id: 会话ID
        user_id: 用户ID

    Returns:
        摘要记录字典或 None
    """
    try:
        with get_db_session() as session:
            summary = crud_conversation_summary.get_latest(
                session, conversation_id, user_id
            )

            if not summary:
                return None

            # 转换为字典，避免 DetachedInstanceError
            return {
                'id': summary.id,
                'conversation_id': summary.conversation_id,
                'user_id': summary.user_id,
                'content': summary.content,
                'last_message_id': summary.last_message_id,
                'create_time': summary.create_time,
                'update_time': summary.update_time,
                'deleted': summary.deleted,
            }
    except Exception as e:
        logger.exception(f"获取摘要记录失败: {e}")
        return None


def _resolve_summary_start_id(summary) -> Optional[str]:
    """解析摘要起始消息 ID

    Args:
        summary: 摘要记录字典或 None

    Returns:
        Optional[str]: 起始消息 ID
    """
    if not summary:
        return None

    # 支持字典和ORM对象两种类型
    if isinstance(summary, dict):
        last_message_id = summary.get('last_message_id')
        update_time = summary.get('update_time')
        create_time = summary.get('create_time')
        conversation_id = summary.get('conversation_id')
        user_id = summary.get('user_id')
    else:
        # ORM对象（兼容旧代码）
        last_message_id = getattr(summary, 'last_message_id', None)
        update_time = getattr(summary, 'update_time', None)
        create_time = getattr(summary, 'create_time', None)
        conversation_id = getattr(summary, 'conversation_id', None)
        user_id = getattr(summary, 'user_id', None)

    # 优先使用 last_message_id
    if last_message_id:
        return last_message_id

    # 否则使用更新时间之前的最大消息 ID
    after_time = update_time or create_time
    if not after_time:
        return None

    return _find_max_message_id_at_or_before(
        conversation_id,
        user_id,
        after_time
    )


def _find_max_message_id_at_or_before(
    conversation_id: str,
    user_id: str,
    before_time: datetime
) -> Optional[str]:
    """查找指定时间之前（含）的最大消息 ID

    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        before_time: 截止时间

    Returns:
        Optional[str]: 最大消息 ID
    """
    try:
        with get_db_session() as session:
            return crud_conversation_message.find_max_id_at_or_before(
                session, conversation_id, user_id, before_time
            )
    except Exception as e:
        logger.exception(f"查找消息 ID 失败: {e}")
        return None


def _get_messages_between_ids(
    conversation_id: str,
    user_id: str,
    after_id: Optional[str],
    cutoff_id: str
) -> List:
    """获取两个 ID 之间的消息列表

    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        after_id: 起始 ID（不包含）
        cutoff_id: 截止 ID（包含）

    Returns:
        List: 消息列表
    """
    try:
        with get_db_session() as session:
            messages = crud_conversation_message.list_between_ids(
                session, conversation_id, user_id, after_id, cutoff_id
            )

            # 在会话内将所有需要的属性提取到字典中，避免 DetachedInstanceError
            return [
                {
                    'id': msg.id,
                    'content': msg.content,
                    'role': msg.role,
                    'create_time': msg.create_time,
                }
                for msg in messages
            ]
    except Exception as e:
        logger.exception(f"获取消息列表失败: {e}")
        return []


def _resolve_last_message_id(to_summarize: List) -> Optional[str]:
    """解析最后一条消息 ID

    Args:
        to_summarize: 待摘要消息列表（可能是字典或ORM对象）

    Returns:
        Optional[str]: 最后一条消息 ID
    """
    for i in range(len(to_summarize) - 1, -1, -1):
        item = to_summarize[i]
        if not item:
            continue

        # 支持字典和ORM对象两种类型
        if isinstance(item, dict):
            msg_id = item.get('id')
        else:
            # ORM对象，需要确保在会话内已经加载了id属性
            msg_id = getattr(item, 'id', None)

        if msg_id:
            return msg_id

    return None


def _summarize_messages(messages: List, existing_summary: str) -> Optional[str]:
    """使用 LLM 生成摘要

    Args:
        messages: 待摘要的消息列表
        existing_summary: 现有摘要内容

    Returns:
        Optional[str]: 生成的摘要内容
    """
    try:
        # 转换为 ChatMessage 列表
        history_messages = _to_history_messages(messages)

        if not history_messages:
            return existing_summary

        # 加载提示词模板
        prompt_template = load_prompt("conversation-summary")

        # 渲染模板，替换变量
        rendered_prompt = prompt_template.replace(
            "{summary_max_chars}",
            str(_SUMMARY_MAX_CHARS)
        )

        # 构建消息列表
        summary_messages = []
        summary_messages.append(ChatMessage(role="system", content=rendered_prompt))

        # 如果有现有摘要，添加到消息中
        if existing_summary:
            summary_messages.append(ChatMessage(
                role="assistant",
                content=(
                    "历史摘要（仅用于合并去重，不得作为事实新增来源；"
                    "若与本轮对话冲突，以本轮对话为准）：\n" + existing_summary.strip()
                )
            ))

        # 添加待摘要的历史消息
        summary_messages.extend(history_messages)

        # 添加最终指令
        summary_messages.append(ChatMessage(
            role="user",
            content=(
                f"合并以上对话与历史摘要，去重后输出更新摘要。"
                f"要求：严格≤{_SUMMARY_MAX_CHARS}字符；仅一行。"
            )
        ))

        # 调用 LLM 生成摘要
        summary_content = _call_llm(summary_messages)

        logger.info(f"对话摘要生成 - 结果长度: {len(summary_content)} 字符")

        return summary_content

    except Exception as e:
        logger.exception(f"对话摘要生成失败 - 消息数: {len(messages)}")
        return existing_summary


def _to_history_messages(messages: List) -> List[ChatMessage]:
    """将数据库消息转换为 ChatMessage 列表

    Args:
        messages: 数据库消息列表（可能是字典或ORM对象）

    Returns:
        List[ChatMessage]: ChatMessage 列表
    """
    if not messages:
        return []

    result = []
    for msg in messages:
        if not msg:
            continue

        # 支持字典和ORM对象两种类型
        if isinstance(msg, dict):
            content = msg.get('content')
            role = msg.get('role', '').lower()
        else:
            # ORM对象
            content = getattr(msg, 'content', None)
            role = getattr(msg, 'role', '').lower()

        if not content or not role:
            continue

        if role == "user":
            result.append(ChatMessage(role="user", content=content))
        elif role == "assistant":
            result.append(ChatMessage(role="assistant", content=content))

    return result


def _to_chat_message(summary_record) -> Optional[ChatMessage]:
    """将摘要记录转换为 ChatMessage

    Args:
        summary_record: 摘要记录对象

    Returns:
        Optional[ChatMessage]: ChatMessage 对象
    """
    if not summary_record or not summary_record.content:
        return None

    return ChatMessage(role="system", content=summary_record.content)


def _call_llm(messages: List[ChatMessage]) -> str:
    """调用 LLM 生成文本

    Args:
        messages: 消息列表

    Returns:
        str: LLM 生成的文本
    """
    try:
        # 转换为 LangChain 消息格式
        lc_messages = []
        for msg in messages:
            if not msg or not msg.content:
                continue
            if msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))

        # 调用 LLM 生成摘要
        _llm = create_chat_model(temperature=0.1)
        response = _llm.invoke(lc_messages)

        # 提取响应文本
        content = response.content if hasattr(response, 'content') else str(response)
        if not content or not content.strip():
            raise ValueError("LLM 返回空内容")

        return content.strip()

    except Exception as e:
        logger.exception(f"LLM 调用失败: {e}")
        raise


def _create_summary(
    conversation_id: str,
    user_id: str,
    content: str,
    last_message_id: str
):
    """创建摘要记录

    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        content: 摘要内容
        last_message_id: 最后一条消息 ID
    """
    try:
        with get_db_session() as session:
            crud_conversation_summary.create(
                session, conversation_id, user_id, content, last_message_id
            )

            logger.debug(f"创建摘要成功 - conversationId: {conversation_id}")

    except Exception as e:
        logger.exception(f"创建摘要失败: {e}")
