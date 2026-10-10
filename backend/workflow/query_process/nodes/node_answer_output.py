from backend.workflow.query_process.state import QueryGraphState
from backend.client.llm_factory import get_system_model
from backend.core.logger import logger
from backend.services.prompt_loader import load_prompt
import re

from backend.schemas.chat import ChatMessage
from backend.services.conversation_memory_service import append
from backend.utils.sse_utils import push_to_session, SSEEvent
from backend.services.stream_task_manager import get_stream_task_manager

_IMAGE_BLOCK_MARKER = "【图片】"
MAX_CONTEXT_CHARS = 12000


def step_1_check_answer(state) -> bool:
  answer = state.get("answer", None)
  if answer:
      logger.info("---Step 1: 发现已有答案，执行流式推送---")
      push_to_session(state["task_id"], SSEEvent.DELTA, {"delta": answer})
      return True
  else:
    return False


def step_2_construct_prompt(state: QueryGraphState) -> str:
  original_query = state.get("question", "")
  rewritten_query = state.get("rewritten_question", "")
  # 优先使用重写后的问题
  question = rewritten_query if rewritten_query else original_query
  history = state.get("history", [])
  reranked_docs = state.get("reranked_docs") or []

  docs = []
  used = 0
  for i, doc in enumerate(reranked_docs, start=1):
    text = (doc.get("text") or "").strip()
    if not text:
      continue
    source = doc.get("source") or ""
    chunk_id = doc.get("chunk_id") or ""
    url = (doc.get("url") or "").strip()
    title = (doc.get("title") or "").strip()
    score = doc.get("score")

    meta_parts = [f"[{i}]"]
    if source:
      meta_parts.append(f"[{source}]")
    if chunk_id:
      meta_parts.append(f"[chunk_id={chunk_id}]")
    if url:
      meta_parts.append(f"[url={url}]")
    if score is not None:
      # 保留四位小数
      meta_parts.append(f"[score={float(score):.4f}]")
    if title:
      meta_parts.append(f"[title={title}]")
    doc = " ".join(meta_parts) + "\n" + text
    if used + len(doc) > MAX_CONTEXT_CHARS:
      break
    docs.append(doc)
    # 计算使用长度！ + 2 两个\n\n
    used += len(doc) + 2
  context_str = "\n\n".join(docs) if docs else "无参考内容"

  history_str = ""
  if history:
    for msg in history:
      role = msg.role
      text = msg.content
      if role == "user" and text:
        history_str += f"用户: {text}\n"
      elif role == "assistant" and text:
        history_str += f"助手: {text}\n"
        
      used += len(history_str) + 2
      if used > MAX_CONTEXT_CHARS:
        break
  else:
    history_str = "无历史对话"

  prompt = load_prompt("answer_out",
    context=context_str,
    history=history_str,
    question=question
  )

  logger.info(f"组装后的提示词为：{prompt}")
  return prompt


def step_3_generate_response(state: QueryGraphState, prompt: str) -> QueryGraphState:
  logger.info("---Step 3: 开始生成回答 (LLM Generation)---")
  logger.debug(f"最终Prompt内容: {prompt}")
  llm = get_system_model()
  task_id = state.get("task_id")
  task_manager = get_stream_task_manager()

  logger.info(f"模式: 流式输出 (Streaming), Session: {task_id}")
  final_text = ""
  try:
    for chunk in llm.stream(prompt):
      if task_manager.is_cancelled(task_id):
        logger.info(f"任务 {task_id} 已被取消，中断流式生成")
        break
      delta = getattr(chunk, "content", "") or ""
      if delta:
        final_text += delta
        push_to_session(task_id, SSEEvent.DELTA, {"delta": delta})
    logger.info(f"流式输出完成，总长度: {len(final_text)}")
  except Exception as e:
    logger.exception(f"流式生成出错: {e}")
    # 发生错误时，尝试推送到前端
    push_to_session(task_id, SSEEvent.ERROR, {"error": str(e)})
  state["answer"] = final_text
  return state


