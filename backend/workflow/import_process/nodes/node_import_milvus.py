from typing import List, Dict, Any
from backend.core.logger import logger
from backend.client.milvus_client import get_milvus_client, delete_with_retry
from backend.utils.snowflake_id_utils import generate_snowflake_id_str


def node_import_milvus(state: Dict[str, Any]) -> Dict[str, Any]:
    current_node = sys._getframe().f_code.co_name
    logger.info(f">>> 开始执行LangGraph节点：{current_node}（Milvus切片数据入库）")

    try:
        # 步骤1：输入数据有效性校验
        chunks_json_data, vector_dimension = step_1_check_input(state)
        doc_id = state["doc_id"]
        kb_id = state["kb_id"]
        collection_name = state["collection_name"]
        user_name = state["user_name"]
        # 步骤2：幂等性，清理旧数据
        step_2_clean_old_data(doc_id, collection_name, chunks_json_data)
        # 步骤3：批量插入数据
        step_3_insert_data(doc_id, kb_id, collection_name, user_name, chunks_json_data)
        #步骤4：更新状态
        step_4_update_document_status(state)
        logger.info("--- Milvus切片数据入库流程完成 ---")
    except Exception as e:
        logger.exception(f"Milvus切片数据入库节点执行失败：{str(e)}")
        raise ValueError(f"Milvus 导入过程中发生错误: {e}")

    return state


def step_1_check_input(state: Dict[str, Any]) -> tuple[List[Dict[str, Any]], int]:
    chunks_json_data = state.get("chunks")
    if not chunks_json_data:
        logger.error("Milvus入库校验失败：state中chunks字段为空")
        raise ValueError("错误: chunks为空，无法执行Milvus入库")
    if not isinstance(chunks_json_data, list) or len(chunks_json_data) == 0:
        logger.error("Milvus入库校验失败：chunks非列表类型或为空列表")
        raise ValueError("错误: chunks数据格式不正确，必须为非空列表")
    first_chunk = chunks_json_data[0]
    if 'dense_vector' not in first_chunk:
        logger.error("Milvus入库校验失败：切片缺失dense_vector字段，上游向量化节点可能执行失败")
        raise ValueError("错误: 数据中缺失dense_vector字段，请检查上游向量化节点执行状态")

    vector_dimension = len(first_chunk['dense_vector'])
    logger.info(
        f"Milvus入库校验通过，待入库切片数：{len(chunks_json_data)} | 向量维度：{vector_dimension}")

    return chunks_json_data, vector_dimension


def step_2_clean_old_data(doc_id : str, collection_name: str, chunks_json_data: List[Dict[str, Any]]):

    from backend.db.database import SessionLocal
    from backend.services import chunk_service

    db = SessionLocal()
    try:
        # 2. 清理 Milvus 旧向量
        delete_with_retry(collection_name, filter=f"metadata['doc_id'] == '{doc_id}'")
        logger.info(f"已删除文档旧向量, doc_id={doc_id}, collection_name={collection_name}")

        deleted_count = chunk_service.delete_by_doc_id(db, doc_id)
        logger.info(f"已删除文档旧分块记录, doc_id={doc_id}, 数量={deleted_count}")
    finally:
        db.close()


def step_3_insert_data(
    doc_id: str,
    kb_id: str,
    collection_name: str,
    user_name: str,
    chunks_json_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:

    milvus_data_to_insert = []
    chunks_data_for_mysql = []
    total_chunks = len(chunks_json_data)
    for idx, item in enumerate(chunks_json_data):
        chunk_id = item.get("chunk_id") or generate_snowflake_id_str()
        item["chunk_id"] = chunk_id

        metadata_dict = {
            "doc_id": doc_id,
            "chunk_index": idx,
            "total_chunks": total_chunks,
        }

        row = {
            "id": chunk_id,
            "embedding": item["dense_vector"],
            "content": item["content"],
            "metadata": metadata_dict,
        }
        milvus_data_to_insert.append(row)

        chunks_data_for_mysql.append({
            "chunk_id": chunk_id,
            "index": idx,
            "content": item["content"],
        })

    from backend.db.database import SessionLocal
    from backend.services import chunk_service

    db = SessionLocal()
    try:
        created_count = chunk_service.batch_create(db, doc_id, kb_id, chunks_data_for_mysql, user_name)
        logger.info(
            f"MySQL分块记录创建完成, doc_id={doc_id}, 新建记录={created_count}"
        )
    finally:
        db.close()

    logger.info(f"Milvus数据插入：准备{len(milvus_data_to_insert)}条切片数据，开始批量插入")
    # 3. 执行批量插入
    milvus_client = get_milvus_client()
    milvus_client.insert(collection_name, milvus_data_to_insert)
    milvus_client.flush(collection_name)
    logger.info(f"Milvus数据插入完成：成功插入{len(milvus_data_to_insert)}条数据")


def step_4_update_document_status(state: Dict[str, Any]):

    from backend.db.database import SessionLocal
    from backend.models.knowledge_document import KnowledgeDocumentModel
    from backend.schemas.enums.document_status import DocumentStatus

    doc_id = state.get("doc_id")
    chunk_count = len(state.get("chunks") or [])

    db = SessionLocal()
    try:
        doc = db.query(KnowledgeDocumentModel).filter(
            KnowledgeDocumentModel.id == doc_id,
            KnowledgeDocumentModel.deleted == 0
        ).first()

        if not doc:
            logger.warning(f"更新文档状态失败：文档不存在, doc_id={doc_id}")
            return

        doc.status = DocumentStatus.SUCCESS.value
        doc.chunk_count = chunk_count
        db.commit()
        logger.info(f"文档状态已更新为成功, doc_id={doc_id}, 分块数={chunk_count}")
    except Exception as e:
        db.rollback()
        logger.exception(f"更新文档状态失败, doc_id={doc_id}: {e}")
        raise ValueError(f"更新文档状态失败: {e}")
    finally:
        db.close()


if __name__ == '__main__':

    import sys
    import os
    from dotenv import load_dotenv

    # 加载环境变量 (自动寻找项目根目录的 .env)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    load_dotenv(os.path.join(project_root, ".env"))

    # 构造测试数据
    dim = 1024
    test_state = {
        "task_id": "test_milvus_task",
        "doc_id": "17805447819085861",
        "collection_name": "wendarobotbak",
        "chunks": [
            {
                "content": "Milvus 测试文本 1",
                "title": "测试标题",
                "item_name": "测试项目_Milvus",  # 必须有 item_name，用于幂等清理
                "parent_title":"test.pdf",
                "part":1,
                "file_title": "test.pdf",
                "dense_vector": [0.1] * dim,  # 模拟 Dense Vector
                "sparse_vector": {1: 0.5, 10: 0.8}  # 模拟 Sparse Vector
            }
        ]
    }

    print("正在执行 Milvus 导入节点测试...")
    try:

            result_state = node_import_milvus(test_state)

            # 验证结果
            chunks = result_state.get("chunks", [])
            if chunks and chunks[0].get("chunk_id"):
                print(f"✅ Milvus 导入测试通过，生成 ID: {chunks[0]['id']}")
            else:
                print("❌ 测试失败：未能获取 chunk_id")

    except Exception as e:
        print(f"❌ 测试失败: {e}")