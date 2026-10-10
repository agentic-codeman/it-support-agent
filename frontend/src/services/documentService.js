import api from './api'

// 获取文档列表（分页）
export const getDocumentsPage = async (kbId, current = 1, size = 10, keyword, chunkStatus) => {
  const response = await api.get(`/knowledge-base/${kbId}/docs`, {
    params: { 
      current, 
      size, 
      keyword: keyword || undefined,
      chunk_status: chunkStatus || undefined
    }
  })
  return response.data
}

// 获取单个文档详情
export const getDocument = async (docId) => {
  const response = await api.get(`/knowledge-base/docs/${docId}`)
  return response.data
}

// 上传文档
export const uploadDocument = async (kbId, formData) => {
  console.log('uploadDocument 被调用')
  console.log('kbId:', kbId)
  console.log('formData entries:')
  for (let pair of formData.entries()) {
    console.log(pair[0] + ': ' + pair[1])
  }
  
  // 注意：不要手动设置 Content-Type，让浏览器自动设置 boundary
  const response = await api.post(`/knowledge-base/${kbId}/docs/upload`, formData)
  console.log('uploadDocument API 响应:', response)
  return response
}

// 开始分块处理
export const startChunkDocument = async (docId) => {
  console.log('startChunkDocument 被调用, docId:', docId)
  const response = await api.post(`/knowledge-base/docs/${docId}/chunk`)
  console.log('API 响应:', response)
  return response
}

// 删除文档
export const deleteDocument = async (docId) => {
  await api.delete(`/knowledge-base/docs/${docId}`)
}

// 更新文档
export const updateDocument = async (docId, data) => {
  await api.put(`/knowledge-base/docs/${docId}`, data)
}

// 启用/禁用文档
export const enableDocument = async (docId, enabled) => {
  await api.patch(`/knowledge-base/docs/${docId}/enable`, null, {
    params: { value: enabled }
  })
}

// 搜索文档
export const searchDocuments = async (keyword, limit = 8) => {
  const response = await api.get('/knowledge-base/docs/search', {
    params: { keyword: keyword || undefined, limit }
  })
  return response.data
}
