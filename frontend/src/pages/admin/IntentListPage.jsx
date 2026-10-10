import { useState, useEffect, useMemo } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { GitBranch, Pencil, RefreshCw, Search, X } from "lucide-react";
import { intentTreeService } from "../../services/intentTreeService";

const ALL_VALUE = "__ALL__";
const ROOT_VALUE = "__ROOT__";
const PAGE_SIZE_OPTIONS = [10, 20, 50];

const LEVEL_OPTIONS = [
  { value: 0, label: "DOMAIN" },
  { value: 1, label: "CATEGORY" },
  { value: 2, label: "TOPIC" }
];

const KIND_OPTIONS = [
  { value: 0, label: "KB" },
  { value: 1, label: "SYSTEM" }
];

/**
 * 意图列表页面
 */
export default function IntentListPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [tree, setTree] = useState([]);
  const [loading, setLoading] = useState(true);
  const [levelFilter, setLevelFilter] = useState(ALL_VALUE);
  const [kindFilter, setKindFilter] = useState(ALL_VALUE);
  const [parentFilter, setParentFilter] = useState(ALL_VALUE);
  const [keyword, setKeyword] = useState("");
  const [pageNo, setPageNo] = useState(1);
  const [pageSize, setPageSize] = useState(PAGE_SIZE_OPTIONS[0]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [batchSubmitting, setBatchSubmitting] = useState(null);

  // 加载意图树
  const loadIntentTree = async () => {
    try {
      setLoading(true);
      const data = await intentTreeService.getIntentTree();
      setTree(data || []);
    } catch (error) {
      alert(error.response?.data?.message || '加载意图列表失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIntentTree();
  }, []);

  // 解析示例问题（必须在 flattenIntentTree 之前定义）
  const parseExamples = (value) => {
    if (!value) return [];
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) {
        return parsed.map(item => String(item)).filter(Boolean);
      }
    } catch {
      // Ignore
    }
    return value.split("\n").map(item => item.trim()).filter(Boolean);
  };

  // 展平树结构
  const flattenIntentTree = (nodes, parentNames = [], parentCodes = []) => {
    const result = [];
    nodes.forEach((node) => {
      const currentNames = [...parentNames, node.name];
      const currentCodes = [...parentCodes, node.intent_code];
      const children = node.children || [];
      
      result.push({
        id: node.id,
        intent_code: node.intent_code,
        name: node.name,
        level: node.level ?? 0,
        kind: node.kind ?? 0,
        parent_code: node.parent_code,
        description: node.description,
        examples: node.examples,
        collection_name: node.collection_name,
        depth: Math.max(currentNames.length - 1, 0),
        path_text: currentNames.join(" > "),
        path_names: currentNames,
        path_codes: currentCodes,
        child_count: children.length,
        example_count: parseExamples(node.examples).length
      });
      
      result.push(...flattenIntentTree(children, currentNames, currentCodes));
    });
    return result;
  };

  const rows = useMemo(() => flattenIntentTree(tree), [tree]);

  // 获取层级标签
  const resolveLevelLabel = (value) => {
    return LEVEL_OPTIONS.find(option => option.value === value)?.label || "UNKNOWN";
  };

  // 获取类型标签
  const resolveKindLabel = (value) => {
    return KIND_OPTIONS.find(option => option.value === value)?.label || "UNKNOWN";
  };

  // 获取类型徽章样式
  const resolveKindBadge = (value) => {
    const label = resolveKindLabel(value);
    if (label === "SYSTEM") return "bg-slate-100 text-slate-600 border-slate-200";
    return "bg-green-50 text-green-700 border-green-200";
  };

  // 获取层级徽章样式
  const resolveLevelBadgeClass = (value) => {
    if (value === 0) return "border-[#91d5ff] bg-[#e6f7ff] text-[#1890FF]";
    if (value === 1) return "border-[#b7eb8f] bg-[#f6ffed] text-[#52C41A]";
    if (value === 2) return "border-[#ffd591] bg-[#fff7e6] text-[#FA8C16]";
    return "border-slate-200 bg-slate-50 text-slate-600";
  };

  // 父节点选项
  const parentOptions = useMemo(() => {
    return [
      { value: ALL_VALUE, label: "全部父节点" },
      { value: ROOT_VALUE, label: "ROOT（根节点）" },
      ...rows.map(row => ({
        value: row.intent_code,
        label: row.path_text
      }))
    ];
  }, [rows]);

  // 过滤后的数据
  const filteredRows = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();
    return rows.filter(row => {
      // 关键词搜索
      if (normalizedKeyword) {
        const searchable = [row.name, row.intent_code, String(row.id), row.path_text]
          .join(" ")
          .toLowerCase();
        if (!searchable.includes(normalizedKeyword)) {
          return false;
        }
      }

      // 层级筛选
      if (levelFilter !== ALL_VALUE && row.level !== Number(levelFilter)) {
        return false;
      }

      // 类型筛选
      if (kindFilter !== ALL_VALUE && row.kind !== Number(kindFilter)) {
        return false;
      }

      // 父节点筛选
      if (parentFilter !== ALL_VALUE) {
        if (parentFilter === ROOT_VALUE) {
          if (row.parent_code) {
            return false;
          }
        } else if (row.parent_code !== parentFilter) {
          return false;
        }
      }

      return true;
    });
  }, [rows, keyword, levelFilter, kindFilter, parentFilter]);

  // 分页计算
  const total = filteredRows.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(pageNo, totalPages);
  const startIndex = (currentPage - 1) * pageSize;
  const pageRows = filteredRows.slice(startIndex, startIndex + pageSize);
  
  const selectedIdSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const selectedRows = useMemo(() => rows.filter(row => selectedIdSet.has(row.id)), [rows, selectedIdSet]);
  const pageRowIds = useMemo(() => pageRows.map(row => row.id), [pageRows]);
  
  const allPageSelected = pageRowIds.length > 0 && pageRowIds.every(id => selectedIdSet.has(id));
  const somePageSelected = !allPageSelected && pageRowIds.some(id => selectedIdSet.has(id));

  // 自动调整页码
  useEffect(() => {
    if (pageNo !== currentPage) {
      setPageNo(currentPage);
    }
  }, [currentPage, pageNo]);

  // 清理已删除的选中项
  useEffect(() => {
    setSelectedIds(prev => prev.filter(id => rows.some(row => row.id === id)));
  }, [rows]);

  // 重置筛选
  const handleResetFilters = () => {
    setKeyword("");
    setLevelFilter(ALL_VALUE);
    setKindFilter(ALL_VALUE);
    setParentFilter(ALL_VALUE);
    setPageNo(1);
  };

  // 切换行选择
  const toggleRowSelect = (id, checked) => {
    setSelectedIds(prev => {
      if (checked) {
        if (prev.includes(id)) return prev;
        return [...prev, id];
      }
      return prev.filter(item => item !== id);
    });
  };

  // 全选当前页
  const togglePageSelect = (checked) => {
    setSelectedIds(prev => {
      if (checked) {
        const next = new Set(prev);
        pageRowIds.forEach(id => next.add(id));
        return Array.from(next);
      }
      const pageIdSet = new Set(pageRowIds);
      return prev.filter(id => !pageIdSet.has(id));
    });
  };

  // 批量删除
  const runBatchDelete = async () => {
    if (selectedRows.length === 0 || batchSubmitting) return;
    if (!confirm(`确认批量删除 ${selectedRows.length} 个节点？该操作不可恢复。`)) {
      return;
    }
    setBatchSubmitting("delete");
    try {
      const targetIds = selectedRows.map(row => row.id);
      await intentTreeService.batchDeleteNodes(targetIds);
      alert(`已删除 ${targetIds.length} 项`);
      await loadIntentTree();
      setSelectedIds([]);
    } catch (error) {
      alert(error.response?.data?.message || '批量删除失败');
      console.error(error);
    } finally {
      setBatchSubmitting(null);
    }
  };

  // 获取资源文本
  const resolveResourceText = (row) => {
    if (row.kind === 0) {
      return row.collection_name || "-";
    }
    return "系统策略";
  };

  const rangeStart = total === 0 ? 0 : startIndex + 1;
  const rangeEnd = total === 0 ? 0 : Math.min(startIndex + pageRows.length, total);
  const isBatchDisabled = Boolean(batchSubmitting);
  const showPagination = !loading && total > 0;

  return (
    <div className="admin-page">
      {/* 页面标题 */}
      <div className="admin-page-header">
        <div>
          <h1 className="admin-page-title">意图列表</h1>
          <p className="admin-page-subtitle">支持多维筛选、分页查看和快速定位到意图树节点</p>
        </div>
      </div>

      {/* 筛选栏 */}
      <div className="space-y-3">
        <div className="rounded-xl border border-slate-200 bg-white p-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            {/* 搜索框 */}
            <div className="relative w-full lg:min-w-[280px] lg:max-w-[420px] lg:flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={keyword}
                onChange={(e) => {
                  setKeyword(e.target.value);
                  setPageNo(1);
                }}
                placeholder="搜索意图名称/ID..."
                className="w-full pl-10 pr-4 py-2 h-10 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-0 focus:border-slate-200"
              />
            </div>

            {/* 筛选器 */}
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={levelFilter}
                onChange={(e) => {
                  setLevelFilter(e.target.value);
                  setPageNo(1);
                }}
                className="h-10 px-3 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-0 w-[136px]"
              >
                <option value={ALL_VALUE}>全部层级</option>
                {LEVEL_OPTIONS.map(option => (
                  <option key={option.value} value={String(option.value)}>
                    {option.label}
                  </option>
                ))}
              </select>

              <select
                value={kindFilter}
                onChange={(e) => {
                  setKindFilter(e.target.value);
                  setPageNo(1);
                }}
                className="h-10 px-3 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-0 w-[136px]"
              >
                <option value={ALL_VALUE}>全部类型</option>
                {KIND_OPTIONS.map(option => (
                  <option key={option.value} value={String(option.value)}>
                    {option.label}
                  </option>
                ))}
              </select>

              <select
                value={parentFilter}
                onChange={(e) => {
                  setParentFilter(e.target.value);
                  setPageNo(1);
                }}
                className="h-10 px-3 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-0 w-[220px]"
              >
                {parentOptions.map(option => (
                  <option key={option.value} value={option.value} title={option.label}>
                    {option.label.length > 30 ? option.label.substring(0, 30) + "..." : option.label}
                  </option>
                ))}
              </select>

              <button
                onClick={loadIntentTree}
                disabled={loading}
                className="h-10 px-3 gap-1.5 border border-slate-200 rounded-lg text-sm bg-white hover:bg-slate-50 transition-colors flex items-center"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                <span>刷新</span>
              </button>

              <button
                onClick={handleResetFilters}
                className="h-10 px-3 gap-1.5 border border-slate-200 rounded-lg text-sm bg-white hover:bg-slate-50 transition-colors flex items-center"
              >
                <X className="h-4 w-4" />
                <span>清空筛选</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 批量操作栏 */}
      {selectedRows.length > 0 && (
        <div className="-mx-6 mb-3">
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-none border-y border-slate-200/80 bg-slate-50 px-6 py-2">
            <span className="text-sm font-medium text-slate-700">已选 {selectedRows.length} 项</span>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={runBatchDelete}
                disabled={isBatchDisabled}
                className="h-8 px-3 text-xs text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
              >
                批量删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 表格 */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          {loading ? (
            <div className="py-10 text-center text-slate-500">加载中...</div>
          ) : pageRows.length === 0 ? (
            <div className="py-10 text-center text-slate-500">
              {rows.length === 0
                ? "暂无意图节点，请先在意图树配置中创建"
                : "没有匹配结果，请调整筛选条件"}
            </div>
          ) : (
            <table className="w-full min-w-[1280px]">
              <thead className="bg-[#F9FAFB]">
                <tr>
                  <th className="w-[48px] px-4 py-2.5 text-left">
                    <input
                      type="checkbox"
                      checked={allPageSelected ? true : somePageSelected ? false : false}
                      ref={el => {
                        if (el) el.indeterminate = somePageSelected;
                      }}
                      onChange={(e) => togglePageSelect(e.target.checked)}
                      disabled={batchSubmitting !== null || pageRows.length === 0}
                      className="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
                    />
                  </th>
                  <th className="w-[300px] px-4 py-2.5 text-left text-xs font-semibold text-slate-500">意图节点</th>
                  <th className="w-[120px] px-4 py-2.5 text-left text-xs font-semibold text-slate-500">层级</th>
                  <th className="w-[120px] px-4 py-2.5 text-left text-xs font-semibold text-slate-500">类型</th>
                  <th className="w-[320px] px-4 py-2.5 text-left text-xs font-semibold text-slate-500">路径</th>
                  <th className="w-[220px] px-4 py-2.5 text-left text-xs font-semibold text-slate-500">关联资源</th>
                  <th className="w-[90px] px-4 py-2.5 text-left text-xs font-semibold text-slate-500">示例数</th>
                  <th className="sticky right-0 z-20 w-[180px] bg-[#F9FAFB] px-4 py-2.5 text-left text-xs font-semibold text-slate-500 shadow-[-1px_0_0_rgba(226,232,240,1)]">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {pageRows.map(row => (
                  <tr key={row.id} className="group text-[13px] hover:!bg-slate-50 transition-colors">
                    <td className="px-4 py-2">
                      <input
                        type="checkbox"
                        checked={selectedIdSet.has(row.id)}
                        onChange={(e) => toggleRowSelect(row.id, e.target.checked)}
                        disabled={batchSubmitting !== null}
                        className="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
                      />
                    </td>
                    <td className="px-4 py-2">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900">{row.name}</span>
                          <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 font-mono text-xs text-slate-600">
                            {row.intent_code}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-0.5 rounded-full border text-xs font-medium ${resolveLevelBadgeClass(row.level)}`}>
                        {resolveLevelLabel(row.level)}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-0.5 rounded-full border text-xs ${resolveKindBadge(row.kind)}`}>
                        {resolveKindLabel(row.kind)}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <div className="flex flex-wrap items-center gap-1">
                        {row.path_names.map((segment, index) => (
                          <span key={`${row.id}-${segment}-${index}`} className="inline-flex items-center gap-1">
                            {index > 0 ? <span className="text-slate-300">/</span> : null}
                            <button
                              type="button"
                              className={`rounded px-1.5 py-0.5 text-xs transition-colors ${
                                index === row.path_names.length - 1
                                  ? "bg-slate-100 text-slate-600 font-medium hover:bg-slate-200"
                                  : "text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                              }`}
                              onClick={() =>
                                navigate(`/admin/intent-tree?intentCode=${encodeURIComponent(row.path_codes[index])}`)
                              }
                            >
                              {segment}
                            </button>
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-2">
                      <div className="truncate text-sm text-slate-700" title={resolveResourceText(row)}>
                        {resolveResourceText(row)}
                      </div>
                    </td>
                    <td className="px-4 py-2">
                      <span className="font-medium text-slate-700">{row.example_count}</span>
                    </td>
                    <td className="sticky right-0 z-10 bg-white px-4 py-2 shadow-[-1px_0_0_rgba(226,232,240,1)] group-hover:bg-slate-50">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() =>
                            navigate(`/admin/intent-list/${row.id}/edit?from=${encodeURIComponent(
                              `${location.pathname}${location.search}`
                            )}`)
                          }
                          className="h-8 px-2.5 text-xs border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors flex items-center gap-1 whitespace-nowrap"
                        >
                          <Pencil className="h-4 w-4" />
                          <span>编辑</span>
                        </button>
                        <button
                          onClick={() =>
                            navigate(`/admin/intent-tree?intentCode=${encodeURIComponent(row.intent_code)}`)
                          }
                          className="h-8 px-2.5 text-xs hover:bg-slate-100 transition-colors flex items-center gap-1 whitespace-nowrap"
                        >
                          <GitBranch className="h-4 w-4" />
                          <span>定位树</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* 分页 */}
      {showPagination && (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-sm text-slate-500">
          <span>共 {total} 条，显示 {rangeStart}-{rangeEnd}</span>
          <div className="flex flex-wrap items-center gap-2">
            <span>每页</span>
            <select
              value={String(pageSize)}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPageNo(1);
              }}
              className="h-8 px-2 text-sm border border-slate-200 rounded-lg focus:outline-none w-[92px]"
            >
              {PAGE_SIZE_OPTIONS.map(size => (
                <option key={size} value={String(size)}>
                  {size} 条
                </option>
              ))}
            </select>
            <button
              onClick={() => setPageNo(1)}
              disabled={currentPage <= 1}
              className="px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              首页
            </button>
            <button
              onClick={() => setPageNo(prev => Math.max(1, prev - 1))}
              disabled={currentPage <= 1}
              className="px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              上一页
            </button>
            <span className="px-2">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setPageNo(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage >= totalPages}
              className="px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              下一页
            </button>
            <button
              onClick={() => setPageNo(totalPages)}
              disabled={currentPage >= totalPages}
              className="px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              末页
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
