"""
知识库文档业务服务层
符合 Google Python 编码规范
"""
import os

from sqlalchemy.orm import Session
from langsmith import traceable, set_run_metadata

from backend.models.knowledge_base import KnowledgeBaseModel
from backend.models.knowledge_document import KnowledgeDocumentModel
from backend.schemas.document import (
    KnowledgeDocumentPageRequest,
    KnowledgeDocumentUpdateRequest,
    KnowledgeDocumentVO,
)
from backend.crud import crud_knowledge_base
from backend.utils.exceptions import ServiceException, ClientException
from backend.utils.path_util import PROJECT_ROOT
from backend.utils.snowflake_id_utils import generate_snowflake_id_str
from backend.client.rustfs_client import get_restfs_client
from backend.schemas.enums.document_status import DocumentStatus

from backend.workflow.import_process.state import *

from backend.core.logger import logger


def upload(db: Session, kb_id: str, file, username: str) -> KnowledgeDocumentVO:
    """上传文档

    Args:
        db: 数据库会话
        kb_id: 知识库ID
        file: 上传的文件对象
        username: 当前用户名

    Returns:
        KnowledgeDocumentVO: 文档视图对象

    Raises:
        ClientException: 知识库不存在
        ServiceException: 文件上传失败
    """
    # 验证知识库存在
    kb = db.query(KnowledgeBaseModel).filter(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.deleted == 0
    ).first()

    if not kb:
        raise ClientException("知识库不存在")

    if not file or not file.filename:
        raise ClientException("文件不能为空")

    # 获取文件类型
    file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    file_type = _get_file_type(file_ext)

    # 生成文档ID
    doc_id = generate_snowflake_id_str()

    # 上传文件到RestFS
    try:
        file_path = _upload_to_restfs(kb.collection_name, doc_id, file)
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise ServiceException(f"文件上传失败: {str(e)}")

    doc_name = file.filename
    file_size = file.size

    # 创建文档记录
    doc_model = KnowledgeDocumentModel(
        id=doc_id,
        kb_id=kb_id,
        doc_name=doc_name,
        file_url=file_path,
        file_type=file_type,
        file_size=file_size,
        status=DocumentStatus.PENDING.value,
        chunk_count=0,
        enabled=1,
        created_by=username,
        updated_by=username
    )

    db.add(doc_model)
    db.commit()
    db.refresh(doc_model)

    logger.info(f"文档上传成功, doc_id={doc_id}, file_name={doc_name}")
    return KnowledgeDocumentVO(**doc_model.to_dict())


def start_chunk(db: Session, doc_id: str, username: str, background_tasks=None) -> dict:
    """开始文档分块处理（异步）

    Args:
        db: 数据库会话
        doc_id: 文档ID
        username: 当前用户名
        background_tasks: FastAPI BackgroundTasks 实例，非空时在响应返回后异步执行导入流程

    Returns:
        dict: 包含 task_id 的字典

    Raises:
        ClientException: 文档不存在
    """

    try:
        doc = _get_doc_or_raise(db, doc_id)
        kb_id = doc.kb_id
        kb = crud_knowledge_base.get_by_id(db, kb_id)
        if not kb:
            raise ClientException("知识库不存在")
        collection_name = kb.collection_name

        # 更新状态为处理中
        doc.status = DocumentStatus.RUNNING.value
        doc.updated_by = username
        db.commit()

        logger.info(f"文档[{doc_id}] 开始执行LangGraph全流程，文件路径：{doc.file_url}")

        # 2. 初始化LangGraph状态：加载默认状态 + 注入当前任务的核心参数
        init_state = get_default_state()
        init_state["doc_id"] = doc_id   #  文档ID
        init_state["kb_id"] = kb_id
        init_state["file_name"] = doc.doc_name
        init_state["file_url"] = doc.file_url  # 文件地址
        init_state["collection_name"] = collection_name
        init_state["bucket_name"] = collection_name
        init_state["local_dir"] = os.path.join(PROJECT_ROOT, "output")
        init_state["user_name"] = username

        background_tasks.add_task(_run_import_flow, init_state, doc_id)

        return {
            'status': doc.status,
            'doc_id': doc_id
        }
    except Exception as e:
        logger.error(f"分块任务提交失败: {e}")
        doc.status = DocumentStatus.FAILED.value
        db.commit()
        raise

