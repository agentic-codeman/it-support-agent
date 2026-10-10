import axios from 'axios'
import { useAuthStore } from '../store/authStore'

// API 基础配置
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器 - 自动添加 token
apiClient.interceptors.request.use(
  (config) => {
    // 从 Zustand store 获取 token
    const state = useAuthStore.getState()
    const token = state.accessToken
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => {
    // 后端返回格式: { code, message, data }
    const { code, message, data } = response.data
    
    // 成功码为 '00000'
    if (code === '00000') {
      return data
    } else {
      // 业务错误
      const error = new Error(message || '请求失败')
      error.code = code
      error.message = message
      return Promise.reject(error)
    }
  },
  (error) => {
    if (error.response) {
      // HTTP 错误
      const { status, data } = error.response
      
      if (status === 401) {
        // Token 过期，清除认证信息并跳转登录
        useAuthStore.getState().logout()
        window.location.href = '/login'
      }
      
      const errorMsg = data?.message || error.message || '请求失败'
      const err = new Error(errorMsg)
      err.code = data?.code || status
      return Promise.reject(err)
    }
    
    return Promise.reject(error)
  }
)

/**
 * 分页查询示例问题列表
 * @param {Object} params - 查询参数
 * @param {number} params.page_num - 页码（默认1）
 * @param {number} params.page_size - 每页数量（默认10）
 * @param {string} params.keyword - 搜索关键词（可选）
 */
export function getSampleQuestionList(params = {}) {
  const { page_num = 1, page_size = 10, keyword } = params
  
  return apiClient.get('/sample-questions', {
    params: {
      page_num,
      page_size,
      keyword,
    },
  })
}

/**
 * 创建示例问题
 * @param {Object} questionData - 示例问题数据
 * @param {string} [questionData.title] - 标题（可选）
 * @param {string} [questionData.description] - 描述（可选）
 * @param {string} questionData.question - 示例问题内容（必填）
 */
export function createSampleQuestion(questionData) {
  return apiClient.post('/sample-questions', questionData)
}

/**
 * 更新示例问题
 * @param {string} questionId - 示例问题ID
 * @param {Object} questionData - 示例问题数据
 * @param {string} [questionData.title] - 标题（可选）
 * @param {string} [questionData.description] - 描述（可选）
 * @param {string} [questionData.question] - 示例问题内容（可选）
 */
export function updateSampleQuestion(questionId, questionData) {
  return apiClient.put(`/sample-questions/${questionId}`, questionData)
}

/**
 * 删除示例问题
 * @param {string} questionId - 示例问题ID
 */
export function deleteSampleQuestion(questionId) {
  return apiClient.delete(`/sample-questions/${questionId}`)
}

/**
 * 随机获取示例问题列表（用于欢迎页展示）
 * @param {number} limit - 返回数量限制，默认3条
 */
export function getRandomSampleQuestions(limit = 3) {
  return apiClient.get('/sample-questions/random', {
    params: { limit },
  }).catch(error => {
    console.error('获取随机示例问题失败:', error)
    return [] // 失败时返回空数组，不影响页面展示
  })
}
