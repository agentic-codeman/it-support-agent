"""
手动触发工单全量同步（首次上线初始化用）
运行方式（在仓库根目录下）：
    python manual_sync_support_tickets_full.py
"""
from backend.tasks.ticket_tasks import sync_support_tickets_full


if __name__ == "__main__":
    count = sync_support_tickets_full()
    print(f"全量同步完成，共写入 {count} 条 chunk")
