import React, { useState } from 'react';
import { Plus, Search, Settings, MessageSquare, MoreHorizontal, Pencil, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

/**
 * 简化版侧边栏组件
 */
const Sidebar = ({ isOpen, onClose, conversations, currentConversationId, onSelectConversation, onCreateConversation }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState('');

  // 过滤会话列表
  const filteredConversations = conversations.filter(conv => 
    conv.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.id?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      {/* 移动端遮罩层 */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/30 backdrop-blur-sm transition-opacity lg:hidden"
          onClick={onClose}
        />
      )}

      {/* 侧边栏 */}
      <aside
        className={`fixed left-0 top-0 z-40 flex h-screen w-[280px] flex-shrink-0 flex-col bg-[#FAFAFA] p-3 transition-transform lg:static lg:h-screen lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Logo 区域 */}
        <div className="border-b border-[#F0F0F0] pb-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#3B82F6]">
              <MessageSquare className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-base font-semibold text-[#1A1A1A]">智能客服</p>
            </div>
          </div>
        </div>

        {/* 快速开始区域 */}
        <div className="py-3 space-y-4">
          <div className="relative overflow-hidden rounded-2xl border border-[#E6EEF6] bg-gradient-to-br from-[#F0F9FF] via-white to-[#FEF3C7] p-3 shadow-[0_14px_30px_rgba(15,23,42,0.08)]">
            <div className="relative">
              <div className="flex items-center justify-between px-1">
                <span className="text-[11px] font-semibold text-[#94A3B8]">快速开始</span>
                <span className="rounded-full bg-white/80 px-2 py-0.5 text-[10px] font-semibold text-[#2563EB]">
                  新内容
                </span>
              </div>
              <button
                type="button"
                className="mt-2 flex w-full items-center gap-3 rounded-2xl bg-white/90 px-4 py-3 text-left shadow-[0_10px_20px_rgba(15,23,42,0.08)] transition-all hover:-translate-y-[1px] hover:shadow-[0_16px_30px_rgba(15,23,42,0.12)]"
                onClick={() => {
                  onCreateConversation();
                  onClose();
                }}
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-[#60A5FA] to-[#2563EB] text-white shadow-[0_6px_14px_rgba(37,99,235,0.3)]">
                  <Plus className="h-4 w-4" />
                </span>
                <span className="flex-1">
                  <span className="block text-sm font-semibold text-[#1F2937]">新建对话</span>
                  <span className="block text-xs text-[#94A3B8]">从空白开始</span>
                </span>
              </button>
              {user?.role === 'admin' && (
                <button
                  type="button"
                  className="mt-2 inline-flex items-center gap-2 rounded-full border border-white/80 bg-white/70 px-3 py-1.5 text-xs font-semibold text-[#1D4ED8] transition-colors hover:bg-white"
                  onClick={() => {
                    navigate('/admin/knowledge');
                    onClose();
                  }}
                >
                  <Settings className="h-3.5 w-3.5" />
                  管理后台
                </button>
              )}
            </div>
          </div>

          {/* 搜索框 */}
          <div className="rounded-2xl border border-[#E6EEF6] bg-white p-3 shadow-[0_12px_26px_rgba(15,23,42,0.06)]">
            <div className="flex items-center justify-between px-1">
              <span className="text-[11px] font-semibold text-[#94A3B8]">搜索对话</span>
            </div>
            <div className="mt-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9CA3AF]" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="搜索对话..."
                  className="h-10 w-full rounded-xl border border-[#E5E7EB] bg-[#F8FAFC] pl-9 pr-3 text-sm text-[#1F2937] placeholder:text-[#9CA3AF] focus:border-[#93C5FD] focus:outline-none transition-colors"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 会话列表 */}
        <div className="relative flex-1 min-h-0">
          <div className="h-full overflow-y-auto">
            {filteredConversations.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center text-[#999999]">
                <MessageSquare className="h-16 w-16" />
                <p className="mt-2 text-[14px]">暂无对话记录</p>
              </div>
            ) : (
              <div className="space-y-1">
                {filteredConversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`group flex items-center justify-between gap-2 rounded-lg px-3 py-2 text-[14px] cursor-pointer transition-colors ${
                      currentConversationId === conv.id
                        ? 'bg-[#DBEAFE] text-[#2563EB]'
                        : 'text-[#333333] hover:bg-[#F5F5F5]'
                    }`}
                    onClick={() => {
                      onSelectConversation(conv.id);
                      onClose();
                    }}
                  >
                    <span className="min-w-0 flex-1 truncate">
                      {conv.title || '新对话'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 用户区域 */}
        <div className="mt-auto pt-3 border-t border-[#F0F0F0]">
          <button
            type="button"
            className="flex w-full items-center gap-2 rounded-lg p-2 text-left transition-colors hover:bg-[#F5F5F5]"
            onClick={logout}
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#3B82F6] text-white">
              <span className="text-sm font-medium">
                {(user?.username || user?.userId || '用户').slice(0, 1).toUpperCase()}
              </span>
            </div>
            <span className="flex-1 truncate text-sm font-medium text-[#1A1A1A]">
              {user?.username || user?.userId || '用户'}
            </span>
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
