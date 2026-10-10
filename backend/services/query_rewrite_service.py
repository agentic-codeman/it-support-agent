"""
查询改写服务
将用户问题改写成适合RAG检索的查询语句，支持上下文感知（不拆分）

支持两种改写方式：
1. LLM 改写：使用大模型进行智能改写（默认）
2. 规则归一化：当开关关闭时，使用规则方式进行归一化
"""
import json
import os
from typing import List, Optional
import httpx
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langsmith import traceable, set_run_metadata

from backend.schemas.intent import RewriteResult
from backend.conf.app_config import RAGConfig
from backend.client.llm_factory import create_chat_model
from backend.schemas.chat import ChatMessage
from backend.services.prompt_loader import load_prompt
from backend.services.query_term_mapping_service import normalize
from backend.utils.llm_response_cleaner import strip_markdown_code_fence

from backend.core.logger import logger

# 提示词模板名称（对应 prompts/query_rewrite.txt）
PROMPT_TEMPLATE_NAME = "query_rewrite"

def rewrite(user_question: str) -> str:
    """将用户问题改写为适合检索的查询（简化版本）

    Args:
        user_question: 原始用户问题

    Returns:
        str: 改写后的检索查询（如果改写失败，则回退原问题）
    """
    try:
        result = rewrite_with_split(user_question)
        return result.rewritten_question
    except Exception as e:
        logger.exception(f"查询改写失败: {e}")
        return user_question


@traceable(name="rewrite_with_split")
def rewrite_with_split(user_question: str, history: Optional[List[ChatMessage]] = None) -> RewriteResult:
    """改写用户问题，支持会话历史（不拆分）

    Args:
        user_question: 原始用户问题
        history: 会话历史消息列表

    Returns:
        RewriteResult: 改写结果
    """
    # 检查是否启用查询改写功能
    if not RAGConfig.QUERY_REWRITE_ENABLED:
        # 方式 2：规则归一化
        return _rule_based_rewrite(user_question)

    # 方式 1：LLM 改写
    return _llm_based_rewrite(user_question, history)


def _llm_based_rewrite(user_question: str, history: Optional[List[ChatMessage]] = None) -> RewriteResult:
    """基于 LLM 的改写方式（不拆分）

    Args:
        user_question: 原始用户问题
        history: 会话历史消息列表

    Returns:
        RewriteResult: 改写结果
    """
    try:
        # 第一步：术语归一化
        normalized_question = normalize(user_question)

        # 第二步：构建消息列表
        messages = []

        system_prompt = load_prompt(PROMPT_TEMPLATE_NAME)

        # 添加系统提示词
        messages.append(SystemMessage(content=system_prompt))

        # 添加历史消息（只保留最近 2 轮对话，即最多 4 条消息）
        if history and len(history) > 0:
            # 过滤掉 system 角色的消息，只保留 user 和 assistant
            filtered_history = [
                msg for msg in history
                if msg.role in ["user", "assistant"]
            ]
            # 取最近 N 条消息（可配置）
            max_messages = RAGConfig.QUERY_REWRITE_MAX_HISTORY_MESSAGES
            recent_history = filtered_history[-max_messages:] if len(filtered_history) > max_messages else filtered_history

            for msg in recent_history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))

        # 添加当前问题（使用归一化后的问题）
        messages.append(HumanMessage(content=normalized_question))

        # 第三步：调用 LLM
        llm = create_chat_model(temperature=0.1)
        response = llm.invoke(messages)
        raw_response = response.content if hasattr(response, 'content') else str(response)

        # 第四步：解析响应
        result = _parse_rewrite(raw_response)

        if result is not None:
            logger.info(
                f"RAG用户问题查询改写（LLM方式）：\n"
                f"原始问题：{user_question}\n"
                f"归一化后：{normalized_question}\n"
                f"改写结果：{result.rewritten_question}"
            )
            return result

        logger.warning(f"查询改写解析失败，使用归一化问题兜底 - normalizedQuestion={normalized_question}")

    except Exception as e:
        logger.opt(exception=True).warning(f"查询改写 LLM 调用失败，使用归一化问题兜底 - question={user_question}")

    # 统一兜底逻辑：使用归一化问题
    normalized_question = normalize(user_question)
    return RewriteResult(rewritten_question=normalized_question)


def _rule_based_rewrite(user_question: str) -> RewriteResult:
    """基于规则的改写方式（不拆分）

    当查询改写功能开关关闭时使用此方式。
    流程：术语归一化

    Args:
        user_question: 原始用户问题

    Returns:
        RewriteResult: 改写结果
    """
    try:
        # 术语归一化
        normalized = normalize(user_question)

        logger.info(
            f"RAG用户问题查询改写（规则方式）：\n"
            f"原始问题：{user_question}\n"
            f"归一化后：{normalized}"
        )

        return RewriteResult(rewritten_question=normalized)

    except Exception as e:
        logger.exception(f"规则改写失败: {e}")
        # 兜底：返回原问题
        return RewriteResult(rewritten_question=user_question)


def _parse_rewrite(raw: str) -> Optional[RewriteResult]:
    """解析 LLM 返回的改写结果

    Args:
        raw: LLM 原始响应字符串

    Returns:
        Optional[RewriteResult]: 解析后的结果，解析失败返回 None
    """
    try:
        # 移除可能存在的 Markdown 代码块标记
        cleaned = strip_markdown_code_fence(raw)

        # 解析 JSON
        data = json.loads(cleaned)

        if not isinstance(data, dict):
            return None

        # 提取 rewrite 字段
        rewrite = data.get("rewrite", "").strip() if isinstance(data.get("rewrite"), str) else ""

        if not rewrite:
            return None

        return RewriteResult(rewritten_question=rewrite)

    except Exception as e:
        logger.opt(exception=True).warning(f"解析改写结果失败，raw={raw[:200]}")
        return None
