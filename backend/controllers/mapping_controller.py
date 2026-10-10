"""
Query Term Mapping API 控制器
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.schemas.query_term_mapping import (
    QueryTermMappingCreateRequest,
    QueryTermMappingUpdateRequest,
)
from backend.services import query_term_mapping_service
from backend.middleware.jwt_auth_middleware import get_current_username
from backend.utils.results import Results, failure_from_exception

router = APIRouter(prefix="/api/mappings", tags=["关键词映射管理"])


@router.post("")
async def create_mapping(
    request: QueryTermMappingCreateRequest,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """创建关键词映射规则
    
    Args:
        request: 创建请求
        db: 数据库会话
        username: 当前登录用户名
        
    Returns:
        Results: 包含新建记录ID的响应
    """
    try:
        mapping_id = query_term_mapping_service.create(db, request, username)
        return Results.success_with_data(mapping_id)
    except Exception as e:
        return failure_from_exception(e)


@router.put("/{mapping_id}")
async def update_mapping(
    mapping_id: str,
    request: QueryTermMappingUpdateRequest,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """更新关键词映射规则
    
    Args:
        mapping_id: 映射规则ID
        request: 更新请求
        db: 数据库会话
        username: 当前登录用户名
        
    Returns:
        Results: 操作结果
    """
    try:
        query_term_mapping_service.update(db, mapping_id, request, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)


@router.delete("/{mapping_id}")
async def delete_mapping(
    mapping_id: str,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """删除关键词映射规则
    
    Args:
        mapping_id: 映射规则ID
        db: 数据库会话
        username: 当前登录用户名
        
    Returns:
        Results: 操作结果
    """
    try:
        query_term_mapping_service.delete(db, mapping_id)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)


@router.get("")
async def page_query_mappings(
    current: int = Query(default=1, ge=1, description="当前页码"),
    size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(default=None, description="关键词搜索"),
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """分页查询关键词映射规则列表
    
    Args:
        current: 当前页码
        size: 每页数量
        keyword: 关键词搜索（匹配原始词或目标词）
        db: 数据库会话
        username: 当前登录用户名
        
    Returns:
        Results: 分页结果
    """
    try:
        page_result = query_term_mapping_service.page_query(db, current, size, keyword)
        return Results.success_with_data(page_result)
    except Exception as e:
        return failure_from_exception(e)


@router.get("/{mapping_id}")
async def query_mapping(
    mapping_id: str,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """查询关键词映射规则详情
    
    Args:
        mapping_id: 映射规则ID
        db: 数据库会话
        username: 当前登录用户名
        
    Returns:
        Results: 映射规则详情
    """
    try:
        mapping_vo = query_term_mapping_service.query_by_id(db, mapping_id)
        return Results.success_with_data(mapping_vo)
    except Exception as e:
        return failure_from_exception(e)
