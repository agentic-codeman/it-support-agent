"""
对话消息排序枚举
"""
from enum import Enum


class ConversationMessageOrder(Enum):
    """对话消息排序方式"""
    
    # 升序排列（从旧到新）
    ASC = "ASC"
    
    # 降序排列（从新到旧）
    DESC = "DESC"
