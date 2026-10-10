"""
基础错误码定义
"""


class BaseErrorCode:
    """基础错误码枚举"""
    
    # 成功码
    SUCCESS = "00000"
    
    # 服务端错误
    SERVICE_ERROR = {
        "code": "50000",
        "message": "服务端错误"
    }
    
    # 客户端错误
    CLIENT_ERROR = {
        "code": "40000",
        "message": "客户端错误"
    }
    
    # 参数错误
    PARAM_ERROR = {
        "code": "40001",
        "message": "参数错误"
    }
    
    # 未授权
    UNAUTHORIZED = {
        "code": "40100",
        "message": "未授权"
    }
    
    # 禁止访问
    FORBIDDEN = {
        "code": "40300",
        "message": "禁止访问"
    }
    
    # 资源不存在
    NOT_FOUND = {
        "code": "40400",
        "message": "资源不存在"
    }
