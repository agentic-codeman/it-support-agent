import { useState, useEffect, useMemo } from "react";
import { ChevronDown, ChevronRight, Pencil, Plus, RefreshCw, Trash2, XCircle } from "lucide-react";
import { intentTreeService } from "../../services/intentTreeService";
import { getKnowledgeBases } from "../../services/knowledgeService";

const LEVEL_OPTIONS = [
  { value: 0, label: "DOMAIN", description: "顶层领域" },
  { value: 1, label: "CATEGORY", description: "业务分类" },
  { value: 2, label: "TOPIC", description: "具体主题" }
];

const KIND_OPTIONS = [
  { value: 0, label: "KB", description: "知识库检索" },
  { value: 1, label: "SYSTEM", description: "系统交互" }
];

const ROOT_PARENT = "__ROOT__";

/**
 * 递归构建树形选项列表（用于父节点下拉框）
 */
const buildTreeOptions = (nodes, prefix = "", depth = 0, result = []) => {
  nodes.forEach((node) => {
    const label = prefix ? `${prefix} > ${node.name}` : node.name;
    result.push({ label, value: node.intent_code, node, depth });
    if (node.children && node.children.length > 0) {
      buildTreeOptions(node.children, label, depth + 1, result);
    }
  });
  return result;
};

/**
 * 意图树配置页面
 */
