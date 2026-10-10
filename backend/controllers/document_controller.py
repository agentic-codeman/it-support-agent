"""
知识库文档 API 控制器
符合 Google Python 编码规范
"""
from fastapi import APIRouter, Depends, Query, UploadFile, File, BackgroundTasks
from typing import Optional
from sqlalchemy.orm import Session
from langsmith import traceable, set_run_metadata
from backend.db.database import get_db
from backend.schemas.document import (
    KnowledgeDocumentPageRequest,
    KnowledgeDocumentUpdateRequest,
)
from backend.services import document_service
from backend.middleware.jwt_auth_middleware import get_current_username
from backend.utils.results import Results, failure_from_exception

router = APIRouter(prefix="/api/knowledge-base", tags=["文档管理"])


@router.post("/{kb_id}/docs/upload")
async def upload_document(
    kb_id: str,
    file: Optional[UploadFile] = File(None, description="上传的文件"),
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """上传文档

    Args:
        kb_id: 知识库ID
        file: 上传的文件
        db: 数据库会话
        username: 当前用户名

    Returns:
        Results: 包含文档信息的响应
    """
    try:
        doc_vo = document_service.upload(db, kb_id, file, username)
        return Results.success_with_data(doc_vo)
    except Exception as e:
        return failure_from_exception(e)



@router.post("/docs/{doc_id}/chunk")
async def start_chunk_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """开始文档分块处理（异步）

    Args:
        doc_id: 文档ID
        background_tasks: FastAPI 后台任务，在响应返回后执行 LangGraph 导入流程
        db: 数据库会话
        username: 当前用户名

    Returns:
        Results: 包含 task_id 的操作结果
    """
    try:
        result = document_service.start_chunk(db, doc_id, username, background_tasks)
        return Results.success_with_data(result)
    except Exception as e:
        return failure_from_exception(e)


@router.delete("/docs/{doc_id}")
async def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """删除文档
    
    Args:
        doc_id: 文档ID
        db: 数据库会话
        username: 当前用户名
        
    Returns:
        Results: 操作结果
    """
    try:
        document_service.delete(db, doc_id, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)


@router.get("/docs/{doc_id}")
async def get_document(
    doc_id: str,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """获取文档详情
    
    Args:
        doc_id: 文档ID
        db: 数据库会话
        username: 当前用户名
        
    Returns:
        Results: 文档详情
    """
    try:
        doc_vo = document_service.get(db, doc_id)
        return Results.success_with_data(doc_vo)
    except Exception as e:
        return failure_from_exception(e)


@router.put("/docs/{doc_id}")
async def update_document(
    doc_id: str,
    request: KnowledgeDocumentUpdateRequest,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """更新文档信息
    
    Args:
        doc_id: 文档ID
        request: 更新请求
        db: 数据库会话
        username: 当前用户名
        
    Returns:
        Results: 操作结果
    """
    try:
        document_service.update(db, doc_id, request, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)


@router.get("/{kb_id}/docs")
async def page_query_documents(
    kb_id: str,
    current: int = Query(default=1, ge=1, description="当前页码"),
    size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(default=None, description="文档名称关键字"),
    chunk_status: Optional[str] = Query(default=None, description="分块状态筛选"),
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """分页查询文档列表
    
    Args:
        kb_id: 知识库ID
        current: 当前页码
        size: 每页数量
        keyword: 文档名称关键字
        chunk_status: 分块状态筛选
        db: 数据库会话
        username: 当前用户名
        
    Returns:
        Results: 分页结果
    """
    try:
        request = KnowledgeDocumentPageRequest(
            current=current,
            size=size,
            keyword=keyword,
            chunk_status=chunk_status
        )
        page_result = document_service.page(db, kb_id, request)
        return Results.success_with_data(page_result)
    except Exception as e:
        return failure_from_exception(e)


@router.patch("/docs/{doc_id}/enable")
async def enable_document(
    doc_id: str,
    value: bool = Query(..., description="是否启用"),
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """启用/禁用文档

    Args:
        doc_id: 文档ID
        value: 是否启用
        db: 数据库会话
        username: 当前用户名

    Returns:
        Results: 操作结果
    """
    try:
        document_service.enable(db, doc_id, value, username)
        return Results.success()
    except Exception as e:
        return failure_from_exception(e)


@router.get("/docs/search")
async def search_documents(
    keyword: Optional[str] = Query(default=None, description="搜索关键字"),
    limit: int = Query(default=8, ge=1, le=50, description="返回数量限制"),
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username)
):
    """搜索文档
    
    Args:
        keyword: 搜索关键字
        limit: 返回数量限制
        db: 数据库会话
        username: 当前用户名
        
    Returns:
        Results: 文档列表
    """
    try:
        results = document_service.search(db, keyword, limit)
        return Results.success_with_data(results)
    except Exception as e:
        return failure_from_exception(e)