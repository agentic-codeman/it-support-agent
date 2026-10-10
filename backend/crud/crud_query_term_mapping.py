"""
查询术语映射数据访问层（CRUD）
将关键词映射相关的数据库读写操作下沉到该模块，供 query_term_mapping_service 调用
符合 Google Python 编码规范
"""
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.models.query_term_mapping import QueryTermMapping


def get_by_id(db: Session, mapping_id: str) -> Optional[QueryTermMapping]:
    """按主键查询映射记录

    Args:
        db: 数据库会话
        mapping_id: 映射规则 ID

    Returns:
        映射记录对象或 None
    """
    return db.query(QueryTermMapping).filter(
        QueryTermMapping.id == mapping_id
    ).first()


def add(db: Session, record: QueryTermMapping) -> None:
    """新增映射记录（不提交，由调用方控制事务）

    Args:
        db: 数据库会话
        record: 已构造好的映射记录对象
    """
    db.add(record)


def delete(db: Session, record: QueryTermMapping) -> None:
    """删除映射记录（不提交，由调用方控制事务）

    Args:
        db: 数据库会话
        record: 待删除的映射记录对象
    """
    db.delete(record)


def list_enabled(db: Session) -> List[QueryTermMapping]:
    """查询所有启用的映射记录（按优先级、更新时间排序）

    Args:
        db: 数据库会话

    Returns:
        启用的映射记录列表
    """
    return db.query(QueryTermMapping).filter(
        QueryTermMapping.enabled == True
    ).order_by(
        QueryTermMapping.priority.desc(),
        QueryTermMapping.update_time.desc()
    ).all()


def page_query(
    db: Session,
    current: int,
    size: int,
    keyword: Optional[str] = None
) -> Tuple[List[QueryTermMapping], int]:
    """分页查询映射记录

    Args:
        db: 数据库会话
        current: 当前页码（从 1 开始）
        size: 每页数量
        keyword: 关键词搜索（匹配 source_term 或 target_term）

    Returns:
        (映射记录列表, 总数) 元组
    """
    query = db.query(QueryTermMapping)

    if keyword:
        keyword = keyword.strip()
        query = query.filter(
            or_(
                QueryTermMapping.source_term.like(f"%{keyword}%"),
                QueryTermMapping.target_term.like(f"%{keyword}%")
            )
        )

    total = query.count()
    records = (
        query.order_by(
            QueryTermMapping.priority.desc(),
            QueryTermMapping.update_time.desc()
        )
        .offset((current - 1) * size)
        .limit(size)
        .all()
    )
    return records, total


__all__ = [
    "get_by_id",
    "add",
    "delete",
    "list_enabled",
    "page_query",
]
