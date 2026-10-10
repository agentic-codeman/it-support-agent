"""
技术支持工单同步服务
将已关闭工单（status=2）同步到 Milvus 向量库以支持知识问答

写入策略：
- 每个工单仅写入 1 条 chunk，chunk_type="problem"
- content = 工单编号 + 标题 + 问题现象 + 根因 + 解决方案（全部参与向量化）

检索策略：
- query -> Milvus topN -> 直接读 chunk 的 content（已含工单编号/标题/问题现象/根因/解决方案）
"""
from datetime import datetime, timedelta, time
from typing import List, Dict

from pymilvus import DataType, Function, FunctionType

from backend.conf.milvus_config import milvus_config
from backend.core.logger import logger
from backend.db.database import SessionLocal
from backend.client.milvus_client import get_milvus_client
from backend.models.support_ticket import SupportTicketModel
from backend.utils.embedding_utils import embed_batch

# 工单状态：2=已关闭
STATUS_CLOSED = 2

# 向量化批次大小
EMBED_BATCH_SIZE = 50


def build_problem_chunk_text(ticket: SupportTicketModel) -> str:
    """构造问题现象 chunk 文本：工单编号 + 标题 + 问题现象 + 根因 + 解决方案

    Args:
        ticket: 工单模型实例

    Returns:
        str: 拼接后的 chunk 文本
    """
    lines = [
        f"工单编号：{ticket.ticket_no}",
        f"标题：{ticket.title}",
    ]
    if ticket.problem_desc:
        lines.append(f"问题现象：{ticket.problem_desc}")
    if ticket.root_cause:
        lines.append(f"根因：{ticket.root_cause}")
    if ticket.solution:
        lines.append(f"解决方案：{ticket.solution}")
    return "\n".join(lines)


def ensure_collection() -> None:
    """确保工单 Collection 存在，不存在则复用现有 Schema 自动创建"""
    client = get_milvus_client()
    name = milvus_config.ticket_collection_name
    if client.has_collection(name):
        return

    logger.info(f"工单集合 {name} 不存在，开始自动创建")
    dim = milvus_config.collection_dimension

    schema = client.create_schema(
        auto_id=False,
        enable_dynamic_field=False,
        description="技术支持工单知识库",
    )
    schema.add_field("id", DataType.VARCHAR, max_length=36, is_primary=True, description="主键ID")
    schema.add_field("content", DataType.VARCHAR, max_length=65535, enable_analyzer=True, description="文本内容")
    schema.add_field("metadata", DataType.JSON, description="元数据")
    schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=dim, description="稠密向量数据")
    schema.add_field("sparse_bm25", DataType.SPARSE_FLOAT_VECTOR, description="稀疏向量（BM25 自动生成）")
    schema.add_function(Function(
        name="bm25_emb",
        function_type=FunctionType.BM25,
        input_field_names=["content"],
        output_field_names=["sparse_bm25"],
    ))

    index_params = client.prepare_index_params()
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

    client.create_collection(name, schema=schema, index_params=index_params)
    client.load_collection(name)
    logger.info(f"工单集合 {name} 创建成功")


def _upsert_tickets(tickets: List[SupportTicketModel]) -> int:
    """将工单批量写入 Milvus（upsert，按 ticket_id 幂等覆盖）

    Args:
        tickets: 待同步的工单列表

    Returns:
        int: 写入的 chunk 数量
    """
    if not tickets:
        return 0

    ensure_collection()
    client = get_milvus_client()
    name = milvus_config.ticket_collection_name

    texts = [build_problem_chunk_text(t) for t in tickets]
    rows: List[Dict] = []

    for i in range(0, len(tickets), EMBED_BATCH_SIZE):
        batch_tickets = tickets[i:i + EMBED_BATCH_SIZE]
        batch_texts = texts[i:i + EMBED_BATCH_SIZE]
        embeddings = embed_batch(batch_texts)

        for ticket, text, vector in zip(batch_tickets, batch_texts, embeddings):
            rows.append({
                "id": str(ticket.id),  # 主键直接使用 ticket_id，保证幂等
                "content": text,
                "metadata": {
                    "ticket_id": ticket.id,
                    "ticket_no": ticket.ticket_no
                },
                "embedding": vector,
            })

    if rows:
        client.upsert(name, rows)
        client.flush(name)

    logger.info(f"工单向量同步完成，写入 {len(rows)} 条 chunk")
    return len(rows)


def full_sync() -> int:
    """全量同步：拉取所有已关闭工单并写入 Milvus

    Returns:
        int: 写入的 chunk 数量
    """
    db = SessionLocal()
    try:
        tickets = db.query(SupportTicketModel).filter(
            SupportTicketModel.status == STATUS_CLOSED
        ).all()
        logger.info(f"工单全量同步：拉取到 {len(tickets)} 条已关闭工单")
        return _upsert_tickets(tickets)
    finally:
        db.close()


def incremental_sync() -> int:
    """增量同步：拉取「更新时间为昨天」且已关闭的工单写入 Milvus

    Returns:
        int: 写入的 chunk 数量
    """
    today = datetime.now().date()
    yesterday_start = datetime.combine(today - timedelta(days=1), time.min)
    yesterday_end = datetime.combine(today, time.min)

    db = SessionLocal()
    try:
        tickets = db.query(SupportTicketModel).filter(
            SupportTicketModel.status == STATUS_CLOSED,
            SupportTicketModel.update_time >= yesterday_start,
            SupportTicketModel.update_time < yesterday_end,
        ).all()
        logger.info(f"工单增量同步：拉取到 {len(tickets)} 条昨日关闭工单")
        return _upsert_tickets(tickets)
    finally:
        db.close()
