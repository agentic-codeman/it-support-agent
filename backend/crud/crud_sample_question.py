"""
示例问题数据访问层（CRUD）
将示例问题相关的数据库读写操作下沉到该模块，供 sample_question_service 调用
符合 Google Python 编码规范
"""
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.models.sample_question import SampleQuestionModel


def get_by_id(db: Session, question_id: str) -> Optional[SampleQuestionModel]:
    """按主键查询未删除示例问题

    Args:
        db: 数据库会话
        question_id: 示例问题 ID

    Returns:
        示例问题对象或 None
    """
    return db.query(SampleQuestionModel).filter(
        SampleQuestionModel.id == question_id,
        SampleQuestionModel.deleted == 0
    ).first()


def page_query(
    db: Session,
    page_num: int,
    page_size: int,
    keyword: Optional[str] = None
) -> Tuple[List[SampleQuestionModel], int]:
    """分页查询未删除示例问题

    Args:
        db: 数据库会话
        page_num: 页码
        page_size: 每页数量
        keyword: 搜索关键词（标题/描述/问题）

    Returns:
        (示例问题列表, 总数) 元组
    """
    query = db.query(SampleQuestionModel).filter(
        SampleQuestionModel.deleted == 0
    )

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (SampleQuestionModel.title.like(like)) |
            (SampleQuestionModel.description.like(like)) |
            (SampleQuestionModel.question.like(like))
        )

    total = query.count()
    items = query.order_by(
        SampleQuestionModel.update_time.desc(),
        SampleQuestionModel.create_time.desc()
    ).offset((page_num - 1) * page_size).limit(page_size).all()

    return items, total


def create(
    db: Session,
    title: Optional[str],
    description: Optional[str],
    question: str
) -> SampleQuestionModel:
    """新增示例问题（不提交，由调用方控制事务）

    Args:
        db: 数据库会话
        title: 展示标题
        description: 描述或提示
        question: 示例问题内容

    Returns:
        创建的示例问题对象
    """
    from backend.utils.snowflake_id_utils import generate_snowflake_id_str

    record = SampleQuestionModel(
        id=generate_snowflake_id_str(),
        title=title,
        description=description,
        question=question,
        deleted=0
    )
    db.add(record)
    return record


def update(
    db: Session,
    record: SampleQuestionModel,
    title: Optional[str] = None,
    description: Optional[str] = None,
    question: Optional[str] = None
) -> SampleQuestionModel:
    """更新示例问题字段

    参数为 None 表示跳过对应字段的更新。

    Args:
        db: 数据库会话
        record: 待更新的示例问题对象
        title: 新标题
        description: 新描述
        question: 新问题内容

    Returns:
        更新后的示例问题对象
    """
    if title is not None:
        record.title = title
    if description is not None:
        record.description = description
    if question is not None:
        record.question = question

    return record


def soft_delete(db: Session, record: SampleQuestionModel) -> None:
    """逻辑删除示例问题（不提交，由调用方控制事务）

    Args:
        db: 数据库会话
        record: 待删除的示例问题对象
    """
    record.deleted = 1


def list_random(db: Session, limit: int) -> List[SampleQuestionModel]:
    """随机查询未删除示例问题列表

    Args:
        db: 数据库会话
        limit: 返回数量限制

    Returns:
        随机示例问题列表
    """
    from sqlalchemy import func

    return db.query(SampleQuestionModel).filter(
        SampleQuestionModel.deleted == 0
    ).order_by(func.rand()).limit(limit).all()


__all__ = [
    "get_by_id",
    "page_query",
    "create",
    "update",
    "soft_delete",
    "list_random",
]