def step_4_write_history(state: QueryGraphState, image_urls = None) -> QueryGraphState:
  conversation_id = state.get("conversation_id")
  user_id = state.get("user_id")
  
  answer = (state.get("answer") or "").strip()
  message = ChatMessage(
      role="assistant",
      content=answer
  )
  try:
        message_id = append(
            conversation_id=conversation_id,
            user_id=user_id,
            message=message
        )
        if message_id:
            logger.info(
                f"消息已保存到数据库 - messageId: {message_id}, conversationId: {conversation_id}")
        else:
            logger.warning("消息保存失败")
  except Exception as e:
    logger.error(f"写入Mongo历史记录失败: {e}")
  return state


def node_answer_output(state: QueryGraphState) -> QueryGraphState:
  logger.info("---node_answer_output (答案生成) 节点开始处理---")
  answer_exists = step_1_check_answer(state)
  if not answer_exists:
    prompt = step_2_construct_prompt(state)
    state["prompt"] = prompt
    step_3_generate_response(state, prompt)
  if state.get("answer"):
    answer = state["answer"]
    logger.info(f"answer 为：{answer}" )
    logger.info("---写入MongoDB历史记录---")
    step_4_write_history(state)
  push_to_session(
    state['task_id'],
    SSEEvent.FINAL,
    {
            "status": "completed"
    }
  )
  logger.info("---node_answer_output 节点处理结束---")
  return state


if __name__ == "__main__":
    print("\n" + "="*50)
    print(">>> 启动 node_answer_output 本地测试")
    print("="*50)
    mock_reranked_docs = [
        {
            "chunk_id": "local_101",
            "source": "local",
            "title": "HAK 180 烫金机操作手册_v2.pdf",
            "score": 0.95,
            "text": """
            HAK 180 烫金机的操作面板位于机器正前方。
            开启电源后，您需要先设置温度，默认建议设置在 110℃ 左右。
            具体的操作面板布局请参考下图：
            ![操作面板布局图](http://local-server/images/panel_view.jpg)
            
            如果是进行局部烫金，请调节侧面的旋钮。
            ![侧面旋钮细节](http://local-server/images/knob_detail.png)
            """
        },
        {
            "chunk_id": None,
            "source": "web",
            "title": "HAK 180 常见故障排除 - 官网",
            "score": 0.88,
            "url": "http://example.com/hak180_troubleshooting.jpeg", # 这是一个直接指向图片的URL（虽然少见，但用于测试提取）
            "text": "如果机器无法加热，请检查保险丝是否熔断..."
        },
        {
            "chunk_id": "local_102",
            "source": "local",
            "title": "安全注意事项",
            "score": 0.82,
            "text": "操作时请务必佩戴隔热手套，避免高温烫伤。"
        }
    ]

    # 模拟历史记录
    mock_history = [
        ChatMessage(role="user", content="你好，这款机器怎么用？"),
        ChatMessage(role="assistant", content="您好！请问您具体指的是哪一款机器？"),
        ChatMessage(role="user", content="HAK 180 烫金机")
    ]

    # 模拟输入状态
    mock_state = {
        "conversation_id": "conversation_001",
        "user_id": "user_001",
        "original_query": "HAK 180 烫金机怎么操作？",
        "rewritten_query": "HAK 180 烫金机的具体操作步骤和面板设置方法",
        "history": mock_history,
        "reranked_docs": mock_reranked_docs,
        "answer": None # 初始无答案
    }

    try:
        result = node_answer_output(mock_state)
        print("\n" + "="*50)
        print(">>> 测试结果摘要:")
        # 1. 验证 Prompt 构建
        if "prompt" in result:
            print(f"[PASS] Prompt 构建成功 (长度: {len(result['prompt'])})")
        else:
            print("[FAIL] Prompt 未构建")
        answer = result.get("answer")
        if answer and len(answer) > 10:
            print(answer)
        else:
            print(f"[WARN] 答案生成可能异常 (Content: {answer})")
        print("="*50)

    except Exception as e:
        logger.exception(f"测试运行期间发生未捕获异常: {e}")
