from backend.workflow.query_process.state import QueryGraphState
from backend.core.logger import logger
from dotenv import load_dotenv,find_dotenv
from pymilvus import AnnSearchRequest, RRFRanker

from backend.client.milvus_client import get_milvus_client
from backend.utils.embedding_utils import embed

load_dotenv(find_dotenv())


def node_search_embedding(state: QueryGraphState):
    logger.info("---search_milvus 开始处理---")

    query = state.get("rewritten_question")
    collection_name = state.get("collection_name")
    logger.info(f"核心入参提取: query='{query}'")
    milvus_client = get_milvus_client()
    query_dense = embed(query)
    dense_search_params = {
        "metric_type": "COSINE",
        "params": {"ef": 64}
    }
    dense_req = AnnSearchRequest(
        data=[query_dense],
        anns_field="embedding",
        param=dense_search_params,
        limit=15,
    )
    sparse_search_params = {
        "metric_type": "BM25",
        "params": {"drop_ratio_search": 0.2}
    }
    sparse_req = AnnSearchRequest(
        data=[query],
        anns_field="sparse_bm25",
        param=sparse_search_params,
        limit=15,
    )
    ranker = RRFRanker(k=60)
    res = milvus_client.hybrid_search(
        collection_name,
        reqs=[dense_req, sparse_req],
        ranker=ranker,
        limit=10,
        output_fields=["content", "metadata"]
    )

    hit_count = len(res[0]) if res and len(res) > 0 else 0
    logger.info(f"节点 search_embedding 处理成功，检索到 {hit_count} 条相关片段")
    if hit_count > 0:
        logger.debug(f"Top1 检索结果示例: {res[0][0]}")

    return {"embedding_chunks": res[0] if res else []}



if __name__ == "__main__":
    # 模拟测试数据
    test_state = {
        "session_id": "test_search_embedding_001",
        "item_names": ["HAK 180 烫金机"],  # 模拟已确认的商品名
        "is_stream": False,
        "collection_name": "devsupport",
        "rewritten_question": "Transformer 结构是怎样的？"
    }

    print("\n>>> 开始测试 node_search_embedding 节点...")
    try:
        # 执行节点函数
        result = node_search_embedding(test_state)
        logger.info(f"检索结果汇总：{result}")
        # 验证结果
        chunks = result.get("embedding_chunks", [])


        node_search_embedding(test_state)



        print(f"\n>>> 测试完成！检索到 {len(chunks)} 条结果")
        
        if chunks:
            print("\n>>> Top 1 结果详情:")
            top1 = chunks[0]
            # 打印关键字段（注意：entity字段可能包含具体业务数据）
            print(f"ID: {top1.get('id')}")
            print(f"Distance: {top1.get('distance')}")
            entity = top1.get('entity', {})
            print(f"Item Name: {entity.get('item_name')}")
            print(f"Content Preview: {entity.get('content', '')[:100]}...")
        else:
            print("\n>>> 警告：未检索到任何结果，请检查 Milvus 数据或 item_names 是否匹配")
            
    except Exception as e:
        logger.exception(f"测试运行失败: {e}")

