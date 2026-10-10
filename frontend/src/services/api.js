import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('=== API 请求拦截器 ===')
    console.log('URL:', config.url)
    console.log('Method:', config.method)
    
    // 如果是 FormData,删除 Content-Type header,让浏览器自动设置 multipart/form-data 和 boundary
    if (config.data instanceof FormData) {
      console.log('检测到 FormData,删除 Content-Type header')
      delete config.headers['Content-Type']
    }
    
    const { accessToken } = useAuthStore.getState()
    console.log('accessToken:', accessToken ? '存在' : '不存在')
    
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
      console.log('已添加 Authorization header')
    }
    
    console.log('请求配置:', config)
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('=== API 响应拦截器 (成功) ===')
    console.log('URL:', response.config.url)
    console.log('Status:', response.status)
    console.log('Response data:', response.data)
    return response.data
  },
  async (error) => {
    console.error('=== API 响应拦截器 (错误) ===')
    console.error('Error:', error)
    console.error('Error response:', error.response)
    console.error('Error message:', error.message)
    
    const originalRequest = error.config

    // 如果响应是401
    if (error.response?.status === 401) {
      console.log('检测到 401 错误')
      
      // 如果是刷新token的请求本身失败，直接登出
      if (originalRequest.url.includes('/auth/refresh')) {
        console.log('刷新token请求失败，清除认证信息')
        useAuthStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(error)
      }
      
      // 如果已经重试过，直接登出
      if (originalRequest._retry) {
        console.log('请求已重试过，清除认证信息')
        useAuthStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(error)
      }
      
      originalRequest._retry = true

      try {
        const { refreshToken } = useAuthStore.getState()
        if (refreshToken) {
          console.log('尝试使用 refresh token 刷新...')
          // 尝试刷新token（使用 api 实例以应用拦截器）
          const refreshResponse = await api.post('/auth/refresh', {
            refresh_token: refreshToken
          })

          if (refreshResponse.data.code === '00000') {
            const { access_token } = refreshResponse.data.data
            useAuthStore.getState().setAuth(
              useAuthStore.getState().user,
              access_token,
              refreshToken
            )

            // 重试原始请求
            originalRequest.headers.Authorization = `Bearer ${access_token}`
            return api(originalRequest)
          }
        }
        
        // 如果没有refreshToken或刷新失败，清除认证信息并跳转
        console.log('没有refreshToken或刷新失败，清除认证信息')
        useAuthStore.getState().logout()
        window.location.href = '/login'
      } catch (refreshError) {
        console.error('Token 刷新失败:', refreshError)
        // 刷新失败，清除认证信息
        useAuthStore.getState().logout()
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

// 认证 API
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  refreshToken: (data) => api.post('/auth/refresh', data),
  getCurrentUser: () => api.get('/auth/me'),
}

export default api
