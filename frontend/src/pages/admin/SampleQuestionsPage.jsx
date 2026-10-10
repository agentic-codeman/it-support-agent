import { useState, useEffect } from "react";
import {
  Plus,
  Pencil,
  Trash2,
  RefreshCw
} from "lucide-react";
import { toast } from 'sonner';
import { 
  getSampleQuestionList, 
  createSampleQuestion, 
  updateSampleQuestion, 
  deleteSampleQuestion 
} from '../../services/sampleQuestionService';

/**
 * 示例问题管理页面
 */
export default function SampleQuestionsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    page_num: 1,
    page_size: 10,
    total: 0,
    total_pages: 0
  });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    question: ''
  });

  // 加载示例问题列表
  const loadQuestions = async (pageNum = pagination.page_num) => {
    try {
      setLoading(true);
      const result = await getSampleQuestionList({
        page_num: pageNum,
        page_size: pagination.page_size,
        keyword: searchQuery || undefined
      });
      
      setQuestions(result.list || []);
      setPagination({
        page_num: result.page_num,
        page_size: result.page_size,
        total: result.total,
        total_pages: result.total_pages
      });
    } catch (error) {
      console.error('加载示例问题列表失败:', error);
      toast.error(error.message || '加载示例问题列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    loadQuestions();
  }, []);

  // 搜索处理
  const handleSearch = () => {
    setPagination(prev => ({ ...prev, page_num: 1 }));
    loadQuestions(1);
  };

  // 刷新
  const handleRefresh = () => {
    setSearchQuery('');
    setPagination(prev => ({ ...prev, page_num: 1 }));
    loadQuestions(1);
  };

  // 分页切换
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      loadQuestions(newPage);
    }
  };

  // 打开创建模态框
  const handleCreate = () => {
    setEditingQuestion(null);
    setFormData({
      title: '',
      description: '',
      question: ''
    });
    setShowCreateModal(true);
  };

  // 打开编辑模态框
  const handleEdit = (question) => {
    setEditingQuestion(question);
    setFormData({
      title: question.title || '',
      description: question.description || '',
      question: question.question || ''
    });
    setShowCreateModal(true);
  };

  // 提交表单
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.question.trim()) {
      toast.error('示例问题内容不能为空');
      return;
    }
    
    try {
      if (editingQuestion) {
        // 更新示例问题
        await updateSampleQuestion(editingQuestion.id, formData);
        toast.success('示例问题更新成功');
      } else {
        // 创建示例问题
        await createSampleQuestion(formData);
        toast.success('示例问题创建成功');
      }
      
      setShowCreateModal(false);
      loadQuestions(pagination.page_num);
    } catch (error) {
      toast.error(error.message || '操作失败');
    }
  };

  // 删除示例问题
  const handleDelete = async (questionId) => {
    const question = questions.find(q => q.id === questionId);
    if (!question) return;
    
    setDeleteTarget(question);
    setShowDeleteConfirm(true);
  };

  // 确认删除
  const confirmDelete = async () => {
    if (!deleteTarget) return;
    
    try {
      await deleteSampleQuestion(deleteTarget.id);
      toast.success('删除成功');
      setShowDeleteConfirm(false);
      setDeleteTarget(null);
      loadQuestions(pagination.page_num);
    } catch (error) {
      toast.error(error.message || '删除失败');
    }
  };

  return (
    <div className="space-y-6">
      {/* 页面标题和操作栏，搜索框和按钮在同一行 */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">示例问题管理</h1>
          <p className="text-sm text-slate-500 mt-1">配置欢迎页的示例问题与推荐问法</p>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="搜索标题/描述/问题"
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent w-[240px]"
          />
          <button 
            onClick={handleSearch}
            className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
          >
            搜索
          </button>
          <button 
            onClick={handleRefresh}
            className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
          >
            <RefreshCw className="h-4 w-4" />
            <span>刷新</span>
          </button>
          <button 
            onClick={handleCreate}
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>新增示例</span>
          </button>
        </div>
      </div>

      {/* 问题列表 - 使用Card样式包裹 */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="text-center py-12 text-slate-400">
            <p>加载中...</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700 w-[180px]">标题</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700 w-[220px]">描述</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">示例问题</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700 w-[170px]">更新时间</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700 w-[180px] text-left">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {questions.map((q) => (
                    <tr key={q.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4 font-medium max-w-[160px] truncate" title={q.title || ""}>{q.title || '-'}</td>
                      <td className="px-6 py-4 max-w-[200px] truncate" title={q.description || ""}>{q.description || '-'}</td>
                      <td className="px-6 py-4 text-sm text-slate-900 max-w-[360px] truncate" title={q.question}>
                        {q.question}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-500">
                        {q.update_time ? new Date(q.update_time).toLocaleString('zh-CN') : '-'}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="inline-flex items-center gap-2">
                          <button 
                            onClick={() => handleEdit(q)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 transition-colors whitespace-nowrap"
                          >
                            <Pencil className="h-4 w-4" />
                            <span>编辑</span>
                          </button>
                          <button 
                            onClick={() => handleDelete(q.id)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm text-red-600 hover:bg-red-50 transition-colors whitespace-nowrap"
                          >
                            <Trash2 className="h-4 w-4" />
                            <span>删除</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {questions.length === 0 && (
              <div className="text-center py-8 text-slate-400">
                <p>暂无示例问题，点击上方按钮新增</p>
              </div>
            )}
          </>
        )}
      </div>

      {/* 分页 */}
      {pagination.total > 0 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-slate-500">
            共 {pagination.total} 条
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handlePageChange(pagination.page_num - 1)}
              disabled={pagination.page_num === 1}
              className="px-3 py-1.5 rounded-lg border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <span className="px-3 py-1.5 text-sm text-slate-600">
              {pagination.page_num} / {pagination.total_pages}
            </span>
            <button
              onClick={() => handlePageChange(pagination.page_num + 1)}
              disabled={pagination.page_num >= pagination.total_pages}
              className="px-3 py-1.5 rounded-lg border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
        </div>
      )}

      {/* 删除确认对话框 */}
      {showDeleteConfirm && deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md mx-4">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900">确认删除</h2>
            </div>
            <div className="p-6">
              <p className="text-sm text-slate-500">删除后该示例问题将不会出现在欢迎页，是否继续？</p>
            </div>
            <div className="p-6 pt-0 flex justify-end gap-3">
              <button
                onClick={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}
                className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm hover:bg-red-700 transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 创建/编辑模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-[520px] mx-4">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900">
                {editingQuestion ? '编辑示例问题' : '新增示例问题'}
              </h2>
              <p className="text-sm text-slate-500 mt-1">配置欢迎页的示例问题和推荐问法</p>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-900 mb-2">标题</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="例如：任务拆解"
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-900 mb-2">描述</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="例如：把目标拆成可执行步骤与优先级"
                  rows={2}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-900 mb-2">示例问题 *</label>
                <textarea
                  value={formData.question}
                  onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                  placeholder="请输入示例问题内容"
                  rows={3}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none min-h-[120px]"
                />
              </div>
              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-violet-600 text-white text-sm hover:bg-violet-700 transition-colors"
                >
                  保存
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
