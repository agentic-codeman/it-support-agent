import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, FileBarChart, FolderOpen, Layers, Pencil, Plus, RefreshCw, Trash2 } from 'lucide-react';
import { 
  getKnowledgeBasesPage, 
  deleteKnowledgeBase, 
  renameKnowledgeBase 
} from '../../services/knowledgeService';
import CreateKnowledgeBaseDialog from '../../components/CreateKnowledgeBaseDialog';

/**
 * 知识库管理页面
 */
export default function KnowledgeBasePage() {
  const navigate = useNavigate();
  const [pageData, setPageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [searchName, setSearchName] = useState('');
  const [keyword, setKeyword] = useState('');
  const [pageNo, setPageNo] = useState(1);
  const [renameDialog, setRenameDialog] = useState({ open: false, kb: null });
  const [renameValue, setRenameValue] = useState('');
  const [stats, setStats] = useState({
    totalCount: 0,
    documentCount: 0,
    activeCount: 0,
    creatorCount: 0
  });
  const [statsLoading, setStatsLoading] = useState(true);
  const statsRequestId = useRef(0);

  const PAGE_SIZE = 10;
  const STATS_PAGE_SIZE = 200;
  const knowledgeBases = pageData?.records || [];

  // 加载知识库列表
  const loadKnowledgeBases = async (current = pageNo, name = keyword) => {
    try {
      setLoading(true);
      const data = await getKnowledgeBasesPage(current, PAGE_SIZE, name || undefined);
      setPageData(data);
    } catch (error) {
      alert(error.response?.data?.message || '加载知识库列表失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 加载统计数据
  const loadStats = useCallback(async (name = keyword) => {
    const requestId = ++statsRequestId.current;
    const normalized = name.trim();
    setStatsLoading(true);
    try {
      const firstPage = await getKnowledgeBasesPage(1, STATS_PAGE_SIZE, normalized || undefined);
      if (statsRequestId.current !== requestId) return;

      let documentTotal = 0;
      let activeTotal = 0;
      const creatorNames = new Set();
      const addRecords = (records = []) => {
        records.forEach((kb) => {
          const docCount = kb.document_count ?? 0;
          documentTotal += docCount;
          if (docCount > 0) {
            activeTotal += 1;
          }
          if (kb.created_by) {
            creatorNames.add(kb.created_by);
          }
        });
      };

      addRecords(firstPage.records || []);

      const totalCount = firstPage.total ?? (firstPage.records?.length || 0);
      const totalPages = firstPage.pages || Math.max(1, Math.ceil(totalCount / STATS_PAGE_SIZE));

      for (let page = 2; page <= totalPages; page += 1) {
        const nextPage = await getKnowledgeBasesPage(page, STATS_PAGE_SIZE, normalized || undefined);
        if (statsRequestId.current !== requestId) return;
        addRecords(nextPage.records || []);
      }

      if (statsRequestId.current !== requestId) return;
      setStats({
        totalCount,
        documentCount: documentTotal,
        activeCount: activeTotal,
        creatorCount: creatorNames.size
      });
    } catch (error) {
      if (statsRequestId.current !== requestId) return;
      console.error(error);
      setStats({
        totalCount: 0,
        documentCount: 0,
        activeCount: 0,
        creatorCount: 0
      });
    } finally {
      if (statsRequestId.current === requestId) {
        setStatsLoading(false);
      }
    }
  }, [keyword]);

  useEffect(() => {
    loadKnowledgeBases();
  }, [pageNo, keyword]);

  useEffect(() => {
    loadStats(keyword);
  }, [keyword, loadStats]);

  // 当重命名对话框打开时，设置初始值
  useEffect(() => {
    if (renameDialog.open) {
      setRenameValue(renameDialog.kb?.name || '');
    }
  }, [renameDialog]);

  const handleSearch = () => {
    setPageNo(1);
    setKeyword(searchName.trim());
  };

  const handleRefresh = () => {
    setPageNo(1);
    loadKnowledgeBases(1, keyword);
    loadStats(keyword);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;

    try {
      await deleteKnowledgeBase(deleteTarget.id);
      alert('删除成功');
      setDeleteTarget(null);
      setPageNo(1);
      await loadKnowledgeBases(1, keyword);
      await loadStats(keyword);
    } catch (error) {
      alert(error.response?.data?.message || '删除失败');
      console.error(error);
    } finally {
      setDeleteTarget(null);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const formatStatValue = (value) => {
    if (statsLoading) return '--';
    return value.toLocaleString('zh-CN');
  };

  const renderEmbeddingModel = (model) => {
    if (!model) return '-';
    const parts = model.split('-');
    if (parts.length < 2) {
      return <span className="text-sm text-slate-700">{model}</span>;
    }
    const head = parts.slice(0, -1).join('-');
    const tail = parts[parts.length - 1];
    return (
      <div className="flex flex-col text-xs text-slate-500">
        <span className="font-medium text-slate-700">{head}</span>
        <span>{tail}</span>
      </div>
    );
  };

  const handleRename = async () => {
    if (!renameDialog.kb) return;
    const nextName = renameValue.trim();
    if (!nextName) {
      alert('请输入知识库名称');
      return;
    }
    if (nextName === renameDialog.kb.name) {
      setRenameDialog({ open: false, kb: null });
      return;
    }
    try {
      await renameKnowledgeBase(renameDialog.kb.id, nextName);
      alert('重命名成功');
      setRenameDialog({ open: false, kb: null });
      await loadKnowledgeBases(pageNo, keyword);
    } catch (error) {
      alert(error.response?.data?.message || '重命名失败');
      console.error(error);
    }
  };

  return (
    <div className="admin-page">
      {/* 页面标题和操作栏 */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">知识库管理</h1>
          <p className="text-sm text-slate-500 mt-1">管理所有知识库及其文档</p>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={searchName}
            onChange={(e) => setSearchName(e.target.value)}
            placeholder="搜索知识库名称"
            className="px-4 py-2 w-[240px] rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white"
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
            <RefreshCw className="h-4 w-4" />
            <span>刷新</span>
          </button>
          <button
            onClick={() => setCreateDialogOpen(true)}
            className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
          >
            <Plus className="h-4 w-4" />
            <span>新建知识库</span>
          </button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        {[
          { label: '知识库', value: stats.totalCount, icon: Database },
          { label: '文档数', value: stats.documentCount, icon: FileBarChart },
          { label: '含文档知识库', value: stats.activeCount, icon: FolderOpen },
          { label: '创建用户数', value: stats.creatorCount, icon: Layers }
        ].map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="bg-white rounded-xl border border-slate-200 px-6 py-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">{item.label}</p>
                    <p className="text-2xl font-semibold text-slate-900">{formatStatValue(item.value)}</p>
                  </div>
                </div>
                <span className="text-xs text-slate-500 px-2 py-0.5 rounded-full bg-slate-50">全部</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* 知识库列表 */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-4">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">名称</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Embedding模型</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Collection</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">文档数</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">负责人</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">创建时间</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">修改时间</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {loading ? (
                <tr>
                  <td colSpan="8" className="text-center py-8 text-slate-500">加载中...</td>
                </tr>
              ) : knowledgeBases.length === 0 ? (
                <tr>
                  <td colSpan="8" className="text-center py-8 text-slate-500">
                    暂无知识库，点击上方按钮创建
                  </td>
                </tr>
              ) : (
                knowledgeBases.map((kb) => (
                  <tr key={kb.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        type="button"
                        className="text-indigo-600 hover:text-indigo-800 font-medium max-w-[200px] truncate block"
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
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border border-slate-200 bg-slate-50 text-slate-600">
                          {kb.collection_name}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">{kb.document_count ?? '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{kb.created_by || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-slate-500">
                      {formatDate(kb.create_time)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-slate-500">
                      {formatDate(kb.update_time)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setRenameDialog({ open: true, kb })}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-sm text-slate-600 hover:bg-slate-50 transition-colors"
                        >
                          <Pencil className="h-4 w-4" />
                          <span>编辑</span>
                        </button>
                        <button
                          onClick={() => setDeleteTarget(kb)}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-sm text-slate-600 hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                          <span>删除</span>
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
        <div className="flex items-center justify-between mt-4">
          <span className="text-sm text-slate-600">共 {pageData.total} 条</span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPageNo((prev) => Math.max(1, prev - 1))}
              disabled={pageData.current <= 1}
              className="px-3 py-1.5 text-sm border border-slate-200 rounded-lg bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white transition-colors"
            >
              上一页
            </button>
            <span className="px-3 py-1.5 text-sm text-slate-600">
              {pageData.current} / {pageData.pages || 1}
            </span>
            <button
              onClick={() => setPageNo((prev) => Math.min(pageData.pages || 1, prev + 1))}
              disabled={pageData.current >= pageData.pages}
              className="px-3 py-1.5 text-sm border border-slate-200 rounded-lg bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white transition-colors"
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
            知识库删除后当前不提供恢复入口。确定要继续吗？
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

      {/* 重命名对话框 */}
      {renameDialog.open && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
          <h3 className="text-lg font-semibold text-slate-900 mb-2">重命名知识库</h3>
          <p className="text-slate-600 mb-4">修改知识库名称</p>
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 mb-2">名称</label>
            <input
              type="text"
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => setRenameDialog({ open: false, kb: null })}
              className="px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleRename}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
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
          setPageNo(1);
          loadKnowledgeBases(1, keyword);
          loadStats(keyword);
        }}
      />
    </div>
  );
}

