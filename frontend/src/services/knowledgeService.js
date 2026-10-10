import api from './api'

// 获取知识库列表（分页）
export const getKnowledgeBasesPage = async (current = 1, size = 10, name) => {
  const response = await api.get('/knowledge-base', {
    params: {
      current,
      size,
      name: name || undefined,
      _t: Date.now() // 添加时间戳避免缓存
    }
  })
  return response.data
}

// 获取知识库列表（用于下拉选择，返回 records 数组）
export const getKnowledgeBases = async (current = 1, size = 200, name) => {
  const page = await getKnowledgeBasesPage(current, size, name)
  return page?.records || []
}

// 获取单个知识库详情
export const getKnowledgeBase = async (id) => {
  const response = await api.get(`/knowledge-base/${id}`)
  return response.data
}

// 创建知识库
export const createKnowledgeBase = async (data) => {
  const response = await api.post('/knowledge-base', data)
  
  // 检查业务状态码
  if (response.code !== '00000') {
    const error = new Error(response.message || '创建失败')
    error.response = { data: response }
    throw error
  }
  
  return response
}

// 更新知识库（重命名）
export const renameKnowledgeBase = async (id, name) => {
  const response = await api.put(`/knowledge-base/${id}`, { name })
  
  // 检查业务状态码
  if (response.code !== '00000') {
    const error = new Error(response.message || '重命名失败')
    error.response = { data: response }
    throw error
  }
  
  return response
}

// 删除知识库
export const deleteKnowledgeBase = async (id) => {
  const response = await api.delete(`/knowledge-base/${id}`)
  
  // 检查业务状态码
  if (response.code !== '00000') {
    // 创建错误对象并抛出
    const error = new Error(response.message || '删除失败')
    error.response = { data: response }
    throw error
  }
  
  return response
}
