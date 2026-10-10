"""
知识库文档分块数据访问层（CRUD）
将分块相关的数据库读写操作下沉到该模块，供 chunk_service 调用
符合 Google Python 编码规范
"""
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.models.knowledge_chunk import KnowledgeChunkModel


def list_by_doc_id(db: Session, doc_id: str) -> List[KnowledgeChunkModel]:
    """查询文档所有未删除分块（按分块序号排序）

    Args:
        db: 数据库会话
        doc_id: 文档ID

    Returns:
        分块列表
    """
    return db.query(KnowledgeChunkModel).filter(
        KnowledgeChunkModel.doc_id == doc_id,
        KnowledgeChunkModel.deleted == 0
    ).order_by(KnowledgeChunkModel.chunk_index).all()


def get_by_doc_and_id(db: Session, doc_id: str, chunk_id: str) -> Optional[KnowledgeChunkModel]:
    """按文档ID和分块ID查询未删除分块

    Args:
        db: 数据库会话
        doc_id: 文档ID
        chunk_id: 分块ID

    Returns:
        分块对象或 None
    """
    return db.query(KnowledgeChunkModel).filter(
        KnowledgeChunkModel.id == chunk_id,
        KnowledgeChunkModel.doc_id == doc_id,
        KnowledgeChunkModel.deleted == 0
    ).first()


def get_by_ids(db: Session, chunk_ids: List[str]) -> List[KnowledgeChunkModel]:
    """按分块ID列表查询未删除分块

    Args:
        db: 数据库会话
        chunk_ids: 分块ID列表

    Returns:
        分块列表
    """
    return db.query(KnowledgeChunkModel).filter(
        KnowledgeChunkModel.id.in_(chunk_ids),
        KnowledgeChunkModel.deleted == 0
    ).all()


def batch_add(db: Session, chunks: List[KnowledgeChunkModel]) -> None:
    """批量新增分块（不提交，由调用方控制事务）

    Args:
        db: 数据库会话
        chunks: 已构造好的分块对象列表
    """
    db.add_all(chunks)


def delete(db: Session, chunk: KnowledgeChunkModel) -> None:
    """物理删除单个分块（不提交，由调用方控制事务）

    Args:
        db: 数据库会话
        chunk: 待删除的分块对象
    """
    db.delete(chunk)


def soft_delete_by_doc_id(db: Session, doc_id: str) -> int:
    """逻辑删除文档所有未删除分块

    Args:
        db: 数据库会话
        doc_id: 文档ID

    Returns:
        int: 影响的分块数量
    """
    return db.query(KnowledgeChunkModel).filter(
        KnowledgeChunkModel.doc_id == doc_id,
        KnowledgeChunkModel.deleted == 0
    ).update({KnowledgeChunkModel.deleted: 1})


def update_enabled_by_doc_id(db: Session, doc_id: str, enabled_value: int) -> int:
    """更新文档所有未删除分块的启用状态

    Args:
        db: 数据库会话
        doc_id: 文档ID
        enabled_value: 目标启用状态（0 或 1）

    Returns:
        int: 影响的分块数量
    """
    return db.query(KnowledgeChunkModel).filter(
        KnowledgeChunkModel.doc_id == doc_id,
        KnowledgeChunkModel.deleted == 0
    ).update({KnowledgeChunkModel.enabled: enabled_value})


def page_query(
    db: Session,
    doc_id: str,
    page_num: int,
    page_size: int,
    enabled: Optional[int] = None
) -> Tuple[List[KnowledgeChunkModel], int]:
    """分页查询分块列表

    Args:
        db: 数据库会话
        doc_id: 文档ID
        page_num: 页码（从 1 开始）
        page_size: 每页数量
        enabled: 启用状态筛选，None 表示不过滤

    Returns:
        (分块列表, 总数) 元组
    """
    query = db.query(KnowledgeChunkModel).filter(
        KnowledgeChunkModel.doc_id == doc_id,
        KnowledgeChunkModel.deleted == 0
    )

    if enabled is not None:
        query = query.filter(KnowledgeChunkModel.enabled == enabled)

    total = query.count()
    offset = (page_num - 1) * page_size
    chunks = query.order_by(KnowledgeChunkModel.chunk_index).offset(offset).limit(page_size).all()
    return chunks, total


__all__ = [
    "list_by_doc_id",
    "get_by_doc_and_id",
    "get_by_ids",
    "batch_add",
    "delete",
    "soft_delete_by_doc_id",
    "update_enabled_by_doc_id",
    "page_query",
]
