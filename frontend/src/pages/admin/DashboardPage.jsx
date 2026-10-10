import { useState, useEffect } from "react";
import {
  Database,
  FileText,
  Users,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react";
import { cn } from "../../lib/utils";

/**
 * Dashboard 仪表盘页面
 */
export default function DashboardPage() {
  const [stats, setStats] = useState({
    knowledgeBases: 0,
    documents: 0,
    users: 0,
    queries: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: 从 API 获取统计数据
    // 模拟数据
    setTimeout(() => {
      setStats({
        knowledgeBases: 6,
        documents: 10,
        users: 1,
        queries: 1234
      });
      setLoading(false);
    }, 500);
  }, []);

  const statCards = [
    {
      title: "知识库",
      value: stats.knowledgeBases,
      icon: Database,
      color: "indigo",
      description: "全部"
    },
    {
      title: "文档数",
      value: stats.documents,
      icon: FileText,
      color: "blue",
      description: "全部"
    },
    {
      title: "用户数",
      value: stats.users,
      icon: Users,
      color: "green",
      description: "全部"
    },
    {
      title: "查询次数",
      value: stats.queries,
      icon: TrendingUp,
      color: "purple",
      description: "总计"
    }
  ];

  const colorClasses = {
    indigo: {
      bg: "bg-indigo-50",
      icon: "bg-indigo-100 text-indigo-600"
    },
    blue: {
      bg: "bg-blue-50",
      icon: "bg-blue-100 text-blue-600"
    },
    green: {
      bg: "bg-green-50",
      icon: "bg-green-100 text-green-600"
    },
    purple: {
      bg: "bg-purple-50",
      icon: "bg-purple-100 text-purple-600"
    }
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">欢迎回来，查看您的知识库运营数据</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          const colors = colorClasses[stat.color];
          
          return (
            <div
              key={stat.title}
              className="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm text-slate-500">{stat.title}</p>
                  <div className="flex items-baseline gap-2 mt-2">
                    <p className="text-3xl font-bold text-slate-900">
                      {loading ? "-" : stat.value}
                    </p>
                    <span className="text-sm text-slate-400">{stat.description}</span>
                  </div>
                </div>
                <div className={cn("p-3 rounded-lg", colors.icon)}>
                  <Icon className="h-6 w-6" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 知识库列表 */}
      <div className="bg-white rounded-xl border border-slate-200">
        <div className="px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900">知识库概览</h2>
          <p className="text-sm text-slate-500 mt-1">最近的知识库及其文档统计</p>
        </div>
        
        <div className="p-6">
          {loading ? (
            <div className="text-center py-12 text-slate-400">
              <Database className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>加载中...</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* 示例数据 */}
              <div className="flex items-center justify-between p-4 rounded-lg bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-4">
                  <div className="p-2 rounded-lg bg-indigo-100 text-indigo-600">
                    <Database className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">扫地机器人知识库</p>
                    <p className="text-sm text-slate-500">Collection: robot_vacuum</p>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <span className="text-slate-600">
                    <span className="font-semibold">5</span> 文档
                  </span>
                  <span className="text-slate-400">2024-03-11</span>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 rounded-lg bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-4">
                  <div className="p-2 rounded-lg bg-blue-100 text-blue-600">
                    <Database className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">智能客服知识库</p>
                    <p className="text-sm text-slate-500">Collection: smart_service</p>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <span className="text-slate-600">
                    <span className="font-semibold">3</span> 文档
                  </span>
                  <span className="text-slate-400">2024-03-08</span>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 rounded-lg bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-4">
                  <div className="p-2 rounded-lg bg-green-100 text-green-600">
                    <Database className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">产品FAQ知识库</p>
                    <p className="text-sm text-slate-500">Collection: product_faq</p>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <span className="text-slate-600">
                    <span className="font-semibold">2</span> 文档
                  </span>
                  <span className="text-slate-400">2024-03-05</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 快速操作 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl p-6 text-white hover:shadow-lg transition-shadow cursor-pointer">
          <Database className="h-8 w-8 mb-3" />
          <h3 className="text-lg font-semibold mb-2">新建知识库</h3>
          <p className="text-sm text-indigo-100">创建新的知识库并上传文档</p>
        </div>

        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white hover:shadow-lg transition-shadow cursor-pointer">
          <FileText className="h-8 w-8 mb-3" />
          <h3 className="text-lg font-semibold mb-2">上传文档</h3>
          <p className="text-sm text-blue-100">向现有知识库添加文档</p>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white hover:shadow-lg transition-shadow cursor-pointer">
          <Users className="h-8 w-8 mb-3" />
          <h3 className="text-lg font-semibold mb-2">用户管理</h3>
          <p className="text-sm text-green-100">管理系统用户和权限</p>
        </div>
      </div>
    </div>
  );
}
