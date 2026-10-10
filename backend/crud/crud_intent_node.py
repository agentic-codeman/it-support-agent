"""
意图节点数据访问层（CRUD）
将意图节点相关的数据库读写操作下沉到该模块，供 intent_node_service 调用
符合 Google Python 编码规范
"""
from typing import Dict, List, Optional

from sqlalchemy import select, update as sa_update
from sqlalchemy.orm import Session

from backend.models.intent_node import IntentNodeModel


def list_all(db: Session) -> List[IntentNodeModel]:
    """查询所有未删除的意图节点（按名称排序）

    Args:
        db: 数据库会话

    Returns:
        意图节点列表
    """
    stmt = select(IntentNodeModel).where(
        IntentNodeModel.deleted == 0
    ).order_by(IntentNodeModel.name)
    return list(db.execute(stmt).scalars().all())


def get_by_id(db: Session, node_id: str) -> Optional[IntentNodeModel]:
    """按主键查询未删除节点

    Args:
        db: 数据库会话
        node_id: 节点 ID

    Returns:
        意图节点对象或 None
    """
    stmt = select(IntentNodeModel).where(
        IntentNodeModel.id == node_id,
        IntentNodeModel.deleted == 0
    )
    return db.execute(stmt).scalar_one_or_none()


def get_by_code(db: Session, intent_code: str) -> Optional[IntentNodeModel]:
    """按意图标识查询未删除节点

    Args:
        db: 数据库会话
        intent_code: 意图标识

    Returns:
        意图节点对象或 None
    """
    stmt = select(IntentNodeModel).where(
        IntentNodeModel.intent_code == intent_code,
        IntentNodeModel.deleted == 0
    )
    return db.execute(stmt).scalar_one_or_none()


def create(db: Session, node: IntentNodeModel) -> IntentNodeModel:
    """新增意图节点

    Args:
        db: 数据库会话
        node: 已构造好的意图节点对象

    Returns:
        新增的意图节点对象
    """
    db.add(node)
    return node


def update(db: Session, node_id: str, update_data: Dict) -> None:
    """按主键更新意图节点字段

    Args:
        db: 数据库会话
        node_id: 节点 ID
        update_data: 待更新的字段映射
    """
    stmt = sa_update(IntentNodeModel).where(
        IntentNodeModel.id == node_id
    ).values(**update_data)
    db.execute(stmt)


def soft_delete_by_ids(db: Session, node_ids: List[str], update_by: str) -> None:
    """按主键列表逻辑删除节点

    Args:
        db: 数据库会话
        node_ids: 节点 ID 列表
        update_by: 操作人
    """
    stmt = sa_update(IntentNodeModel).where(
        IntentNodeModel.id.in_(node_ids)
    ).values(
        deleted=1,
        update_by=update_by
    )
    db.execute(stmt)


def find_descendant_ids(db: Session, parent_code: str) -> List[str]:
    """递归查找某节点所有后代节点的 ID

    Args:
        db: 数据库会话
        parent_code: 父节点意图标识

    Returns:
        所有后代节点的 ID 列表
    """
    stmt = select(IntentNodeModel).where(
        IntentNodeModel.parent_code == parent_code,
        IntentNodeModel.deleted == 0
    )
    children = list(db.execute(stmt).scalars().all())

    ids: List[str] = []
    for child in children:
        ids.append(child.id)
        ids.extend(find_descendant_ids(db, child.intent_code))
    return ids


__all__ = [
    "list_all",
    "get_by_id",
    "get_by_code",
    "create",
    "update",
    "soft_delete_by_ids",
    "find_descendant_ids",
]
