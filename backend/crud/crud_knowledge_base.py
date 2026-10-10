"""
知识库数据访问层（CRUD）
将知识库相关的数据库读写操作下沉到该模块，供 knowledge_service 调用
符合 Google Python 编码规范
"""
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.knowledge_base import KnowledgeBaseModel
from backend.models.knowledge_document import KnowledgeDocumentModel


def get_by_id(db: Session, kb_id: str) -> Optional[KnowledgeBaseModel]:
    """按 ID 查询未删除知识库

    Args:
        db: 数据库会话
        kb_id: 知识库ID

    Returns:
        知识库对象或 None
    """
    return db.query(KnowledgeBaseModel).filter(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.deleted == 0
    ).first()


def get_by_name(db: Session, name: str, exclude_id: Optional[str] = None) -> Optional[KnowledgeBaseModel]:
    """按名称查询未删除知识库（可排除指定 ID）

    Args:
        db: 数据库会话
        name: 知识库名称
        exclude_id: 排除的知识库ID（用于重命名时排除自身）

    Returns:
        知识库对象或 None
    """
    query = db.query(KnowledgeBaseModel).filter(
        KnowledgeBaseModel.name == name,
        KnowledgeBaseModel.deleted == 0
    )
    if exclude_id:
        query = query.filter(KnowledgeBaseModel.id != exclude_id)
    return query.first()


def get_by_collection_name(db: Session, collection_name: str) -> Optional[KnowledgeBaseModel]:
    """按 Collection 名称查询未删除知识库

    Args:
        db: 数据库会话
        collection_name: Collection名称

    Returns:
        知识库对象或 None
    """
    return db.query(KnowledgeBaseModel).filter(
        KnowledgeBaseModel.collection_name == collection_name,
        KnowledgeBaseModel.deleted == 0
    ).first()


def add(db: Session, kb: KnowledgeBaseModel) -> None:
    """新增知识库（不提交，由调用方控制事务）

    Args:
        db: 数据库会话
        kb: 已构造好的知识库对象
    """
    db.add(kb)


def page_query(
    db: Session,
    current: int,
    size: int,
    name: Optional[str] = None
) -> Tuple[List[KnowledgeBaseModel], int]:
    """分页查询知识库列表

    Args:
        db: 数据库会话
        current: 当前页码（从 1 开始）
        size: 每页数量
        name: 知识库名称（模糊搜索）

    Returns:
        (知识库列表, 总数) 元组
    """
    query = db.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.deleted == 0)

    if name:
        query = query.filter(KnowledgeBaseModel.name.like(f"%{name}%"))

    total = query.count()
    items = query.order_by(KnowledgeBaseModel.update_time.desc()) \
        .offset((current - 1) * size) \
        .limit(size) \
        .all()
    return items, total


def count_documents(db: Session, kb_id: str) -> int:
    """统计知识库下未删除文档数量

    Args:
        db: 数据库会话
        kb_id: 知识库ID

    Returns:
        int: 文档数量
    """
    return db.query(KnowledgeDocumentModel).filter(
        KnowledgeDocumentModel.kb_id == kb_id,
        KnowledgeDocumentModel.deleted == 0
    ).count()


def count_documents_by_kb_ids(db: Session, kb_ids: List[str]) -> Dict[str, int]:
    """批量统计各知识库下未删除文档数量

    Args:
        db: 数据库会话
        kb_ids: 知识库ID列表

    Returns:
        Dict[str, int]: {知识库ID: 文档数量} 映射
    """
    if not kb_ids:
        return {}

    rows = db.query(
        KnowledgeDocumentModel.kb_id,
        func.count(KnowledgeDocumentModel.id).label('count')
    ).filter(
        KnowledgeDocumentModel.kb_id.in_(kb_ids),
        KnowledgeDocumentModel.deleted == 0
    ).group_by(KnowledgeDocumentModel.kb_id).all()

    return {row.kb_id: row.count for row in rows}


__all__ = [
    "get_by_id",
    "get_by_name",
    "get_by_collection_name",
    "add",
    "page_query",
    "count_documents",
    "count_documents_by_kb_ids",
]
