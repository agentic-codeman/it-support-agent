import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { createKnowledgeBase } from '../services/knowledgeService'

function CreateKnowledgeBaseDialog({ open, onOpenChange, onSuccess }) {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    embedding_model: '',
    collection_name: ''
  })

  // 重置表单
  useEffect(() => {
    if (!open) {
      setFormData({
        name: '',
        embedding_model: '',
        collection_name: ''
      })
    }
  }, [open])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // 验证
    if (!formData.name.trim()) {
      toast.error('请输入知识库名称')
      return
    }
    if (!formData.embedding_model.trim()) {
      toast.error('请输入Embedding模型')
      return
    }
    if (!formData.collection_name.trim()) {
      toast.error('请输入Collection名称')
      return
    }
    if (!/^[a-z0-9]+$/.test(formData.collection_name)) {
      toast.error('Collection名称只能包含小写英文字母和数字')
      return
    }

    try {
      setLoading(true)
      await createKnowledgeBase(formData)
      toast.success('创建成功')
      setFormData({
        name: '',
        embedding_model: '',
        collection_name: ''
      })
      onOpenChange(false)
      onSuccess()
    } catch (error) {
      toast.error(error.response?.data?.message || '创建失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleDialogOpenChange = (nextOpen) => {
    if (!nextOpen) {
      setFormData({
        name: '',
        embedding_model: '',
        collection_name: ''
      })
    }
    onOpenChange(nextOpen)
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* 对话框头部 */}
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">创建知识库</h3>
          <p className="text-sm text-gray-600 mt-1">
            创建一个新的知识库，用于存储和检索文档
          </p>
        </div>

        {/* 表单内容 */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              知识库名称
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="例如：产品文档库"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              为知识库起一个易于识别的名称
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Embedding模型
            </label>
            <select
              value={formData.embedding_model}
              onChange={(e) => setFormData({ ...formData, embedding_model: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">选择Embedding模型</option>
              <option value="bge-m3:latest">bge-m3:latest</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              选择用于向量化文档的模型
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Collection名称
            </label>
            <input
              type="text"
              value={formData.collection_name}
              onChange={(e) => setFormData({ ...formData, collection_name: e.target.value.toLowerCase() })}
              placeholder="例如：productdocs"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              只能包含小写英文字母和数字
            </p>
          </div>

          {/* 按钮区域 */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={() => handleDialogOpenChange(false)}
              disabled={loading}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '创建中...' : '创建'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateKnowledgeBaseDialog
