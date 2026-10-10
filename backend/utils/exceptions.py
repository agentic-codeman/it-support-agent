"""
自定义异常类
"""
from typing import Optional


class AbstractException(Exception):
    """抽象异常基类"""
    
    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self._error_message = message
        self._error_code = error_code
        self._cause = cause
    
    @property
    def error_code(self) -> Optional[str]:
        """获取错误码"""
        return self._error_code
    
    @property
    def error_message(self) -> Optional[str]:
        """获取错误消息"""
        return self._error_message
    
    @property
    def cause(self) -> Optional[Exception]:
        """获取原始异常"""
        return self._cause


class ServiceException(AbstractException):
    """服务端异常"""
    
    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message or "服务端错误",
            error_code=error_code or "50000",
            cause=cause
        )


class ClientException(AbstractException):
    """客户端异常"""
    
    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message or "客户端错误",
            error_code=error_code or "40000",
            cause=cause
        )


class ParamException(AbstractException):
    """参数异常"""
    
    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message or "参数错误",
            error_code=error_code or "40001",
            cause=cause
        )
