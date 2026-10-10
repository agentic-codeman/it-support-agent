import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, User as UserIcon, Database, MessageSquare } from 'lucide-react'
import { authAPI } from '../services/api'
import { useAuthStore } from '../store/authStore'

function Dashboard() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-primary-600">
                Wenda Agent
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-gray-700">
                <UserIcon className="h-5 w-5" />
                <span className="font-medium">{user?.username}</span>
                <span className="text-xs bg-primary-100 text-primary-600 px-2 py-1 rounded-full">
                  {user?.role}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 text-gray-600 hover:text-red-600 transition-colors px-4 py-2 rounded-lg hover:bg-red-50"
              >
                <LogOut className="h-5 w-5" />
                <span>退出登录</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* 主内容 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 欢迎卡片 */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            欢迎回来，{user?.username}！👋
          </h2>
          <p className="text-gray-600 text-lg">
            您已成功登录系统，现在可以开始使用智能问答功能了。
          </p>
        </div>

        {/* 快速访问 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div 
            onClick={() => navigate('/chat')}
            className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl shadow-lg p-6 text-white cursor-pointer hover:shadow-xl transition-shadow"
          >
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-white/20 rounded-xl">
                <MessageSquare className="h-8 w-8" />
              </div>
              <div>
                <h3 className="text-xl font-bold">智能客服</h3>
                <p className="text-blue-100 mt-1">基于知识库的智能对话</p>
              </div>
            </div>
          </div>

          <div 
            onClick={() => navigate('/admin/knowledge')}
            className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl shadow-lg p-6 text-white cursor-pointer hover:shadow-xl transition-shadow"
          >
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-white/20 rounded-xl">
                <Database className="h-8 w-8" />
              </div>
              <div>
                <h3 className="text-xl font-bold">知识库管理</h3>
                <p className="text-purple-100 mt-1">管理文档和向量存储</p>
              </div>
            </div>
          </div>
        </div>

        {/* 用户信息卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              用户信息
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-gray-600">用户名</span>
                <span className="font-medium text-gray-900">{user?.username}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-gray-600">角色</span>
                <span className="font-medium text-gray-900 capitalize">{user?.role}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-gray-600">创建时间</span>
                <span className="font-medium text-gray-900">{user?.create_time}</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              系统状态
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <span className="text-green-700 font-medium">认证状态</span>
                <span className="text-green-600 font-semibold">已登录</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <span className="text-blue-700 font-medium">Token类型</span>
                <span className="text-blue-600 font-semibold">JWT + OAuth2</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                <span className="text-purple-700 font-medium">API状态</span>
                <span className="text-purple-600 font-semibold">正常</span>
              </div>
            </div>
          </div>
        </div>

        {/* 功能卡片 */}
        <div className="mt-8 bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl shadow-lg p-8 text-white">
          <h3 className="text-2xl font-bold mb-4">
            开始使用智能问答
          </h3>
          <p className="text-primary-100 mb-6">
            系统已准备就绪，您可以开始提问了。我们使用先进的AI技术为您提供准确的回答。
          </p>
          <button 
            onClick={() => navigate('/chat')}
            className="bg-white text-primary-600 px-6 py-3 rounded-xl font-semibold hover:bg-primary-50 transition-colors flex items-center space-x-2"
          >
            <MessageSquare className="h-5 w-5" />
            <span>开始对话</span>
          </button>
        </div>

        {/* 知识库管理入口 */}
        <div className="mt-6 bg-white rounded-2xl shadow-lg p-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-primary-100 rounded-xl">
                <Database className="h-8 w-8 text-primary-600" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900">知识库管理</h3>
                <p className="text-gray-600 mt-1">管理所有知识库及其文档，支持向量存储和全文检索</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/admin/knowledge')}
              className="px-6 py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-colors flex items-center space-x-2"
            >
              <span>进入管理</span>
              <Database className="h-5 w-5" />
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Dashboard
