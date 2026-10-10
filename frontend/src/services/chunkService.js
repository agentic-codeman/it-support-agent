import api from './api'

// 分页查询分块列表
export const getChunksPage = async (docId, current = 1, size = 10, enabled) => {
  const response = await api.get(`/knowledge-base/docs/${docId}/chunks`, {
    params: { 
      current, 
      size,
      enabled: enabled !== undefined ? enabled : undefined
    }
  })
  return response.data
}

// 删除分块
export const deleteChunk = async (docId, chunkId) => {
  await api.delete(`/knowledge-base/docs/${docId}/chunks/${chunkId}`)
}

// 启用/禁用单个分块
export const toggleChunk = async (docId, chunkId, enabled) => {
  await api.patch(`/knowledge-base/docs/${docId}/chunks/${chunkId}/enable`, null, {
    params: { value: enabled }
  })
}

// 批量启用/禁用分块
export const batchToggleChunks = async (docId, enabled, chunkIds = null) => {
  const data = chunkIds ? { chunk_ids: chunkIds } : null
  await api.patch(`/knowledge-base/docs/${docId}/chunks/batch-enable`, data, {
    params: { value: enabled }
  })
}

// 全量启用/禁用分块
export const toggleAllChunks = async (docId, enabled) => {
  await api.patch(`/knowledge-base/docs/${docId}/chunks/toggle-all`, null, {
    params: { value: enabled }
  })
}
