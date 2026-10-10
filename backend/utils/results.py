"""
构建全局返回对象构造器，方便开发者构建全局返回对象
对应 Java 中的 Results 类
符合 Google Python 编码规范
"""
from typing import Optional, Any
from backend.utils.result import Result
from backend.utils.error_code import BaseErrorCode
from backend.utils.exceptions import AbstractException


class Results:
    """响应结果构造器"""

    @staticmethod
    def success() -> Result:
        """
        构造成功响应
        
        Returns:
            Result: 成功响应对象
        """
        return Result().set_code(Result.SUCCESS_CODE)

    @staticmethod
    def success_with_data(data: Any) -> Result:
        """
        构造带返回数据的成功响应
        
        Args:
            data: 返回数据
            
        Returns:
            Result: 带数据的成功响应对象
        """
        return Result().set_code(Result.SUCCESS_CODE).set_data(data)

    @staticmethod
    def failure() -> Result:
        """
        构建服务端失败响应
        
        Returns:
            Result: 失败响应对象
        """
        return (
            Result()
            .set_code(BaseErrorCode.SERVICE_ERROR["code"])
            .set_message(BaseErrorCode.SERVICE_ERROR["message"])
        )

    @staticmethod
    def failure_from_exception(exception) -> Result:
        """
        通过 AbstractException 或普通异常构建失败响应
        
        Args:
            exception: 自定义异常对象或普通异常
            
        Returns:
            Result: 失败响应对象
        """
        # 如果是 AbstractException，使用其错误码和消息
        if isinstance(exception, AbstractException):
            error_code = exception.error_code or BaseErrorCode.SERVICE_ERROR["code"]
            error_message = exception.error_message or BaseErrorCode.SERVICE_ERROR["message"]
        else:
            # 普通异常，使用默认错误码和异常消息
            error_code = BaseErrorCode.SERVICE_ERROR["code"]
            error_message = str(exception)
        
        return Result().set_code(error_code).set_message(error_message)

    @staticmethod
    def failure_with_code(error_code: str, error_message: str) -> Result:
        """
        通过 errorCode、errorMessage 构建失败响应
        
        Args:
            error_code: 错误码
            error_message: 错误消息
            
        Returns:
            Result: 失败响应对象
        """
        return Result().set_code(error_code).set_message(error_message)


# 便捷函数（可选）
def success() -> Result:
    """构造成功响应"""
    return Results.success()


def success_with_data(data: Any) -> Result:
    """构造带数据的成功响应"""
    return Results.success_with_data(data)


def failure() -> Result:
    """构造服务端失败响应"""
    return Results.failure()


def failure_from_exception(exception) -> Result:
    """通过异常构造失败响应"""
    return Results.failure_from_exception(exception)


def failure_with_code(error_code: str, error_message: str) -> Result:
    """通过错误码和消息构造失败响应"""
    return Results.failure_with_code(error_code, error_message)
