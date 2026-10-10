import { useState, useEffect } from "react";
import {
  Search,
  Plus,
  Pencil,
  Trash2,
  Users,
  Shield,
  RefreshCw,
  UserPlus
} from "lucide-react";
import { toast } from 'sonner';
import { getUserList, createUser, updateUser, deleteUser } from '../../services/userService';

/**
 * 工具函数：合并类名
 */
function cn(...inputs) {
  return inputs.filter(Boolean).join(" ");
}

/**
 * 用户管理页面
 */
export default function UsersPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    page_num: 1,
    page_size: 10,
    total: 0,
    total_pages: 0
  });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    role: 'user',
    avatar: ''
  });

  // 加载用户列表
  const loadUsers = async (page_num = 1, keyword = searchQuery) => {
    try {
      setLoading(true);
      const result = await getUserList({
        page_num,
        page_size: pagination.page_size,
        keyword: keyword || undefined
      });
      
      setUsers(result.list || []);
      setPagination({
        ...pagination,
        page_num: result.page_num || page_num,
        total: result.total || 0,
        total_pages: result.total_pages || 0
      });
    } catch (error) {
      console.error('加载用户列表失败:', error);
      toast.error(error.message || '加载用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    loadUsers();
  }, []);

  // 搜索处理
  const handleSearch = () => {
    loadUsers(1, searchQuery);
  };

  // 刷新
  const handleRefresh = () => {
    setSearchQuery('');
    loadUsers(1);
  };

  const roleLabels = {
    admin: "管理员",
    user: "普通用户"
  };

  // 打开创建模态框
  const handleOpenCreate = () => {
    setEditingUser(null);
    setFormData({
      username: '',
      password: '',
      role: 'user',
      avatar: ''
    });
    setShowCreateModal(true);
  };

  // 打开编辑模态框
  const handleOpenEdit = (user) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      password: '',
      role: user.role,
      avatar: user.avatar || ''
    });
    setShowCreateModal(true);
  };

  // 关闭模态框
  const handleCloseModal = () => {
    setShowCreateModal(false);
    setEditingUser(null);
    setFormData({
      username: '',
      password: '',
      role: 'user',
      avatar: ''
    });
  };

  // 提交表单
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (editingUser) {
        // 更新用户
        const updateData = {
          username: formData.username,
          role: formData.role,
          avatar: formData.avatar || undefined
        };
        
        // 如果填写了密码，则更新密码
        if (formData.password) {
          updateData.password = formData.password;
        }
        
        await updateUser(editingUser.id, updateData);
        toast.success('用户更新成功');
      } else {
        // 创建用户
        await createUser(formData);
        toast.success('用户创建成功');
      }
      
      handleCloseModal();
      loadUsers(pagination.page_num);
    } catch (error) {
      console.error('操作失败:', error);
      toast.error(error.message || '操作失败');
    }
  };

  // 删除用户
  const handleDelete = async (userId) => {
    if (!window.confirm('确定要删除该用户吗？')) {
      return;
    }
    
    try {
      await deleteUser(userId);
      toast.success('用户删除成功');
      loadUsers(pagination.page_num);
    } catch (error) {
      console.error('删除失败:', error);
      toast.error(error.message || '删除失败');
    }
  };

  // 分页处理
  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > pagination.total_pages) return;
    loadUsers(newPage);
  };

  return (
    <div className="space-y-6">
      {/* 页面标题和操作栏 */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">用户管理</h1>
          <p className="text-sm text-slate-500 mt-1">管理后台账号与角色权限</p>
        </div>
        <div className="flex items-center gap-3">
          {/* 搜索框 */}
          <div className="relative w-[220px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="搜索用户名或角色"
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-white border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          {/* 搜索按钮 */}
          <button
            onClick={handleSearch}
            className="px-5 py-2.5 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors whitespace-nowrap"
          >
            搜索
          </button>
          {/* 刷新按钮 */}
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors whitespace-nowrap"
          >
            <RefreshCw className="h-4 w-4" />
            <span>刷新</span>
          </button>
          {/* 新增用户按钮 */}
          <button 
            onClick={handleOpenCreate}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all whitespace-nowrap"
          >
            <UserPlus className="h-4 w-4" />
            <span>新增用户</span>
          </button>
        </div>
      </div>

      {/* 用户列表 */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600">用户</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600">角色</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600">创建时间</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600">更新时间</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          {user.avatar ? (
                            <img src={user.avatar} alt={user.username} className="h-10 w-10 rounded-full object-cover" />
                          ) : (
                            <div className="h-10 w-10 rounded-full bg-indigo-500 flex items-center justify-center text-white font-semibold text-sm">
                              {user.username.charAt(0).toUpperCase()}
                            </div>
                          )}
                          <div>
                            <div className="text-sm font-medium text-slate-900">{user.username}</div>
                            <div className="text-xs text-slate-500">{user.role === 'admin' ? '默认管理员' : '普通用户'}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={cn(
                          "inline-flex items-center px-3 py-1 rounded-full text-xs font-medium",
                          user.role === "admin" 
                            ? "bg-indigo-50 text-indigo-600" 
                            : "bg-slate-50 text-slate-600"
                        )}>
                          {roleLabels[user.role]}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-500">{user.create_time || '-'}</td>
                      <td className="px-6 py-4 text-sm text-slate-500">{user.update_time || '-'}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button 
                            onClick={() => handleOpenEdit(user)}
                            className="p-2 rounded-lg text-slate-400 hover:text-indigo-600 transition-colors"
                            title="编辑"
                          >
                            <Pencil className="h-4 w-4" />
                          </button>
                          <button 
                            onClick={() => handleDelete(user.id)}
                            className="p-2 rounded-lg text-slate-400 hover:text-red-600 transition-colors"
                            title="删除"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {users.length === 0 && (
              <div className="text-center py-12 text-slate-400">
                <Users className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>暂无用户数据</p>
              </div>
            )}

            {/* 分页 */}
            {pagination.total > 0 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200">
                <div className="text-sm text-slate-600">
                  共 {pagination.total} 条
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handlePageChange(pagination.page_num - 1)}
                    disabled={pagination.page_num <= 1}
                    className="px-3 py-1.5 rounded-lg border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    上一页
                  </button>
                  <span className="text-sm text-slate-600 px-2">
                    {pagination.page_num} / {pagination.total_pages}
                  </span>
                  <button
                    onClick={() => handlePageChange(pagination.page_num + 1)}
                    disabled={pagination.page_num >= pagination.total_pages}
                    className="px-3 py-1.5 rounded-lg border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    下一页
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* 创建/编辑用户模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900">
                {editingUser ? '编辑用户' : '新建用户'}
              </h3>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  用户名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({...formData, username: e.target.value})}
                  required
                  minLength={3}
                  maxLength={64}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="请输入用户名"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  密码 {editingUser && <span className="text-slate-400">（不填则不修改）</span>}
                  {!editingUser && <span className="text-red-500">*</span>}
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required={!editingUser}
                  minLength={6}
                  maxLength={128}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="请输入密码"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  角色
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="user">普通用户</option>
                  <option value="admin">管理员</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  头像 URL
                </label>
                <input
                  type="url"
                  value={formData.avatar}
                  onChange={(e) => setFormData({...formData, avatar: e.target.value})}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="https://example.com/avatar.jpg"
                />
              </div>
            </form>
            <div className="px-6 py-4 border-t border-slate-200 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={handleCloseModal}
                className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-50 transition-colors"
              >
                取消
              </button>
              <button
                type="submit"
                onClick={handleSubmit}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                {editingUser ? '保存' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
