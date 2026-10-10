"""
示例问题控制器
提供示例问题的 RESTful API 接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.utils.results import Results
from backend.utils.exceptions import AbstractException
from backend.schemas.sample_question import (
    SampleQuestionCreateRequest,
    SampleQuestionUpdateRequest,
    SampleQuestionPageRequest,
    SampleQuestionVO
)
from backend.services import sample_question_service
from backend.middleware.jwt_auth_middleware import require_admin
from backend.core.logger import logger

router = APIRouter(prefix="/sample-questions", tags=["示例问题管理"])


@router.get("/random")
async def list_random_sample_questions(
    request: Request,
    limit: int = 3,
    db: Session = Depends(get_db)
):
    """
    随机获取示例问题列表（用于欢迎页展示）
    
    Args:
        limit: 返回数量限制，默认3条
        
    Returns:
        随机示例问题列表
    """
    try:
        result = sample_question_service.list_random_questions(db, limit)
        data = [q.model_dump(mode='json') for q in result]
        return JSONResponse(content={"code": "00000", "message": "", "data": data})
    except Exception as e:
        logger.exception(f"获取随机示例问题失败: {str(e)}")
        return JSONResponse(status_code=500, content={"code": "50000", "message": str(e), "data": None})


@router.get("")
async def page_query_sample_questions(
    request: Request,
    page_num: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)  # 需要管理员权限
):
    """
    分页查询示例问题列表
    
    Args:
        page_num: 页码
        page_size: 每页数量
        keyword: 搜索关键词（标题/描述/问题）
        
    Returns:
        分页示例问题列表
    """
    try:
        # 构建分页请求对象
        page_request = SampleQuestionPageRequest(
            page_num=page_num,
            page_size=page_size,
            keyword=keyword
        )
        
        result = sample_question_service.page_query(db, page_request)
        return Results.success_with_data(result.model_dump(mode='json'))
    except AbstractException as e:
        logger.error(f"查询示例问题列表失败: {e.error_message}")
        return Results.failure_from_exception(e)
    except Exception as e:
        logger.exception(f"查询示例问题列表失败: {str(e)}")
        return Results.failure_with_code("50000", str(e))


@router.post("")
async def create_sample_question(
    request: SampleQuestionCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)  # 需要管理员权限
):
    """
    创建示例问题
    
    Args:
        request: 示例问题创建请求
        
    Returns:
        创建的示例问题信息
    """
    try:
        question = sample_question_service.create(db, request)
        return Results.success_with_data(SampleQuestionVO.model_validate(question).model_dump(mode='json'))
    except AbstractException as e:
        logger.error(f"创建示例问题失败: {e.error_message}")
        return Results.failure_from_exception(e)
    except Exception as e:
        logger.exception(f"创建示例问题失败: {str(e)}")
        return Results.failure_with_code("50000", str(e))


@router.put("/{question_id}")
async def update_sample_question(
    question_id: str,
    request: SampleQuestionUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)  # 需要管理员权限
):
    """
    更新示例问题
    
    Args:
        question_id: 示例问题ID
        request: 示例问题更新请求
        
    Returns:
        更新结果
    """
    try:
        question = sample_question_service.update(db, question_id, request)
        return Results.success_with_data({
            "message": "示例问题更新成功",
            "question": SampleQuestionVO.model_validate(question).model_dump(mode='json')
        })
    except AbstractException as e:
        logger.error(f"更新示例问题失败: {e.error_message}")
        return Results.failure_from_exception(e)
    except Exception as e:
        logger.exception(f"更新示例问题失败: {str(e)}")
        return Results.failure_with_code("50000", str(e))


@router.delete("/{question_id}")
async def delete_sample_question(
    question_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)  # 需要管理员权限
):
    """
    删除示例问题（逻辑删除）
    
    Args:
        question_id: 示例问题ID
        
    Returns:
        删除结果
    """
    try:
        sample_question_service.delete(db, question_id)
        return Results.success_with_data({"message": "示例问题删除成功"})
    except AbstractException as e:
        logger.error(f"删除示例问题失败: {e.error_message}")
        return Results.failure_from_exception(e)
    except Exception as e:
        logger.exception(f"删除示例问题失败: {str(e)}")
        return Results.failure_with_code("50000", str(e))
