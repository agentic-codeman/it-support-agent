"""
知识库业务服务层
符合 Google Python 编码规范
"""
from typing import Optional
from sqlalchemy.orm import Session
from pymilvus import DataType, Function, FunctionType

from backend.conf.milvus_config import milvus_config
from backend.models.knowledge_base import KnowledgeBaseModel
from backend.schemas.knowledge import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseUpdateRequest,
    KnowledgeBaseVO,
)
from backend.utils.exceptions import ServiceException, ClientException
from backend.crud import crud_knowledge_base
from backend.client.milvus_client import get_milvus_client
from backend.client.rustfs_client import get_restfs_client

from backend.core.logger import logger


def create(db: Session, request: KnowledgeBaseCreateRequest, username: str) -> str:
    """创建知识库

    Args:
        db: 数据库会话
        request: 创建知识库请求
        username: 当前登录用户名

    Returns:
        str: 知识库ID

    Raises:
        ServiceException: 知识库名称已存在
    """
    # 名称重复校验（去除空格）
    name = request.name.replace(" ", "")
    if crud_knowledge_base.get_by_name(db, name):
        raise ServiceException(f"知识库名称已存在：{request.name}")

    # Collection名称重复校验
    if crud_knowledge_base.get_by_collection_name(db, request.collection_name):
        raise ServiceException(f"Collection名称已被占用：{request.collection_name}")

    # 创建知识库记录
    kb_model = KnowledgeBaseModel(
        name=request.name,
        collection_name=request.collection_name,
        embedding_model=request.embedding_model,
        created_by=username,
        updated_by=username
    )

    crud_knowledge_base.add(db, kb_model)
    db.flush()

    # 创建 Milvus Collection 和 RestFS Bucket
    try:
        _create_milvus_collection(request.collection_name)
        logger.info(f"成功创建 Milvus Collection: {request.collection_name}")

        _create_restfs_bucket(request.collection_name)
        logger.info(f"成功创建 RestFS Bucket: {request.collection_name}")

    except Exception as e:
        # 如果任一步骤失败，回滚数据库操作
        db.rollback()
        logger.error(f"创建向量存储或对象存储失败: {e}")
        raise ServiceException(f"创建存储空间失败：{str(e)}")

    # 提交数据库事务
    db.commit()
    db.refresh(kb_model)

    logger.info(f"成功创建知识库，kb_id={kb_model.id}, name={request.name}")
    return kb_model.id


def rename(db: Session, kb_id: str, request: KnowledgeBaseUpdateRequest, username: str) -> None:
    """重命名知识库

    Args:
        db: 数据库会话
        kb_id: 知识库ID
        request: 更新请求
        username: 当前登录用户名

    Raises:
        ClientException: 知识库不存在或名称为空
    """
    kb = _get_kb_or_raise(db, kb_id)

    if not request.name:
        raise ClientException("知识库名称不能为空")

    # 名称重复校验（排除当前知识库）
    name = request.name.replace(" ", "")
    if crud_knowledge_base.get_by_name(db, name, exclude_id=kb_id):
        raise ServiceException(f"知识库名称已存在：{request.name}")

    # 更新知识库
    kb.name = request.name
    kb.updated_by = username

    db.commit()
    logger.info(f"成功重命名知识库, kb_id={kb_id}, new_name={request.name}")


def delete(db: Session, kb_id: str, username: str) -> None:
    """删除知识库（逻辑删除）

    Args:
        db: 数据库会话
        kb_id: 知识库ID
        username: 当前登录用户名

    Raises:
        ClientException: 知识库不存在或还有文档
    """
    kb = _get_kb_or_raise(db, kb_id)

    # 检查是否还有文档
    doc_count = crud_knowledge_base.count_documents(db, kb_id)
    if doc_count > 0:
        raise ClientException("当前知识库下还有文档，请先删除文档")

    # 删除 Milvus Collection（失败则中断，避免残留空 Collection）
    milvus_client = get_milvus_client()
    collection_name = kb.collection_name
    if milvus_client.has_collection(collection_name):
        milvus_client.drop_collection(collection_name)
        logger.info(f"成功删除 Milvus Collection: {collection_name}")

    # 逻辑删除
    kb.deleted = 1
    kb.updated_by = username

    db.commit()
    logger.info(f"成功删除知识库, kb_id={kb_id}, collection_name={kb.collection_name}")


def query_by_id(db: Session, kb_id: str) -> KnowledgeBaseVO:
    """根据ID查询知识库详情

    Args:
        db: 数据库会话
        kb_id: 知识库ID

    Returns:
        KnowledgeBaseVO: 知识库视图对象

    Raises:
        ClientException: 知识库不存在
    """
    kb = _get_kb_or_raise(db, kb_id)
    return KnowledgeBaseVO(**kb.to_dict())


