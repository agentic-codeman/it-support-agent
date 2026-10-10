"""
RAG 聊天相关的 Pydantic Schema
符合 Google Python 编码规范
"""
from pydantic import BaseModel, Field
from typing import Optional
from dataclasses import dataclass


class StopTaskRequest(BaseModel):
    """停止任务请求模型"""
    task_id: str = Field(..., description="任务 ID")


@dataclass
class ChatMessage:
    """聊天消息数据类"""
    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class ConversationMessageVO:
    """对话消息视图对象"""
    id: str  # 消息ID
    conversation_id: str  # 会话ID
    role: str  # 角色：user/assistant
    content: str  # 消息内容
    vote: Optional[int] = None  # 投票：1=点赞, -1=点踩, None=未投票
    create_time: Optional[str] = None  # 创建时间
