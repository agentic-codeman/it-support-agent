"""
意图节点注册表服务
管理意图树的加载、缓存和查询
"""
import json
import time
from typing import List, Optional, Dict
from backend.schemas.intent import IntentNode
from backend.models.intent_node import IntentNodeModel
from backend.db.database import get_db_session
from backend.client.redis_client import get_redis_client

from backend.core.logger import logger

INTENT_TREE_CACHE_KEY = "ragent:intent:tree"
CACHE_EXPIRE_SECONDS = 7 * 24 * 60 * 60


def get_node_by_id(node_id: str) -> Optional[IntentNode]:
    """根据 ID 获取意图节点

    Args:
        node_id: 节点 ID

    Returns:
        Optional[IntentNode]: 意图节点，不存在则返回 None
    """
    _, _, id_to_node = load_intent_tree_data()
    return id_to_node.get(node_id)


def get_all_nodes() -> List[IntentNode]:
    """获取所有意图节点

    Returns:
        List[IntentNode]: 所有节点列表
    """
    all_nodes, _, _ = load_intent_tree_data()
    return all_nodes


def get_leaf_nodes() -> List[IntentNode]:
    """获取所有叶子节点（用于意图分类）

    Returns:
        List[IntentNode]: 叶子节点列表
    """
    _, leaf_nodes, _ = load_intent_tree_data()
    return leaf_nodes


def get_roots() -> List[IntentNode]:
    """获取根节点列表

    Returns:
        List[IntentNode]: 根节点列表
    """
    # 需要从完整数据中提取根节点
    all_nodes, _, id_to_node = load_intent_tree_data()
    roots = [node for node in all_nodes if node.parent_id is None or node.parent_id not in id_to_node]
    return roots


def _load_intent_tree_from_db() -> List[IntentNode]:
    """从数据库加载意图树

    核心逻辑：
    1. 查出所有未删除节点（扁平结构）
    2. DO -> IntentNode（第一遍：先把所有节点建出来，放到 map 里）
    3. 第二遍：根据 parentId 组装 parent -> children
    4. 填充 fullPath

    Returns:
        List[IntentNode]: 根节点列表
    """
    try:
        # 步骤1：查出所有未删除节点（扁平结构）
        with get_db_session() as session:
            from sqlalchemy import select
            stmt = select(IntentNodeModel).where(IntentNodeModel.deleted == 0)
            result = session.execute(stmt)
            intent_node_models = result.scalars().all()

            # 在会话内提前获取所有需要的属性，避免 DetachedInstanceError
            models_data = []
            for model in intent_node_models:
                models_data.append({
                    'id': model.id,
                    'intent_code': model.intent_code,
                    'name': model.name,
                    'level': model.level,
                    'kb_id': model.kb_id,
                    'parent_code': model.parent_code,
                    'description': model.description,
                    'examples': model.examples,
                    'collection_name': model.collection_name,
                    'kind': model.kind,  # 添加 kind 字段
                })

        if not models_data:
            logger.info("数据库中未找到任何意图节点")
            return []

        logger.info(f"从数据库加载了 {len(models_data)} 个意图节点")

        # 步骤2：DO -> IntentNode（第一遍：先把所有节点建出来，放到 map 里）
        id_to_node: Dict[str, IntentNode] = {}
        for data in models_data:
            # 解析 examples JSON 字符串
            examples = []
            if data['examples']:
                try:
                    examples = json.loads(data['examples'])
                except (json.JSONDecodeError, TypeError):
                    # 如果不是 JSON 格式，尝试按逗号分割
                    examples = [e.strip() for e in data['examples'].split(',') if e.strip()]

            kind_map = {0: 'KB', 1: 'SYSTEM'}
            kind = kind_map.get(data['kind'], 'KB')

            node = IntentNode(
                id=data['intent_code'],  # ← 关键：使用 intent_code 作为 ID
                name=data['name'],
                kind=kind,
                level=data['level'],  # ← 添加 level 字段
                kb_id=data['kb_id'],
                parent_id=data['parent_code'],  # ← 关键：使用 parent_code 作为 parent_id
                description=data['description'] or '',
                examples=examples,
                collection_name=data['collection_name'],
                children=[]  # ← 确保 children 不为 None
            )
            id_to_node[node.id] = node

        # 步骤3：第二遍：根据 parentId 组装 parent -> children
        roots = []
        for node in id_to_node.values():
            parent_id = node.parent_id
            if parent_id is None or parent_id.strip() == '':
                # 没有 parentId，当作根节点
                roots.append(node)
                continue

            parent = id_to_node.get(parent_id)
            if parent is None:
                # 找不到父节点，兜底也当作根节点，避免节点丢失
                logger.warning(f"节点 {node.id} 的父节点 {parent_id} 不存在，将其作为根节点")
                roots.append(node)
                continue

            # 追加到父节点的 children
            if parent.children is None:
                parent.children = []
            parent.children.append(node)

        _fill_full_path(roots, None)

        logger.info(f"意图树从数据库加载完成: 总节点数={len(id_to_node)}, 根节点数={len(roots)}")

        return roots

    except Exception as e:
        logger.exception(f"从数据库加载意图树失败: {e}")
        return []


