"""
嵌入工具 - 调用 Embedding API 生成向量
符合 Google Python 编码规范
"""
from typing import List, Optional

from backend.conf.model_config import model_config
from backend.client.llm_factory import get_embedding_model

from backend.core.logger import logger

_dimension = model_config.embedding_dimension


def embed(text: str, model: Optional[str] = None) -> List[float]:
    """将单个文本转换为向量

    Args:
        text: 输入文本
        model: 嵌入模型名称（暂不支持动态切换，使用配置的模型）

    Returns:
        List[float]: 向量表示（浮点数列表）
    """
    if not text or not text.strip():
        return [0.0] * _dimension

    vectors = embed_batch([text])
    return vectors[0] if vectors else [0.0] * _dimension


def embed_batch(texts: List[str], model: Optional[str] = None) -> List[List[float]]:
    """批量将文本转换为向量

    Args:
        texts: 输入文本列表
        model: 嵌入模型名称（暂不支持动态切换，使用配置的模型）

    Returns:
        List[List[float]]: 向量列表
    """
    if not texts:
        return []

    valid_texts = [text if text and text.strip() else " " for text in texts]

    try:
        logger.info(f"调用 Ollama Embedding, model={model_config.embedding_model}, batch_size={len(valid_texts)}")

        vectors = get_embedding_model().embed_documents(valid_texts)

        logger.info(f"Embedding 完成，生成 {len(vectors)} 个向量，维度 {_dimension}")
        return vectors

    except Exception as e:
        logger.error(f"Embedding 失败: {e}")
        raise Exception(f"Embedding 失败: {str(e)}")


__all__ = [
    "embed",
    "embed_batch",
]
