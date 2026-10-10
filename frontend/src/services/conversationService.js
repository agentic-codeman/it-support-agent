/**
 * 会话服务
 * 提供会话列表、重命名、删除等功能
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
 * 获取会话列表
 * @returns {Promise<Array>} 会话列表
 */
export async function listConversations() {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/conversations`, {
    method: 'GET',
    headers: {
      'Authorization': token ? `Bearer ${token}` : ''
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取会话列表失败');
  }

  const result = await response.json();
  return result.data || [];
}

/**
 * 重命名会话
 * @param {string} conversationId - 会话 ID
 * @param {string} title - 新标题
 * @returns {Promise<Object>} 操作结果
 */
export async function renameConversation(conversationId, title) {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    },
    body: JSON.stringify({ title })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '重命名失败');
  }

  return await response.json();
}

/**
 * 删除会话
 * @param {string} conversationId - 会话 ID
 * @returns {Promise<Object>} 操作结果
 */
export async function deleteConversation(conversationId) {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': token ? `Bearer ${token}` : ''
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '删除失败');
  }

  return await response.json();
}

/**
 * 获取会话消息列表
 * @param {string} conversationId - 会话 ID
 * @returns {Promise<Array>} 消息列表
 */
export async function listMessages(conversationId) {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}/messages`, {
    method: 'GET',
    headers: {
      'Authorization': token ? `Bearer ${token}` : ''
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取消息列表失败');
  }

  const result = await response.json();
  return result.data || [];
}
