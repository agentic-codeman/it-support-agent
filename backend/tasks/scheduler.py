"""
基于 schedule 库的轻量级定时任务调度器
嵌入 FastAPI 进程内运行（后台守护线程），替代原 Celery Beat
"""
import threading
import time

import schedule

from backend.core.logger import logger
from backend.tasks.ticket_tasks import sync_support_tickets_daily

# 调度循环退出信号（模块级单例，start/stop 共享）
_stop_event = threading.Event()


def _scheduler_loop() -> None:
    """后台调度循环：每秒检查一次是否有待执行任务"""
    while not _stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)


def start_scheduler() -> None:
    """启动调度器后台线程并注册定时任务"""
    # 工单增量同步：每天凌晨 2 点（本地时区，容器内通过 TZ=Asia/Shanghai 指定）
    schedule.every().day.at("02:00").do(sync_support_tickets_daily)

    thread = threading.Thread(
        target=_scheduler_loop,
        name="ticket-sync-scheduler",
        daemon=True,
    )
    thread.start()
    logger.info("定时任务调度器已启动（工单增量同步：每天 02:00）")


def stop_scheduler() -> None:
    """停止调度器后台线程"""
    _stop_event.set()
    logger.info("定时任务调度器已停止")
