/**
 * 消息反馈服务
 * 提供点赞、点踩等反馈功能
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
 * 提交消息反馈（点赞/点踩）
 * @param {string} messageId - 消息ID
 * @param {string} conversationId - 会话ID
 * @param {number} vote - 投票值：1=点赞，-1=点踩
 * @param {string} reason - 反馈原因（可选）
 * @param {string} comment - 补充说明（可选）
 * @returns {Promise<Object>} 操作结果
 */
export async function submitFeedback(messageId, conversationId, vote, reason = null, comment = null) {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/feedback/message/${messageId}?conversation_id=${conversationId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    },
    body: JSON.stringify({
      vote,
      reason,
      comment
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '反馈提交失败');
  }

  return await response.json();
}

/**
 * 获取当前用户对指定消息的投票
 * @param {string} messageId - 消息ID
 * @returns {Promise<number|null>} 投票值：1=点赞，-1=点踩，null=未投票
 */
export async function getMessageVote(messageId) {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/feedback/message/${messageId}/vote`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '查询投票失败');
  }

  const result = await response.json();
  return result.data?.vote || null;
}
