"""
流式任务管理器
管理活跃的流式任务，支持硬取消（asyncio.Task.cancel）
"""
import asyncio
from typing import Optional, Dict

from backend.core.logger import logger


class StreamTaskManager:
    """流式任务管理器
    
    支持硬取消：bind_handle 时绑定 asyncio.Task，cancel() 直接调用 task.cancel()
    在任意 await 挂起点立即注入 CancelledError 中断执行。
    """
    
    def __init__(self):
        """初始化任务管理器"""
        # 活跃任务字典：{task_id: {"cancelled": bool, "task": asyncio.Task | None}}
        self._active_tasks: Dict[str, dict] = {}
    
    def bind_handle(self, task_id: str, task: asyncio.Task = None):
        """注册任务并绑定 asyncio.Task
        
        Args:
            task_id: 任务 ID
            task: asyncio.Task 对象，cancel() 时会直接调用 task.cancel() 实现硬取消
        """
        self._active_tasks[task_id] = {
            "cancelled": False,
            "task": task,
        }
        logger.debug(f"任务 {task_id} 已注册")
    
    def cancel(self, task_id: str) -> bool:
        """取消任务（硬取消）
        
        标记 cancelled=True 并直接调用 task.cancel()，
        在任意 await 挂起点立即注入 CancelledError 中断执行。
        
        Args:
            task_id: 任务 ID
            
        Returns:
            bool: 是否成功取消
        """
        if task_id in self._active_tasks:
            self._active_tasks[task_id]["cancelled"] = True
            task = self._active_tasks[task_id].get("task")
            if task and not task.done():
                task.cancel()
                logger.info(f"任务 {task_id} 已硬取消")
            else:
                logger.info(f"任务 {task_id} 已标记为取消（task 已完成或未绑定）")
            return True
        else:
            logger.warning(f"任务 {task_id} 不存在或已完成")
            return False
    
    def is_cancelled(self, task_id: str) -> bool:
        """检查任务是否已取消
        
        Args:
            task_id: 任务 ID
            
        Returns:
            bool: 是否已取消
        """
        if task_id in self._active_tasks:
            return self._active_tasks[task_id].get("cancelled", False)
        return True  # 任务不存在视为已取消
    
    def cleanup(self, task_id: str):
        """清理任务
        
        Args:
            task_id: 任务 ID
        """
        if task_id in self._active_tasks:
            del self._active_tasks[task_id]
            logger.debug(f"任务 {task_id} 已清理")
    
    def get_active_count(self) -> int:
        """获取活跃任务数量
        
        Returns:
            int: 活跃任务数
        """
        return len(self._active_tasks)
    
    def get_stats(self) -> dict:
        """获取任务统计信息
        
        Returns:
            dict: 任务统计
        """
        cancelled_count = sum(1 for t in self._active_tasks.values() if t.get("cancelled"))
        active_count = len(self._active_tasks) - cancelled_count
        
        return {
            "total": len(self._active_tasks),
            "active": active_count,
            "cancelled": cancelled_count
        }


# 全局单例
_stream_task_manager: Optional[StreamTaskManager] = None


def get_stream_task_manager() -> StreamTaskManager:
    """获取流式任务管理器单例
    
    Returns:
        StreamTaskManager: 任务管理器实例
    """
    global _stream_task_manager
    if _stream_task_manager is None:
        _stream_task_manager = StreamTaskManager()
    return _stream_task_manager
