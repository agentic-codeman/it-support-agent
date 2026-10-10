import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Bot,
  Plus,
  Search,
  Pencil,
  Trash2,
  MoreHorizontal,
  Settings,
  MessageSquare,
  LogOut
} from 'lucide-react';
import { listConversations, renameConversation, deleteConversation } from '../services/conversationService';
import { useAuthStore } from '../store/authStore';

/**
 * 会话侧边栏组件
 * 显示历史对话列表，支持新建、重命名、删除会话
 */
const ConversationSidebar = ({ 
  conversations, 
  currentConversationId, 
  onSelectConversation, 
  onNewConversation,
  onLoadConversations 
}) => {
  const [query, setQuery] = useState('');
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const renameInputRef = useRef(null);
  const { user, logout } = useAuthStore();

  // 加载会话列表
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      setIsLoading(true);
      const list = await listConversations();
      if (onLoadConversations) {
        onLoadConversations(list);
      }
    } catch (error) {
      console.error('加载会话列表失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 过滤会话列表
  const filteredSessions = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    if (!keyword) return conversations;
    return conversations.filter((session) => {
      const title = (session.title || '新对话').toLowerCase();
      return title.includes(keyword) || session.conversationId.toLowerCase().includes(keyword);
    });
  }, [query, conversations]);

  // 分组会话列表（今天、7天内、30天内、更早）
  const groupedSessions = useMemo(() => {
    const now = new Date();
    const groups = new Map();
    const order = [];

    const resolveLabel = (value) => {
      const parsed = value ? new Date(value) : now;
      const diff = Math.max(0, Math.floor((now - parsed) / (1000 * 60 * 60 * 24)));
      if (diff === 0) return '今天';
      if (diff <= 7) return '7天内';
      if (diff <= 30) return '30天内';
      return '更早';
    };

    filteredSessions.forEach((session) => {
      const label = resolveLabel(session.lastTime);
      if (!groups.has(label)) {
        groups.set(label, []);
        order.push(label);
      }
      groups.get(label).push(session);
    });

    return order.map((label) => ({
      label,
      items: groups.get(label) || []
    }));
  }, [filteredSessions]);

  // 自动聚焦重命名输入框
  useEffect(() => {
    if (renamingId) {
      renameInputRef.current?.focus();
      renameInputRef.current?.select();
    }
  }, [renamingId]);

  // 开始重命名
  const startRename = (id, title) => {
    setRenamingId(id);
    setRenameValue(title || '新对话');
  };

  // 取消重命名
  const cancelRename = () => {
    setRenamingId(null);
    setRenameValue('');
  };

  // 提交重命名
  const commitRename = async () => {
    if (!renamingId) return;
    const nextTitle = renameValue.trim();
    if (!nextTitle) {
      cancelRename();
      return;
    }
    const currentTitle = conversations.find((s) => s.conversationId === renamingId)?.title || '新对话';
    if (nextTitle === currentTitle) {
      cancelRename();
      return;
    }
    try {
      await renameConversation(renamingId, nextTitle);
      await loadConversations();
      cancelRename();
    } catch (error) {
      console.error('重命名失败:', error);
      alert(error.message || '重命名失败');
    }
  };

  // 删除会话
  const confirmDelete = (session) => {
    setDeleteTarget(session);
    setShowDeleteDialog(true);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteConversation(deleteTarget.conversationId);
      // 如果删除的是当前会话，切换到新会话
      if (currentConversationId === deleteTarget.conversationId && onNewConversation) {
        onNewConversation();
      }
      setShowDeleteDialog(false);
      setDeleteTarget(null);
      await loadConversations();
    } catch (error) {
      console.error('删除失败:', error);
      alert(error.message || '删除失败');
    }
  };

  const handleSelectSession = (session) => {
    if (renamingId === session.conversationId) return;
    if (renamingId) {
      cancelRename();
    }
    onSelectConversation(session.conversationId);
  };

  const sessionTitleFont = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif';

  return (
    <>
      {/* 侧边栏主体 */}
      <aside className="flex h-screen w-[280px] flex-shrink-0 flex-col bg-[#FAFAFA] p-3">
        {/* 头部 Logo */}
        <div className="border-b border-[#F0F0F0] pb-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#3B82F6]">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <div style={{ fontFamily: sessionTitleFont }}>
              <p className="text-base font-semibold text-[#1A1A1A]">智能客服</p>
            </div>
          </div>
        </div>

        {/* 快速开始和搜索区域 */}
        <div className="py-3 space-y-4">
          {/* 快速开始卡片 */}
          <div className="relative overflow-hidden rounded-2xl border border-[#E6EEF6] bg-gradient-to-br from-[#F0F9FF] via-white to-[#FEF3C7] p-3 shadow-[0_14px_30px_rgba(15,23,42,0.08)]">
            <span
              aria-hidden="true"
              className="absolute -right-10 -top-10 h-24 w-24 rounded-full bg-[#BAE6FD]/70 blur-2xl"
            />
            <span
              aria-hidden="true"
              className="absolute -left-12 -bottom-10 h-28 w-28 rounded-full bg-[#FDE68A]/70 blur-2xl"
            />
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
                onClick={onNewConversation}
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-[#60A5FA] to-[#2563EB] text-white shadow-[0_6px_14px_rgba(37,99,235,0.3)]">
                  <Plus className="h-4 w-4" />
                </span>
                <span className="flex-1">
                  <span className="block text-sm font-semibold text-[#1F2937]">新建对话</span>
                  <span className="block text-xs text-[#94A3B8]">从空白开始</span>
                </span>
              </button>
              <button
                type="button"
                className="mt-2 inline-flex items-center gap-2 rounded-full border border-white/80 bg-white/70 px-3 py-1.5 text-xs font-semibold text-[#1D4ED8] transition-colors hover:bg-white"
                onClick={() => window.open('/admin', '_blank')}
              >
                <Settings className="h-3.5 w-3.5" />
                管理后台
              </button>
            </div>
          </div>

          {/* 搜索对话卡片 */}
          <div className="rounded-2xl border border-[#E6EEF6] bg-white p-3 shadow-[0_12px_26px_rgba(15,23,42,0.06)]">
            <div className="flex items-center justify-between px-1">
              <span className="text-[11px] font-semibold text-[#94A3B8]">搜索对话</span>
              <span className="text-[10px] text-[#CBD5F5]">Ctrl / Cmd + K</span>
            </div>
            <div className="mt-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9CA3AF]" />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="搜索对话..."
                  className="h-10 w-full rounded-xl border border-[#E5E7EB] bg-[#F8FAFC] pl-9 pr-3 text-sm text-[#1F2937] placeholder:text-[#9CA3AF] focus:border-[#93C5FD] focus:outline-none transition-colors"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 会话列表 */}
        <div className="relative flex-1 min-h-0">
          <div className="h-full overflow-y-auto sidebar-scroll">
            {conversations.length === 0 && isLoading ? (
              <div
                className="flex h-full items-center justify-center text-[#999999]"
                style={{ fontFamily: sessionTitleFont }}
              >
                <span>加载会话中...</span>
              </div>
            ) : filteredSessions.length === 0 ? (
              <div
                className="flex h-full flex-col items-center justify-center text-[#999999]"
                style={{ fontFamily: sessionTitleFont }}
              >
                <MessageSquare className="h-16 w-16" />
                <p className="mt-2 text-[14px]">暂无对话记录</p>
              </div>
            ) : (
              <div>
                {groupedSessions.map((group, index) => (
                  <div key={group.label} className="flex flex-col">
                    {index === 0 && <div className="mt-0" />}
                    {index > 0 && <div className="mt-4" />}
                    <p className="mb-1.5 pl-3 text-[12px] font-normal leading-[18px] text-[#999999]">
                      {group.label}
                    </p>
                    {group.items.map((session) => (
                      <div
                        key={session.conversationId}
                        className={`
                          group my-[1px] flex min-h-[40px] cursor-pointer items-center justify-between gap-2 rounded-lg px-3 py-2 text-[14px] leading-[22px] transition-colors duration-200
                          ${
                            currentConversationId === session.conversationId
                              ? 'bg-[#DBEAFE] text-[#2563EB]'
                              : 'text-[#333333] hover:bg-[#F5F5F5]'
                          }
                        `}
                        role="button"
                        tabIndex={0}
                        onClick={() => handleSelectSession(session)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleSelectSession(session);
                          }
                        }}
                      >
                        {renamingId === session.conversationId ? (
                          <input
                            ref={renameInputRef}
                            value={renameValue}
                            onChange={(e) => setRenameValue(e.target.value)}
                            onClick={(e) => e.stopPropagation()}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                e.preventDefault();
                                commitRename();
                              }
                              if (e.key === 'Escape') {
                                e.preventDefault();
                                cancelRename();
                              }
                            }}
                            onBlur={() => {
                              commitRename();
                            }}
                            className="h-6 flex-1 rounded-md border border-[#E5E5E5] bg-white px-2 text-[14px] leading-[22px] text-[#333333] focus:border-[#2563EB] focus:outline-none"
                          />
                        ) : (
                          <span className="min-w-0 flex-1 truncate font-normal" style={{ fontFamily: sessionTitleFont }}>
                            {session.title || '新对话'}
                          </span>
                        )}
                        {/* 操作菜单按钮 */}
                        <div className="relative">
                          <button
                            type="button"
                            className={`
                              flex h-6 w-6 items-center justify-center rounded text-[#666666] transition-opacity duration-150 hover:bg-[rgba(0,0,0,0.06)]
                              ${
                                currentConversationId === session.conversationId
                                  ? 'pointer-events-auto opacity-100 text-[#2563EB]'
                                  : 'pointer-events-none opacity-0 group-hover:pointer-events-auto group-hover:opacity-100'
                              }
                            `}
                            onClick={(e) => {
                              e.stopPropagation();
                            }}
                            aria-label="会话操作"
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </button>
                          {/* 下拉菜单（简单实现） */}
                          {renamingId !== session.conversationId && (
                            <div className="hidden group-hover:block absolute right-0 top-full mt-1 w-32 rounded-lg border-0 bg-white py-1 shadow-[0_4px_16px_rgba(0,0,0,0.12)] z-50">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  startRename(session.conversationId, session.title || '新对话');
                                }}
                                className="flex w-full items-center px-4 py-2 text-[14px] text-[#333333] hover:bg-[#F5F5F5]"
                              >
                                <Pencil className="mr-2 h-4 w-4" />
                                重命名
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  confirmDelete(session);
                                }}
                                className="flex w-full items-center px-4 py-2 text-[14px] text-[#FF4D4F] hover:bg-[#F5F5F5]"
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                删除
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
          {/* 底部渐变遮罩 */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-0 bottom-0 z-10 h-5 bg-gradient-to-b from-transparent to-[#FAFAFA]"
          />
        </div>

        {/* 底部用户信息 */}
        <div className="mt-auto pt-3">
          <div className="flex w-full items-center gap-2 rounded-lg p-2 text-left transition-colors hover:bg-[#F5F5F5]">
            <div className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full bg-[#3B82F6] text-white">
              <span className="text-sm font-medium">
                {(user?.username || user?.userId || '用户').slice(0, 1).toUpperCase()}
              </span>
            </div>
            <span className="flex-1 truncate text-sm font-medium text-[#1A1A1A]">
              {/^\d+$/.test(user?.username || user?.userId || '') ? '用户' : (user?.username || user?.userId || '用户')}
            </span>
            <button
              onClick={() => logout()}
              className="flex h-6 w-6 items-center justify-center rounded text-[#999999] hover:bg-[rgba(0,0,0,0.06)]"
              title="退出登录"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* 删除确认对话框 */}
      {showDeleteDialog && deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-[#1A1A1A] mb-2">删除该会话？</h3>
            <p className="text-sm text-[#666666] mb-6">
              [{deleteTarget.title || '该会话'}] 将被永久删除，无法恢复。
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowDeleteDialog(false);
                  setDeleteTarget(null);
                }}
                className="px-4 py-2 rounded-lg border border-[#E5E5E5] text-[#333333] hover:bg-[#F5F5F5]"
              >
                取消
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 rounded-lg bg-[#FF4D4F] text-white hover:bg-[#FF7875]"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ConversationSidebar;