@traceable(name="_run_import_flow")
def _run_import_flow(init_state: dict, doc_id: str) -> None:
    """执行 LangGraph 导入流程，失败时回写文档失败状态

    说明：后台任务执行时请求已结束，db 对应的 session 已被关闭，
    因此失败回写使用独立的 SessionLocal 会话，避免复用已关闭的连接。

    Args:
        init_state: LangGraph 初始状态
        doc_id: 文档ID
    """

    from backend.db.database import SessionLocal
    # 延迟导入，避免 document_service 与 main_graph/node_import_milvus 之间的循环导入
    from backend.workflow.import_process.main_graph import kb_import_app
    try:
        set_run_metadata(thread_id=doc_id)
        kb_import_app.invoke(init_state)
    except Exception as e:
        logger.error(f"LangGraph导入流程执行失败, doc_id={doc_id}: {e}")
        db = SessionLocal()
        try:
            doc = db.query(KnowledgeDocumentModel).filter(
                KnowledgeDocumentModel.id == doc_id
            ).first()
            if doc:
                doc.status = DocumentStatus.FAILED.value
                db.commit()
        except Exception as inner_e:
            logger.error(f"回写文档失败状态出错, doc_id={doc_id}: {inner_e}")
        finally:
            db.close()


def delete(db: Session, doc_id: str, username: str) -> None:
    """删除文档（逻辑删除）

    Args:
        db: 数据库会话
        doc_id: 文档ID
        username: 当前用户名

    Raises:
        ClientException: 文档不存在
    """
    doc = _get_doc_or_raise(db, doc_id)

    kb = crud_knowledge_base.get_by_id(db, doc.kb_id)
    if not kb:
        raise ClientException("知识库不存在")

    # 删除 Milvus 向量（失败必须中断，否则文档已删但向量残留会导致检索不一致）
    try:
        from backend.client.milvus_client import delete_with_retry
        delete_with_retry(kb.collection_name, filter=f"metadata['doc_id'] == '{doc_id}'")
    except Exception as e:
        logger.error(f"删除文档向量失败, doc_id={doc_id}: {e}")
        raise ServiceException(f"删除文档向量失败: {str(e)}")

    # 逻辑删除分块记录
    from backend.services import chunk_service
    chunk_service.delete_by_doc_id(db, doc_id)

    # 逻辑删除文档
    doc.deleted = 1
    doc.updated_by = username
    db.commit()

    logger.info(f"文档删除成功, doc_id={doc_id}")


def get(db: Session, doc_id: str) -> KnowledgeDocumentVO:
    """获取文档详情

    Args:
        db: 数据库会话
        doc_id: 文档ID

    Returns:
        KnowledgeDocumentVO: 文档视图对象

    Raises:
        ClientException: 文档不存在
    """
    doc = _get_doc_or_raise(db, doc_id)
    return KnowledgeDocumentVO(**doc.to_dict())


def update(
    db: Session,
    doc_id: str,
    request: KnowledgeDocumentUpdateRequest,
    username: str
) -> None:
    """更新文档信息

    Args:
        db: 数据库会话
        doc_id: 文档ID
        request: 更新请求
        username: 当前用户名

    Raises:
        ClientException: 文档不存在
    """
    # 查询文档是否存在
    doc = _get_doc_or_raise(db, doc_id)

    # 使用 getattr 安全获取字段值，兼容 Pydantic V2
    doc_name = getattr(request, 'doc_name', None)
    title = getattr(request, 'title', None)


    # 这样可以确保字段被正确更新
    update_fields = {}
    if doc_name is not None:
        update_fields['doc_name'] = doc_name.strip()
        logger.info(f"将更新文档名称: {doc_name.strip()}")
    if title is not None:
        update_fields['title'] = title.strip() if title else title

    update_fields['updated_by'] = username

    # 使用 update() 方法直接执行 SQL 更新
    db.query(KnowledgeDocumentModel).filter(
        KnowledgeDocumentModel.id == doc_id
    ).update(update_fields)

    db.commit()

    # 验证更新结果
    updated_doc = db.query(KnowledgeDocumentModel).filter(
        KnowledgeDocumentModel.id == doc_id
    ).first()
    logger.info(f"文档更新成功, doc_id={doc_id}, 新名称={updated_doc.doc_name}")

