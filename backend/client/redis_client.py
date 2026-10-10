import redis

from backend.conf.redis_config import redis_config

from backend.core.logger import logger


class RedisClient:
    """Redis 客户端封装，基于共享连接池。

    请勿直接实例化，使用模块级单例 ``redis_client`` 或
    ``get_redis_client()`` 获取全局唯一实例。
    """

    def __init__(self, pool: redis.ConnectionPool):
        self.client = redis.Redis(connection_pool=pool)

    def ping(self) -> bool:
        """健康检查，连接异常时返回 False（不抛出）。"""
        try:
            return bool(self.client.ping())
        except redis.RedisError as e:
            logger.error(f"Redis ping 失败: {e}")
            return False

    def get_raw_client(self) -> redis.Redis | None:
        """返回原生 redis.Redis 实例；连接失败时返回 None（调用方降级为内存缓存）。"""
        return self.client if self.ping() else None

    # ----- 常用基础操作封装 -----

    def set(self, key: str, value: str, ex: int = None) -> bool:
        """设置 String 键值，ex 为过期时间（秒）。"""
        return self.client.set(key, value, ex=ex)

    def get(self, key: str) -> str | None:
        """获取 String 值。"""
        return self.client.get(key)

    def delete(self, *keys: str) -> int:
        """删除一个或多个键，返回删除的键数量。"""
        return self.client.delete(*keys)

    def hset(self, name: str, key: str, value: str) -> int:
        """设置 Hash 字段。"""
        return self.client.hset(name, key, value)

    def hget(self, name: str, key: str) -> str | None:
        """获取 Hash 字段值。"""
        return self.client.hget(name, key)


def _build_pool() -> redis.ConnectionPool:
    """根据 redis_config 构建连接池。"""
    return redis.ConnectionPool(
        host=redis_config.host,
        port=redis_config.port,
        db=redis_config.db,
        password=redis_config.password or None,
        decode_responses=True,   # 自动将返回的 bytes 转换为 str
        max_connections=20,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )


# 模块级连接池与客户端：模块导入时创建一次，天然单例。
_pool = _build_pool()
redis_client = RedisClient(_pool)


def get_redis_client() -> RedisClient:
    """获取全局唯一的 RedisClient 实例。"""
    return redis_client


if __name__ == "__main__":
    client = get_redis_client()

    # 1. 单例测试：工厂函数返回的始终是模块级实例
    logger.info(f"单例测试: get_redis_client() is redis_client -> {get_redis_client() is redis_client}")

    # 2. 健康检查
    logger.info(f"ping 测试: {client.ping()}")

    # 3. String 读写与删除
    client.set("test:string", "hello redis", ex=60)
    logger.info(f"set/get 测试: {client.get('test:string')}")
    client.delete("test:string")
    logger.info(f"delete 测试: 删除后 get -> {client.get('test:string')}")

    # 4. Hash 读写
    client.hset("test:hash", "field1", "value1")
    logger.info(f"hset/hget 测试: {client.hget('test:hash', 'field1')}")
    client.delete("test:hash")
