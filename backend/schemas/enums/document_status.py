"""
文档处理状态枚举
"""
from enum import Enum


class DocumentStatus(Enum):
    """文档处理状态枚举
    
    表示文档在处理过程中可能处于的各种状态
    """
    
    # 文档待处理
    PENDING = "pending"
    
    # 文档处理中
    RUNNING = "running"
    
    # 文档处理失败
    FAILED = "failed"
    
    # 文档处理成功
    SUCCESS = "success"
    
    @classmethod
    def from_code(cls, code: str) -> "DocumentStatus":
        """从状态码获取枚举值
        
        Args:
            code: 状态码字符串
            
        Returns:
            DocumentStatus: 对应的枚举值
            
        Raises:
            ValueError: 如果状态码无效
        """
        for status in cls:
            if status.value == code:
                return status
        raise ValueError(f"Invalid document status code: {code}")
    
    @classmethod
    def get_all_codes(cls) -> list[str]:
        """获取所有状态码
        
        Returns:
            list[str]: 所有状态码列表
        """
        return [status.value for status in cls]