def load_intent_tree_data():
    """从Redis加载意图树并构建内存结构

    核心逻辑：
    1. 从Redis读取（如果不存在会自动从数据库加载）
    2. 如果Redis也没有，从数据库加载并缓存
    3. 构建内存结构并返回三元组，调用方应加载一次后向下传递复用

    Returns:
        Tuple[List[IntentNode], List[IntentNode], Dict[str, IntentNode]]:
            (all_nodes, leaf_nodes, id_to_node) 三元组
    """
    try:
        # 步骤1：从Redis读取
        roots = _get_intent_tree_from_cache()

        if not roots:
            logger.info("Redis 缓存为空，尝试从数据库加载意图树")
            roots = _load_intent_tree_from_db()
            if roots:
                logger.info(f"从数据库加载了 {len(roots)} 个根节点，保存到 Redis 缓存")
                save_intent_tree_to_cache(roots)

        # 步骤3：构建内存结构（临时使用）
        if not roots:
            logger.warning("意图树数据为空（Redis 和数据库均无数据）")
            return [], [], {}

        all_nodes = _flatten(roots)

        leaf_nodes = [n for n in all_nodes if n.is_leaf()]

        id_to_node = {node.id: node for node in all_nodes}

        logger.debug(
            f"意图树数据加载完成, 总节点数: {len(all_nodes)}, "
            f"叶子节点数: {len(leaf_nodes)}"
        )

        return all_nodes, leaf_nodes, id_to_node

    except Exception as e:
        logger.exception(f"加载意图树数据失败: {e}")
        # 失败时返回空数据
        return [], [], {}


def _get_intent_tree_from_cache() -> List[IntentNode]:
    """从Redis获取意图树缓存

    Returns:
        List[IntentNode]: 意图树根节点列表，如果缓存不存在则返回空列表
    """
    redis_client = get_redis_client().get_raw_client()
    if not redis_client:
        logger.warning("Redis 客户端未配置，无法从缓存加载意图树")
        return []

    try:
        cache_json = redis_client.get(INTENT_TREE_CACHE_KEY)
        if cache_json is None:
            logger.info("意图树缓存不存在，需要从数据库加载")
            return []

        # 反序列化 JSON
        if isinstance(cache_json, bytes):
            cache_json = cache_json.decode('utf-8')

        roots_data = json.loads(cache_json)

        # 从扁平数据构建树形结构
        return build_tree_from_flat_nodes(roots_data)

    except Exception as e:
        logger.exception(f"从Redis读取意图树缓存失败: {e}")
        return []


def save_intent_tree_to_cache(roots: List[IntentNode]):
    """将意图树保存到Redis缓存

    Args:
        roots: 意图树根节点列表
    """
    redis_client = get_redis_client().get_raw_client()
    if not redis_client:
        logger.warning("Redis 客户端未配置，无法保存意图树到缓存")
        return

    try:
        # 将树形结构展平为列表
        flat_nodes = _flatten_to_list(roots)

        # 序列化为 JSON
        cache_json = json.dumps(flat_nodes, ensure_ascii=False)

        redis_client.setex(INTENT_TREE_CACHE_KEY, CACHE_EXPIRE_SECONDS, cache_json)

        logger.info(f"意图树已保存到 Redis 缓存，节点数: {len(flat_nodes)}")

    except Exception as e:
        logger.exception(f"保存意图树到 Redis 缓存失败: {e}")


