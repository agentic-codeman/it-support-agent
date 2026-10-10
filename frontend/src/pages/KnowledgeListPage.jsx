import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Database, FileBarChart, FolderOpen, Layers, Pencil, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { 
  getKnowledgeBasesPage, 
  deleteKnowledgeBase, 
  renameKnowledgeBase 
} from '../services/knowledgeService'
import CreateKnowledgeBaseDialog from '../components/CreateKnowledgeBaseDialog'

const PAGE_SIZE = 10
const STATS_PAGE_SIZE = 200

function KnowledgeListPage() {
  const navigate = useNavigate()
  const [pageData, setPageData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [searchName, setSearchName] = useState('')
  const [keyword, setKeyword] = useState('')
  const [pageNo, setPageNo] = useState(1)
  const [renameDialog, setRenameDialog] = useState({ open: false, kb: null })
  const [renameValue, setRenameValue] = useState('')
  const [stats, setStats] = useState({
    totalCount: 0,
    documentCount: 0,
    activeCount: 0,
    creatorCount: 0
  })
  const [statsLoading, setStatsLoading] = useState(true)
  const statsRequestId = useRef(0)

  const knowledgeBases = pageData?.records || []

  // 加载知识库列表
  const loadKnowledgeBases = async (current = pageNo, name = keyword) => {
    try {
      setLoading(true)
      const data = await getKnowledgeBasesPage(current, PAGE_SIZE, name || undefined)
      setPageData(data)
    } catch (error) {
      alert(error.response?.data?.message || '加载知识库列表失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  // 加载统计数据
  const loadStats = useCallback(async (name = keyword) => {
    const requestId = ++statsRequestId.current
    const normalized = name.trim()
    setStatsLoading(true)
    try {
      const firstPage = await getKnowledgeBasesPage(1, STATS_PAGE_SIZE, normalized || undefined)
      if (statsRequestId.current !== requestId) return

      let documentTotal = 0
      let activeTotal = 0
      const creatorNames = new Set()
      const addRecords = (records = []) => {
        records.forEach((kb) => {
          const docCount = kb.document_count ?? 0
          documentTotal += docCount
          if (docCount > 0) {
            activeTotal += 1
          }
          if (kb.created_by) {
            creatorNames.add(kb.created_by)
          }
        })
      }

      addRecords(firstPage.records || [])

      const totalCount = firstPage.total ?? (firstPage.records?.length || 0)
      const totalPages = firstPage.pages || Math.max(1, Math.ceil(totalCount / STATS_PAGE_SIZE))

      for (let page = 2; page <= totalPages; page += 1) {
        const nextPage = await getKnowledgeBasesPage(page, STATS_PAGE_SIZE, normalized || undefined)
        if (statsRequestId.current !== requestId) return
        addRecords(nextPage.records || [])
      }

      if (statsRequestId.current !== requestId) return
      setStats({
        totalCount,
        documentCount: documentTotal,
        activeCount: activeTotal,
        creatorCount: creatorNames.size
      })
    } catch (error) {
      if (statsRequestId.current !== requestId) return
      console.error(error)
      setStats({
        totalCount: 0,
        documentCount: 0,
        activeCount: 0,
        creatorCount: 0
      })
    } finally {
      if (statsRequestId.current === requestId) {
        setStatsLoading(false)
      }
    }
  }, [keyword])

  useEffect(() => {
    loadKnowledgeBases()
  }, [pageNo, keyword])

  useEffect(() => {
    loadStats(keyword)
  }, [keyword, loadStats])

  // 当重命名对话框打开时，设置初始值
  useEffect(() => {
    if (renameDialog.open) {
      setRenameValue(renameDialog.kb?.name || '')
    }
  }, [renameDialog])

  const handleSearch = () => {
    setPageNo(1)
    setKeyword(searchName.trim())
  }

  const handleRefresh = () => {
    setPageNo(1)
    loadKnowledgeBases(1, keyword)
    loadStats(keyword)
  }

  const handleDelete = async () => {
    if (!deleteTarget) return

    try {
      await deleteKnowledgeBase(deleteTarget.id)
      alert('删除成功')
      setDeleteTarget(null)
      setPageNo(1)
      await loadKnowledgeBases(1, keyword)
      await loadStats(keyword)
    } catch (error) {
      alert(error.response?.data?.message || '删除失败')
      console.error(error)
    } finally {
      setDeleteTarget(null)
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  const formatStatValue = (value) => {
    if (statsLoading) return '--'
    return value.toLocaleString('zh-CN')
  }

  const renderEmbeddingModel = (model) => {
    if (!model) return '-'
    const parts = model.split('-')
    if (parts.length < 2) {
      return <span className="text-sm text-slate-700">{model}</span>
    }
    const head = parts.slice(0, -1).join('-')
    const tail = parts[parts.length - 1]
    return (
      <div className="flex flex-col text-xs text-slate-500">
        <span className="font-medium text-slate-700">{head}</span>
        <span>{tail}</span>
      </div>
    )
  }

  const getCollectionBadgeClass = (name) => {
    const value = (name || '').toLowerCase()
    if (value.includes('biz')) {
      return 'border-blue-200 bg-blue-50 text-blue-700'
    }
    if (value.includes('group')) {
      return 'border-purple-200 bg-purple-50 text-purple-700'
    }
    return 'border-slate-200 bg-slate-100 text-slate-600'
  }

  const handleRename = async () => {
    if (!renameDialog.kb) return
    const nextName = renameValue.trim()
    if (!nextName) {
      alert('请输入知识库名称')
      return
    }
    if (nextName === renameDialog.kb.name) {
      setRenameDialog({ open: false, kb: null })
      return
    }
    try {
      await renameKnowledgeBase(renameDialog.kb.id, nextName)
      alert('重命名成功')
      setRenameDialog({ open: false, kb: null })
      await loadKnowledgeBases(pageNo, keyword)
    } catch (error) {
      alert(error.response?.data?.message || '重命名失败')
      console.error(error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">知识库管理</h1>
              <p className="text-gray-600 mt-1">管理所有知识库及其文档</p>
            </div>
            <div className="flex items-center space-x-3">
              <input
                type="text"
                value={searchName}
                onChange={(e) => setSearchName(e.target.value)}
                placeholder="搜索知识库名称"
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent w-[220px]"
              />
              <button
                onClick={handleSearch}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                搜索
              </button>
              <button
                onClick={handleRefresh}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                刷新
              </button>
              <button
                onClick={() => setCreateDialogOpen(true)}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center"
              >
                <Plus className="w-4 h-4 mr-2" />
                新建知识库
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[
            { label: '知识库', value: stats.totalCount, icon: Database, scope: '全部' },
            { label: '文档数', value: stats.documentCount, icon: FileBarChart, scope: '全部' },
            { label: '含文档知识库', value: stats.activeCount, icon: FolderOpen, scope: '全部' },
            { label: '创建用户数', value: stats.creatorCount, icon: Layers, scope: '全部' }
          ].map((item) => {
            const Icon = item.icon
            return (
              <div key={item.label} className="bg-white rounded-xl shadow-md p-6 relative overflow-hidden">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-primary-100 rounded-lg">
                    <Icon className="h-5 w-5 text-primary-600" />
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">{item.label}</div>
                    <div className="text-2xl font-bold text-gray-900">{formatStatValue(item.value)}</div>
                  </div>
                </div>
                <span className="absolute top-4 right-4 text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
                  {item.scope}
                </span>
              </div>
            )
          })}
        </div>

        {/* 表格卡片 */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="p-6">
            {loading ? (
              <div className="text-center py-8 text-gray-500">加载中...</div>
            ) : knowledgeBases.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                暂无知识库，点击上方按钮创建
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[200px]">名称</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[180px]">Embedding模型</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[220px]">Collection</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[90px]">文档数</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[120px]">负责人</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[160px]">创建时间</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[160px]">修改时间</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[150px]">操作</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {knowledgeBases.map((kb) => (
                      <tr key={kb.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            type="button"
                            className="text-primary-600 hover:text-primary-800 font-medium max-w-[200px] truncate block"
                            onClick={() => navigate(`/admin/knowledge/${kb.id}`)}
                          >
                            {kb.name}
                          </button>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {renderEmbeddingModel(kb.embedding_model)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {kb.collection_name ? (
                            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getCollectionBadgeClass(kb.collection_name)}`}>
                              {kb.collection_name}
                            </span>
                          ) : (
                            '-'
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">{kb.document_count ?? '-'}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{kb.created_by || '-'}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                          {formatDate(kb.create_time)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                          {formatDate(kb.update_time)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => setRenameDialog({ open: true, kb })}
                              className="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center text-sm"
                            >
                              <Pencil className="w-4 h-4 mr-1" />
                              编辑
                            </button>
                            <button
                              onClick={() => setDeleteTarget(kb)}
                              className="px-3 py-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors flex items-center text-sm"
                            >
                              <Trash2 className="w-4 h-4 mr-1" />
                              删除
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* 分页 */}
        {pageData && (
          <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
            <span>共 {pageData.total} 条</span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPageNo((prev) => Math.max(1, prev - 1))}
                disabled={pageData.current <= 1}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                上一页
              </button>
              <span>
                {pageData.current} / {pageData.pages}
              </span>
              <button
                onClick={() => setPageNo((prev) => Math.min(pageData.pages || 1, prev + 1))}
                disabled={pageData.current >= pageData.pages}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
              知识库删除后当前不提供恢复入口。确定要继续吗？
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
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

      {/* 重命名对话框 */}
      {renameDialog.open && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">重命名知识库</h3>
            <p className="text-gray-600 mb-4">修改知识库名称</p>
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">名称</label>
              <input
                type="text"
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setRenameDialog({ open: false, kb: null })}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleRename}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 创建知识库对话框 */}
      <CreateKnowledgeBaseDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSuccess={() => {
          setPageNo(1)
          loadKnowledgeBases(1, keyword)
          loadStats(keyword)
        }}
      />
    </div>
  )
}

export default KnowledgeListPage
