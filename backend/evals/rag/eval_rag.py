"""
RAGAS 端到端评测 —— 对当前 RAG 链路（LangGraph query_app）进行评测

评测指标：
- Context Precision (context_precision_with_reference): 检索到的上下文中，相关片段是否排在前面
- Context Recall (context_recall): 标准答案（ground_truth）中的关键信息是否被检索到
- Faithfulness (faithfulness): 生成的回答是否忠实于检索到的上下文
- Answer Relevancy (answer_relevancy): 生成的回答与用户问题的相关程度

评测流程：
1. 从 data/eval/rag/技术支持评测数据集.xlsx 加载 (question, ground_truth)
2. 对每个问题运行完整的查询图 query_app，得到最终 answer 与 reranked_docs（作为检索上下文）
3. 使用 RAGAS 对四项指标逐样本评分
4. 打印均值并保存 CSV / JSON

使用方式：
    cd 项目根目录
    .venv311/Scripts/python.exe -m backend.evals.rag.eval_rag
"""
import os
import sys
import json
import math
import asyncio
from typing import List, Dict

import pandas as pd

# 确保项目根目录在 sys.path 中（backend/evals/rag -> 项目根目录需上溯 4 级）
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv()


# ========== 评测配置 ==========

DATASET_PATH = os.path.join(
    _PROJECT_ROOT, "data", "eval", "rag", "技术支持评测数据集.xlsx",
)

# 评测使用的用户 / 会话标识
# - user_id 使用独立的评测用户，避免污染真实用户数据
# - conversation_id 每个样本单独生成，保证单轮独立（无历史串扰）
EVAL_USER_ID = os.getenv("EVAL_USER_ID", "eval_ragas_user")

# 结果输出目录
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "results",
)


# ========== 加载评测数据集 ==========

def load_eval_dataset() -> List[Dict]:
    """从 Excel 文件加载评测数据集。

    Excel 文件需包含 question 和 ground_truth 两列。

    Returns:
        List[Dict]: 每条包含 question / ground_truth 的字典
    """
    df = pd.read_excel(DATASET_PATH)
    dataset = []
    for _, row in df.iterrows():
        question = str(row["question"]).strip()
        gt = str(row["ground_truth"]).strip()
        if question and gt:
            dataset.append({"question": question, "ground_truth": gt})
    print(f"✅ 已从 {DATASET_PATH} 加载 {len(dataset)} 条评测数据")
    return dataset


# ========== 运行查询链路，获取 answer 与 contexts ==========

def _run_single_question(question: str, index: int) -> Dict:
    """对单个问题运行完整查询图，返回 answer 与检索到的上下文。

    Args:
        question: 用户问题
        index: 样本序号（用于日志）

    Returns:
        Dict: 包含 answer 与 contexts 的字典；执行异常时 answer 记录错误信息
    """
    from backend.workflow.query_process.main_graph import query_app
    from backend.services.stream_task_manager import get_stream_task_manager
    from backend.utils.sse_utils import create_sse_queue, remove_sse_queue
    from backend.utils.snowflake_id_utils import generate_snowflake_id_str

    task_id = generate_snowflake_id_str()
    conversation_id = generate_snowflake_id_str()

    # 关键：必须先绑定任务，否则 node_answer_output 中 is_cancelled 对未注册任务
    # 恒返回 True，导致流式生成立即中断、answer 为空。
    get_stream_task_manager().bind_handle(task_id, None)
    create_sse_queue(task_id)

    state = {
        "question": question,
        "task_id": task_id,
        "session_id": task_id,
        "conversation_id": conversation_id,
        "user_id": EVAL_USER_ID,
    }

    try:
        result = query_app.invoke(state)

        answer = (result.get("answer") or "").strip()
        reranked_docs = result.get("reranked_docs") or []
        contexts = [
            d.get("text", "").strip()
            for d in reranked_docs
            if (d.get("text") or "").strip()
        ]
        return {"answer": answer, "contexts": contexts}

    except Exception as e:
        # 单个样本执行失败不应中断整个评测
        print(f"    ❌ [{index}] 查询链路执行异常: {e}")
        return {"answer": f"[错误] {e}", "contexts": []}

    finally:
        remove_sse_queue(task_id)
        get_stream_task_manager().cleanup(task_id)


