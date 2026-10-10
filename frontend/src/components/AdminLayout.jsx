import { useState, useEffect, useMemo } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  ChevronDown,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  ClipboardList,
  Database,
  GitBranch,
  Github,
  Layers,
  Lightbulb,
  LogOut,
  Menu,
  MessageSquare,
  KeyRound,
  Settings,
  Users,
  Brain
} from "lucide-react";
import { cn } from "../lib/utils";

// AdminLayout.jsx 在 components 目录，所以使用 ../lib/utils

/**
 * 管理后台布局组件
 */
export default function AdminLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const [openGroups, setOpenGroups] = useState({});

  // 获取当前用户信息
  const user = useMemo(() => {
    try {
      const token = localStorage.getItem("token");
      if (token) {
        const payload = JSON.parse(atob(token.split(".")[1]));
        return {
          username: payload.sub || "管理员",
          role: payload.role || "admin"
        };
      }
    } catch (e) {
      console.error("解析用户信息失败:", e);
    }
    return { username: "管理员", role: "admin" };
  }, []);

  // 菜单配置
  const menuGroups = [
    {
      title: "导航",
      items: [
        {
          path: "/admin/knowledge",
          label: "知识库管理",
          icon: Database
        },
        {
          id: "intent",
          path: "/admin/intent",
          label: "意图管理",
          icon: Layers,
          children: [
            {
              path: "/admin/intent-tree",
              label: "意图树配置",
              icon: GitBranch
            },
            {
              path: "/admin/intent-list",
              label: "意图列表",
              icon: ClipboardList
            }
          ]
        },
        {
          path: "/admin/mappings",
          label: "关键词映射",
          icon: KeyRound
        }
      ]
    },
    {
      title: "设置",
      items: [
        {
          path: "/admin/users",
          label: "用户管理",
          icon: Users
        },
        {
          path: "/admin/sample-questions",
          label: "示例问题",
          icon: Lightbulb
        }
      ]
    }
  ];

  // 面包屑映射
  const breadcrumbMap = {
    knowledge: "知识库管理",
    "intent-tree": "意图树配置",
    "intent-list": "意图列表",
    mappings: "关键词映射",
    "sample-questions": "示例问题",
    settings: "系统设置",
    users: "用户管理",
    doc: "文档管理",
    chunks: "切片管理"
  };

  // 计算面包屑
  const breadcrumbs = useMemo(() => {
    const segments = location.pathname.split("/").filter(Boolean);
    const items = [
      { label: "首页", to: "/admin/knowledge" }
    ];

    if (segments[0] !== "admin") return items;
    
    const section = segments[1];
    if (section) {
      if (section === "intent-tree" || section === "intent-list") {
        items.push({
          label: "意图管理",
          to: "/admin/intent-tree"
        });
        items.push({
          label: breadcrumbMap[section] || section
        });
      } else if (section === "knowledge") {
        // 知识库管理
        items.push({
          label: "知识库管理",
          to: "/admin/knowledge"
        });
        
        // 如果有 kbId，说明进入了知识库详情页（文档管理）
        if (segments[2]) {
          const kbId = segments[2];
          
          // 判断是否是文档管理页面：/admin/knowledge/:id
          // segments[3] 不存在时，就是文档管理页面
          if (!segments[3]) {
            items.push({
              label: "文档管理"
            });
          }
          // 判断是否是分块管理页面：/admin/knowledge/:kbId/doc/:docId/chunks
          else if (segments[3] === "doc" && segments[5] === "chunks") {
            // 先显示文档管理
            items.push({
              label: "文档管理"
            });
            // 再显示切片管理
            items.push({
              label: "切片管理"
            });
          }
        }
      } else {
        items.push({
          label: breadcrumbMap[section] || section
        });
      }
    }

    return items;
  }, [location.pathname]);

  // 处理退出登录
  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  // 检查菜单项是否激活
  const isLeafActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(`${path}/`);
  };

  // 检查分组是否激活
  const isGroupActive = (children) => {
    return children.some(child => isLeafActive(child.path));
  };

  // 渲染菜单项
  const renderMenuItem = (item, collapsed) => {
    if (!item.children || item.children.length === 0) {
      const Icon = item.icon;
      const isActive = isLeafActive(item.path);
      
      return (
        <Link
          key={item.path}
          to={item.path}
          title={collapsed ? item.label : undefined}
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
            "text-slate-300 hover:text-white hover:bg-white/10",
            isActive && "bg-indigo-600 text-white",
            collapsed && "justify-center"
          )}
        >
          <Icon className="h-5 w-5 flex-shrink-0" />
          {!collapsed && <span>{item.label}</span>}
        </Link>
      );
    }

    // 有子菜单的项
    const groupId = item.id;
    const isOpen = openGroups[groupId];
    const groupIsActive = isGroupActive(item.children);

    if (collapsed) {
      return item.children.map(child => {
        const ChildIcon = child.icon;
        const isActive = isLeafActive(child.path);
        return (
          <Link
            key={child.path}
            to={child.path}
            title={child.label}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors justify-center",
              "text-slate-300 hover:text-white hover:bg-white/10",
              isActive && "bg-indigo-600 text-white"
            )}
          >
            <ChildIcon className="h-5 w-5" />
          </Link>
        );
      });
    }

    return (
      <div key={item.label} className="space-y-1">
        <button
          type="button"
          onClick={() => setOpenGroups(prev => ({ ...prev, [groupId]: !prev[groupId] }))}
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors w-full",
            groupIsActive ? "text-white" : "text-slate-300 hover:text-white hover:bg-white/10"
          )}
        >
          <item.icon className="h-5 w-5 flex-shrink-0" />
          <span className="flex-1 text-left">{item.label}</span>
          {isOpen ? (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-slate-400" />
          )}
        </button>
        {isOpen && (
          <div className="ml-6 space-y-1">
            {item.children.map(child => {
              const ChildIcon = child.icon;
              const isActive = isLeafActive(child.path);
              return (
                <Link
                  key={child.path}
                  to={child.path}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                    "text-slate-300 hover:text-white hover:bg-white/10",
                    isActive && "bg-indigo-600 text-white"
                  )}
                >
                  <ChildIcon className="h-4 w-4 flex-shrink-0" />
                  <span>{child.label}</span>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-slate-50">
      {/* 左侧导航栏 */}
      <aside className={cn(
        "flex flex-col bg-slate-900 text-white transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}>
        {/* Logo 区域 */}
        <div className="flex items-center gap-3 p-4 border-b border-slate-800">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-indigo-600 text-white font-bold text-lg flex-shrink-0">
            W
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <h1 className="text-sm font-semibold truncate">智能客服管理后台</h1>
            </div>
          )}
        </div>

        {/* 导航菜单 */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {menuGroups.map(group => (
            <div key={group.title} className="space-y-2">
              {!collapsed && (
                <p className="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  {group.title}
                </p>
              )}
              <div className="space-y-1">
                {group.items.map(item => renderMenuItem(item, collapsed))}
              </div>
            </div>
          ))}
        </nav>

        {/* 底部区域 */}
        <div className="p-3 border-t border-slate-800 space-y-2">
          <button
            type="button"
            onClick={() => setCollapsed(prev => !prev)}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-white/10 transition-colors w-full"
          >
            {collapsed ? (
              <ChevronsRight className="h-5 w-5" />
            ) : (
              <>
                <ChevronsLeft className="h-5 w-5" />
                <span>收起侧边栏</span>
              </>
            )}
          </button>
        </div>
      </aside>

      {/* 主内容区域 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 顶部工具栏 */}
        <header className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-200">
          <div className="flex items-center gap-4">
            {/* 移动端菜单按钮 */}
            <button
              type="button"
              className="lg:hidden p-2 rounded-lg hover:bg-slate-100"
              onClick={() => setCollapsed(prev => !prev)}
            >
              <Menu className="h-5 w-5" />
            </button>
          </div>

          <div className="flex items-center gap-4">
            {/* 返回聊天 */}
            <Link
              to="/chat"
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 transition-colors"
            >
              <MessageSquare className="h-4 w-4" />
              <span>返回聊天</span>
            </Link>

            {/* 用户菜单 */}
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 font-semibold text-sm">
                {user.username.charAt(0).toUpperCase()}
              </div>
              <span className="text-sm text-slate-700">{user.username}</span>
              <button
                onClick={handleLogout}
                className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-red-500 transition-colors"
                title="退出登录"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </header>

        {/* 页面内容 */}
        <main className="flex-1 overflow-y-auto px-8 py-8">
          {/* 面包屑导航 */}
          <nav className="mb-4">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              {breadcrumbs.map((item, index) => (
                <div key={`${item.label}-${index}`} className="flex items-center gap-2">
                  {item.to && index < breadcrumbs.length - 1 ? (
                    <Link to={item.to} className="text-slate-500 hover:text-slate-700 transition-colors">
                      {item.label}
                    </Link>
                  ) : (
                    <span className={index === breadcrumbs.length - 1 ? "text-slate-700 font-medium" : "text-slate-500"}>
                      {item.label}
                    </span>
                  )}
                  {index < breadcrumbs.length - 1 && (
                    <span className="text-slate-400">/</span>
                  )}
                </div>
              ))}
            </div>
          </nav>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
