import React, { useState, useRef, useEffect } from 'react';
import { Send, StopCircle, Sparkles, Lightbulb, Bot, BookOpen, Check, ArrowUpRight, Menu } from 'lucide-react';
import { streamChat, stopTask } from '../services/chatService';
import ConversationSidebar from '../components/ConversationSidebar';
import FeedbackButtons from '../components/FeedbackButtons';
import MarkdownRenderer from '../components/MarkdownRenderer';
import { listMessages as listMessagesService } from '../services/conversationService';
import { getRandomSampleQuestions } from '../services/sampleQuestionService';

// 将回复中的「工单系统」转成可点击链接，跳转到工单系统提单页（新标签页打开）
const linkifyTicket = (content) => {
  if (!content) return content;
  const ticketUrl = `${window.location.origin}/ticket`;
  return content.replace(/工单系统/g, `[工单系统](${ticketUrl})`);
};

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [deepThinking, setDeepThinking] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true); // 默认打开侧边栏
  const [conversations, setConversations] = useState([]);
  const [promptPresets, setPromptPresets] = useState([
    {
      title: '故障排查',
      description: '快速定位并解决扫地机常见问题',
      prompt: '扫地机器人无法启动/充电，如何排查？',
      icon: BookOpen
    },
    {
      title: '选购建议',
      description: '根据需求推荐合适的扫地机型号',
      prompt: '100平米瓷砖地面，有宠物，推荐哪款扫地机器人？',
      icon: Check
    },
    {
      title: '维护保养',
      description: '了解日常清洁和保养方法',
      prompt: '扫地机器人滚刷缠绕毛发，如何清理？',
      icon: Lightbulb
    }
  ]);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // 图标映射
  const ICONS = [BookOpen, Check, Lightbulb];

  // 加载示例问题
  useEffect(() => {
    let active = true;
    const loadSampleQuestions = async () => {
      try {
        const questions = await getRandomSampleQuestions(3);
        if (!active || !questions || questions.length === 0) {
          return;
        }
        
        const mapped = questions
          .filter((item) => item.question && item.question.trim())
          .slice(0, 3)
          .map((item, index) => {
            const question = item.question.trim();
            const title =
              item.title?.trim() ||
              (question.length > 12 ? `${question.slice(0, 12)}...` : question) ||
              `推荐问法 ${index + 1}`;
            const description = item.description?.trim() || '直接点选即可开始对话';
            return {
              id: item.id,
              title,
              description,
              prompt: question,
              icon: ICONS[index % ICONS.length]
            };
          });
        
        if (mapped.length > 0) {
          setPromptPresets(mapped);
        }
      } catch (error) {
        console.error('加载示例问题失败:', error);
      }
    };

    loadSampleQuestions();
    return () => {
      active = false;
    };
  }, []);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 自动调整文本框高度
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [inputValue]);

  // 应用预设问题
  const applyPreset = (prompt) => {
    if (isLoading) return;
    setInputValue(prompt);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    const question = inputValue;
    setInputValue('');
    setIsLoading(true);

    // 创建 AI 消息占位符
    const aiMessageId = Date.now() + 1;
    setMessages(prev => [
      ...prev,
      {
        id: aiMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toLocaleTimeString(),
        status: 'streaming'
      }
    ]);

    try {
      const taskId = await streamChat({
        question,
        conversationId,
        deepThinking,
        // ✅ 收到 META 事件时立即设置 currentTaskId（用于中断）
        onMeta: ({ taskId: newTaskId, conversationId: newConvId }) => {
          console.log('✅ 收到 META 事件，设置 currentTaskId:', newTaskId);
          setCurrentTaskId(newTaskId);
          if (newConvId && !conversationId) {
            setConversationId(newConvId);
          }
        },
        onMessage: (content) => {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === aiMessageId
                ? { ...msg, content: msg.content + content }
                : msg
            )
          );
        },
        onComplete: ({ taskId: completedTaskId, conversationId: newConvId, messageId, image_urls }) => {
          setMessages(prev =>
            prev.map(msg => {
              if (msg.id !== aiMessageId) return msg;
              // 后端通过 final 事件额外下发的图片 URL：追加为 Markdown 图片（去重，避免与正文内联图片重复）
              let content = msg.content;
              if (Array.isArray(image_urls) && image_urls.length > 0) {
                const missing = image_urls.filter((url) => url && !content.includes(url));
                if (missing.length > 0) {
                  content = `${content.trimEnd()}\n\n${missing.map((url) => `![图片](${url})`).join('\n')}`;
                }
              }
              return { ...msg, status: 'complete', messageId: messageId || msg.messageId, content };
            })
          );
          setConversationId(newConvId);
          setCurrentTaskId(null);  // 完成后清除
          setIsLoading(false);
        },
        onError: (error) => {
          console.error('聊天错误:', error);
          setMessages(prev =>
            prev.map(msg =>
              msg.id === aiMessageId
                ? {
                    ...msg,
                    content: msg.content || `错误: ${error.message}`,
                    status: 'error'
                  }
                : msg
            )
          );
          setIsLoading(false);
          setCurrentTaskId(null);  // 错误时清除
        }
      });

      // 注意：这里的 taskId 是 streamChat 返回的，但已经在 onMeta 中设置过了
      // 这里保留是为了兼容性
      if (taskId && !currentTaskId) {
        setCurrentTaskId(taskId);
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      setIsLoading(false);
    }
  };

  // 停止生成
  const handleStopGeneration = async () => {
    if (currentTaskId) {
      try {
        await stopTask(currentTaskId);
        setMessages(prev =>
          prev.map(msg =>
            msg.status === 'streaming'
              ? { ...msg, status: 'stopped', content: msg.content + '\n\n[已停止生成]' }
              : msg
          )
        );
        setIsLoading(false);
        setCurrentTaskId(null);
      } catch (error) {
        console.error('停止任务失败:', error);
      }
    }
  };

  // 清空对话
  const handleClearChat = () => {
    setMessages([]);
    setConversationId(null);
    setCurrentTaskId(null);
    setIsLoading(false);
  };

  // 创建新会话
  const handleCreateConversation = () => {
    handleClearChat();
    // 重新加载会话列表
    import('../services/conversationService').then(({ listConversations }) => {
      listConversations().then(setConversations).catch(console.error);
    });
  };

  // 选择会话
  const handleSelectConversation = (convId) => {
    setConversationId(convId);
    // 加载该会话的历史消息
    import('../services/conversationService').then(({ listMessages }) => {
      listMessages(convId).then((messages) => {
        // 转换消息格式
        const formattedMessages = messages.map((msg) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: msg.create_time ? new Date(msg.create_time).toLocaleTimeString() : '',
          status: 'complete',
          messageId: msg.role === 'assistant' ? msg.id : undefined,
          vote: msg.vote
        }));
        setMessages(formattedMessages);
      }).catch((error) => {
        console.error('加载消息失败:', error);
        setMessages([]);
      });
    });
  };

  // 加载会话列表回调
  const handleLoadConversations = (list) => {
    setConversations(list);
  };

  // 处理键盘事件
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const hasContent = inputValue.trim().length > 0;
  const showWelcome = messages.length === 0 && !isLoading;

  // 欢迎屏幕直接内联渲染。CSS 动画（fadeUp）只在元素重新挂载时才会重播，
  // 普通 re-render 不会重播动画，因此无需 useMemo 缓存。之前用 useMemo 且依赖
  // 数组漏掉了 inputValue / promptPresets，导致受控 textarea 的 value 属性过期，
  // 出现「无法输入文字、退格无法删除」的问题。
  const welcomeScreen = (
    <div className="relative flex min-h-full items-center justify-center overflow-hidden px-4 py-16 sm:px-6">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-gradient-to-br from-[#F8FAFC] via-white to-[#EFF6FF]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          backgroundImage: 'radial-gradient(circle, #e5e7eb 1px, transparent 1px)',
          backgroundSize: '40px 40px'
        }}
      />

      <div className="relative w-full max-w-[860px]">
        <div
          className="mt-10 opacity-0"
          style={{ animation: 'fadeUp 0.6s ease-out 80ms forwards' }}
        >
          <div
            className={`relative flex flex-col rounded-3xl border bg-white/80 px-5 pt-4 pb-3 shadow-[0_8px_24px_rgba(0,0,0,0.08)] backdrop-blur-xl transition-all duration-200 ${
              isFocused
                ? 'border-[#BFDBFE] shadow-[0_4px_12px_rgba(59,130,246,0.15)]'
                : 'border-white/70 hover:border-[#D4D4D4]'
            }`}
          >
            <div className="relative">
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                onCompositionStart={() => setIsComposing(true)}
                onCompositionEnd={() => setIsComposing(false)}
                placeholder={deepThinking ? '输入需要深度分析的问题...' : '输入你的问题...'}
                disabled={isLoading}
                rows={1}
                className="max-h-40 min-h-[52px] w-full resize-none border-0 bg-transparent px-2 pt-2 pb-2 text-[15px] text-[#1F2937] placeholder:text-[#9CA3AF] focus:outline-none sm:text-base"
                style={{ minHeight: '52px' }}
              />
              <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-[10px] bg-gradient-to-b from-white/0 via-white/40 to-white/90" />
            </div>
            <div className="mt-3 flex items-center justify-end">
              <button
                onClick={isLoading ? handleStopGeneration : handleSendMessage}
                disabled={!hasContent && !isLoading}
                className={`inline-flex items-center justify-center rounded-full p-2.5 transition-all duration-200 ${
                  isLoading
                    ? 'bg-[#FEE2E2] text-[#EF4444] hover:bg-[#FECACA]'
                    : hasContent
                    ? 'bg-[#3B82F6] text-white hover:bg-[#2563EB]'
                    : 'cursor-not-allowed bg-[#F5F5F5] text-[#CCCCCC]'
                }`}
              >
                {isLoading ? <StopCircle className="h-4 w-4" /> : <Send className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <p className="mt-3 text-center text-xs text-[#94A3B8]">
            <kbd className="rounded bg-white/80 px-1.5 py-0.5 text-[#6B7280] shadow-sm">Enter</kbd>{' '}
            发送
            <span className="px-1.5">·</span>
            <kbd className="rounded bg-white/80 px-1.5 py-0.5 text-[#6B7280] shadow-sm">
              Shift + Enter
            </kbd>{' '}
            换行
            {isLoading && <span className="ml-2 animate-pulse">生成中...</span>}
          </p>
        </div>

        <div
          className="mt-10 opacity-0"
          style={{ animation: 'fadeUp 0.6s ease-out 160ms forwards' }}
        >
          <div className="flex items-center justify-center gap-2 text-xs uppercase tracking-[0.24em] text-[#94A3B8]">
            <span className="h-px w-8 bg-[#E5E7EB]" />
            试试这些开场
            <span className="h-px w-8 bg-[#E5E7EB]" />
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {promptPresets.map((preset) => {
              const Icon = preset.icon;
              return (
                <button
                  key={preset.title}
                  type="button"
                  onClick={() => applyPreset(preset.prompt)}
                  disabled={isLoading}
                  className={`group rounded-2xl border border-white/70 bg-white/70 p-4 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-[#BFDBFE] hover:shadow-md ${
                    isLoading ? 'cursor-not-allowed opacity-60' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#EFF6FF] text-[#2563EB]">
                      <Icon className="h-4 w-4" />
                    </span>
                    <div>
                      <p className="text-sm font-semibold text-[#1F2937]">{preset.title}</p>
                      <p className="text-xs text-[#6B7280]">{preset.description}</p>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center gap-2 text-xs text-[#94A3B8]">
                    <span className="min-w-0 flex-1 truncate">推荐问法：{preset.prompt}</span>
                    <ArrowUpRight className="h-3.5 w-3.5 text-[#CBD5F5] transition-colors group-hover:text-[#3B82F6]" />
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen bg-[#FAFAFA]">
      {/* 会话侧边栏 */}
      {sidebarOpen && (
        <ConversationSidebar
          conversations={conversations}
          currentConversationId={conversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleCreateConversation}
          onLoadConversations={handleLoadConversations}
        />
      )}

      <div className="flex min-h-screen flex-1 flex-col bg-white">

        <div className="flex-1 overflow-y-auto">
          {showWelcome ? (
            welcomeScreen
          ) : (
            <div className="px-6 py-8">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center max-w-md">
                    <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl flex items-center justify-center">
                      <Sparkles className="w-10 h-10 text-blue-600" />
                    </div>
                    <h2 className="text-2xl font-semibold text-[#1A1A1A] mb-3">开始智能对话</h2>
                    <p className="text-[#666666] mb-8">输入问题，获取基于知识库的智能回答</p>
                  </div>
                </div>
              ) : (
                <div className="max-w-3xl mx-auto space-y-6">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} group`}
                    >
                      <div
                        className={`max-w-[80%] ${
                          message.role === 'assistant' ? '' : 'rounded-2xl px-5 py-3.5'
                        }`}
                      >
                        {/* 消息气泡 */}
                        <div
                          className={`${
                            message.role === 'user'
                              ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-md rounded-2xl px-5 py-3.5'
                              : message.status === 'error'
                              ? 'bg-red-50 text-red-800 border border-red-200 rounded-2xl px-5 py-3.5'
                              : 'bg-white text-[#1A1A1A] border border-[#E5E5E5] shadow-sm rounded-2xl px-5 py-3.5'
                          }`}
                        >
                          {/* 消息内容 */}
                          <div className="text-[15px] leading-relaxed">
                            {message.content ? (
                              message.role === 'assistant' ? (
                                <MarkdownRenderer content={linkifyTicket(message.content)} />
                              ) : (
                                <div className="whitespace-pre-wrap break-words">{message.content}</div>
                              )
                            ) : message.role === 'assistant' && message.status === 'streaming' ? (
                              <div className="flex items-center space-x-1">
                                <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                                <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                                <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                              </div>
                            ) : null}
                          </div>
                          {message.status === 'error' && (
                            <p className="text-xs text-red-600 mt-2">生成已中断</p>
                          )}
                        </div>
                        
                        {/* 反馈按钮（仅助手消息且已完成时显示） */}
                        {message.role === 'assistant' && message.status === 'complete' && message.messageId && (
                          <FeedbackButtons
                            messageId={message.messageId}
                            conversationId={conversationId}
                            content={message.content}
                            vote={message.vote || null}
                          />
                        )}
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
          )}
        </div>

        {!showWelcome && (
          <div className="bg-white border-t border-[#E5E5E5] px-6 py-4">
            <div className="max-w-3xl mx-auto">
              <div
                className={`relative flex flex-col rounded-2xl border bg-white px-4 pt-3 pb-2 transition-all duration-200 ${
                  isFocused
                    ? 'border-[#D4D4D4] shadow-[0_4px_12px_rgba(0,0,0,0.06)]'
                    : 'border-[#E5E5E5] hover:border-[#D4D4D4]'
                }`}
              >
                <textarea
                  ref={textareaRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  onFocus={() => setIsFocused(true)}
                  onBlur={() => setIsFocused(false)}
                  placeholder={deepThinking ? '输入需要深度分析的问题...' : '输入你的问题...'}
                  disabled={isLoading}
                  rows={1}
                  className="max-h-40 min-h-[44px] w-full resize-none border-0 bg-transparent px-2 pt-2 pb-2 pr-2 text-[15px] text-[#333333] shadow-none placeholder:text-[#999999] focus-visible:ring-0 disabled:opacity-60"
                  style={{ minHeight: '44px' }}
                />
                <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-[10px] bg-gradient-to-b from-white/0 via-white/40 to-white/90" />
                
                <div className="relative mt-2 flex items-center justify-end">
                  
                  <button
                    onClick={isLoading ? handleStopGeneration : handleSendMessage}
                    disabled={!hasContent && !isLoading}
                    className={`rounded-full p-2.5 transition-all duration-200 ${
                      isLoading
                        ? 'bg-[#FEE2E2] text-[#EF4444] hover:bg-[#FECACA]'
                        : hasContent
                        ? 'bg-[#3B82F6] text-white hover:bg-[#2563EB]'
                        : 'cursor-not-allowed bg-[#F5F5F5] text-[#CCCCCC]'
                    }`}
                  >
                    {isLoading ? <StopCircle className="h-4 w-4" /> : <Send className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              

              
              <p className="text-center text-xs text-[#999999] mt-3">
                <kbd className="rounded bg-[#F5F5F5] px-1.5 py-0.5 text-[#666666]">Enter</kbd> 发送
                <span className="px-1.5">·</span>
                <kbd className="rounded bg-[#F5F5F5] px-1.5 py-0.5 text-[#666666]">
                  Shift + Enter
                </kbd>{' '}
                换行
                {isLoading && <span className="ml-2 animate-pulse">生成中...</span>}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatPage;
