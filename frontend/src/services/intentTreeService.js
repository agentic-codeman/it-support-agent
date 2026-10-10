/**
 * 意图树服务层
 */
import api from './api';

/**
 * 获取意图树结构
 * @returns {Promise<Array>} 意图树节点数组
 */
export async function getIntentTree() {
  const response = await api.get('/intent-tree/trees');
  return response.data || [];
}

/**
 * 创建意图节点
 * @param {Object} payload 节点数据
 * @returns {Promise<string>} 新创建的节点ID
 */
export async function createIntentNode(payload) {
  const response = await api.post('/intent-tree', payload);
  return response.data;
}

/**
 * 更新意图节点
 * @param {string} nodeId 节点ID
 * @param {Object} payload 更新数据
 * @returns {Promise<void>}
 */
export async function updateIntentNode(nodeId, payload) {
  await api.put(`/intent-tree/${nodeId}`, payload);
}

/**
 * 删除意图节点
 * @param {string} nodeId 节点ID
 * @returns {Promise<void>}
 */
export async function deleteIntentNode(nodeId) {
  await api.delete(`/intent-tree/${nodeId}`);
}

/**
 * 批量删除节点
 * @param {Array<string>} ids 节点ID列表
 * @returns {Promise<void>}
 */
export async function batchDeleteNodes(ids) {
  await api.post('/intent-tree/batch/delete', { ids });
}

// 导出服务对象
export const intentTreeService = {
  getIntentTree,
  createIntentNode,
  updateIntentNode,
  deleteIntentNode,
  batchDeleteNodes
};
