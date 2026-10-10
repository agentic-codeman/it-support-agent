import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ChevronDown, Eye, HelpCircle, RefreshCw, ShieldCheck, ShieldX, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { getChunksPage, deleteChunk, toggleChunk, batchToggleChunks, toggleAllChunks } from '../services/chunkService'
import { getDocument } from '../services/documentService'

const PAGE_SIZE = 10

const truncateText = (value, max = 120) => {
  if (!value) return '-'
  if (value.length <= max) return value
  return `${value.slice(0, max)}...`
}

const formatDate = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN')
}

const enabledLabel = (enabled) => (enabled === 1 ? '启用' : '禁用')

function KnowledgeChunksPage() {
  const { kbId, docId } = useParams()
  const navigate = useNavigate()
  const [doc, setDoc] = useState(null)
  const [pageData, setPageData] = useState(null)
  const [pageNo, setPageNo] = useState(1)
  const [loading, setLoading] = useState(false)
  const [enabledFilter, setEnabledFilter] = useState(undefined)
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [editDialog, setEditDialog] = useState({ open: false, chunk: null })
  const [deleteTarget, setDeleteTarget] = useState(null)
  const chunks = pageData?.records || []

  const selectedList = useMemo(() => Array.from(selectedIds), [selectedIds])

  const loadDocument = async () => {
    if (!docId) return
    try {
      const data = await getDocument(docId)
      setDoc(data)
    } catch (error) {
      toast.error(error.response?.data?.message || '加载文档失败')
      console.error(error)
    }
  }

  const loadChunks = async (current = pageNo, enabled = enabledFilter) => {
    if (!docId) return
    setLoading(true)
    try {
      const data = await getChunksPage(docId, current, PAGE_SIZE, enabled)
      setPageData(data)
    } catch (error) {
      toast.error(error.response?.data?.message || '加载分块失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDocument()
  }, [docId])

  useEffect(() => {
    loadChunks()
  }, [docId, pageNo, enabledFilter])

  useEffect(() => {
    setSelectedIds(new Set())
  }, [docId, enabledFilter])

  const allSelected = chunks.length > 0 && chunks.every((chunk) => selectedIds.has(String(chunk.id)))

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedIds(new Set())
      return
    }
    const next = new Set(selectedIds)
    chunks.forEach((chunk) => next.add(String(chunk.id)))
    setSelectedIds(next)
  }

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const handleBatchToggle = async (enabled) => {
    if (!docId) return
    if (selectedList.length === 0) {
      toast.error('请选择需要操作的分块')
      return
    }
    const targetValue = enabled ? 1 : 0
    const selectedChunks = chunks.filter((c) => selectedList.includes(String(c.id)))
    const needChange = selectedChunks.some((c) => c.enabled !== targetValue)
    if (!needChange) {
      toast.info(enabled ? '所选分块已全部启用' : '所选分块已全部禁用')
      return
    }
    try {
      await batchToggleChunks(docId, enabled, selectedList)
      toast.success(enabled ? '批量启用成功' : '批量禁用成功')
      setSelectedIds(new Set())
      await loadChunks(pageNo, enabledFilter)
    } catch (error) {
      toast.error(error.response?.data?.message || (enabled ? '批量启用失败' : '批量禁用失败'))
      console.error(error)
    }
  }

  const handleDelete = async () => {
    if (!docId || !deleteTarget) return
    try {
      await deleteChunk(docId, String(deleteTarget.id))
      toast.success('删除成功')
      setDeleteTarget(null)
      await loadChunks(pageNo, enabledFilter)
    } catch (error) {
      toast.error(error.response?.data?.message || '删除失败')
      console.error(error)
    }
  }

  const handleToggleEnabled = async (chunk) => {
    if (!docId) return
    try {
      const enable = chunk.enabled !== 1
      await toggleChunk(docId, String(chunk.id), enable)
      toast.success(enable ? '已启用' : '已禁用')
      await loadChunks(pageNo, enabledFilter)
    } catch (error) {
      toast.error(error.response?.data?.message || '操作失败')
      console.error(error)
    }
  }

  const handleToggleAll = async (enabled) => {
    if (!docId) return
    const targetValue = enabled ? 1 : 0
    const allEnabled = chunks.every((c) => c.enabled === targetValue)
    if (allEnabled) {
      toast.info(enabled ? '所有分块已全部启用' : '所有分块已全部禁用')
      return
    }
    try {
      await toggleAllChunks(docId, enabled)
      toast.success(enabled ? '全量启用成功' : '全量禁用成功')
      await loadChunks(pageNo, enabledFilter)
    } catch (error) {
      toast.error(error.response?.data?.message || (enabled ? '全量启用失败' : '全量禁用失败'))
      console.error(error)
    }
  }

  return (
    <div className="admin-page">
      {/* 页面头部 */}
      <div className="admin-page-header flex flex-row items-center justify-between">
        <div>
          <h1 className="admin-page-title">分块管理</h1>
          <p className="admin-page-subtitle">
            {doc?.file_name || docId} {kbId ? `（知识库: ${kbId}）` : ''}
          </p>
        </div>
        <div className="admin-page-actions flex items-center gap-3">
          <button
            onClick={() => navigate(`/admin/knowledge/${kbId}`)}
            className="admin-btn-secondary"
          >
            返回文档
          </button>
        </div>
      </div>

      {/* 卡片容器 */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
        {/* 卡片头部 */}
        <div className="px-6 py-5 border-b border-gray-200">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Chunk 列表</h3>
              <p className="text-sm text-gray-500 mt-0.5">支持查看、启停、批量操作</p>
            </div>
            <div className="flex flex-1 flex-wrap items-center justify-end gap-2">
              <div className="relative w-[160px]">
                <select
                  value={enabledFilter === undefined ? 'all' : String(enabledFilter)}
                  onChange={(e) => {
                    setPageNo(1)
                    setEnabledFilter(e.target.value === 'all' ? undefined : Number(e.target.value))
                  }}
                  className="h-8 w-full appearance-none px-3 pr-8 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-xs text-slate-700 bg-white cursor-pointer"
                >
                  <option value="all">全部状态</option>
                  <option value="1">启用</option>
                  <option value="0">禁用</option>
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
              </div>
              <button
                onClick={() => {
                  setPageNo(1)
                  loadChunks(1, enabledFilter)
                }}
                className="admin-btn-secondary"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                刷新
              </button>
              <button
                onClick={() => handleBatchToggle(true)}
                disabled={selectedList.length === 0}
                className="admin-btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ShieldCheck className="w-4 h-4 mr-2" />
                批量启用
              </button>
              <button
                onClick={() => handleBatchToggle(false)}
                disabled={selectedList.length === 0}
                className="admin-btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ShieldX className="w-4 h-4 mr-2" />
                批量禁用
              </button>
              <button
                onClick={() => handleToggleAll(true)}
                className="admin-btn-secondary"
              >
                全量启用
              </button>
              <button
                onClick={() => handleToggleAll(false)}
                className="admin-btn-secondary"
              >
                全量禁用
              </button>
            </div>
          </div>
        </div>

        {/* 卡片内容 */}
        <div className="pt-0 pb-6">
          {/* 表格内容 */}
          <div className="overflow-x-auto">
            {loading ? (
              <div className="py-8 text-center text-gray-500">加载中...</div>
            ) : chunks.length === 0 ? (
              <div className="py-8 text-center text-gray-500">暂无分块</div>
            ) : (
              <table className="w-full caption-bottom text-sm">
                <thead className="[&_tr]:border-b bg-gray-50">
                  <tr>
                    <th className="h-14 px-4 text-left align-middle font-semibold text-slate-500 w-[48px]">
                      <input type="checkbox" checked={allSelected} onChange={toggleSelectAll} />
                    </th>
                    <th className="h-14 px-4 text-left align-middle font-semibold text-slate-500 w-[70px]">序号</th>
                    <th className="h-14 px-4 text-left align-middle font-semibold text-slate-500">内容</th>
                    <th className="h-14 px-4 text-left align-middle font-semibold text-slate-500 w-[90px]">状态</th>
                    <th className="h-14 px-4 text-left align-middle font-semibold text-slate-500 w-[90px]">字符数</th>
                    <th className="h-14 px-4 text-left align-middle font-semibold text-slate-500 w-[90px]">Token</th>
                    <th className="h-14 px-4 text-left align-middle font-semibold text-slate-500 w-[170px]">更新时间</th>
                    <th className="h-14 px-4 text-left align-middle font-semibold text-slate-500 w-[140px]">操作</th>
                  </tr>
                </thead>
                <tbody className="[&_tr:last-child]:border-0">
                  {chunks.map((chunk) => (
                    <tr key={chunk.id} className="border-b border-gray-100 transition-colors hover:bg-[#F9FAFB]">
                      <td className="px-4 py-3.5 align-middle">
                        <input
                          type="checkbox"
                          checked={selectedIds.has(String(chunk.id))}
                          onChange={() => toggleSelect(String(chunk.id))}
                        />
                      </td>
                      <td className="px-4 py-3.5 align-middle text-sm text-gray-700">{chunk.chunk_index ?? '-'}</td>
                      <td className="px-4 py-3.5 align-middle max-w-[360px] text-sm text-slate-500 break-all">
                        {truncateText(chunk.content)}
                      </td>
                      <td className="px-4 py-3.5 align-middle">
                        <span
                          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                            chunk.enabled === 1 
                              ? 'bg-blue-50 text-blue-700 border border-blue-200' 
                              : 'bg-gray-50 text-gray-600 border border-gray-200'
                          }`}
                        >
                          {enabledLabel(chunk.enabled)}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 align-middle text-sm text-gray-700">{chunk.char_count ?? '-'}</td>
                      <td className="px-4 py-3.5 align-middle text-sm text-gray-700">{chunk.token_count ?? '-'}</td>
                      <td className="px-4 py-3.5 align-middle text-sm text-gray-500">{formatDate(chunk.update_time)}</td>
                      <td className="px-4 py-3.5 align-middle text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => setEditDialog({ open: true, chunk })}
                            className="admin-btn-sm admin-btn-secondary"
                          >
                            <Eye className="w-4 h-4 mr-0.1" />
                            查看
                          </button>
                          <button
                            onClick={() => handleToggleEnabled(chunk)}
                            className="admin-btn-sm admin-btn-secondary"
                          >
                            {chunk.enabled === 1 ? '禁用' : '启用'}
                          </button>
                          <button
                            onClick={() => setDeleteTarget(chunk)}
                            className="admin-btn-ghost"
                          >
                            <Trash2 className="w-4 h-4 mr-0.1" />
                            删除
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* 分页 */}
            {pageData ? (
              <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-sm text-slate-500">
                <span>共 {pageData.total} 条</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPageNo((prev) => Math.max(1, prev - 1))}
                    disabled={pageData.current <= 1}
                    className="admin-btn-sm admin-btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    上一页
                  </button>
                  <span>
                    {pageData.current} / {pageData.pages}
                  </span>
                  <button
                    onClick={() => setPageNo((prev) => Math.min(pageData.pages || 1, prev + 1))}
                    disabled={pageData.current >= pageData.pages}
                    className="admin-btn-sm admin-btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    下一页
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* 查看分块对话框 */}
      <ChunkDialog
        open={editDialog.open}
        chunk={editDialog.chunk}
        onClose={() => setEditDialog({ open: false, chunk: null })}
      />

      {/* 删除确认对话框 */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full shadow-xl">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">确认删除分块？</h3>
              <p className="text-sm text-gray-600">该分块将被删除且向量会清理。</p>
            </div>
            <div className="px-6 py-4 bg-gray-50 rounded-b-lg flex justify-end gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="admin-btn-secondary"
              >
                取消
              </button>
              <button
                onClick={handleDelete}
                className="admin-btn-danger"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ChunkDialog({ open, chunk, onClose }) {
  if (!open) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-[760px] w-full shadow-xl flex flex-col max-h-[85vh]">
        {/* 对话框头部 */}
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">查看分块</h3>
          <p className="text-sm text-gray-600 mt-1">分块内容详情</p>
        </div>

        {/* 对话框内容 */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="flex flex-col">
            <label className="text-sm font-medium text-gray-700 mb-2">内容</label>
            <div className="whitespace-pre-wrap break-all text-sm text-gray-700 bg-gray-50 rounded-lg p-4 min-h-[280px]">
              {chunk?.content || '-'}
            </div>
          </div>
        </div>

        {/* 对话框底部 */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 rounded-b-lg flex justify-end">
          <button
            onClick={onClose}
            className="admin-btn-secondary"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  )
}

export default KnowledgeChunksPage
