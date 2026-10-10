"""
Query Term Mapping Service (关键词映射服务层)
将 CRUD 操作下沉到 crud 模块，服务层仅保留业务逻辑
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.utils.snowflake_id_utils import generate_snowflake_id_str
from backend.models.query_term_mapping import QueryTermMapping
from backend.schemas.query_term_mapping import (
    QueryTermMappingCreateRequest,
    QueryTermMappingUpdateRequest,
    QueryTermMappingVO,
)
from backend.utils.exceptions import ClientException
from backend.crud import crud_query_term_mapping
from backend.db.database import SessionLocal

from backend.core.logger import logger


def create(db: Session, request: QueryTermMappingCreateRequest, username: str) -> str:
    """创建关键词映射规则

    Args:
        db: 数据库会话
        request: 创建请求
        username: 当前登录用户名

    Returns:
        str: 新建记录的 ID

    Raises:
        ClientException: 参数校验失败
    """
    if not request.source_term or not request.source_term.strip():
        raise ClientException("原始词不能为空")
    if not request.target_term or not request.target_term.strip():
        raise ClientException("目标词不能为空")

    source_term = request.source_term.strip()
    target_term = request.target_term.strip()

    record = QueryTermMapping(
        id=generate_snowflake_id_str(),
        domain=request.domain.strip() if request.domain else None,
        source_term=source_term,
        target_term=target_term,
        match_type=request.match_type,
        priority=request.priority,
        enabled=request.enabled,
        remark=request.remark.strip() if request.remark else None,
        create_by=username,
        update_by=username,
    )

    crud_query_term_mapping.add(db, record)
    db.commit()
    db.refresh(record)

    return record.id


def update(db: Session, mapping_id: str, request: QueryTermMappingUpdateRequest, username: str) -> None:
    """更新关键词映射规则

    Args:
        db: 数据库会话
        mapping_id: 映射规则 ID
        request: 更新请求
        username: 当前登录用户名

    Raises:
        ClientException: 记录不存在或参数校验失败
    """
    record = _get_mapping_or_raise(db, mapping_id)

    if request.domain is not None:
        record.domain = request.domain.strip() if request.domain else None
    if request.source_term is not None:
        if not request.source_term.strip():
            raise ClientException("原始词不能为空")
        record.source_term = request.source_term.strip()
    if request.target_term is not None:
        if not request.target_term.strip():
            raise ClientException("目标词不能为空")
        record.target_term = request.target_term.strip()
    if request.match_type is not None:
        record.match_type = request.match_type
    if request.priority is not None:
        record.priority = request.priority
    if request.enabled is not None:
        record.enabled = request.enabled
    if request.remark is not None:
        record.remark = request.remark.strip() if request.remark else None

    record.update_by = username
    db.commit()


def delete(db: Session, mapping_id: str) -> None:
    """删除关键词映射规则

    Args:
        db: 数据库会话
        mapping_id: 映射规则 ID

    Raises:
        ClientException: 记录不存在
    """
    record = _get_mapping_or_raise(db, mapping_id)
    crud_query_term_mapping.delete(db, record)
    db.commit()


def query_by_id(db: Session, mapping_id: str) -> QueryTermMappingVO:
    """根据 ID 查询关键词映射规则

    Args:
        db: 数据库会话
        mapping_id: 映射规则 ID

    Returns:
        QueryTermMappingVO: 映射规则视图对象

    Raises:
        ClientException: 记录不存在
    """
    record = _get_mapping_or_raise(db, mapping_id)
    return _to_vo(record)


def page_query(
    db: Session,
    current: int,
    size: int,
    keyword: Optional[str] = None
) -> dict:
    """分页查询关键词映射规则

    Args:
        db: 数据库会话
        current: 当前页码
        size: 每页数量
        keyword: 关键词搜索（匹配 source_term 或 target_term）

    Returns:
        dict: 分页结果 {records, total, current, size, pages}
    """
    records, total = crud_query_term_mapping.page_query(db, current, size, keyword)

    pages = (total + size - 1) // size if total > 0 else 0

    return {
        "records": [_to_vo(r) for r in records],
        "total": total,
        "current": current,
        "size": size,
        "pages": pages,
    }


def _get_mapping_or_raise(db: Session, mapping_id: str) -> QueryTermMapping:
    """根据 ID 加载记录，不存在则抛出异常

    Args:
        db: 数据库会话
        mapping_id: 映射规则 ID

    Returns:
        QueryTermMapping: 映射记录对象

    Raises:
        ClientException: 记录不存在
    """
    record = crud_query_term_mapping.get_by_id(db, mapping_id)

    if not record:
        raise ClientException("映射规则不存在")

    return record



# 模块级缓存：按优先级、长度排序后的启用映射规则列表
_cached_mappings: Optional[List[QueryTermMapping]] = None


def load_mappings(db: Optional[Session] = None) -> None:
    """从数据库加载所有启用的映射规则到缓存

    Args:
        db: 数据库会话，缺省时自行创建并关闭短生命周期会话
    """
    global _cached_mappings
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        db_list = crud_query_term_mapping.list_enabled(db)

        # 按优先级降序、source_term 长度降序排序
        db_list.sort(
            key=lambda m: (
                m.priority if m.priority else 0,
                len(m.source_term) if m.source_term else 0
            ),
            reverse=True
        )

        _cached_mappings = db_list
        logger.info(f"查询归一化映射规则加载完成, 共加载 {len(db_list)} 条规则")
    except Exception as e:
        logger.exception(f"加载映射规则失败: {e}")
        _cached_mappings = []
    finally:
        if own_session:
            db.close()


def normalize(text: str) -> str:
    """对用户问题进行术语归一化

    Args:
        text: 用户原始问题

    Returns:
        str: 归一化后的问题
    """
    if not text or not text.strip():
        return text

    # 如果缓存为空，尝试加载
    if _cached_mappings is None:
        load_mappings()

    if not _cached_mappings:
        return text

    result = text
    for mapping in _cached_mappings:
        # 只处理精确匹配 (match_type = 1)
        if mapping.match_type != 1:
            continue

        source = mapping.source_term
        target = mapping.target_term
        if not source or not target:
            continue

        result = _apply_mapping(result, source, target)

    if result != text:
        logger.info(f"查询归一化: original='{text}', normalized='{result}'")

    return result


def _apply_mapping(text: str, source_term: str, target_term: str) -> str:
    """安全归一化替换

    - 只替换 source_term
    - 如果当前位置本身已经是 target_term 起始，则不重复替换
    """
    if not text or not source_term:
        return text

    result = []
    idx = 0
    text_len = len(text)
    source_len = len(source_term)
    target_len = len(target_term)

    while idx < text_len:
        if text[idx:idx + source_len] == source_term:
            # 检查当前位置是否已经是 target_term
            if (target_len > 0 and
                idx + target_len <= text_len and
                text[idx:idx + target_len] == target_term):
                # 已经是目标词，不替换
                result.append(text[idx])
                idx += 1
            else:
                # 执行替换
                result.append(target_term)
                idx += source_len
        else:
            result.append(text[idx])
            idx += 1

    return ''.join(result)


def _to_vo(record: QueryTermMapping) -> QueryTermMappingVO:
    """将数据库记录转换为视图对象

    Args:
        record: 数据库记录

    Returns:
        QueryTermMappingVO: 视图对象
    """
    return QueryTermMappingVO(
        id=record.id,
        domain=record.domain,
        source_term=record.source_term,
        target_term=record.target_term,
        match_type=record.match_type,
        priority=record.priority,
        enabled=record.enabled,
        remark=record.remark,
        create_by=record.create_by,
        update_by=record.update_by,
        create_time=record.create_time,
        update_time=record.update_time,
    )


__all__ = [
    "create",
    "update",
    "delete",
    "query_by_id",
    "page_query",
    "load_mappings",
    "normalize",
]
