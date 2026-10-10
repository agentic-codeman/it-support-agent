"""
知识库 API 控制器
符合 Google Python 编码规范
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.schemas.knowledge import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseUpdateRequest,
)
from backend.services import knowledge_service
from backend.middleware.jwt_auth_middleware import get_current_username
from backend.utils.results import Results, failure_from_exception

router = APIRouter(prefix="/api/knowledge-base", tags=["知识库管理"])


@router.post("")
async def create_knowledge_base(
    request: KnowledgeBaseCreateRequest,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """创建知识库
    
    Args:
        request: 创建知识库请求
        db: 数据库会话
        username: 当前登录用户名
        
    Returns:
        Results: 包含知识库ID的响应
    """
    try:
        kb_id = knowledge_service.create(db, request, username)
        return Results.success_with_data(kb_id)
    except Exception as e:
        return failure_from_exception(e)


@router.put("/{kb_id}")
async def rename_knowledge_base(
    kb_id: str,
    request: KnowledgeBaseUpdateRequest,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """重命名知识库
    
    Args:
        kb_id: 知识库ID
        request: 更新请求
        db: 数据库会话
        username: 当前登录用户名
        
    Returns:
        Results: 操作结果
    """
    try:
        knowledge_service.rename(db, kb_id, request, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """删除知识库
    
    Args:
        kb_id: 知识库ID
        db: 数据库会话
        username: 当前登录用户名
        
    Returns:
        Results: 操作结果
    """
    try:
        knowledge_service.delete(db, kb_id, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)


@router.get("/{kb_id}")
async def query_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """查询知识库详情
    
    Args:
        kb_id: 知识库ID
        db: 数据库会话
        
    Returns:
        Results: 知识库详情
    """
    try:
        kb_vo = knowledge_service.query_by_id(db, kb_id)
        return Results.success_with_data(kb_vo)
    except Exception as e:
        return failure_from_exception(e)


@router.get("")
async def page_query_knowledge_base(
    current: int = Query(default=1, ge=1, description="当前页码"),
    size: int = Query(default=10, ge=1, le=500, description="每页数量"),
    name: Optional[str] = Query(default=None, description="知识库名称（模糊搜索）"),
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """分页查询知识库列表
    
    Args:
        current: 当前页码
        size: 每页数量
        name: 知识库名称（模糊搜索）
        db: 数据库会话
        
    Returns:
        Results: 分页结果
    """
    try:
        page_result = knowledge_service.page_query(db, current, size, name)
        return Results.success_with_data(page_result)
    except Exception as e:
        return failure_from_exception(e)
