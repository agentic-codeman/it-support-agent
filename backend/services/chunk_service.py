"""
知识库分块服务层
符合 Google Python 编码规范
"""
import hashlib
from typing import List
from sqlalchemy.orm import Session

from backend.core.logger import logger
from backend.crud import crud_chunk
from backend.models.knowledge_chunk import KnowledgeChunkModel
from backend.utils.exceptions import ServiceException


def delete_by_doc_id(db: Session, doc_id: str) -> int:
    """删除文档的所有分块（逻辑删除）

    Args:
        db: 数据库会话
        doc_id: 文档ID

    Returns:
        int: 删除的分块数量
    """
    try:
        # 逻辑删除文档所有分块
        count = crud_chunk.soft_delete_by_doc_id(db, doc_id)
        if count == 0:
            logger.debug(f"文档没有分块记录, doc_id={doc_id}")
            return 0

        db.commit()
        logger.info(f"已删除文档分块, doc_id={doc_id}, 数量={count}")
        return count

    except Exception as e:
        db.rollback()
        logger.error(f"删除文档分块失败, doc_id={doc_id}: {e}")
        raise ServiceException(f"删除文档分块失败: {str(e)}")


def batch_create(db: Session, doc_id: str, kb_id: str, chunks_data: List[dict], username: str) -> int:
    """批量创建分块记录

    - contentHash: 使用 SHA-256 计算内容哈希
    - tokenCount: 估算 Token 数量（中文字符按 1.5 个 token 计算）

    Args:
        db: 数据库会话
        doc_id: 文档ID
        kb_id: 知识库ID
        chunks_data: 分块数据列表，每个元素包含：
            - chunk_id: 分块ID
            - index: 分块序号
            - content: 分块内容
        username: 当前用户名

    Returns:
        int: 创建的分块数量
    """
    try:
        if not chunks_data:
            logger.warning(f"分块数据为空, doc_id={doc_id}")
            return 0

        # 构建分块模型列表
        chunk_models = []
        for chunk_data in chunks_data:
            content = chunk_data.get("content", "")

            # 计算字符数
            char_count = len(content)

            content_hash = _calculate_content_hash(content)

            token_count = _estimate_token_count(content)

            chunk_model = KnowledgeChunkModel(
                id=chunk_data["chunk_id"],
                kb_id=kb_id,
                doc_id=doc_id,
                chunk_index=chunk_data["index"],
                content=content,
                content_hash=content_hash,
                char_count=char_count,
                token_count=token_count,
                enabled=1,
                created_by=username,
                updated_by=username
            )
            chunk_models.append(chunk_model)

        # 批量插入
        crud_chunk.batch_add(db, chunk_models)
        db.commit()

        logger.info(f"批量创建分块成功, doc_id={doc_id}, 数量={len(chunk_models)}")
        return len(chunk_models)

    except Exception as e:
        db.rollback()
        logger.error(f"批量创建分块失败, doc_id={doc_id}: {e}")
        raise ServiceException(f"批量创建分块失败: {str(e)}")


def list_by_doc_id(db: Session, doc_id: str) -> List[KnowledgeChunkModel]:
    """查询文档的所有分块

    Args:
        db: 数据库会话
        doc_id: 文档ID

    Returns:
        List[KnowledgeChunkModel]: 分块列表
    """
    try:
        chunks = crud_chunk.list_by_doc_id(db, doc_id)
        return chunks

    except Exception as e:
        logger.error(f"查询文档分块失败, doc_id={doc_id}: {e}")
        raise ServiceException(f"查询文档分块失败: {str(e)}")


