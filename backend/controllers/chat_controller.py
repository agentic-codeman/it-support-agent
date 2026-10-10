"""
RAG 聊天控制器
两步式流式问答：提交任务（返回 task_id） -> 订阅流 /stream/{task_id}
支持任务取消 /stop
"""
import asyncio
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from langsmith import traceable, set_run_metadata

from backend.workflow.query_process.main_graph import query_app
from backend.workflow.query_process.state import QueryGraphState
from backend.schemas.user_context import UserContext
from backend.schemas.chat import StopTaskRequest
from backend.services.stream_task_manager import get_stream_task_manager
from backend.utils.result import success_result
from backend.utils.snowflake_id_utils import generate_snowflake_id_str
from backend.utils.sse_utils import create_sse_queue, sse_generator, push_to_session, SSEEvent

from backend.core.logger import logger

router = APIRouter(prefix="/api/rag/v3", tags=["RAG Chat"])


@router.get("/chat")
async def chat(question: str, conversation_id: str = None, deep_thinking: bool = False):
    """第一步：提交对话，返回 task_id 与 conversation_id，后台异步执行查询图

    Args:
        question: 用户问题
        conversation_id: 会话 ID（可选，空时创建新会话）
        deep_thinking: 是否开启深度思考模式
    """
    try:
        # 生成任务 ID
        task_id = generate_snowflake_id_str()

        # 如果没有提供会话 ID，说明是新会话
        if not conversation_id:
            conversation_id = generate_snowflake_id_str()

        user_id = UserContext.get_user_id()

        # 创建 SSE 队列（key = task_id）
        create_sse_queue(task_id)

        # 后台运行查询图，并注册到任务管理器以便取消
        task_manager = get_stream_task_manager()
        task = asyncio.create_task(
            asyncio.to_thread(run_query_graph, question, task_id, user_id, conversation_id)
        )
        task_manager.bind_handle(task_id, task)
        # 任务结束后自动清理
        task.add_done_callback(lambda _: task_manager.cleanup(task_id))

        return success_result(data={"task_id": task_id, "conversation_id": conversation_id})
    except Exception as e:
        logger.exception(f"发起对话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream/{task_id}")
async def stream(task_id: str, request: Request):
    """第二步：订阅 SSE 流，实时返回结果"""
    return StreamingResponse(
        sse_generator(task_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@traceable(name="run_query_graph")
def run_query_graph(question: str, task_id: str, user_id: str, conversation_id: str, is_stream: bool = True):
    set_run_metadata(thread_id=conversation_id, task_id=task_id, user_id=user_id)
    """后台运行查询图（LangGraph），结果通过 SSE 队列推送给前端"""
    logger.info(
        f"开始流程图处理... question={question}, task_id={task_id}, "
        f"user_id={user_id}, conversation_id={conversation_id}, is_stream={is_stream}"
    )
    default_state = QueryGraphState(
        question=question,
        original_query=question,
        task_id=task_id,
        session_id=task_id,
        conversation_id=conversation_id,
        user_id=user_id,
        is_stream=is_stream,
    )
    try:
        query_app.invoke(default_state)
    except Exception as e:
        logger.error(f"流程执行异常: {e}")


@router.post("/stop")
async def stop_task(request: StopTaskRequest):
    """停止指定任务（主动取消后台执行）"""
    try:
        task_manager = get_stream_task_manager()
        task_manager.cancel(request.task_id)
        return success_result(message="任务不存在或已完成")
    except Exception as e:
        logger.exception(f"停止任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
