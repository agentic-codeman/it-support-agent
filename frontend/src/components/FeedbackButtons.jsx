import React, { useState } from 'react';
import { Copy, ThumbsUp, ThumbsDown } from 'lucide-react';
import { submitFeedback } from '../services/feedbackService';

/**
 * 消息反馈按钮组件
 * 提供复制、点赞、点踩功能
 * 
 * @param {Object} props
 * @param {string} props.messageId - 消息ID
 * @param {string} props.conversationId - 会话ID
 * @param {string} props.content - 消息内容
 * @param {number|null} props.vote - 当前投票值：1=点赞，-1=点踩，null=未投票
 */
const FeedbackButtons = ({ messageId, conversationId, content, vote: initialVote }) => {
  const [vote, setVote] = useState(initialVote);
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * 处理复制
   */
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      showToast('复制成功', 'success');
    } catch (error) {
      console.error('复制失败:', error);
      showToast('复制失败', 'error');
    }
  };

  /**
   * 处理点赞/点踩
   * @param {number} newVote - 新的投票值：1=点赞，-1=点踩
   */
  const handleVote = async (newVote) => {
    if (isSubmitting) return;

    // 如果点击的是已选中的投票，则取消投票
    const nextVote = vote === newVote ? null : newVote;

    setIsSubmitting(true);
    
    // 乐观更新 UI
    const previousVote = vote;
    setVote(nextVote);

    try {
      if (nextVote !== null) {
        // 提交投票
        await submitFeedback(messageId, conversationId, nextVote);
        showToast(nextVote === 1 ? '点赞成功' : '点踩成功', 'success');
      } else {
        // 取消投票（再次调用 API 设置为 null 或删除记录）
        // 这里简化处理，直接前端更新
        showToast('已取消', 'info');
      }
    } catch (error) {
      console.error('反馈提交失败:', error);
      // 回滚 UI
      setVote(previousVote);
      showToast(error.message || '反馈失败', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * 显示提示消息
   */
  const showToast = (message, type = 'info') => {
    // 简单的 toast 实现，可以使用更完善的库如 react-toastify
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 px-4 py-2 rounded-lg shadow-lg z-50 transition-all duration-300 ${
      type === 'success' ? 'bg-green-500 text-white' :
      type === 'error' ? 'bg-red-500 text-white' :
      'bg-blue-500 text-white'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => document.body.removeChild(toast), 300);
    }, 2000);
  };

  return (
    <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
      {/* 复制按钮 */}
      <button
        onClick={handleCopy}
        className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
        title="复制内容"
      >
        <Copy className="w-4 h-4" />
      </button>

      {/* 点赞按钮 */}
      <button
        onClick={() => handleVote(1)}
        disabled={isSubmitting}
        className={`p-1.5 rounded-lg transition-colors ${
          vote === 1
            ? 'bg-blue-100 text-blue-600 hover:bg-blue-200'
            : 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'
        } ${isSubmitting ? 'cursor-not-allowed opacity-50' : ''}`}
        title="点赞"
      >
        <ThumbsUp className="w-4 h-4" />
      </button>

      {/* 点踩按钮 */}
      <button
        onClick={() => handleVote(-1)}
        disabled={isSubmitting}
        className={`p-1.5 rounded-lg transition-colors ${
          vote === -1
            ? 'bg-red-100 text-red-600 hover:bg-red-200'
            : 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'
        } ${isSubmitting ? 'cursor-not-allowed opacity-50' : ''}`}
        title="点踩"
      >
        <ThumbsDown className="w-4 h-4" />
      </button>
    </div>
  );
};

export default FeedbackButtons;
