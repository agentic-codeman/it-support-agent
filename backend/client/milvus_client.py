"""Milvus 向量数据库客户端（pymilvus 原生 MilvusClient 单例）。

请勿直接实例化，使用模块级单例 ``milvus_client`` 或 ``get_milvus_client()`` 获取全局唯一实例。
"""
import time

from pymilvus import MilvusClient
from pymilvus.exceptions import MilvusException

from backend.conf.milvus_config import milvus_config
from backend.core.logger import logger

# 模块级单例：模块导入时创建一次，天然单例。
milvus_client = MilvusClient(uri=milvus_config.uri)

# 集合处于 recovering（恢复中）状态时 Milvus 返回的错误码：query node 尚未分配到 channel
RECOVERING_ERROR_CODE = 106

# 删除操作遇到 recovering 瞬态错误时的重试次数与间隔（该状态通常数秒内自行恢复）
DELETE_MAX_RETRIES = 3
DELETE_RETRY_DELAY_SECONDS = 2.0


def get_milvus_client() -> MilvusClient:
    """获取全局唯一的 MilvusClient 实例。"""
    return milvus_client


def _is_recovering_error(exc: Exception) -> bool:
    """判断是否为 Milvus 集合 recovering（恢复中）的瞬态错误。

    Milvus standalone 在重启、加载未完全就绪或 rebalance 期间，集合会短暂处于
    recovering 状态，此时查询节点尚未分配到 channel，delete/query 会报
    "loaded collection do not found any channel in target, may be in recovery"。
    """
    if not isinstance(exc, MilvusException):
        return False
    if getattr(exc, "code", None) == RECOVERING_ERROR_CODE:
        return True
    message = (getattr(exc, "message", "") or "").lower()
    return "recovering" in message or "in recovery" in message


def delete_with_retry(collection_name: str, *, ids=None, filter: str = None) -> dict:
    """删除 Milvus 向量，遇到集合 recovering 瞬态错误时自动退避重试。

    Args:
        collection_name: 集合名称
        ids: 待删除的主键列表
        filter: 删除过滤表达式（按 metadata 字段）

    Returns:
        dict: 删除结果（含 delete_count）

    Raises:
        MilvusException: 重试耗尽后仍失败，或非 recovering 类错误
    """
    last_exc: Exception | None = None
    for attempt in range(DELETE_MAX_RETRIES):
        try:
            return milvus_client.delete(collection_name, ids=ids, filter=filter)
        except MilvusException as exc:
            if not _is_recovering_error(exc):
                raise
            last_exc = exc
            # 触发一次 load 刷新，帮助集合尽快结束 recovering 状态
            try:
                milvus_client.refresh_load(collection_name)
            except Exception:
                pass
            logger.warning(
                f"Milvus 集合 {collection_name} 处于 recovering 状态，"
                f"第 {attempt + 1}/{DELETE_MAX_RETRIES} 次删除失败，"
                f"{DELETE_RETRY_DELAY_SECONDS}s 后重试: {exc}"
            )
            time.sleep(DELETE_RETRY_DELAY_SECONDS)
    raise last_exc