def page_query(
    db: Session,
    current: int,
    size: int,
    name: Optional[str] = None
) -> dict:
    """分页查询知识库列表

    Args:
        db: 数据库会话
        current: 当前页码
        size: 每页数量
        name: 知识库名称（模糊搜索）

    Returns:
        dict: 分页结果
    """
    logger.info(f"分页查询知识库: current={current}, size={size}, name={name}")

    items, total = crud_knowledge_base.page_query(db, current, size, name)

    # 批量查询每个知识库的文档数量
    kb_ids = [item.id for item in items]
    doc_counts = crud_knowledge_base.count_documents_by_kb_ids(db, kb_ids)

    # 转换为 VO，包含文档数量
    records = []
    for item in items:
        vo_data = item.to_dict()
        vo_data['document_count'] = doc_counts.get(item.id, 0)
        records.append(KnowledgeBaseVO(**vo_data))

    return {
        "records": records,
        "total": total,
        "current": current,
        "size": size,
        "pages": (total + size - 1) // size if size > 0 else 0
    }


def _get_kb_or_raise(db: Session, kb_id: str) -> KnowledgeBaseModel:
    """获取知识库或抛出异常

    Args:
        db: 数据库会话
        kb_id: 知识库ID

    Returns:
        KnowledgeBaseModel: 知识库模型

    Raises:
        ClientException: 知识库不存在
    """
    kb = crud_knowledge_base.get_by_id(db, kb_id)

    if not kb:
        raise ClientException("知识库不存在")

    return kb


def _create_milvus_collection(collection_name: str) -> None:
    """创建 Milvus Collection

    Args:
        collection_name: Collection名称

    Raises:
        Exception: 创建失败时抛出异常（包括 Collection 已存在的情况）
    """
    try:
        from backend.conf.model_config import model_config

        # 获取 Milvus 客户端
        milvus_client = get_milvus_client()

        # 创建 Collection（如果已存在会抛出异常，与 Java 实现保持一致）
        if milvus_client.has_collection(collection_name):
            raise Exception(f"向量空间已存在：{collection_name}")

        dimension = model_config.embedding_dimension

        # 构建 BM25 混合检索 Schema（id / content / metadata / embedding / sparse_bm25）
        schema = milvus_client.create_schema(
            auto_id=False,
            enable_dynamic_field=False,
            description=f"知识库: {collection_name}",
        )
        schema.add_field("id", DataType.VARCHAR, max_length=36, is_primary=True, description="主键ID")
        schema.add_field("content", DataType.VARCHAR, max_length=65535, enable_analyzer=True, description="文本内容")
        schema.add_field("metadata", DataType.JSON, description="元数据")
        schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=dimension, description="稠密向量数据")
        schema.add_field("sparse_bm25", DataType.SPARSE_FLOAT_VECTOR, description="稀疏向量（BM25 自动生成）")
        schema.add_function(Function(
            name="bm25_emb",
            function_type=FunctionType.BM25,
            input_field_names=["content"],
            output_field_names=["sparse_bm25"],
        ))

        # 构建稠密（HNSW+COSINE）与稀疏（BM25）索引
        index_params = milvus_client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type=milvus_config.index_type,
            metric_type=milvus_config.metric_type,
            params=milvus_config.index_params,
        )
        index_params.add_index(
            field_name="sparse_bm25",
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="BM25",
            params={"drop_ratio_build": 0.2},
        )

        milvus_client.create_collection(collection_name, schema=schema, index_params=index_params)
        milvus_client.load_collection(collection_name)
        logger.info(f"成功创建 Milvus Collection: {collection_name} (dimension={dimension})")

    except Exception as e:
        logger.error(f"创建 Milvus Collection 失败: {e}")
        raise


def _create_restfs_bucket(bucket_name: str) -> None:
    """创建 RestFS Bucket（S3 兼容存储桶）

    Args:
        bucket_name: 存储桶名称

    Raises:
        Exception: 创建失败时抛出异常
    """
    try:
        # 获取 RestFS 客户端
        restfs_client = get_restfs_client()

        # 创建存储桶
        restfs_client.create_bucket(bucket_name)
        logger.info(f"成功创建 RestFS Bucket: {bucket_name}")

    except Exception as e:
        logger.error(f"创建 RestFS Bucket 失败: {e}")
        raise


__all__ = [
    "create",
    "rename",
    "delete",
    "query_by_id",
    "page_query",
]