export default function IntentTreePage() {
  const [tree, setTree] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCode, setSelectedCode] = useState(null);
  const [expandedMap, setExpandedMap] = useState({});
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState("create");
  const [dialogParent, setDialogParent] = useState(null);
  const [editingNode, setEditingNode] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [knowledgeBases, setKnowledgeBases] = useState([]);

  // 构建树形选项列表
  const treeOptions = useMemo(() => buildTreeOptions(tree), [tree]);

  // 加载意图树
  const loadTree = async () => {
    try {
      setLoading(true);
      const data = await intentTreeService.getIntentTree();
      setTree(data || []);
      if (data && data.length > 0 && !selectedCode) {
        setSelectedCode(data[0].intent_code);
      }
    } catch (error) {
      alert(error.response?.data?.message || '加载意图树失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 加载知识库列表（用于 KB 类型节点的下拉选择）
  const loadKnowledgeBases = async () => {
    try {
      const data = await getKnowledgeBases();
      setKnowledgeBases(data || []);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    loadTree();
    loadKnowledgeBases();
  }, []);

  // 查找节点
  const findNodeByCode = (nodes, code) => {
    if (!code) return null;
    for (const node of nodes) {
      if (node.intent_code === code) return node;
      if (node.children && node.children.length > 0) {
        const found = findNodeByCode(node.children, code);
        if (found) return found;
      }
    }
    return null;
  };

  const selectedNode = useMemo(() => findNodeByCode(tree, selectedCode), [tree, selectedCode]);

  // 解析示例问题
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

  // 获取层级标签
  const resolveLevelLabel = (value) => {
    return LEVEL_OPTIONS.find(option => option.value === (value ?? 0))?.label || "UNKNOWN";
  };

  // 获取类型标签
  const resolveKindLabel = (value) => {
    return KIND_OPTIONS.find(option => option.value === (value ?? 0))?.label || "UNKNOWN";
  };

  // 打开创建对话框
  const openCreateDialog = (parent) => {
    setDialogMode("create");
    setDialogParent(parent || null);
    setEditingNode(null);
    setDialogOpen(true);
  };

  // 打开编辑对话框
  const openEditDialog = (node) => {
    setDialogMode("edit");
    setEditingNode(node);
    setDialogParent(null);
    setDialogOpen(true);
  };

  // 删除节点
  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await intentTreeService.deleteIntentNode(deleteTarget.id);
      alert('删除成功');
      await loadTree();
    } catch (error) {
      alert(error.response?.data?.message || '删除失败');
      console.error(error);
    } finally {
      setDeleteTarget(null);
    }
  };

  // 渲染树节点
  const renderNode = (node, depth = 0) => {
    const hasChildren = Boolean(node.children && node.children.length > 0);
    const isExpanded = expandedMap[node.intent_code] !== false;
    const isSelected = selectedCode === node.intent_code;

    return (
      <div key={node.intent_code}>
        <div
          className={`group flex cursor-pointer items-center justify-between rounded-xl px-3 py-2 transition-colors ${
            isSelected ? "bg-slate-100 text-slate-900" : "hover:bg-slate-50"
          }`}
          style={{ paddingLeft: `${depth * 16 + 12}px` }}
          onClick={() => setSelectedCode(node.intent_code)}
        >
          <div className="flex items-center gap-2">
            {hasChildren ? (
              <button
                type="button"
                className="flex h-5 w-5 items-center justify-center rounded-md text-muted-foreground hover:text-foreground"
                onClick={(event) => {
                  event.stopPropagation();
                  setExpandedMap(prev => ({
                    ...prev,
                    [node.intent_code]: !isExpanded
                  }));
                }}
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </button>
            ) : (
              <span className="h-5 w-5" />
            )}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-foreground">{node.name}</span>
              <span className="px-2 py-0.5 rounded-full border border-slate-200 bg-slate-100 text-xs text-slate-600">
                {resolveLevelLabel(node.level)}
              </span>
              <span className="px-2 py-0.5 rounded-full border border-slate-200 bg-slate-100 text-xs text-slate-600">
                {resolveKindLabel(node.kind)}
              </span>
            </div>
          </div>
          <div className="hidden items-center gap-2 text-xs text-muted-foreground group-hover:flex">
            <span className="truncate">{node.intent_code}</span>
          </div>
        </div>
        {hasChildren && isExpanded
          ? node.children?.map(child => renderNode(child, depth + 1))
          : null}
      </div>
    );
  };

  return (
    <div className="admin-page">
      {/* 页面标题和操作栏 */}
      <div className="admin-page-header">
        <div>
          <h1 className="admin-page-title">意图树配置</h1>
          <p className="admin-page-subtitle">配置意图层级、类型和节点关系</p>
        </div>
        <div className="admin-page-actions">
          <button
            onClick={loadTree}
            className="flex items-center gap-2 px-6 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            <span>刷新</span>
          </button>
          <button
            onClick={() => openCreateDialog(null)}
            className="admin-primary-gradient flex items-center gap-2 px-6 py-2 rounded-lg text-sm font-medium"
          >
            <Plus className="w-4 h-4 mr-2" />
            <span>新建根节点</span>
          </button>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        {/* 左侧：意图树结构 */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="px-6 pt-5 pb-4 border-b border-slate-100">
            <h2 className="text-base font-semibold text-slate-900">意图树结构</h2>
            <p className="text-sm text-slate-500 mt-1">点击节点查看详情或进行编辑</p>
          </div>
          <div className="p-4 space-y-2 max-h-[calc(100vh-300px)] overflow-y-auto">
            {loading ? (
              <div className="py-10 text-center text-slate-500">加载中...</div>
            ) : tree.length === 0 ? (
              <div className="py-10 text-center text-slate-500">暂无节点，请先创建</div>
            ) : (
              tree.map(node => renderNode(node))
            )}
          </div>
        </div>

        {/* 右侧：节点详情 */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="px-6 pt-5 pb-4 border-b border-slate-100">
            <h2 className="text-base font-semibold text-slate-900">节点详情</h2>
            <p className="text-sm text-slate-500 mt-1">查看并管理当前选择的节点</p>
          </div>
          <div className="p-6">
            {!selectedNode ? (
              <div className="py-10 text-center text-slate-500">请选择左侧节点</div>
            ) : (
              <div className="space-y-4">
                {/* 节点头部 */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-lg font-semibold text-slate-900">{selectedNode.name}</h3>
                      <span className="px-2 py-0.5 rounded-full border border-slate-200 bg-slate-100 text-xs text-slate-600">
                        {resolveLevelLabel(selectedNode.level)}
                      </span>
                      <span className="px-2 py-0.5 rounded-full border border-slate-200 bg-slate-100 text-xs text-slate-600">
                        {resolveKindLabel(selectedNode.kind)}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">{selectedNode.intent_code}</p>
                  </div>
                  <div className="flex flex-col gap-2">
                    <button
                      onClick={() => openCreateDialog(selectedNode)}
                      className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm"
                    >
                      <Plus className="w-4 h-4" />
                      <span>新建子节点</span>
                    </button>
                    <button
                      onClick={() => openEditDialog(selectedNode)}
                      className="flex items-center gap-2 px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors text-sm text-slate-600"
                    >
                      <Pencil className="w-4 h-4" />
                      <span>编辑节点</span>
                    </button>
                    <button
                      onClick={() => setDeleteTarget(selectedNode)}
                      className="flex items-center gap-2 px-4 py-2 border border-red-200 rounded-lg hover:bg-red-50 transition-colors text-sm text-red-600"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span>删除节点</span>
                    </button>
                  </div>
                </div>

                {/* 节点信息 */}
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">父节点</span>
                    <span>{selectedNode.parent_code || "ROOT"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Collection</span>
                    <span>{selectedNode.collection_name || "-"}</span>
                  </div>
                </div>

                {/* 描述 */}
                <div>
                  <p className="text-sm font-medium text-slate-900">描述</p>
                  <p className="mt-1 text-sm text-slate-500">
                    {selectedNode.description || "暂无描述"}
                  </p>
                </div>

                {/* 示例问题 */}
                <div>
                  <p className="text-sm font-medium text-slate-900">示例问题</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(() => {
                      const examples = parseExamples(selectedNode.examples);
                      if (examples.length === 0) {
                        return <span className="text-sm text-slate-500">暂无示例</span>;
                      }
                      return examples.map((item, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 rounded-full bg-slate-100 text-xs text-slate-600"
                        >
                          {item}
                        </span>
                      ));
                    })()}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 删除确认对话框 */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-slate-900 mb-2">确认删除节点？</h3>
            <p className="text-slate-600 mb-6">
              节点 [{deleteTarget.name}] 将被永久删除，无法恢复。
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 创建/编辑对话框 */}
      {dialogOpen && (
        <IntentNodeDialog
          open={dialogOpen}
          mode={dialogMode}
          parentNode={dialogParent}
          node={editingNode}
          treeOptions={treeOptions}
          knowledgeBases={knowledgeBases}
          onClose={() => {
            setDialogOpen(false);
            setEditingNode(null);
            setDialogParent(null);
          }}
          onSuccess={() => {
            setDialogOpen(false);
            setEditingNode(null);
            setDialogParent(null);
            loadTree();
          }}
        />
      )}
    </div>
  );
}

/**
 * 意图节点对话框组件
 */
function IntentNodeDialog({ open, mode, parentNode, node, treeOptions, knowledgeBases, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    intent_code: '',
    level: 0,
    kind: 0,
    parent_code: ROOT_PARENT,
    kb_id: '',
    collection_name: '',
    description: '',
    examples_text: ''
  });
  const [submitting, setSubmitting] = useState(false);

  // 构建父节点选项（编辑模式下排除当前节点，防止自引用）
  const parentOptions = useMemo(() => {
    const filtered = mode === 'edit' && node
      ? treeOptions.filter(item => item.value !== node.intent_code)
      : treeOptions;
    const rootOption = { label: 'ROOT', value: ROOT_PARENT, depth: 0 };
    return [rootOption, ...filtered];
  }, [mode, node, treeOptions]);

  // 初始化表单数据
  useEffect(() => {
    if (mode === "edit" && node) {
      const examples = parseExamplesForEdit(node.examples);
      setFormData({
        name: node.name || '',
        intent_code: node.intent_code || '',
        level: node.level ?? 0,
        kind: node.kind ?? 0,
        parent_code: node.parent_code || ROOT_PARENT,
        kb_id: '',
        collection_name: node.collection_name || '',
        description: node.description || '',
        examples_text: examples
      });
    } else {
      // 创建模式：根据父节点设置默认值
      const nextLevel = parentNode ? Math.min((parentNode.level ?? 0) + 1, 2) : 0;
      const parentKind = parentNode?.kind ?? 0;

      setFormData({
        name: '',
        intent_code: '',
        level: nextLevel,
        kind: parentKind,
        parent_code: parentNode?.intent_code || ROOT_PARENT,
        kb_id: '',
        collection_name: '',
        description: '',
        examples_text: ''
      });
    }
  }, [mode, node, parentNode]);

  // 解析示例问题用于编辑
  const parseExamplesForEdit = (value) => {
    if (!value) return '';
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) {
        return parsed.join('\n');
      }
    } catch {
      // Ignore
    }
    return value;
  };

  // 解析示例问题
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

  // 提交表单
  const handleSubmit = async () => {
    // 验证
    if (!formData.name.trim()) {
      alert('请输入节点名称');
      return;
    }
    if (!formData.intent_code.trim()) {
      alert('请输入意图标识');
      return;
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(formData.intent_code)) {
      alert('意图标识仅支持字母、数字、-和_');
      return;
    }

    const parentCode = formData.parent_code === ROOT_PARENT ? null : formData.parent_code;
    const examples = formData.examples_text
      ? formData.examples_text.split("\n").map(item => item.trim()).filter(Boolean)
      : [];

    // KB 节点（TOPIC 层级）必须选择知识库
    if (mode === "create" && formData.kind === 0 && formData.level === 2 && !formData.kb_id) {
      alert('TOPIC 节点请选择知识库');
      return;
    }

    try {
      setSubmitting(true);

      if (mode === "create") {
        const payload = {
          kb_id: formData.kind === 0 ? formData.kb_id : undefined,
          intent_code: formData.intent_code.trim(),
          name: formData.name.trim(),
          level: formData.level,
          parent_code: parentCode,
          description: formData.description?.trim() || undefined,
          examples: examples.length > 0 ? examples : undefined,
          kind: formData.kind
        };
        await intentTreeService.createIntentNode(payload);
        alert('创建成功');
      } else if (node) {
        const payload = {
          name: formData.name.trim(),
          level: formData.level,
          parent_code: parentCode,
          description: formData.description?.trim() || undefined,
          examples: examples.length > 0 ? examples : undefined,
          collection_name: formData.kind === 0 ? formData.collection_name?.trim() || undefined : undefined,
          kind: formData.kind
        };
        await intentTreeService.updateIntentNode(node.id, payload);
        alert('更新成功');
      }
      
      onSuccess();
    } catch (error) {
      alert(error.response?.data?.message || (mode === "create" ? '创建失败' : '更新失败'));
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-[#F8F9FB] rounded-3xl p-8 max-w-3xl w-full mx-4 shadow-xl max-h-[85vh] overflow-y-auto">
        {/* 对话框头部 */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-slate-900">
              {mode === "create" ? "新建意图节点" : "编辑意图节点"}
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              {mode === "create" ? "配置意图节点的层级、类型与描述信息" : "更新节点基础信息"}
            </p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <XCircle className="w-6 h-6" />
          </button>
        </div>

        {/* 表单内容 */}
        <div className="space-y-5">
          {/* 基本信息 */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-base font-medium text-slate-900 mb-2">
                节点名称 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="例如：OA系统"
                className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm"
              />
            </div>

            <div>
              <label className="block text-base font-medium text-slate-900 mb-2">
                意图标识 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.intent_code}
                onChange={(e) => setFormData({ ...formData, intent_code: e.target.value })}
                placeholder="例如：biz-oa"
                disabled={mode === "edit"}
                className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm disabled:bg-slate-100"
              />
            </div>
          </div>

          {/* 层级和类型 */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-base font-medium text-slate-900 mb-2">层级</label>
              <div className="relative">
                <select
                  value={formData.level}
                  onChange={(e) => setFormData({ ...formData, level: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm appearance-none bg-white"
                >
                  {LEVEL_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label} - {opt.description}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                  </svg>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-base font-medium text-slate-900 mb-2">类型</label>
              <div className="relative">
                <select
                  value={formData.kind}
                  onChange={(e) => setFormData({ ...formData, kind: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm appearance-none bg-white"
                >
                  {KIND_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label} - {opt.description}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* 父节点 */}
          <div>
            <label className="block text-base font-medium text-slate-900 mb-2">父节点</label>
            <div className="relative">
              <select
                value={formData.parent_code}
                onChange={(e) => setFormData({ ...formData, parent_code: e.target.value })}
                className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm appearance-none bg-white"
              >
                {parentOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </div>
            </div>
          </div>

          {/* 知识库选择（创建模式下 KB 类型显示） */}
          {mode === "create" && formData.kind === 0 && (
            <div>
              <label className="block text-base font-medium text-slate-900 mb-2">
                知识库{formData.level === 2 ? "（必填）" : "（可选）"}
              </label>
              <div className="relative">
                <select
                  value={formData.kb_id}
                  onChange={(e) => setFormData({ ...formData, kb_id: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm appearance-none bg-white"
                >
                  <option value="">请选择知识库</option>
                  {knowledgeBases.map((kb) => (
                    <option key={kb.id} value={kb.id}>
                      {kb.name} ({kb.collection_name})
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                  </svg>
                </div>
              </div>
            </div>
          )}

          {/* Collection 名称（编辑模式下 KB 类型显示） */}
          {mode === "edit" && formData.kind === 0 && (
            <div>
              <label className="block text-base font-medium text-slate-900 mb-2">
                Collection 名称
              </label>
              <input
                type="text"
                value={formData.collection_name}
                onChange={(e) => setFormData({ ...formData, collection_name: e.target.value })}
                placeholder="向量数据库 Collection 名称"
                className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm"
              />
            </div>
          )}

          {/* 描述与示例 */}
          <details className="rounded-lg border px-4 py-3" open>
            <summary className="cursor-pointer text-sm font-medium text-slate-900">
              描述与示例
            </summary>
            <div className="mt-3 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-900 mb-2">描述</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="节点的语义说明与应用场景"
                  rows={3}
                  className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-900 mb-2">示例问题</label>
                <textarea
                  value={formData.examples_text}
                  onChange={(e) => setFormData({ ...formData, examples_text: e.target.value })}
                  placeholder="每行一个示例问题"
                  rows={3}
                  className="w-full px-4 py-3 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm resize-none"
                />
              </div>
            </div>
          </details>

        </div>

        {/* 对话框底部按钮 */}
        <div className="flex justify-end gap-4 mt-8">
          <button
            onClick={onClose}
            className="px-8 py-2.5 border border-slate-200 rounded-2xl hover:bg-slate-50 transition-colors text-sm font-medium text-slate-700"
            disabled={submitting}
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            className="px-8 py-2.5 bg-indigo-600 text-white rounded-2xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium shadow-md shadow-indigo-200"
            disabled={submitting}
          >
            {submitting ? (mode === "create" ? "创建中..." : "保存中...") : mode === "create" ? "创建" : "保存"}
          </button>
        </div>
      </div>
    </div>
  );
}