def _calculate_content_hash(content: str) -> str:
    """计算内容哈希值 (SHA-256)


    Args:
        content: 文本内容

    Returns:
        str: SHA-256 哈希值（十六进制字符串）
    """
    if not content:
        return ""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def _estimate_token_count(content: str) -> int:
    """估算 Token 数量

    - 空白字符不计入
    - ASCII 字符（英文、数字、标点）：4 字符 ≈ 1 token
    - CJK 字符（中日韩）：1 字符 = 1 token
    - 其他字符：2 字符 ≈ 1 token

    Args:
        content: 文本内容

    Returns:
        int: 估算的 Token 数量
    """
    if not content:
        return 0

    ascii_count = 0
    cjk_count = 0
    other_count = 0

    for char in content:
        # 跳过空白字符
        if char.isspace():
            continue

        # ASCII 字符 (U+0000 ~ U+007F)
        if ord(char) <= 0x7F:
            ascii_count += 1
        # CJK 字符（中日韩统一表意文字及其扩展）
        elif _is_cjk(char):
            cjk_count += 1
        # 其他字符
        else:
            other_count += 1

    # 计算 Token 数
    ascii_tokens = (ascii_count + 3) // 4  # 4 字符 ≈ 1 token
    other_tokens = (other_count + 1) // 2  # 2 字符 ≈ 1 token
    total = ascii_tokens + cjk_count + other_tokens  # CJK: 1 字符 = 1 token

    return max(total, 1)


def _is_cjk(char: str) -> bool:
    """判断是否为 CJK（中日韩）字符


    Args:
        char: 单个字符

    Returns:
        bool: 是否为 CJK 字符
    """
    code_point = ord(char)

    # CJK 统一表意文字范围
    cjk_ranges = [
        (0x4E00, 0x9FFF),      # CJK Unified Ideographs
        (0x3400, 0x4DBF),      # CJK Unified Ideographs Extension A
        (0x20000, 0x2A6DF),    # CJK Unified Ideographs Extension B
        (0x2A700, 0x2B73F),    # CJK Unified Ideographs Extension C
        (0x2B740, 0x2B81F),    # CJK Unified Ideographs Extension D
        (0x2B820, 0x2CEAF),    # CJK Unified Ideographs Extension E
        (0x2CEB0, 0x2EBEF),    # CJK Unified Ideographs Extension F
        (0xF900, 0xFAFF),      # CJK Compatibility Ideographs
        (0x2F800, 0x2FA1F),    # CJK Compatibility Ideographs Supplement
        (0x2E80, 0x2EFF),      # CJK Radicals Supplement
        (0x3000, 0x303F),      # CJK Symbols and Punctuation
        (0x3040, 0x309F),      # Hiragana
        (0x30A0, 0x30FF),      # Katakana
        (0x31F0, 0x31FF),      # Katakana Phonetic Extensions
        (0xAC00, 0xD7AF),      # Hangul Syllables
        (0x1100, 0x11FF),      # Hangul Jamo
        (0x3130, 0x318F),      # Hangul Compatibility Jamo
    ]

    return any(start <= code_point <= end for start, end in cjk_ranges)


def update_enabled_by_doc_id(db: Session, doc_id: str, enabled: bool) -> int:
    """更新文档所有分块的启用状态

    Args:
        db: 数据库会话
        doc_id: 文档ID
        enabled: 是否启用

    Returns:
        int: 更新的分块数量
    """
    try:
        enabled_value = 1 if enabled else 0
        count = crud_chunk.update_enabled_by_doc_id(db, doc_id, enabled_value)

        db.commit()
        logger.info(f"更新分块启用状态, doc_id={doc_id}, enabled={enabled}, 数量={count}")
        return count

    except Exception as e:
        db.rollback()
        logger.error(f"更新分块启用状态失败, doc_id={doc_id}: {e}")
        raise ServiceException(f"更新分块启用状态失败: {str(e)}")


