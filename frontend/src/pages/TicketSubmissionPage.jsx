import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ClipboardList, Send, User, Phone } from 'lucide-react';
import { toast } from 'sonner';
import { useAuthStore } from '../store/authStore';

/**
 * 工单系统提单静态页面
 *
 * 说明：当前为纯前端静态页面，不涉及后端接口。
 * 表单字段对齐后端 SupportTicketModel（title / problem_desc / submitter_no），
 * 提交后仅在前端展示模拟结果，不做实际持久化。
 */
const TicketSubmissionPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const defaultSubmitter = user?.username || user?.userId || '';

  const [form, setForm] = useState({
    title: '',
    description: '',
    submitter: defaultSubmitter,
    contact: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!form.title.trim()) {
      toast.error('请填写工单标题');
      return;
    }
    if (!form.description.trim()) {
      toast.error('请填写问题现象描述');
      return;
    }

    // 生成模拟工单编号（静态演示，不落库）
    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const seq = String(Math.floor(Math.random() * 10000)).padStart(4, '0');
    const ticketNo = `GD${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}${seq}`;

    toast.success(`工单提交成功，工单编号：${ticketNo}`);
    setForm({
      title: '',
      description: '',
      submitter: defaultSubmitter,
      contact: ''
    });
  };

  return (
    <div className="min-h-screen bg-[#FAFAFA]">
      {/* 顶部导航栏 */}
      <header className="border-b border-[#E5E5E5] bg-white">
        <div className="mx-auto flex h-16 max-w-3xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate('/chat')}
              className="flex h-9 w-9 items-center justify-center rounded-lg text-[#666666] transition-colors hover:bg-[#F5F5F5] hover:text-[#1A1A1A]"
              aria-label="返回对话"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#3B82F6]">
                <ClipboardList className="h-4 w-4 text-white" />
              </span>
              <h1 className="text-lg font-semibold text-[#1A1A1A]">工单系统</h1>
            </div>
          </div>
        </div>
      </header>

      {/* 主内容 */}
      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-[#1A1A1A]">提交工单</h2>
          <p className="mt-1 text-sm text-[#666666]">
            如智能客服未能解决您的问题，请填写以下信息，我们会尽快为您处理。
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-[#E5E5E5] bg-white p-6 shadow-sm"
        >
          {/* 工单标题 */}
          <div className="mb-5">
            <label htmlFor="title" className="mb-1.5 block text-sm font-medium text-[#1A1A1A]">
              工单标题 <span className="text-[#FF4D4F]">*</span>
            </label>
            <input
              id="title"
              name="title"
              value={form.title}
              onChange={handleChange}
              placeholder="请简要描述问题，例如：扫地机器人无法充电"
              className="h-11 w-full rounded-xl border border-[#E5E5E5] bg-white px-3 text-sm text-[#1F2937] placeholder:text-[#9CA3AF] transition-colors focus:border-[#3B82F6] focus:outline-none"
            />
          </div>

          {/* 问题现象描述 */}
          <div className="mb-5">
            <label htmlFor="description" className="mb-1.5 block text-sm font-medium text-[#1A1A1A]">
              问题现象描述 <span className="text-[#FF4D4F]">*</span>
            </label>
            <textarea
              id="description"
              name="description"
              value={form.description}
              onChange={handleChange}
              rows={5}
              placeholder="请详细描述您遇到的问题，包括操作步骤、故障现象、已尝试的解决方法等"
              className="w-full resize-none rounded-xl border border-[#E5E5E5] bg-white px-3 py-2.5 text-sm text-[#1F2937] placeholder:text-[#9CA3AF] transition-colors focus:border-[#3B82F6] focus:outline-none"
            />
          </div>

          {/* 提交人信息 */}
          <div className="mb-5 grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="submitter" className="mb-1.5 block text-sm font-medium text-[#1A1A1A]">
                提交人（工号 / 姓名）
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9CA3AF]" />
                <input
                  id="submitter"
                  name="submitter"
                  value={form.submitter}
                  onChange={handleChange}
                  placeholder="请输入您的工号或姓名"
                  className="h-11 w-full rounded-xl border border-[#E5E5E5] bg-white pl-9 pr-3 text-sm text-[#1F2937] placeholder:text-[#9CA3AF] transition-colors focus:border-[#3B82F6] focus:outline-none"
                />
              </div>
            </div>
            <div>
              <label htmlFor="contact" className="mb-1.5 block text-sm font-medium text-[#1A1A1A]">
                联系方式（选填）
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9CA3AF]" />
                <input
                  id="contact"
                  name="contact"
                  value={form.contact}
                  onChange={handleChange}
                  placeholder="手机号或邮箱，便于我们联系您"
                  className="h-11 w-full rounded-xl border border-[#E5E5E5] bg-white pl-9 pr-3 text-sm text-[#1F2937] placeholder:text-[#9CA3AF] transition-colors focus:border-[#3B82F6] focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* 提交按钮 */}
          <div className="flex items-center justify-end gap-3 border-t border-[#F0F0F0] pt-5">
            <button
              type="button"
              onClick={() => navigate('/chat')}
              className="rounded-xl border border-[#E5E5E5] px-4 py-2.5 text-sm font-medium text-[#333333] transition-colors hover:bg-[#F5F5F5]"
            >
              取消
            </button>
            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-xl bg-[#3B82F6] px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#2563EB]"
            >
              <Send className="h-4 w-4" />
              提交工单
            </button>
          </div>
        </form>

        <p className="mt-4 text-center text-xs text-[#94A3B8]">
          当前为静态演示页面，提交数据暂不保存
        </p>
      </main>
    </div>
  );
};

export default TicketSubmissionPage;
