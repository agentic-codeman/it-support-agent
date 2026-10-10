"""
工单同步任务
- 每日凌晨 2 点增量同步昨日关闭的工单（由 scheduler 定时触发）
- 首次上线需手动触发一次全量同步
"""
import time

from backend.core.logger import logger
from backend.services import ticket_sync_service

# 任务失败重试次数与间隔（对齐原 Celery 任务 max_retries=3 / default_retry_delay=60）
_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 60


def sync_support_tickets_daily() -> int:
    """每日增量同步：拉取「更新时间为昨天」且已关闭的工单写入 Milvus"""
    logger.info("开始执行工单增量同步任务")
    return _sync_with_retry("增量", ticket_sync_service.incremental_sync)


def sync_support_tickets_full() -> int:
    """全量同步：拉取所有已关闭工单写入 Milvus（首次初始化用，手动触发）"""
    logger.info("开始执行工单全量同步任务")
    return _sync_with_retry("全量", ticket_sync_service.full_sync)


def _sync_with_retry(name: str, sync_func) -> int:
    """执行同步并做有限重试；失败返回 0 而不抛异常，避免打断调度线程"""
    last_exc = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            count = sync_func()
            logger.info(f"工单{name}同步任务完成，写入 {count} 条 chunk")
            return count
        except Exception as e:
            last_exc = e
            logger.exception(f"工单{name}同步失败（第 {attempt}/{_MAX_RETRIES} 次）: {e}")
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY_SECONDS)
    logger.error(f"工单{name}同步重试耗尽，放弃本次同步: {last_exc}")
    return 0
