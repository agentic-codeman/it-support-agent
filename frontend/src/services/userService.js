/**
 * 用户管理 API 服务
 */
import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
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
 * 获取当前用户信息
 */
export function getCurrentUser() {
  return apiClient.get('/users/me')
}

/**
 * 分页查询用户列表
 * @param {Object} params - 查询参数
 * @param {number} params.page_num - 页码（默认1）
 * @param {number} params.page_size - 每页数量（默认10）
 * @param {string} params.keyword - 搜索关键词（可选）
 */
export function getUserList(params = {}) {
  const { page_num = 1, page_size = 10, keyword } = params
  
  return apiClient.get('/users', {
    params: {
      page_num,
      page_size,
      keyword,
    },
  })
}

/**
 * 创建用户
 * @param {Object} userData - 用户数据
 * @param {string} userData.username - 用户名
 * @param {string} userData.password - 密码
 * @param {string} userData.role - 角色（admin/user）
 * @param {string} [userData.avatar] - 头像URL（可选）
 */
export function createUser(userData) {
  return apiClient.post('/users', userData)
}

/**
 * 更新用户
 * @param {string} userId - 用户ID
 * @param {Object} userData - 用户数据
 * @param {string} [userData.username] - 用户名（可选）
 * @param {string} [userData.password] - 新密码（可选）
 * @param {string} [userData.role] - 角色（可选）
 * @param {string} [userData.avatar] - 头像URL（可选）
 */
export function updateUser(userId, userData) {
  return apiClient.put(`/users/${userId}`, userData)
}

/**
 * 删除用户
 * @param {string} userId - 用户ID
 */
export function deleteUser(userId) {
  return apiClient.delete(`/users/${userId}`)
}