def page(
    db: Session,
    kb_id: str,
    request: KnowledgeDocumentPageRequest
) -> dict:
    """分页查询文档列表

    Args:
        db: 数据库会话
        kb_id: 知识库ID
        request: 分页查询请求

    Returns:
        dict: 分页结果
    """
    # 构建查询
    query = db.query(KnowledgeDocumentModel).filter(
        KnowledgeDocumentModel.kb_id == kb_id,
        KnowledgeDocumentModel.deleted == 0
    )

    # 关键字搜索
    if request.keyword:
        query = query.filter(
            KnowledgeDocumentModel.doc_name.like(f"%{request.keyword}%")
        )

    # 状态筛选
    if request.chunk_status:
        query = query.filter(
            KnowledgeDocumentModel.status == request.chunk_status
        )

    # 总数查询
    total = query.count()

    # 分页查询
    items = query.order_by(KnowledgeDocumentModel.create_time.desc()) \
        .offset((request.current - 1) * request.size) \
        .limit(request.size) \
        .all()

    # 转换为VO
    records = [KnowledgeDocumentVO(**item.to_dict()) for item in items]

    return {
        "records": records,
        "total": total,
        "current": request.current,
        "size": request.size,
        "pages": (total + request.size - 1) // request.size if request.size > 0 else 0
    }


def enable(db: Session, doc_id: str, enabled: bool, username: str) -> None:
    """启用/禁用文档

    Args:
        db: 数据库会话
        doc_id: 文档ID
        enabled: 是否启用
        username: 当前用户名

    Raises:
        ClientException: 文档不存在
    """
    doc = _get_doc_or_raise(db, doc_id)

    kb = crud_knowledge_base.get_by_id(db, doc.kb_id)
    if not kb:
        raise ClientException("知识库不存在")

    # 同步文档所有分块：更新 MySQL 分块启用状态 + 同步 Milvus 向量库
    from backend.services import chunk_service
    chunk_service.toggle_enabled_by_doc_id(
        db,
        doc_id=doc_id,
        collection_name=kb.collection_name,
        embedding_model=kb.embedding_model,
        enabled=enabled,
        username=username,
    )

    doc.enabled = 1 if enabled else 0
    doc.updated_by = username
    db.commit()

    logger.info(f"文档{'启用' if enabled else '禁用'}成功, doc_id={doc_id}")


def search(db: Session, keyword: str, limit: int) -> list:
    """搜索文档

    Args:
        db: 数据库会话
        keyword: 搜索关键字
        limit: 返回数量限制

    Returns:
        list: 文档列表
    """
    query = db.query(KnowledgeDocumentModel).filter(
        KnowledgeDocumentModel.deleted == 0,
        KnowledgeDocumentModel.enabled == 1
    )

    if keyword:
        query = query.filter(
            KnowledgeDocumentModel.doc_name.like(f"%{keyword}%")
        )

    items = query.order_by(KnowledgeDocumentModel.create_time.desc()) \
        .limit(limit) \
        .all()

    return [
        {
            "id": item.id,
            "kb_id": item.kb_id,
            "file_name": item.doc_name,  # 使用数据库字段名
            "title": None,  # 旧表无此字段
            "chunk_count": item.chunk_count
        }
        for item in items
    ]

def _get_doc_or_raise(db: Session, doc_id: str) -> KnowledgeDocumentModel:
    """获取文档或抛出异常

    Args:
        db: 数据库会话
        doc_id: 文档ID

    Returns:
        KnowledgeDocumentModel: 文档模型

    Raises:
        ClientException: 文档不存在
    """
    doc = db.query(KnowledgeDocumentModel).filter(
        KnowledgeDocumentModel.id == doc_id,
        KnowledgeDocumentModel.deleted == 0
    ).first()

    if not doc:
        raise ClientException("文档不存在")

    return doc


def _get_file_type(file_ext: str) -> str:
    """根据文件扩展名获取文件类型

    Args:
        file_ext: 文件扩展名

    Returns:
        str: 文件类型
    """
    type_map = {
        'pdf': 'pdf',
        'doc': 'doc',
        'docx': 'docx',
        'txt': 'txt',
        'md': 'markdown',
        'markdown': 'markdown',
        'csv': 'csv',
        'xlsx': 'excel',
        'xls': 'excel',
    }
    return type_map.get(file_ext, 'unknown')


def _upload_to_restfs(
    bucket_name: str,
    doc_id: str,
    file
) -> str:
    """上传文件到RestFS

    Args:
        bucket_name: 存储桶名称
        doc_id: 文档ID
        file: 文件对象

    Returns:
        str: 文件路径
    """
    try:
        restfs_client = get_restfs_client()

        # 确保bucket存在
        restfs_client.ensure_bucket_exists(bucket_name)

        # 生成文件路径
        file_name = file.filename
        file_path = f"documents/{doc_id}/{file_name}"

        # 上传文件
        restfs_client.upload_file_bytes(bucket_name, file_path, file.file.read())

        return file_path

    except Exception as e:
        logger.error(f"上传文件到RestFS失败: {e}")
        raise


__all__ = [
    "upload",
    "start_chunk",
    "delete",
    "get",
    "update",
    "page",
    "enable",
    "search",
]