def run_pipeline(dataset: List[Dict]) -> List[Dict]:
    """对评测数据集中的每个问题运行完整查询链路。

    Args:
        dataset: 评测数据集（含 question / ground_truth）

    Returns:
        List[Dict]: 每条包含 question / ground_truth / answer / contexts
    """
    samples = []
    for i, item in enumerate(dataset):
        question = item["question"]
        print(f"\n🔍 [{i + 1}/{len(dataset)}] 运行查询链路: {question[:50]}...")

        result = _run_single_question(question, i + 1)

        preview = result["answer"][:80].replace("\n", " ") + (
            "..." if len(result["answer"]) > 80 else ""
        )
        print(f"   📦 检索到 {len(result['contexts'])} 个上下文片段")
        print(f"   ✅ 回答 ({len(result['answer'])} 字符): {preview}")

        samples.append({
            "question": question,
            "ground_truth": item["ground_truth"],
            "answer": result["answer"],
            "contexts": result["contexts"],
        })

    return samples


# ========== RAGAS 评测 ==========

def _apply_vertexai_shim():
    """兼容补丁：ragas 0.4.x 硬编码了 langchain_community.chat_models.vertexai，
    但部分 langchain-community 版本已移除该模块，需注入空 shim 避免 ImportError。"""
    import importlib
    import types

    if "langchain_community.chat_models.vertexai" in sys.modules:
        return
    try:
        importlib.import_module("langchain_community.chat_models.vertexai")
    except (ImportError, ModuleNotFoundError):
        shim = types.ModuleType("langchain_community.chat_models.vertexai")
        shim.ChatVertexAI = type("ChatVertexAI", (), {})  # 空占位类
        sys.modules["langchain_community.chat_models.vertexai"] = shim


async def evaluate(samples: List[Dict]) -> Dict[str, List[float]]:
    """使用 RAGAS 对四项指标逐样本评分。

    Args:
        samples: run_pipeline 返回的数据（question/ground_truth/answer/contexts）

    Returns:
        Dict: {指标名: [每样本分数]}
    """
    _apply_vertexai_shim()

    import instructor
    from openai import AsyncOpenAI
    from ragas.llms import llm_factory
    from ragas.embeddings.base import embedding_factory
    from ragas.metrics.collections import (
        ContextPrecisionWithReference,
        ContextRecall,
        Faithfulness,
        AnswerRelevancy,
    )
    from backend.conf.model_config import model_config

    # 统一的基础 LLM 客户端（DashScope OpenAI 兼容端点）
    client = AsyncOpenAI(api_key=model_config.api_key, base_url=model_config.base_url)

    # 各指标使用独立的 LLM 包装，因 qwen 系列对结构化输出支持不同，需不同 instructor 模式：
    # - Context 指标：Mode.MD_JSON（DashScope 兼容模式不支持 response_format json_schema，
    #   改用 markdown 代码块输出 JSON，避免结构化输出返回空 {}）
    # - Faithfulness：Mode.TOOLS（qwen-max 不遵循 NLI 提示词的输出字段名，用 function-call 强制字段）
    # - AnswerRelevancy：无需 instructor（仅生成问题 + 向量相似度）
    llm_ctx = llm_factory(model_config.llm_model, client=client, max_tokens=8192)
    llm_ctx.client = instructor.from_openai(client, mode=instructor.Mode.MD_JSON)

    llm_faith = llm_factory(model_config.llm_model, client=client, max_tokens=8192)
    llm_faith.client = instructor.from_openai(client, mode=instructor.Mode.TOOLS)

    llm_ar = llm_factory(model_config.llm_model, client=client, max_tokens=8192)

    # 向量嵌入：与检索链路使用相同的 Ollama bge-m3 模型（/v1 为 OpenAI 兼容端点）
    embedding_base = model_config.embedding_api_url.replace("/api/embed", "/v1")
    embedding_client = AsyncOpenAI(api_key="ollama", base_url=embedding_base)
    embeddings = embedding_factory(
        "openai", model=model_config.embedding_model, client=embedding_client,
    )

    cp_metric = ContextPrecisionWithReference(llm=llm_ctx)
    cr_metric = ContextRecall(llm=llm_ctx)
    faith_metric = Faithfulness(llm=llm_faith)
    ar_metric = AnswerRelevancy(llm=llm_ar, embeddings=embeddings)

    cp_scores: List[float] = []
    cr_scores: List[float] = []
    faith_scores: List[float] = []
    ar_scores: List[float] = []

    print("\n📊 正在进行 RAGAS 评测...")
    total = len(samples)
    for i, s in enumerate(samples):
        question = s["question"]
        reference = s["ground_truth"]
        answer = s["answer"]
        contexts = s["contexts"]

        print(f"  评测样本 {i + 1}/{total}: {question[:40]}...")

        # --- Context Precision / Recall：需要检索上下文 ---
        if not contexts:
            cp_scores.append(0.0)
            cr_scores.append(0.0)
        else:
            try:
                cp = await cp_metric.ascore(
                    user_input=question,
                    reference=reference,
                    retrieved_contexts=contexts,
                )
                cp_scores.append(cp.value)
            except Exception as e:
                print(f"    ⚠️ ContextPrecision 评分失败: {e}")
                cp_scores.append(float("nan"))

            try:
                cr = await cr_metric.ascore(
                    user_input=question,
                    retrieved_contexts=contexts,
                    reference=reference,
                )
                cr_scores.append(cr.value)
            except Exception as e:
                print(f"    ⚠️ ContextRecall 评分失败: {e}")
                cr_scores.append(float("nan"))

        # --- Faithfulness：需要回答 + 检索上下文 ---
        if not answer or answer.startswith("[错误]") or not contexts:
            faith_scores.append(0.0)
        else:
            try:
                f = await faith_metric.ascore(
                    user_input=question,
                    response=answer,
                    retrieved_contexts=contexts,
                )
                faith_scores.append(f.value)
            except Exception as e:
                print(f"    ⚠️ Faithfulness 评分失败: {e}")
                faith_scores.append(float("nan"))

        # --- Answer Relevancy：需要回答 ---
        if not answer or answer.startswith("[错误]"):
            ar_scores.append(0.0)
        else:
            try:
                ar = await ar_metric.ascore(
                    user_input=question,
                    response=answer,
                )
                ar_scores.append(ar.value)
            except Exception as e:
                print(f"    ⚠️ AnswerRelevancy 评分失败: {e}")
                ar_scores.append(float("nan"))

    return {
        "context_precision": cp_scores,
        "context_recall": cr_scores,
        "faithfulness": faith_scores,
        "answer_relevancy": ar_scores,
    }


