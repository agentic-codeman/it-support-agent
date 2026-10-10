import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, FolderOpen, PlayCircle, Pencil, Trash2, RefreshCw, Upload, CheckCircle, XCircle, AlertCircle, FileBarChart, FileUp } from 'lucide-react'
import { getDocumentsPage, deleteDocument, startChunkDocument, enableDocument, updateDocument, getDocument, uploadDocument } from '../services/documentService'
import { getKnowledgeBase } from '../services/knowledgeService'
import UploadDocumentDialog from '../components/UploadDocumentDialog'

const PAGE_SIZE = 10

function KnowledgeDocumentsPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  
  const [pageData, setPageData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [kbInfo, setKbInfo] = useState(null)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [keyword, setKeyword] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [pageNo, setPageNo] = useState(1)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [chunkTarget, setChunkTarget] = useState(null)
  const [detailTarget, setDetailTarget] = useState(null)
  const [detailName, setDetailName] = useState('')
  const [detailSaving, setDetailSaving] = useState(false)
  const [logTarget, setLogTarget] = useState(null)
  const [logData, setLogData] = useState(null)
  const [logLoading, setLogLoading] = useState(false)

  const documents = pageData?.records || []

  // 加载知识库信息
  useEffect(() => {
    const loadKbInfo = async () => {
      try {
        const data = await getKnowledgeBase(id)
        setKbInfo(data)
      } catch (error) {
        console.error('加载知识库信息失败', error)
      }
    }
    loadKbInfo()
  }, [id])

  // 加载文档列表
  const loadDocuments = async (current = pageNo, kw = keyword, status = statusFilter) => {
    try {
      setLoading(true)
      const data = await getDocumentsPage(id, current, PAGE_SIZE, kw || undefined, status || undefined)
      setPageData(data)
    } catch (error) {
      alert(error.response?.data?.message || '加载文档列表失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [pageNo, keyword, statusFilter])

  const handleSearch = () => {
    setPageNo(1)
    setKeyword(searchKeyword.trim())
  }

  const handleRefresh = () => {
    setPageNo(1)
    loadDocuments(1, keyword, statusFilter)
  }

  const handleDelete = async () => {
    if (!deleteTarget) return

    try {
      await deleteDocument(deleteTarget.id)
      alert('删除成功')
      setDeleteTarget(null)
      setPageNo(1)
      await loadDocuments(1, keyword, statusFilter)
    } catch (error) {
      alert(error.response?.data?.message || '删除失败')
      console.error(error)
    } finally {
      setDeleteTarget(null)
    }
  }

  const handleChunk = async (docId) => {
    console.log('=== 点击分块处理 ===')
    console.log('docId:', docId)
    alert(`准备调用分块接口, docId: ${docId}`)
    
    try {
      console.log('开始调用 startChunkDocument...')
      const result = await startChunkDocument(docId)
      console.log('startChunkDocument 返回结果:', result)
      
      alert('分块处理已启动')
      loadDocuments(pageNo, keyword, statusFilter)
    } catch (error) {
      console.error('分块处理失败:', error)
      console.error('错误详情:', error.response?.data)
      alert(error.response?.data?.message || '分块处理失败')
    }
  }

  const handleEnable = async (docId, enabled) => {
    try {
      await enableDocument(docId, enabled)
      loadDocuments(pageNo, keyword, statusFilter)
    } catch (error) {
      alert(error.response?.data?.message || '操作失败')
      console.error(error)
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return '-'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getStatusBadge = (status) => {
    const statusDotClass = (status) => {
      if (!status) return 'bg-gray-400'
      const normalized = status.toLowerCase()
      if (normalized === 'success') return 'bg-green-500'
      if (normalized === 'failed') return 'bg-red-500'
      if (normalized === 'running') return 'bg-amber-500'
      if (normalized === 'pending') return 'bg-slate-400'
      return 'bg-gray-400'
    }
    return (
      <div className="inline-flex items-center gap-2 text-xs text-gray-500">
        <span className={`h-2 w-2 rounded-full ${statusDotClass(status)}`} />
        <span>{status || '-'}</span>
      </div>
    )
  }

  return (
    <div className="admin-page">
      {/* 页面头部 */}
      <div className="admin-page-header flex flex-row items-center justify-between">
        <div>
          <h1 className="admin-page-title">文档管理</h1>
          <p className="admin-page-subtitle">{kbInfo?.name} {kbInfo?.collection_name ? `（${kbInfo?.collection_name}）` : ''}</p>
        </div>
        <div className="admin-page-actions flex items-center gap-3">
          <button
            onClick={() => navigate('/admin/knowledge')}
            className="admin-btn-secondary"
          >
            返回知识库
          </button>
          <button
            onClick={() => setUploadDialogOpen(true)}
            className="admin-btn-primary flex items-center"
          >
            <Upload className="w-4 h-4 mr-2" />
            上传文档
          </button>
        </div>
      </div>

      {/* 文档列表卡片 */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        {/* 搜索栏 */}
        <div className="px-6 py-5 border-b border-gray-200">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h3 className="text-base font-semibold text-gray-900">文档列表</h3>
                <p className="text-sm text-gray-500 mt-0.5">支持筛选与分块管理</p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  placeholder="搜索文档名称"
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent w-[200px]"
                />
                <button
                  onClick={handleSearch}
                  className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  搜索
                </button>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="h-10 px-3 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white pr-8 w-[160px]"
                  style={{
                    backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                    backgroundPosition: 'right 0.5rem center',
                    backgroundRepeat: 'no-repeat',
                    backgroundSize: '1.5em 1.5em'
                  }}
                >
                  <option value="">全部状态</option>
                  <option value="pending">待处理</option>
                  <option value="running">处理中</option>
                  <option value="success">成功</option>
                  <option value="failed">失败</option>
                </select>
                <button
                  onClick={handleRefresh}
                  className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  刷新
                </button>
              </div>
          </div>
        </div>

        {/* 表格内容 */}
        <div className="overflow-x-auto">
            {loading ? (
              <div className="text-center py-8 text-gray-500">加载中...</div>
            ) : documents.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                暂无文档，点击上方按钮上传
              </div>
            ) : (
              <table className="w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 tracking-wider w-[240px]">文档</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 tracking-wider w-[100px]">状态</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 tracking-wider w-[60px]">启用</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 tracking-wider w-[70px]">分块数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 tracking-wider w-[80px]">类型</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 tracking-wider w-[80px]">大小</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 tracking-wider w-[150px]">更新时间</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 tracking-wider text-left w-[140px]">操作</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {documents.map((doc) => (
                      <tr key={doc.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex min-w-0 max-w-[280px] items-center gap-2">
                            <FolderOpen className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <button
                              type="button"
                              onClick={() => navigate(`/admin/knowledge/${id}/doc/${doc.id}/chunks`)}
                              className="text-blue-600 hover:text-blue-800 font-medium cursor-pointer truncate text-left"
                              title={doc.file_name || ""}
                            >
                              {doc.file_name}
                            </button>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="inline-flex items-center gap-2 text-xs text-gray-500">
                            <span className={`h-2 w-2 rounded-full ${(() => {
                              if (!doc.chunk_status) return 'bg-gray-400'
                              const normalized = doc.chunk_status.toLowerCase()
                              if (normalized === 'success') return 'bg-green-500'
                              if (normalized === 'failed') return 'bg-red-500'
                              if (normalized === 'running') return 'bg-amber-500'
                              if (normalized === 'pending') return 'bg-slate-400'
                              return 'bg-gray-400'
                            })()}`} />
                            <span>{doc.chunk_status || '-'}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={doc.enabled === 1}
                              onChange={(e) => handleEnable(doc.id, e.target.checked ? 1 : 0)}
                              className="sr-only peer"
                            />
                            <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                          </label>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-xs text-gray-500">{doc.chunk_count || '-'}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-xs text-gray-500">{doc.file_type}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatFileSize(doc.file_size)}</td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-500">
                            <div>{formatDate(doc.update_time)?.split(' ')[0] || '-'}</div>
                            <div className="text-xs text-gray-400">{formatDate(doc.update_time)?.split(' ')[1] || ''}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-1">
                            <button
                              onClick={async () => {
                                try {
                                  const detail = await getDocument(doc.id)
                                  setDetailTarget(detail)
                                  setDetailName(detail.file_name || '')
                                } catch (error) {
                                  console.error('加载文档详情失败', error)
                                  alert('加载文档详情失败')
                                }
                              }}
                              className="p-2 text-gray-400 hover:text-blue-500 rounded transition-colors"
                              title="编辑"
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleChunk(doc.id)}
                              className="p-2 text-gray-400 hover:text-blue-500 rounded transition-colors"
                              title="分块"
                            >
                              <PlayCircle className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => navigate(`/admin/knowledge/${id}/doc/${doc.id}/chunks`)}
                              className="p-2 text-gray-400 hover:text-blue-500 rounded transition-colors"
                              title="分块详情"
                            >
                              <FileBarChart className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setDeleteTarget(doc)}
                              className="p-2 text-gray-400 hover:text-red-500 rounded transition-colors"
                              title="删除"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
            )}
          </div>

        {/* 分页 */}
        {pageData && (
          <div className="px-6 py-4 flex flex-wrap items-center justify-between gap-2 text-sm text-gray-500">
            <span>共 {pageData.total} 条</span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPageNo((prev) => Math.max(1, prev - 1))}
                disabled={pageData.current <= 1}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                上一页
              </button>
              <span className="text-sm text-gray-600">
                {pageData.current} / {pageData.pages}
              </span>
              <button
                onClick={() => setPageNo((prev) => Math.min(pageData.pages || 1, prev + 1))}
                disabled={pageData.current >= pageData.pages}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                下一页
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 删除确认对话框 */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">确认删除</h3>
            <p className="text-gray-600 mb-6">
              确定要删除文档 "{deleteTarget.file_name}" 吗？此操作不可恢复。
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 上传文档对话框 */}
      <UploadDocumentDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        kbId={id}
        onSuccess={() => {
          setPageNo(1)
          loadDocuments(1, keyword, statusFilter)
        }}
      />

      {/* 编辑文档对话框 */}
      {detailTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">编辑文档</h3>
            <p className="text-sm text-gray-500 mb-6">修改文档配置，保存后需重新分块才会生效</p>
            
            <div className="space-y-4">
              {/* 文档名称 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">文档名称</label>
                <input
                  type="text"
                  value={detailName}
                  onChange={(e) => setDetailName(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setDetailTarget(null)}
                className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                关闭
              </button>
              <button
                onClick={async () => {
                  if (!detailName.trim()) {
                    alert('文档名称不能为空')
                    return
                  }
                  
                  console.log('=== 开始保存文档 ===')
                  console.log('文档 ID:', detailTarget.id)
                  console.log('新文档名:', detailName.trim())
                  
                  setDetailSaving(true)
                  try {
                    const requestData = {
                      doc_name: detailName.trim()
                    }
                    console.log('请求数据:', JSON.stringify(requestData))
                    console.log('请求 URL:', `/knowledge-base/docs/${detailTarget.id}`)
                    console.log('请求方法: PUT')
                    
                    const response = await updateDocument(detailTarget.id, requestData)
                    console.log('保存成功，响应:', response)
                    
                    alert('保存成功')
                    setDetailTarget(null)
                    
                    // 重新加载文档列表
                    console.log('重新加载文档列表...')
                    await loadDocuments(pageNo, keyword, statusFilter)
                  } catch (error) {
                    console.error('保存失败', error)
                    console.error('错误详情:', error.response?.data)
                    console.error('错误状态:', error.response?.status)
                    alert(error.response?.data?.message || '保存失败')
                  } finally {
                    setDetailSaving(false)
                  }
                }}
                disabled={detailSaving}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {detailSaving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default KnowledgeDocumentsPage
