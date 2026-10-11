/**
 * RAG 聊天服务
 * 两步式流式问答：提交任务（/chat） -> 订阅 SSE 流（/stream/{task_id}）
 */

import { useAuthStore } from '../store/authStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * 获取认证 token
 */
function getAuthToken() {
  const state = useAuthStore.getState();
  return state.accessToken || null;
}

/**
 * 构建请求头（自动附带认证 token）
 */
function buildHeaders(extra = {}) {
  const token = getAuthToken();
  return {
    'Authorization': token ? `Bearer ${token}` : '',
    ...extra,
  };
}

/**
 * 流式聊天（两步式）
 *
 * 第一步：POST /api/rag/v3/chat 提交问题，返回 { task_id, conversation_id }
 * 第二步：GET /api/rag/v3/stream/{task_id} 订阅 SSE 流，实时接收结果
 *
 * SSE 事件（命名事件，格式为 `event: xxx\ndata: {...}`）：
 *   - ready     连接建立
 *   - progress  节点进度（status / done_list / running_list）
 *   - delta     LLM 流式增量（data.delta）
 *   - final     最终完整答案（data.answer / data.image_urls）
 *   - error     错误信息（data.error）
 *
 * @param {Object} params - 聊天参数
 * @param {string} params.question - 用户问题
 * @param {string} [params.conversationId] - 会话 ID
 * @param {Function} params.onMessage - 增量内容回调（参数为字符串 delta）
 * @param {Function} params.onComplete - 完成回调（参数为 { taskId, conversationId, answer, image_urls }）
 * @param {Function} params.onError - 错误回调（参数为 Error）
 * @param {Function} [params.onMeta] - 提交成功后立即回调（参数为 { taskId, conversationId }）
 * @param {Function} [params.onProgress] - 进度回调（参数为 { status, done_list, running_list }）
 * @returns {Promise<string>} 任务 ID
 */
export async function streamChat({
  question,
  conversationId,
  onMessage,
  onComplete,
  onError,
  onMeta,
  onProgress,
}) {
  let reader = null;

  try {
    // ---------- 第一步：提交任务，获取 task_id ----------
    const body = { question };
    if (conversationId) {
      body.conversation_id = conversationId;
    }

    const chatUrl = `${API_BASE_URL}/api/rag/v3/chat`;
    const chatRes = await fetch(chatUrl, {
      method: 'POST',
      headers: buildHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(body),
    });

    if (!chatRes.ok) {
      throw new Error(`提交任务失败 (HTTP ${chatRes.status})`);
    }

    const chatJson = await chatRes.json();
    const taskId = chatJson?.data?.task_id;
    const convId = chatJson?.data?.conversation_id || conversationId;

    if (!taskId) {
      throw new Error('后端未返回 task_id');
    }

    // 提前把 taskId / conversationId 交给上层（用于中断按钮、会话记录）
    if (onMeta) {
      onMeta({ taskId, conversationId: convId });
    }

    // ---------- 第二步：订阅 SSE 流 ----------
    const streamUrl = `${API_BASE_URL}/api/rag/v3/stream/${taskId}`;
    const streamRes = await fetch(streamUrl, {
      method: 'GET',
      headers: buildHeaders({ Accept: 'text/event-stream' }),
    });

    if (!streamRes.ok) {
      throw new Error(`订阅流失败 (HTTP ${streamRes.status})`);
    }

    reader = streamRes.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let eventName = '';

    // 分发单个 SSE 事件；返回 true 表示应结束读取
    const dispatch = (data) => {
      switch (eventName) {
        case 'ready':
          // 连接建立，无需处理
          break;
        case 'progress':
          if (onProgress) {
            onProgress(data);
          }
          break;
        case 'delta':
          if (onMessage && data.delta) {
            onMessage(data.delta);
          }
          break;
        case 'final':
          if (onComplete) {
            onComplete({
              taskId,
              conversationId: convId,
              answer: data.answer,
              image_urls: data.image_urls,
            });
          }
          return true;
        case 'error':
          if (onError) {
            onError(new Error(data.error || '未知错误'));
          }
          return true;
        case '__close__':
          // 后端主动关闭连接信号
          return true;
        default:
          console.warn('未知 SSE 事件:', eventName, data);
      }
      return false;
    };

    let finished = false;
    while (!finished) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const rawLine of lines) {
        const line = rawLine.endsWith('\r') ? rawLine.slice(0, -1) : rawLine;
        if (line.startsWith('event:')) {
          eventName = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          const dataStr = line.slice(5).trim();
          if (!dataStr) {
            continue;
          }
          let data;
          try {
            data = JSON.parse(dataStr);
          } catch (error) {
            console.error('解析 SSE data 失败:', error, 'Line:', dataStr);
            continue;
          }
          if (dispatch(data)) {
            finished = true;
            break;
          }
        }
      }
    }

    return taskId;
  } catch (error) {
    console.error('流式聊天失败:', error);
    if (onError) {
      onError(error);
    }
    throw error;
  } finally {
    // 结束后主动关闭连接，触发后端清理队列与后台任务
    if (reader) {
      try {
        await reader.cancel();
      } catch (error) {
        // 忽略取消异常
      }
    }
  }
}

/**
 * 停止任务
 * @param {string} taskId - 任务 ID
 * @returns {Promise<Object>} 停止结果
 */
export async function stopTask(taskId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/rag/v3/stop`, {
      method: 'POST',
      headers: buildHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ task_id: taskId }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('停止任务失败:', error);
    throw error;
  }
}