# ========== 结果输出 ==========

def _avg(vals: List[float]) -> float:
    """计算均值，忽略 NaN。"""
    valid = [v for v in vals if not math.isnan(v)]
    return sum(valid) / len(valid) if valid else 0.0


def print_and_save_results(results: Dict[str, List[float]], samples: List[Dict]):
    """打印评测结果并保存到 CSV / JSON。

    Args:
        results: evaluate 返回的 {指标名: [每样本分数]}
        samples: 含 question/ground_truth/answer/contexts 的样本列表
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    means = {name: _avg(vals) for name, vals in results.items()}

    print("\n" + "=" * 60)
    print("  RAGAS 评测结果")
    print("=" * 60)
    for name, mean in means.items():
        valid = sum(1 for v in results[name] if not math.isnan(v))
        print(f"  {name:<22} {mean:.4f}  (有效样本 {valid}/{len(results[name])})")
    print("=" * 60)

    # 构建 DataFrame（每行一个样本）
    results_df = pd.DataFrame({
        "question": [s["question"] for s in samples],
        "ground_truth": [s["ground_truth"] for s in samples],
        "answer": [s["answer"] for s in samples],
        "context_count": [len(s["contexts"]) for s in samples],
        "context_precision": results["context_precision"],
        "context_recall": results["context_recall"],
        "faithfulness": results["faithfulness"],
        "answer_relevancy": results["answer_relevancy"],
    })

    csv_path = os.path.join(OUTPUT_DIR, "ragas_eval_results.csv")
    results_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\n📁 CSV 结果已保存到 {csv_path}")

    results_json = {
        "metrics": means,
        "per_sample": [
            {
                "question": s["question"],
                "ground_truth": s["ground_truth"],
                "answer": s["answer"],
                "contexts": s["contexts"],
                "scores": {
                    name: (results[name][i] if not math.isnan(results[name][i]) else None)
                    for name in results
                },
            }
            for i, s in enumerate(samples)
        ],
    }
    json_path = os.path.join(OUTPUT_DIR, "ragas_eval_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_json, f, ensure_ascii=False, indent=2)
    print(f"📁 JSON 结果已保存到 {json_path}")


# ========== 主入口 ==========

def main():
    print("=" * 60)
    print("  RAGAS 端到端评测（Context Precision / Recall / Faithfulness / Answer Relevancy）")
    print("=" * 60)

    dataset = load_eval_dataset()
    if not dataset:
        print("\n⚠️  评测数据集为空，请检查 Excel 文件内容")
        return
    print(f"  评测样本数: {len(dataset)}")

    # 1. 运行查询链路，收集 answer 与 contexts
    samples = run_pipeline(dataset)

    # 2. 执行 RAGAS 评测
    results = asyncio.run(evaluate(samples))

    # 3. 输出并保存结果
    print_and_save_results(results, samples)


if __name__ == "__main__":
    main()
