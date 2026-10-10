import { useState, useRef } from 'react'
import { X, Upload, FileText } from 'lucide-react'
import { uploadDocument } from '../services/documentService'

function UploadDocumentDialog({ open, onClose, kbId, onSuccess }) {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)

  if (!open) return null

  const isSupportedFile = (selectedFile) => {
    if (!selectedFile?.name) return false
    const ext = selectedFile.name.split('.').pop()?.toLowerCase() || ''
    return ['pdf', 'md', 'markdown'].includes(ext)
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      if (!isSupportedFile(selectedFile)) {
        alert('仅支持 PDF、Markdown 格式')
        e.target.value = ''
        return
      }
      setFile(selectedFile)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      if (!isSupportedFile(droppedFile)) {
        alert('仅支持 PDF、Markdown 格式')
        return
      }
      setFile(droppedFile)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setDragging(false)
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return '-'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!file) {
      alert('请选择文件')
      return
    }

    if (!kbId) {
      alert('知识库ID不能为空')
      return
    }

    try {
      setUploading(true)

      const formData = new FormData()
      formData.append('file', file)

      await uploadDocument(kbId, formData)

      alert('上传成功')
      handleClose()
      if (onSuccess) {
        onSuccess()
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message || '上传失败'
      alert(errorMsg)
    } finally {
      setUploading(false)
    }
  }

  const handleClose = () => {
    setFile(null)
    setDragging(false)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* 头部 */}
        <div className="flex items-center justify-between px-8 pt-7 pb-5 border-b border-gray-100">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">上传文档</h3>
            <p className="text-sm text-gray-500 mt-1">选择本地文件上传到知识库</p>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="px-8 py-6">
          {/* 拖拽上传区域 / 已选文件卡片 */}
          {!file ? (
            <div
              onClick={() => inputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-14 cursor-pointer transition-colors ${
                dragging
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-300 bg-gray-50 hover:border-indigo-400 hover:bg-indigo-50/50'
              }`}
            >
              <div className="w-14 h-14 rounded-full bg-white border border-gray-200 flex items-center justify-center mb-4">
                <Upload className="w-7 h-7 text-indigo-500" />
              </div>
              <p className="text-base font-medium text-gray-700">
                拖拽文件到此处，或 <span className="text-indigo-600">点击上传</span>
              </p>
              <p className="text-sm text-gray-400 mt-2">
                支持 PDF、Markdown 格式
              </p>
              <input
                ref={inputRef}
                type="file"
                onChange={handleFileChange}
                className="hidden"
                accept=".pdf,.md,.markdown"
              />
            </div>
          ) : (
            <div className="rounded-2xl border border-gray-200 p-5">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center flex-shrink-0">
                  <FileText className="w-6 h-6 text-indigo-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                  <p className="text-xs text-gray-400 mt-1">{formatFileSize(file.size)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setFile(null)}
                  className="text-gray-400 hover:text-red-500 transition-colors p-1"
                  disabled={uploading}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="mt-4 text-right">
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
                  disabled={uploading}
                >
                  重新选择
                </button>
                <input
                  ref={inputRef}
                  type="file"
                  onChange={handleFileChange}
                  className="hidden"
                  accept=".pdf,.md,.markdown"
                />
              </div>
            </div>
          )}

          {/* 按钮 */}
          <div className="flex items-center justify-end space-x-3 mt-8">
            <button
              type="button"
              onClick={handleClose}
              className="px-6 py-2.5 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50 transition-colors font-medium"
              disabled={uploading}
            >
              取消
            </button>
            <button
              type="submit"
              disabled={!file || uploading}
              className="px-6 py-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? '上传中...' : '上传'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default UploadDocumentDialog