def toggle_enabled_by_doc_id(
    db: Session,
    doc_id: str,
    collection_name: str,
    embedding_model: str,
    enabled: bool,
    username: str,
) -> int:
    """启用/禁用文档的所有分块，并同步向量库

    - 禁用：从向量库删除文档所有分块向量，避免被检索到
    - 启用：重新生成向量并写入向量库，恢复检索能力

    Args:
        db: 数据库会话
        doc_id: 文档ID
        collection_name: Milvus 集合名称
        embedding_model: 嵌入模型名称
        enabled: 是否启用
        username: 当前用户名

    Returns:
        int: 更新的分块数量
    """
    try:
        enabled_value = 1 if enabled else 0

        # 1. 同步向量库（先于数据库提交，失败则整体回滚，保证一致）
        if enabled:
            # 启用：幂等清理旧向量后，重新生成向量并插入
            _delete_doc_chunks_from_vector(collection_name, doc_id)
            chunks = crud_chunk.list_by_doc_id(db, doc_id)
            _batch_sync_chunks_to_vector(collection_name, doc_id, chunks, embedding_model)
        else:
            # 禁用：删除文档在向量库中的所有分块向量
            _delete_doc_chunks_from_vector(collection_name, doc_id)

        # 2. 更新 MySQL 分块启用状态
        count = crud_chunk.update_enabled_by_doc_id(db, doc_id, enabled_value)
        db.commit()

        logger.info(f"更新文档分块启用状态, doc_id={doc_id}, enabled={enabled}, 数量={count}")
        return count

    except Exception as e:
        db.rollback()
        logger.error(f"更新文档分块启用状态失败, doc_id={doc_id}: {e}")
        raise ServiceException(f"更新文档分块启用状态失败: {str(e)}")


def page_query(db: Session, doc_id: str, request) -> dict:
    """分页查询分块列表


    Args:
        db: 数据库会话
        doc_id: 文档ID
        request: 分页查询请求

    Returns:
        dict: 分页结果
    """
    try:
        from backend.schemas.knowledge import KnowledgeChunkVO

        # 分页查询
        chunks, total = crud_chunk.page_query(
            db, doc_id, request.current, request.size, request.enabled
        )

        # 转换为 VO
        records = [KnowledgeChunkVO(**chunk.to_dict()) for chunk in chunks]

        return {
            "records": records,
            "total": total,
            "current": request.current,
            "size": request.size,
            "pages": (total + request.size - 1) // request.size if request.size > 0 else 0
        }

    except Exception as e:
        logger.error(f"分页查询分块失败, doc_id={doc_id}: {e}")
        raise ServiceException(f"分页查询分块失败: {str(e)}")


