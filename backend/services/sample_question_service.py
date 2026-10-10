"""
示例问题服务
提供示例问题的业务逻辑
符合 Google Python 编码规范
"""
import math
from typing import List

from sqlalchemy.orm import Session

from backend.crud import crud_sample_question
from backend.models.sample_question import SampleQuestionModel
from backend.schemas.sample_question import (
    SampleQuestionCreateRequest,
    SampleQuestionUpdateRequest,
    SampleQuestionPageRequest,
    SampleQuestionPageResponse,
    SampleQuestionVO
)
from backend.utils.exceptions import ClientException

from backend.core.logger import logger


def page_query(db: Session, request: SampleQuestionPageRequest) -> SampleQuestionPageResponse:
    """分页查询示例问题

    Args:
        db: 数据库会话
        request: 分页请求

    Returns:
        分页响应结果
    """
    items, total = crud_sample_question.page_query(
        db,
        page_num=request.page_num,
        page_size=request.page_size,
        keyword=request.keyword
    )

    total_pages = math.ceil(total / request.page_size) if total > 0 else 0

    return SampleQuestionPageResponse(
        list=[SampleQuestionVO.model_validate(item) for item in items],
        total=total,
        page_num=request.page_num,
        page_size=request.page_size,
        total_pages=total_pages
    )


def create(db: Session, request: SampleQuestionCreateRequest) -> SampleQuestionModel:
    """创建示例问题

    Args:
        db: 数据库会话
        request: 创建请求

    Returns:
        创建的示例问题对象

    Raises:
        ClientException: 示例问题内容为空
    """
    if not request.question or not request.question.strip():
        raise ClientException("示例问题内容不能为空")

    try:
        question = crud_sample_question.create(
            db,
            title=request.title,
            description=request.description,
            question=request.question.strip()
        )

        db.commit()
        db.refresh(question)

        logger.info(f"创建示例问题成功: {question.id}")
        return question
    except Exception:
        db.rollback()
        raise


def update(db: Session, question_id: str, request: SampleQuestionUpdateRequest) -> SampleQuestionModel:
    """更新示例问题

    Args:
        db: 数据库会话
        question_id: 示例问题 ID
        request: 更新请求

    Returns:
        更新后的示例问题对象

    Raises:
        ClientException: 示例问题不存在或内容为空
    """
    question = _get_or_raise(db, question_id)

    if request.question is not None and not request.question.strip():
        raise ClientException("示例问题内容不能为空")

    try:
        crud_sample_question.update(
            db,
            question,
            title=request.title,
            description=request.description,
            question=request.question.strip() if request.question is not None else None
        )

        db.commit()
        db.refresh(question)

        logger.info(f"更新示例问题成功: {question_id}")
        return question
    except Exception:
        db.rollback()
        raise


def delete(db: Session, question_id: str) -> None:
    """删除示例问题（逻辑删除）

    Args:
        db: 数据库会话
        question_id: 示例问题 ID

    Raises:
        ClientException: 示例问题不存在
    """
    question = _get_or_raise(db, question_id)

    try:
        crud_sample_question.soft_delete(db, question)

        db.commit()

        logger.info(f"删除示例问题成功: {question_id}")
    except Exception:
        db.rollback()
        raise


def list_random_questions(db: Session, limit: int = 3) -> List[SampleQuestionVO]:
    """随机获取示例问题列表（用于欢迎页展示）

    Args:
        db: 数据库会话
        limit: 返回数量限制，默认 3 条

    Returns:
        随机示例问题列表
    """
    questions = crud_sample_question.list_random(db, limit)

    return [SampleQuestionVO.model_validate(q) for q in questions]


def _get_or_raise(db: Session, question_id: str) -> SampleQuestionModel:
    """获取示例问题或抛出异常

    Args:
        db: 数据库会话
        question_id: 示例问题 ID

    Returns:
        示例问题模型

    Raises:
        ClientException: 示例问题不存在
    """
    question = crud_sample_question.get_by_id(db, question_id)

    if not question:
        raise ClientException("示例问题不存在")

    return question


__all__ = [
    "page_query",
    "create",
    "update",
    "delete",
    "list_random_questions",
]
