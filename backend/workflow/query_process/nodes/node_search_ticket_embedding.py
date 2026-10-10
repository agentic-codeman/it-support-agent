from backend.workflow.query_process.state import QueryGraphState
from backend.conf.milvus_config import milvus_config
from backend.core.logger import logger
from dotenv import load_dotenv,find_dotenv
from pymilvus import AnnSearchRequest, RRFRanker

from backend.client.milvus_client import get_milvus_client
from backend.utils.embedding_utils import embed

load_dotenv(find_dotenv())


def node_search_ticket_embedding(state: QueryGraphState):

    logger.info("---search_milvus 开始处理---")

    query = state.get("rewritten_question")
    client = get_milvus_client()
    collection_name = milvus_config.ticket_collection_name
    query_dense = embed(query)

    dense_req = AnnSearchRequest(
        data=[query_dense],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"ef": 64}},
        limit=15,
    )
    sparse_req = AnnSearchRequest(
        data=[query],
        anns_field="sparse_bm25",
        param={"metric_type": "BM25", "params": {"drop_ratio_search": 0.2}},
        limit=15,
    )
    res = client.hybrid_search(
        collection_name,
        reqs=[dense_req, sparse_req],
        ranker=RRFRanker(k=60),
        limit=10,
        output_fields=["content"],
    )

    hits = res[0] if res else []
    result = [hit["entity"].get("content", "") for hit in hits]
    logger.info(f"工单检索：命中 {len(result)} 条解决方案")
    return {"ticket_embedding_chunks": result}



if __name__ == "__main__":
    # 模拟测试数据
    test_state = {
        "session_id": "test_search_embedding_001",
        "rewritten_query": "HAK 180 烫金机使用说明",  # 模拟改写后的查询
        "item_names": ["HAK 180 烫金机"],  # 模拟已确认的商品名
        "is_stream": False,
        "collection_name": "devsupport",
        "rewritten_question": "Transformer 结构是怎样的？"
    }

    print("\n>>> 开始测试 node_search_embedding 节点...")
    try:
        # 执行节点函数
        result = node_search_ticket_embedding(test_state)
        logger.info(f"检索结果汇总：{result}")
    except Exception as e:
        logger.exception(f"测试运行失败: {e}")