def delete(db: Session, doc_id: str, chunk_id: str, username: str) -> None:
    """删除分块


    Args:
        db: 数据库会话
        doc_id: 文档ID
        chunk_id: 分块ID
        username: 当前用户名
    """
    try:
        # 1. 验证文档存在
        from backend.models.knowledge_document import KnowledgeDocumentModel
        from backend.schemas.enums.document_status import DocumentStatus
        from backend.models.knowledge_base import KnowledgeBaseModel

        document = db.query(KnowledgeDocumentModel).filter(
            KnowledgeDocumentModel.id == doc_id,
            KnowledgeDocumentModel.deleted == 0
        ).first()

        if not document:
            raise ServiceException("文档不存在")

        # 2. 检查文档是否正在处理中
        if document.status == DocumentStatus.RUNNING.value:
            raise ServiceException("文档正在分块处理中，暂不支持删除 Chunk")

        # 3. 验证Chunk存在且属于该文档
        chunk = crud_chunk.get_by_doc_and_id(db, doc_id, chunk_id)

        if not chunk:
            raise ServiceException("Chunk 不存在")

        if chunk.doc_id != doc_id:
            raise ServiceException("Chunk 不属于该文档")

        # 4. 获取知识库信息（用于向量库同步）
        kb = db.query(KnowledgeBaseModel).filter(
            KnowledgeBaseModel.id == document.kb_id,
            KnowledgeBaseModel.deleted == 0
        ).first()

        if not kb:
            raise ServiceException("知识库不存在")

        collection_name = kb.collection_name

        # 5. 从向量库删除（先于数据库提交，失败则整体回滚，保证一致）
        _delete_chunk_from_vector(collection_name, chunk_id)

        # 6. 物理删除Chunk（直接删除）
        crud_chunk.delete(db, chunk)

        # 7. 更新文档的chunk_count（减少1，但不小于0）
        if document.chunk_count and document.chunk_count > 0:
            document.chunk_count = document.chunk_count - 1

        db.commit()

        logger.info(f"删除 Chunk 成功, kb_id={document.kb_id}, doc_id={doc_id}, chunk_id={chunk_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"删除分块失败, chunk_id={chunk_id}: {e}")
        raise ServiceException(f"删除分块失败: {str(e)}")


def enable_chunk(db: Session, doc_id: str, chunk_id: str, enabled: bool, username: str) -> None:
    """启用或禁用单个分块


    Args:
        db: 数据库会话
        doc_id: 文档ID
        chunk_id: 分块ID
        enabled: 是否启用
        username: 当前用户名
    """
    try:
        # 1. 验证文档存在
        from backend.models.knowledge_document import KnowledgeDocumentModel
        from backend.schemas.enums.document_status import DocumentStatus
        from backend.models.knowledge_base import KnowledgeBaseModel

        document = db.query(KnowledgeDocumentModel).filter(
            KnowledgeDocumentModel.id == doc_id,
            KnowledgeDocumentModel.deleted == 0
        ).first()

        if not document:
            raise ServiceException("文档不存在")

        # 2. 检查文档是否正在处理中
        if document.status == DocumentStatus.RUNNING.value:
            raise ServiceException("文档正在分块处理中，暂不支持修改 Chunk 状态")

        # 3. 验证文档启用状态（启用Chunk前必须确保文档已启用）
        _validate_document_enabled_for_chunk_enable(document, enabled)

        # 4. 验证Chunk存在且属于该文档
        chunk = crud_chunk.get_by_doc_and_id(db, doc_id, chunk_id)

        if not chunk:
            raise ServiceException("分块不存在")

        if chunk.doc_id != doc_id:
            raise ServiceException("分块不属于该文档")

        # 5. 检查状态是否已变化，避免重复操作
        enabled_value = 1 if enabled else 0
        if chunk.enabled == enabled_value:
            logger.debug(f"分块状态已是目标值，无需更新, chunk_id={chunk_id}, enabled={enabled}")
            return

        # 6. 获取知识库信息（用于向量库同步）
        kb = db.query(KnowledgeBaseModel).filter(
            KnowledgeBaseModel.id == document.kb_id,
            KnowledgeBaseModel.deleted == 0
        ).first()

        if not kb:
            raise ServiceException("知识库不存在")

        # 7. 同步向量数据库（先于数据库提交，失败则整体回滚，保证一致）
        if enabled:
            # 启用：同步到向量库
            _sync_chunk_to_vector(kb.collection_name, doc_id, chunk, kb.embedding_model)
        else:
            # 禁用：从向量库删除
            _delete_chunk_from_vector(kb.collection_name, chunk_id)

        # 8. 更新Chunk状态
        chunk.enabled = enabled_value
        chunk.updated_by = username

        db.commit()

        action = "启用" if enabled else "禁用"
        logger.info(f"{action}分块成功, chunk_id={chunk_id}, doc_id={doc_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"更新分块启用状态失败, chunk_id={chunk_id}: {e}")
        raise ServiceException(f"更新分块启用状态失败: {str(e)}")


def _validate_document_enabled_for_chunk_enable(document, enable_chunk: bool) -> None:
    """启用 chunk 前必须保证所属文档为启用状态


    Args:
        document: 文档模型
        enable_chunk: 是否启用chunk
    """
    if not enable_chunk:
        return

    if document.enabled != 1:
        raise ServiceException("文档未启用，无法启用Chunk，请先启用文档")


def _sync_chunk_to_vector(collection_name: str, doc_id: str, chunk, embedding_model: str) -> None:
    """将单个 chunk 同步到向量库


    Args:
        collection_name: Collection名称
        doc_id: 文档ID
        chunk: 分块模型
        embedding_model: 嵌入模型名称
    """
    try:
        from backend.client.milvus_client import get_milvus_client
        from backend.utils.embedding_utils import embed

        # 生成向量
        embedding = embed(chunk.content, embedding_model)

        # 插入向量库
        milvus_client = get_milvus_client()
        milvus_client.insert(
            collection_name,
            {
                "id": chunk.id,
                "content": chunk.content,
                "metadata": {
                    "doc_id": doc_id,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                },
                "embedding": embedding,
            },
        )

        logger.debug(f"同步 Chunk 到向量库成功, collection={collection_name}, chunk_id={chunk.id}")

    except Exception as e:
        logger.error(f"同步 Chunk 到向量库失败, chunk_id={chunk.id}: {e}")
        raise


def _delete_chunk_from_vector(collection_name: str, chunk_id: str) -> None:
    """从向量库删除单个 chunk


    Args:
        collection_name: Collection名称
        chunk_id: 分块ID
    """
    try:
        from backend.client.milvus_client import delete_with_retry

        delete_with_retry(collection_name, ids=[chunk_id])

        logger.debug(f"从向量库删除 Chunk 成功, collection={collection_name}, chunk_id={chunk_id}")

    except Exception as e:
        logger.error(f"从向量库删除 Chunk 失败, chunk_id={chunk_id}: {e}")
        raise


def _batch_sync_chunks_to_vector(
    collection_name: str,
    doc_id: str,
    chunks: List[KnowledgeChunkModel],
    embedding_model: str
) -> None:
    """批量将 chunk 同步到向量库


    Args:
        collection_name: Collection名称
        doc_id: 文档ID
        chunks: 分块模型列表
        embedding_model: 嵌入模型名称
    """
    try:
        from backend.client.milvus_client import get_milvus_client
        from backend.utils.embedding_utils import embed_batch

        if not chunks:
            return

        # 批量生成向量
        texts = [chunk.content for chunk in chunks]
        embeddings = embed_batch(texts, embedding_model)

        if len(embeddings) != len(chunks):
            raise ServiceException("向量结果数量不匹配")

        # 批量插入向量库
        milvus_client = get_milvus_client()

        rows = [
            {
                "id": chunk.id,
                "content": chunk.content,
                "metadata": {
                    "doc_id": doc_id,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                },
                "embedding": embeddings[i],
            }
            for i, chunk in enumerate(chunks)
        ]
        milvus_client.insert(collection_name, rows)

        logger.debug(
            f"批量同步 Chunk 到向量库成功, collection={collection_name}, doc_id={doc_id}, count={len(chunks)}"
        )

    except Exception as e:
        logger.error(f"批量同步 Chunk 到向量库失败, doc_id={doc_id}: {e}")
        raise


def _batch_delete_chunks_from_vector(collection_name: str, chunk_ids: List[str]) -> None:
    """批量从向量库删除 chunk


    Args:
        collection_name: Collection名称
        chunk_ids: 分块ID列表
    """
    try:
        from backend.client.milvus_client import delete_with_retry

        if not chunk_ids:
            return

        delete_with_retry(collection_name, ids=chunk_ids)

        logger.debug(
            f"批量从向量库删除 Chunk 成功, collection={collection_name}, count={len(chunk_ids)}"
        )

    except Exception as e:
        logger.error(f"批量从向量库删除 Chunk 失败: {e}")
        raise


def _delete_doc_chunks_from_vector(collection_name: str, doc_id: str) -> None:
    """按文档ID从向量库删除该文档的所有 chunk

    参考 node_import_milvus 中按 metadata['doc_id'] 清理旧向量的实现

    Args:
        collection_name: Collection名称
        doc_id: 文档ID
    """
    try:
        from backend.client.milvus_client import delete_with_retry

        delete_with_retry(collection_name, filter=f"metadata['doc_id'] == '{doc_id}'")

        logger.debug(f"从向量库删除文档全部分块成功, collection={collection_name}, doc_id={doc_id}")

    except Exception as e:
        logger.error(f"从向量库删除文档全部分块失败, doc_id={doc_id}: {e}")
        raise


def batch_toggle_enabled(db: Session, doc_id: str, request, enabled: bool, username: str) -> None:
    """批量启用或禁用分块


    Args:
        db: 数据库会话
        doc_id: 文档ID
        request: 批量操作请求（包含分块ID列表）
        enabled: 是否启用
        username: 当前用户名
    """
    try:
        # 1. 验证请求参数
        if not request or not request.chunk_ids:
            raise ServiceException("请指定需要操作的 Chunk，全量启用/禁用请使用文档启用接口")

        requested_ids = request.chunk_ids

        # 2. 限制批量操作数量
        if len(requested_ids) > 500:
            raise ServiceException("单次批量操作 Chunk 数量不能超过 500")

        # 3. 验证文档存在
        from backend.models.knowledge_document import KnowledgeDocumentModel
        from backend.schemas.enums.document_status import DocumentStatus
        from backend.models.knowledge_base import KnowledgeBaseModel

        document = db.query(KnowledgeDocumentModel).filter(
            KnowledgeDocumentModel.id == doc_id,
            KnowledgeDocumentModel.deleted == 0
        ).first()

        if not document:
            raise ServiceException("文档不存在")

        # 4. 检查文档处理状态
        if document.status == DocumentStatus.RUNNING.value:
            raise ServiceException("文档正在分块处理中，暂不支持批量修改 Chunk 状态")

        # 5. 验证文档启用状态
        _validate_document_enabled_for_chunk_enable(document, enabled)

        # 6. 验证所有Chunk存在且属于该文档
        found_chunks = crud_chunk.get_by_ids(db, requested_ids)

        if len(found_chunks) != len(requested_ids):
            raise ServiceException(
                f"存在无效的 Chunk ID，请求 {len(requested_ids)} 个，实际找到 {len(found_chunks)} 个"
            )

        for chunk in found_chunks:
            if chunk.doc_id != doc_id:
                raise ServiceException(f"Chunk {chunk.id} 不属于文档 {doc_id}")

        # 7. 只更新状态需要变化的Chunk（优化）
        enabled_value = 1 if enabled else 0

        need_update_chunks = [c for c in found_chunks if c.enabled != enabled_value]
        need_update_ids = [chunk.id for chunk in need_update_chunks]

        # 8. 状态已全部一致时抛出提示
        if not need_update_ids:
            action = "启用" if enabled else "禁用"
            raise ServiceException(f"所有 Chunk 已全部{action}，无需重复操作")

        # 9. 获取知识库信息
        kb = db.query(KnowledgeBaseModel).filter(
            KnowledgeBaseModel.id == document.kb_id,
            KnowledgeBaseModel.deleted == 0
        ).first()

        if not kb:
            raise ServiceException("知识库不存在")

        collection_name = kb.collection_name
        embedding_model = kb.embedding_model

        # 10. 同步向量库（先于数据库提交，失败则整体回滚，保证一致）
        if enabled:
            _batch_sync_chunks_to_vector(
                collection_name=collection_name,
                doc_id=doc_id,
                chunks=need_update_chunks,
                embedding_model=embedding_model
            )
        else:
            _batch_delete_chunks_from_vector(
                collection_name=collection_name,
                chunk_ids=need_update_ids
            )

        # 11. 批量更新数据库状态
        for chunk in need_update_chunks:
            chunk.enabled = enabled_value
            chunk.updated_by = username

        db.commit()

        action = "启用" if enabled else "禁用"
        logger.info(
            f"批量{action}Chunk 成功, kb_id={document.kb_id}, doc_id={doc_id}, count={len(need_update_ids)}"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"批量更新分块启用状态失败, doc_id={doc_id}: {e}")
        raise ServiceException(f"批量更新分块启用状态失败: {str(e)}")


__all__ = [
    "delete_by_doc_id",
    "batch_create",
    "list_by_doc_id",
    "update_enabled_by_doc_id",
    "toggle_enabled_by_doc_id",
    "page_query",
    "delete",
    "enable_chunk",
    "batch_toggle_enabled",
]
