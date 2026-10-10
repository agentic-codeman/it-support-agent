"""
意图节点 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.schemas.intent_node import (
    IntentNodeCreateRequest,
    IntentNodeUpdateRequest,
    BatchOperationRequest
)
from backend.db.database import get_db
from backend.services import intent_node_service
from backend.utils.results import Results, failure_from_exception
from backend.schemas.user_context import get_current_username

router = APIRouter(prefix="/api/intent-tree", tags=["意图节点管理"])


@router.get("/trees", summary="获取意图树结构")
async def get_intent_tree(db: Session = Depends(get_db)):
    """获取完整的意图树结构

    Returns:
        根节点列表（包含嵌套的子节点）
    """
    try:
        tree = intent_node_service.get_intent_tree(db)
        return Results.success_with_data(tree)
    except Exception as e:
        return failure_from_exception(e)


@router.post("", summary="创建意图节点")
async def create_intent_node(
    request: IntentNodeCreateRequest,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """创建新的意图节点

    Args:
        request: 创建请求
        username: 当前用户名

    Returns:
        新创建的节点ID
    """
    try:
        node_id = intent_node_service.create_node(db, request, username)
        return Results.success_with_data(node_id)
    except Exception as e:
        return failure_from_exception(e)


@router.put("/{node_id}", summary="更新意图节点")
async def update_intent_node(
    node_id: str,
    request: IntentNodeUpdateRequest,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """更新意图节点信息

    Args:
        node_id: 节点ID
        request: 更新请求
        username: 当前用户名
    """
    try:
        intent_node_service.update_node(db, node_id, request, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)


@router.delete("/{node_id}", summary="删除意图节点")
async def delete_intent_node(
    node_id: str,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """删除意图节点（软删除，同时删除所有子节点）

    Args:
        node_id: 节点ID
        username: 当前用户名
    """
    try:
        intent_node_service.delete_node(db, node_id, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)


@router.post("/batch/delete", summary="批量删除节点")
async def batch_delete_nodes(
    request: BatchOperationRequest,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """批量删除意图节点

    Args:
        request: 包含节点ID列表的请求
        username: 当前用户名
    """
    try:
        intent_node_service.batch_delete_nodes(db, request.ids, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)
