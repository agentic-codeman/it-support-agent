"""
工具模块包
提供通用的工具类和函数
符合 Google Python 编码规范
"""
from backend.utils.result import Result
from backend.utils.error_code import BaseErrorCode
from backend.utils.exceptions import (
    AbstractException,
    ServiceException,
    ClientException,
    ParamException,
)
from backend.utils.results import (
    Results,
    success,
    success_with_data,
    failure,
    failure_from_exception,
    failure_with_code,
)

__all__ = [
    "Result",
    "BaseErrorCode",
    "AbstractException",
    "ServiceException",
    "ClientException",
    "ParamException",
    "Results",
    "success",
    "success_with_data",
    "failure",
    "failure_from_exception",
    "failure_with_code",
]
