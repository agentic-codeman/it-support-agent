"""
Rerank 工具函数 - 使用阿里云百炼 Qwen3-Rerank API
配置来源于 backend.conf.model_config 的 lm_config
"""
from typing import List, Dict, Any, Optional

import httpx

from backend.conf.model_config import model_config

from backend.core.logger import logger

DEFAULT_TOP_N = 5


def rerank(
    query: str,
    documents: List[str],
    top_n: Optional[int] = None
) -> List[Dict[str, Any]]:
    """对文档列表进行重排序

    Args:
        query: 查询文本
        documents: 待排序的文档列表
        top_n: 返回前 N 个结果（默认 5）

    Returns:
        List[Dict]: 重排序后的结果列表，每个元素包含:
            - index: 原始文档索引
            - text: 文档文本
            - score: 相关性分数
    """
    if not documents:
        return []

    top_n = top_n or DEFAULT_TOP_N

    try:
        logger.info(f"调用 Qwen Rerank API - query长度: {len(query)}, 文档数: {len(documents)}")

        # 构建请求体（对齐阿里云百炼 API 格式）
        payload = {
            "model": model_config.rerank_model,
            "input": {
                "query": query,
                "documents": documents
            },
            "parameters": {
                "top_n": min(top_n, len(documents))
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {model_config.api_key}"
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                model_config.rerank_base_url,
                json=payload,
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"❌ Rerank API 请求失败: {response.status_code} - {response.text}")
                return _degrade(documents)

            result = response.json()

            # 解析响应（对齐阿里云百炼 API 响应格式）
            reranked_results = []
            for item in result.get("output", {}).get("results", []):
                idx = item.get("index", 0)
                reranked_results.append({
                    "index": idx,
                    "text": documents[idx],
                    "score": item.get("relevance_score", 0.0)
                })

            logger.info(f"✅ Rerank 完成 - 返回 {len(reranked_results)} 个结果")
            return reranked_results

    except Exception as e:
        logger.exception(f"❌ Rerank 失败: {e}")
        return _degrade(documents)


def _degrade(documents: List[str]) -> List[Dict[str, Any]]:
    """降级：返回原始顺序。"""
    return [
        {"index": i, "text": doc, "score": 0.5}
        for i, doc in enumerate(documents)
    ]
