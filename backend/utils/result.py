"""
Result response object - Python equivalent of Java Result class
符合 Google Python 编码规范
"""
from typing import Optional, Any, ClassVar, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')


class Result(BaseModel, Generic[T]):
    """Global response object"""
    
    SUCCESS_CODE: ClassVar[str] = "00000"
    
    code: str = ""
    message: str = ""
    data: Optional[T] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def set_code(self, code: str) -> 'Result':
        """Set response code"""
        self.code = code
        return self
    
    def set_message(self, message: str) -> 'Result':
        """Set response message"""
        self.message = message
        return self
    
    def set_data(self, data: Any) -> 'Result':
        """Set response data"""
        self.data = data
        return self
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return self.model_dump()
    
    def __repr__(self):
        return f"Result(code={self.code}, message={self.message}, data={self.data})"


def success_result(data: Any = None, message: str = "成功") -> Result:
    """Create a success result"""
    return Result(
        code=Result.SUCCESS_CODE,
        message=message,
        data=data
    )


def error_result(message: str = "失败", code: str = "ERROR") -> Result:
    """Create an error result"""
    return Result(
        code=code,
        message=message,
        data=None
    )
