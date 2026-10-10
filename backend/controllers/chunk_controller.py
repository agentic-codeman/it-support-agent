"""
知识库分块 API 控制器
符合 Google Python 编码规范
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.schemas.knowledge import (
    KnowledgeChunkPageRequest,
    KnowledgeChunkBatchRequest,
)
from backend.services import chunk_service
from backend.middleware.jwt_auth_middleware import get_current_username
from backend.utils.results import Results, failure_from_exception

router = APIRouter(prefix="/api/knowledge-base", tags=["分块管理"])


@router.get("/docs/{doc_id}/chunks")
async def page_query_chunks(
    doc_id: str,
    current: int = Query(default=1, ge=1, description="当前页码"),
    size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    enabled: Optional[int] = Query(default=None, description="启用状态筛选"),
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """分页查询分块列表
    
    Args:
        doc_id: 文档ID
        current: 当前页码
        size: 每页数量
        enabled: 启用状态筛选
        db: 数据库会话
        username: 当前用户名
        
    Returns:
        Results: 分页的分块列表
    """
    try:
        request = KnowledgeChunkPageRequest(
            current=current,
            size=size,
            enabled=enabled
        )
        page_result = chunk_service.page_query(db, doc_id, request)
        return Results.success_with_data(page_result)
    except Exception as e:
        return failure_from_exception(e)


@router.delete("/docs/{doc_id}/chunks/{chunk_id}")
async def delete_chunk(
    doc_id: str,
    chunk_id: str,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """删除分块
    
    Args:
        doc_id: 文档ID
        chunk_id: 分块ID
        db: 数据库会话
        username: 当前用户名
        
    Returns:
        Results: 操作结果
    """
    try:
        chunk_service.delete(db, doc_id, chunk_id, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)


@router.patch("/docs/{doc_id}/chunks/{chunk_id}/enable")
async def enable_chunk(
    doc_id: str,
    chunk_id: str,
    value: bool = Query(..., description="是否启用"),
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """启用或禁用单个分块
    
    Args:
        doc_id: 文档ID
        chunk_id: 分块ID
        value: 是否启用
        db: 数据库会话
        username: 当前用户名
        
    Returns:
        Results: 操作结果
    """
    try:
        chunk_service.enable_chunk(db, doc_id, chunk_id, value, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)


@router.patch("/docs/{doc_id}/chunks/batch-enable")
async def batch_enable_chunks(
    doc_id: str,
    value: bool = Query(..., description="是否启用"),
    request: Optional[KnowledgeChunkBatchRequest] = None,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """批量启用或禁用分块
    
    Args:
        doc_id: 文档ID
        value: 是否启用
        request: 批量操作请求（包含分块ID列表）
        db: 数据库会话
        username: 当前用户名
        
    Returns:
        Results: 操作结果
    """
    try:
        chunk_service.batch_toggle_enabled(db, doc_id, request, value, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)


@router.patch("/docs/{doc_id}/chunks/toggle-all")
async def toggle_all_chunks(
    doc_id: str,
    value: bool = Query(..., description="是否启用"),
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """全量启用或禁用文档的所有分块
    
    Args:
        doc_id: 文档ID
        value: 是否启用
        db: 数据库会话
        username: 当前用户名
        
    Returns:
        Results: 操作结果
    """
    try:
        # 批量操作不传 chunk_ids 时，表示对所有分块操作
        chunk_service.batch_toggle_enabled(db, doc_id, None, value, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)
