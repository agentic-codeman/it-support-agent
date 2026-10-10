"""
Redis 分布式锁工具

基于 SET NX EX 实现，供需要跨实例互斥的场景（如对话摘要）复用。
"""
from backend.client.redis_client import get_redis_client

from backend.core.logger import logger

# 模块级单例：复用全局共享连接池（对齐 redis_client 的收敛策略）
_redis_client = get_redis_client().get_raw_client()


def try_lock(lock_key: str, ttl: int) -> bool:
    """尝试获取分布式锁

    Args:
        lock_key: 锁的 key
        ttl: 锁的过期时间（秒）

    Returns:
        bool: 是否成功获取锁。Redis 不可用时返回 False。
    """
    if not _redis_client:
        logger.warning(f"Redis 不可用，无法获取锁 - lockKey: {lock_key}")
        return False

    try:
        # SET NX EX：仅在键不存在时设置，并附带过期时间
        result = _redis_client.set(lock_key, "1", nx=True, ex=ttl)

        if result:
            logger.debug(f"获取 Redis 分布式锁成功 - lockKey: {lock_key}")
            return True

        logger.debug(f"获取 Redis 分布式锁失败（锁已存在） - lockKey: {lock_key}")
        return False

    except Exception as e:
        logger.exception(f"获取分布式锁失败: {e}")
        return False


def unlock(lock_key: str):
    """释放分布式锁

    Args:
        lock_key: 锁的 key
    """
    if not _redis_client:
        return

    try:
        _redis_client.delete(lock_key)
        logger.debug(f"释放 Redis 分布式锁成功 - lockKey: {lock_key}")
    except Exception as e:
        logger.exception(f"释放分布式锁失败: {e}")
