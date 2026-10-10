import { useState, useEffect, useCallback } from "react";
import {
  Search,
  Plus,
  Edit,
  Trash2,
  KeyRound,
  RefreshCw,
  CheckCircle2,
  XCircle
} from "lucide-react";
import { mappingService } from "../../services/mappingService";

/**
 * 关键词映射管理页面
 */
export default function KeywordMappingPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [keyword, setKeyword] = useState("");
  const [pageNo, setPageNo] = useState(1);
  const [pageData, setPageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editData, setEditData] = useState(null);

  const PAGE_SIZE = 10;
  const mappings = pageData?.records || [];

  // 加载关键词映射列表
  const loadMappings = useCallback(async (current = pageNo, kw = keyword) => {
    try {
      setLoading(true);
      const data = await mappingService.pageQuery(current, PAGE_SIZE, kw || undefined);
      setPageData(data);
    } catch (error) {
      alert(error.response?.data?.message || '加载关键词映射列表失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [pageNo, keyword]);

  useEffect(() => {
    loadMappings();
  }, [pageNo, keyword, loadMappings]);

  // 当编辑对话框打开时，设置初始值
  useEffect(() => {
    if (editDialogOpen && editData) {
      // 数据已在 handleEdit 中设置
    }
  }, [editDialogOpen, editData]);

  const handleSearch = () => {
    setPageNo(1);
    setKeyword(searchQuery.trim());
  };

  const handleRefresh = () => {
    setPageNo(1);
    setSearchQuery("");
    setKeyword("");
    loadMappings(1, "");
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;

    try {
      await mappingService.delete(deleteTarget.id);
      alert('删除成功');
      setDeleteTarget(null);
      setPageNo(1);
      await loadMappings(1, keyword);
    } catch (error) {
      alert(error.response?.data?.message || '删除失败');
      console.error(error);
    } finally {
      setDeleteTarget(null);
    }
  };

  const handleEdit = (mapping) => {
    setEditData(mapping);
    setEditDialogOpen(true);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const getMatchTypeLabel = (type) => {
    const labels = {
      1: '精确匹配',
      2: '前缀匹配',
      3: '正则匹配',
      4: '整词匹配'
    };
    return labels[type] || '-';
  };

  return (
    <div className="admin-page">
      {/* 页面标题和操作栏 */}
      <div className="admin-page-header">
        <div>
          <h1 className="admin-page-title">关键词映射管理</h1>
          <p className="admin-page-subtitle">配置查询归一化的关键词映射规则</p>
        </div>
        <div className="admin-page-actions">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="搜索原始词/目标词"
            className="w-[240px] px-4 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white"
          />
          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors"
          >
            搜索
          </button>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-6 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            <span>刷新</span>
          </button>
          <button
            onClick={() => {
              setEditData(null);
              setCreateDialogOpen(true);
            }}
            className="admin-primary-gradient flex items-center gap-2 px-6 py-2 rounded-lg text-sm font-medium"
          >
            <Plus className="w-4 h-4 mr-2" />
            <span>新增映射</span>
          </button>
        </div>
      </div>

      {/* 映射列表 */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
            <table className="w-full min-w-[980px]">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="w-[170px] px-6 py-4 text-left font-semibold text-slate-700">原始词</th>
                  <th className="w-[170px] px-6 py-4 text-left font-semibold text-slate-700">目标词</th>
                  <th className="w-[100px] px-6 py-4 text-left font-semibold text-slate-700 whitespace-nowrap">匹配类型</th>
                  <th className="w-[100px] px-6 py-4 text-left font-semibold text-slate-700 whitespace-nowrap">优先级</th>
                  <th className="w-[100px] px-6 py-4 text-left font-semibold text-slate-700 whitespace-nowrap">状态</th>
                  <th className="w-[180px] px-6 py-4 text-left font-semibold text-slate-700">备注</th>
                  <th className="w-[160px] px-6 py-4 text-left font-semibold text-slate-700">创建时间</th>
                  <th className="w-[160px] px-6 py-4 text-left font-semibold text-slate-700">更新时间</th>
                  <th className="w-[150px] px-6 py-4 text-left font-semibold text-slate-700">操作</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {loading ? (
                <tr>
                  <td colSpan="9" className="text-center py-8 text-slate-500">加载中...</td>
                </tr>
              ) : mappings.length === 0 ? (
                <tr>
                  <td colSpan="9" className="text-center py-8 text-slate-500">
                    暂无映射规则，点击上方按钮新增
                  </td>
                </tr>
              ) : (
                mappings.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 font-medium max-w-[160px] truncate" title={m.source_term}>
                      {m.source_term}
                    </td>
                    <td className="px-6 py-4 max-w-[160px] truncate" title={m.target_term}>
                      {m.target_term}
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-3 py-1 rounded-full bg-slate-100 text-xs text-slate-600 whitespace-nowrap">
                        {getMatchTypeLabel(m.match_type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-600 whitespace-nowrap">{m.priority}</td>
                    <td className="px-6 py-4">
                      {m.enabled ? (
                        <span className="px-3 py-1 rounded-full border border-indigo-200 bg-indigo-50 text-xs text-indigo-700 whitespace-nowrap">
                          启用
                        </span>
                      ) : (
                        <span className="px-3 py-1 rounded-full border border-slate-200 bg-slate-100 text-xs text-slate-500 whitespace-nowrap">
                          禁用
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-500 max-w-[160px] truncate" title={m.remark || ""}>
                      {m.remark || '-'}
                    </td>
                    <td className="px-6 py-4 text-slate-500 whitespace-nowrap">
                      {formatDate(m.create_time)}
                    </td>
                    <td className="px-6 py-4 text-slate-500 whitespace-nowrap">
                      {formatDate(m.update_time || m.create_time)}
                    </td>
                    <td className="px-6 py-4 text-center whitespace-nowrap">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => handleEdit(m)}
                          className="flex items-center gap-1 px-3 py-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors text-sm text-slate-600"
                        >
                          <Edit className="w-4 h-4" />
                          编辑
                        </button>
                        <button
                          onClick={() => setDeleteTarget(m)}
                          className="flex items-center gap-1 px-3 py-1.5 hover:bg-slate-50 transition-colors text-sm text-slate-600"
                        >
                          <Trash2 className="w-4 h-4" />
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 分页 */}
      {pageData && (
        <div className="flex items-center justify-between mt-4 text-sm text-slate-600">
          <span>共 {pageData.total} 条</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPageNo((prev) => Math.max(1, prev - 1))}
              disabled={pageData.current <= 1}
              className="px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <span className="px-2">
              {pageData.current} / {pageData.pages}
            </span>
            <button
              onClick={() => setPageNo((prev) => Math.min(pageData.pages || 1, prev + 1))}
              disabled={pageData.current >= pageData.pages}
              className="px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
        </div>
      )}

      {/* 删除确认对话框 */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-slate-900 mb-2">确认删除</h3>
            <p className="text-slate-600 mb-6">
              确定要删除该映射规则吗？
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
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

      {/* 编辑对话框 */}
      {editDialogOpen && editData && (
        <MappingDialog
          open={editDialogOpen}
          onClose={() => {
            setEditDialogOpen(false);
            setEditData(null);
          }}
          data={editData}
          mode="edit"
          onSuccess={() => {
            setEditDialogOpen(false);
            setEditData(null);
            loadMappings(pageNo, keyword);
          }}
        />
      )}

      {/* 创建对话框 */}
      {createDialogOpen && (
        <MappingDialog
          open={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          data={null}
          mode="create"
          onSuccess={() => {
            setCreateDialogOpen(false);
            setPageNo(1);
            loadMappings(1, keyword);
          }}
        />
      )}
    </div>
  );
}

/**
 * 创建/编辑映射对话框
 */
function MappingDialog({ open, onClose, data, mode, onSuccess }) {
  const [formData, setFormData] = useState({
    source_term: '',
    target_term: '',
    match_type: 1,
    priority: 0,
    enabled: true,
    remark: ''
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (data) {
      setFormData({
        source_term: data.source_term || '',
        target_term: data.target_term || '',
        match_type: data.match_type || 1,
        priority: data.priority || 0,
        enabled: data.enabled !== undefined ? data.enabled : true,
        remark: data.remark || ''
      });
    } else {
      setFormData({
        source_term: '',
        target_term: '',
        match_type: 1,
        priority: 0,
        enabled: true,
        remark: ''
      });
    }
  }, [data]);

  const handleSubmit = async () => {
    if (!formData.source_term.trim()) {
      alert('请输入原始词');
      return;
    }
    if (!formData.target_term.trim()) {
      alert('请输入映射词');
      return;
    }

    try {
      setSubmitting(true);
      if (mode === 'create') {
        await mappingService.create(formData);
        alert('创建成功');
      } else {
        await mappingService.update(data.id, formData);
        alert('更新成功');
      }
      onSuccess();
    } catch (error) {
      alert(error.response?.data?.message || (mode === 'create' ? '创建失败' : '更新失败'));
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-[#F8F9FB] rounded-3xl p-8 max-w-2xl w-full mx-4 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-slate-900">
              {mode === 'create' ? '新增映射规则' : '编辑映射规则'}
            </h3>
            <p className="text-sm text-slate-500 mt-1">配置查询归一化的关键词映射</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <XCircle className="w-6 h-6" />
          </button>
        </div>

        <div className="space-y-5">
          <div>
            <label className="block text-base font-medium text-slate-900 mb-2">
              原始词 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.source_term}
              onChange={(e) => setFormData({ ...formData, source_term: e.target.value })}
              placeholder="用户输入的原始关键词"
              className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm"
            />
          </div>

          <div>
            <label className="block text-base font-medium text-slate-900 mb-2">
              目标词 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.target_term}
              onChange={(e) => setFormData({ ...formData, target_term: e.target.value })}
              placeholder="归一化后的目标关键词"
              className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-base font-medium text-slate-900 mb-2">
                匹配类型
              </label>
              <div className="relative">
                <select
                  value={formData.match_type}
                  onChange={(e) => setFormData({ ...formData, match_type: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm appearance-none bg-white"
                >
                  <option value={1}>精确匹配</option>
                  <option value={2}>前缀匹配</option>
                  <option value={3}>正则匹配</option>
                  <option value={4}>整词匹配</option>
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-base font-medium text-slate-900 mb-2">
                优先级
              </label>
              <input
                type="number"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
                className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-base font-medium text-slate-900 mb-2">
              启用状态
            </label>
            <div className="relative">
              <select
                value={formData.enabled}
                onChange={(e) => setFormData({ ...formData, enabled: e.target.value === 'true' })}
                className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm appearance-none bg-white"
              >
                <option value="true">启用</option>
                <option value="false">禁用</option>
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-base font-medium text-slate-900 mb-2">
              备注
            </label>
            <input
              type="text"
              value={formData.remark}
              onChange={(e) => setFormData({ ...formData, remark: e.target.value })}
              placeholder="可选备注信息"
              className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm"
            />
          </div>
        </div>

        <div className="flex justify-end gap-4 mt-8">
          <button
            onClick={onClose}
            className="px-8 py-2.5 border border-slate-200 rounded-2xl hover:bg-slate-50 transition-colors text-sm font-medium text-slate-700"
            disabled={submitting}
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            className="px-8 py-2.5 bg-indigo-600 text-white rounded-2xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium shadow-md shadow-indigo-200"
            disabled={submitting}
          >
            {submitting ? '提交中...' : '保存'}
          </button>
        </div>
      </div>
    </div>
  );
}
