import sys
import os
from typing import Any, List, Dict

from backend.workflow.import_process.state import ImportGraphState
from backend.core.logger import logger
from backend.utils.embedding_utils import embed_batch
from backend.utils.snowflake_id_utils import generate_snowflake_id_str


def node_bge_embedding(state: ImportGraphState) -> ImportGraphState:
    current_node = sys._getframe().f_code.co_name
    logger.info(f">>> 开始执行LangGraph节点：{current_node}")

    logger.info("--- BGE-M3 文本向量化处理启动 ---")

    try:
        texts_to_embed = step_1_validate_input(state)

        output_data = step_2_generate_embeddings(texts_to_embed)

        state['chunks'] = output_data
        logger.info(f"--- BGE-M3 向量化处理完成，共处理 {len(output_data)} 条文本切片 ---")
    except Exception as e:
        logger.exception(f"BGE-M3向量化节点执行失败：{str(e)}")

    return state


def step_1_validate_input(state: ImportGraphState) -> List[Dict[str, Any]]:
    texts_to_embed = state.get("chunks")
    if not isinstance(texts_to_embed, list) or not texts_to_embed:
        logger.error("向量化输入校验失败：chunks字段为空或非有效列表")
        raise ValueError("错误: 无有效文本切片数据，无法执行向量化处理")

    logger.info(f"向量化输入校验通过，待处理文本切片数量：{len(texts_to_embed)}")
    return texts_to_embed


def step_2_generate_embeddings(texts_to_embed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output_data = []
    batch_size = 5

    total = len(texts_to_embed)
    for i in range(0, total, batch_size):
        batch_texts = texts_to_embed[i:i + batch_size]
        start_idx, end_idx = i + 1, min(i + len(batch_texts), total)

        try:
            input_texts = []
            for doc in batch_texts:
                content = doc["content"]
                input_texts.append(content)

            dense_vectors = embed_batch(input_texts)
            if not dense_vectors:
                logger.warning(f"第{start_idx}-{end_idx}条切片：向量生成返回空，保留原数据")
                output_data.extend(batch_texts)
                continue

            for j, doc in enumerate(batch_texts):
                item = doc.copy()
                item["dense_vector"] = dense_vectors[j]
                item["index"] = i + j
                item["chunk_id"] = generate_snowflake_id_str()
                output_data.append(item)

            logger.info(f"第{start_idx}-{end_idx}条切片：稠密向量生成成功")

        except Exception as e:
            logger.exception(
                f"第{start_idx}-{end_idx}条切片：向量生成失败，保留原数据 | 错误原因：{str(e)}"
            )
            output_data.extend(batch_texts)
            continue

    return output_data


if __name__ == '__main__':
    # 加载环境变量：定位项目根目录下的.env，读取模型路径/设备等配置
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    # 构造模拟测试状态：模拟上游节点输出的chunks数据，贴合真实业务场景
    test_state = ImportGraphState({
        "task_id": "test_task_embedding_001",  # 测试任务ID
        "chunks": [  # 模拟带item_name的文本切片（上游商品名称识别节点产出）
            {
                "content": "这是一个测试文档的内容，用于验证向量化是否成功。",
                "title": "测试文档标题",
                "item_name": "测试项目",
                "file_title": "测试文件.pdf"
            },
            {
                "content": "这是第二个测试文档的内容，用于验证批量处理逻辑。",
                "title": "测试文档标题2",
                "item_name": "测试项目",
                "file_title": "测试文件.pdf"
            }
        ]
    })

    # 执行本地测试
    logger.info("=== BGE-M3向量化节点本地单元测试启动 ===")
    try:
        # 调用核心节点函数
        result_state = node_bge_embedding(test_state)
        # 提取测试结果
        result_chunks = result_state.get("chunks", [])

        # 打印测试结果统计
        logger.info(f"=== 向量化节点本地测试完成 ===")
        logger.info(f"测试任务ID：{test_state.get('task_id')}")
        logger.info(f"待处理切片数：2 | 实际处理切片数：{len(result_chunks)}")
        logger.info(f"向量维度：{result_chunks}")

        # 验证向量生成结果（打印向量字段是否存在）
        for idx, chunk in enumerate(result_chunks):
            has_dense = "dense_vector" in chunk
            has_sparse = "sparse_vector" in chunk
            logger.info(
                f"第{idx + 1}条切片：稠密向量生成{'' if has_dense else '未'}成功 | 稀疏向量生成{'' if has_sparse else '未'}成功")

    except Exception as e:
        logger.exception(f"=== 向量化节点本地测试失败 ===" f"错误原因：{str(e)}")
        # 新手友好提示：给出核心排查方向
        logger.warning("排查提示：请检查BGE-M3模型路径、显存是否充足、环境变量配置是否正确")