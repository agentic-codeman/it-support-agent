"""LLM 模型工厂

基于 `backend.conf.model_config` 统一生成各模型实例，采用「模块级单例 + 工厂函数」模式：

- ``create_chat_model()`` / ``get_chat_model()``   主对话模型（llm_model）
- ``get_system_model()``                          系统意图模型（system_model）
- ``get_vl_model()``                              多模态视觉模型（vl_model）
- ``create_embedding_model()`` / ``get_embedding_model()``  向量嵌入模型（embedding_model）

Rerank 走 HTTP API（见 ``backend.utils.rerank_utils``），不在本工厂管理。
"""
from typing import Optional

from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai import ChatOpenAI

from backend.conf.model_config import model_config

from backend.core.logger import logger


def create_chat_model(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    streaming: bool = True,
    **kwargs,
) -> ChatOpenAI:
    """工厂方法：按需构建一个 OpenAI 兼容的 ChatOpenAI 实例（不缓存）。

    Args:
        model: 模型名，默认取配置 llm_model。
        temperature: 采样温度，默认取配置 llm_temperature。
        streaming: 是否开启流式输出，默认 True（invoke 同样可用）。
        **kwargs: 透传给 ChatOpenAI 的额外参数（如 model_kwargs）。
    """
    return ChatOpenAI(
        model=model or model_config.llm_model,
        temperature=model_config.llm_temperature if temperature is None else temperature,
        streaming=streaming,
        api_key=model_config.api_key,
        base_url=model_config.base_url,
        **kwargs,
    )


def create_embedding_model() -> OllamaEmbeddings:
    """工厂方法：构建向量嵌入模型实例（当前为 Ollama bge-m3，不缓存）。"""
    base_url = model_config.embedding_api_url.replace("/api/embed", "")
    return OllamaEmbeddings(model=model_config.embedding_model, base_url=base_url)


# ---- 模块级单例（惰性初始化）----

_chat_model: Optional[ChatOpenAI] = None
_system_model: Optional[ChatOpenAI] = None
_vl_model: Optional[ChatOpenAI] = None
_embedding_model: Optional[OllamaEmbeddings] = None


def get_chat_model() -> ChatOpenAI:
    """获取主对话模型单例（llm_model）。"""
    global _chat_model
    if _chat_model is None:
        _chat_model = create_chat_model()
        logger.info(f"[LLM工厂] 初始化主对话模型：{model_config.llm_model}")
    return _chat_model


def get_system_model() -> ChatOpenAI:
    """获取系统意图模型单例（system_model）。"""
    global _system_model
    if _system_model is None:
        _system_model = create_chat_model(model=model_config.system_model)
        logger.info(f"[LLM工厂] 初始化系统意图模型：{model_config.system_model}")
    return _system_model


def get_vl_model() -> ChatOpenAI:
    """获取多模态视觉模型单例（vl_model），用于图片摘要等。"""
    global _vl_model
    if _vl_model is None:
        _vl_model = create_chat_model(model=model_config.vl_model)
        logger.info(f"[LLM工厂] 初始化多模态视觉模型：{model_config.vl_model}")
    return _vl_model


def get_embedding_model() -> OllamaEmbeddings:
    """获取向量嵌入模型单例（embedding_model）。"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = create_embedding_model()
        logger.info(f"[LLM工厂] 初始化向量嵌入模型：{model_config.embedding_model}")
    return _embedding_model