def clear_intent_tree_cache():
    """清除Redis缓存"""
    redis_client = get_redis_client().get_raw_client()
    if not redis_client:
        return

    try:
        redis_client.delete(INTENT_TREE_CACHE_KEY)
        logger.info("意图树缓存已清除")
    except Exception as e:
        logger.exception(f"清除意图树缓存失败: {e}")


def _flatten(roots: List[IntentNode]) -> List[IntentNode]:
    """展平树结构为列表

    Args:
        roots: 根节点列表

    Returns:
        List[IntentNode]: 所有节点的扁平列表
    """
    result = []
    stack = list(roots)

    while stack:
        node = stack.pop()
        result.append(node)
        if node.children:
            # 逆序压栈，保证顺序一致
            for child in reversed(node.children):
                stack.append(child)

    return result


def _flatten_to_list(roots: List[IntentNode]) -> List[Dict]:
    """将树形结构展平为字典列表（用于序列化）

    Args:
        roots: 根节点列表

    Returns:
        List[Dict]: 扁平的节点字典列表
    """
    all_nodes = _flatten(roots)

    flat_nodes = []
    for node in all_nodes:
        flat_nodes.append({
            'id': node.id,
            'name': node.name,
            'kind': node.kind,
            'level': node.level,  # ← 添加 level 字段
            'kb_id': node.kb_id,
            'parent_id': node.parent_id,
            'description': node.description,
            'examples': node.examples,
            'collection_name': node.collection_name,
        })

    return flat_nodes


def build_tree_from_flat_nodes(flat_nodes: List[Dict]) -> List[IntentNode]:
    """从扁平节点列表构建树形结构

    Args:
        flat_nodes: 扁平节点列表，每个节点包含 id, parent_id 等字段

    Returns:
        List[IntentNode]: 根节点列表
    """
    # 第一遍：创建所有节点
    id_to_node: Dict[str, IntentNode] = {}
    for node_data in flat_nodes:
        node = IntentNode(
            id=node_data['id'],
            name=node_data['name'],
            kind=node_data.get('kind', 'KB'),
            level=node_data.get('level', 0),  # ← 添加 level 字段
            kb_id=node_data.get('kb_id'),
            parent_id=node_data.get('parent_id'),
            description=node_data.get('description', ''),
            examples=node_data.get('examples', []),
            collection_name=node_data.get('collection_name'),
            children=[]
        )
        id_to_node[node.id] = node

    # 第二遍：组装父子关系
    roots = []
    for node in id_to_node.values():
        if node.parent_id is None or node.parent_id not in id_to_node:
            # 没有父节点或父节点不存在，作为根节点
            roots.append(node)
        else:
            # 添加到父节点的 children
            parent = id_to_node[node.parent_id]
            parent.children.append(node)

    # 第三遍：填充 full_path
    _fill_full_path(roots, None)

    logger.info(f"意图树构建完成: 总节点数={len(id_to_node)}, "
               f"根节点数={len(roots)}, 叶子节点数={len([n for n in id_to_node.values() if n.is_leaf()])}")

    return roots


def _fill_full_path(nodes: List[IntentNode], parent: Optional[IntentNode]):
    """填充 full_path 字段

    Args:
        nodes: 节点列表
        parent: 父节点
    """
    if not nodes:
        return

    for node in nodes:
        if parent is None:
            node.full_path = node.name
        else:
            node.full_path = f"{parent.full_path} > {node.name}"

        if node.children:
            _fill_full_path(node.children, node)


def format_leaf_nodes_for_prompt(leaf_nodes: List[IntentNode]) -> str:
    """格式化叶子节点列表用于提示词

    Args:
        leaf_nodes: 叶子节点列表（由调用方加载一次后传入，避免重复读 Redis）

    Returns:
        str: 格式化的节点列表字符串
    """
    sb = []

    for node in leaf_nodes:
        # 直接使用字符串拼接，避免 f-string 与 LangChain 模板变量冲突
        sb.append("- id=" + str(node.id) + "\n")
        sb.append("  path=" + str(node.full_path) + "\n")
        sb.append("  description=" + str(node.description) + "\n")

        # 添加节点类型标识
        if node.is_system():
            sb.append("  type=SYSTEM\n")
        else:
            sb.append("  type=KB\n")

        # 添加示例问题
        if node.examples:
            examples_str = ' / '.join(node.examples)
            sb.append("  examples=" + examples_str + "\n")

        sb.append("\n")

    result = "".join(sb)
    logger.debug(f"格式化后的意图列表:\n{result}")
    return result
