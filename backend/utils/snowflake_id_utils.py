"""
分布式 ID 生成器 - 基于 snowflake-id 开源库封装
符合 Google Python 编码规范
"""
import threading
import time

from snowflake import SnowflakeGenerator

# 起始时间戳（2020-01-01 00:00:00 UTC），与既有数据 ID 长度保持一致
EPOCH = 1577836800000

# 全局单例生成器 + 锁。snowflake-id 库自身非线程安全，
# FastAPI 同步接口在多线程下并发调用，需加锁串行化。
_default_generator = SnowflakeGenerator(instance=1, epoch=EPOCH)
_lock = threading.Lock()


def _next_available_id() -> int:
    """生成一个有效 ID。

    snowflake-id 的 next() 在同毫秒序列号耗尽或时钟回拨时会返回 None，
    此处循环等待跨过当前毫秒后重试。
    """
    while True:
        with _lock:
            value = next(_default_generator)
        if value is not None:
            return value
        time.sleep(0.0005)


def generate_snowflake_id() -> int:
    """生成雪花算法 ID。

    Returns:
        int: 生成的唯一 ID
    """
    return _next_available_id()


def generate_snowflake_id_str() -> str:
    """生成雪花算法 ID 字符串。

    Returns:
        str: 生成的唯一 ID 字符串
    """
    return str(_next_available_id())
