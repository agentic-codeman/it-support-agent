"""
意图节点服务层
"""
import json
from typing import List, Dict
from sqlalchemy.orm import Session

from backend.models.intent_node import IntentNodeModel
from backend.schemas.intent_node import (
    IntentNodeCreateRequest,
    IntentNodeUpdateRequest,
    IntentNodeTreeResponse
)
from backend.crud import crud_intent_node
from backend.crud import crud_knowledge_base
from backend.services.intent_node_registry import clear_intent_tree_cache
from backend.utils.snowflake_id_utils import generate_snowflake_id_str
from backend.utils.exceptions import ClientException

from backend.core.logger import logger


def get_intent_tree(db: Session) -> List[IntentNodeTreeResponse]:
    """获取意图树结构

    Args:
        db: 数据库会话

    Returns:
        List[IntentNodeTreeResponse]: 根节点列表（包含子节点）
    """
    try:
        models = crud_intent_node.list_all(db)

        if not models:
            return []

        # 构建 intent_code 到节点的映射（关键修复：用 code 而非 id 作为键）
        code_to_node: Dict[str, IntentNodeTreeResponse] = {}
        for model in models:
            node = _model_to_tree_response(model)
            code_to_node[node.intent_code] = node

        # 组装树结构
        roots = []
        for node in code_to_node.values():
            parent_code = node.parent_code
            if not parent_code or parent_code not in code_to_node:
                # 没有父节点或父节点不存在，作为根节点
                roots.append(node)
            else:
                # 添加到父节点的 children
                parent = code_to_node[parent_code]
                if parent.children is None:
                    parent.children = []
                parent.children.append(node)

        # 按名称排序
        roots.sort(key=lambda x: x.name or "")
        _sort_children(roots)

        return roots

    except Exception as e:
        logger.exception(f"获取意图树失败: {e}")
        raise ClientException(f"获取意图树失败: {str(e)}")


def create_node(db: Session, request: IntentNodeCreateRequest, username: str) -> str:
    """创建意图节点

    Args:
        db: 数据库会话
        request: 创建请求
        username: 用户名

    Returns:
        str: 新创建的节点ID
    """
    try:
        # 检查 intent_code 是否已存在
        if crud_intent_node.get_by_code(db, request.intent_code):
            raise ClientException(f"意图标识已存在: {request.intent_code}")

        # TOPIC 级别的 RAG 检索节点必须指定目标知识库
        # level 2=TOPIC, kind 0=KB
        if request.level == 2 and request.kind == 0 and not request.kb_id:
            raise ClientException("TOPIC级别的RAG检索节点必须指定目标知识库")

        # 如果指定了父节点，检查父节点是否存在
        if request.parent_code:
            if not crud_intent_node.get_by_code(db, request.parent_code):
                raise ClientException(f"父节点 '{request.parent_code}' 不存在")

        # 转换 examples 为 JSON 字符串
        examples_json = None
        if request.examples:
            examples_json = json.dumps(request.examples, ensure_ascii=False)

        # 创建时若选择了知识库，自动回填 collection_name（查询时实际使用该字段）
        kb_id = request.kb_id or None
        collection_name = None
        if kb_id:
            kb = crud_knowledge_base.get_by_id(db, kb_id)
            if kb:
                collection_name = kb.collection_name

        # 创建节点
        node_id = generate_snowflake_id_str()
        model = IntentNodeModel(
            id=node_id,
            kb_id=kb_id,
            intent_code=request.intent_code,
            name=request.name,
            level=request.level,
            parent_code=request.parent_code,
            description=request.description,
            examples=examples_json,
            collection_name=collection_name,
            kind=request.kind or 0,
            create_by=username,
            update_by=username,
            deleted=0
        )

        crud_intent_node.create(db, model)
        db.commit()

        # 清除 Redis 缓存，下次读取时重新从数据库加载
        clear_intent_tree_cache()

        logger.info(f"创建意图节点成功: id={node_id}, code={request.intent_code}")
        return node_id

    except ClientException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"创建意图节点失败: {e}")
        raise ClientException(f"创建意图节点失败: {str(e)}")


def update_node(db: Session, node_id: str, request: IntentNodeUpdateRequest, username: str) -> None:
    """更新意图节点

    Args:
        db: 数据库会话
        node_id: 节点ID
        request: 更新请求
        username: 用户名
    """
    try:
        # 查询节点
        model = crud_intent_node.get_by_id(db, node_id)

        if not model:
            raise ClientException(f"节点 '{node_id}' 不存在")

        # 如果修改了 parent_code，检查新的父节点是否存在且不是自己
        if request.parent_code is not None:
            if request.parent_code == model.intent_code:
                raise ClientException("父节点不能是自己")

            if request.parent_code:
                if not crud_intent_node.get_by_code(db, request.parent_code):
                    raise ClientException(f"父节点 '{request.parent_code}' 不存在")

        # 更新字段
        update_data = {}
        if request.name is not None:
            update_data['name'] = request.name
        if request.level is not None:
            update_data['level'] = request.level
        if request.parent_code is not None:
            update_data['parent_code'] = request.parent_code
        if request.description is not None:
            update_data['description'] = request.description
        if request.examples is not None:
            update_data['examples'] = json.dumps(request.examples, ensure_ascii=False)
        if request.collection_name is not None:
            update_data['collection_name'] = request.collection_name
        if request.kind is not None:
            update_data['kind'] = request.kind

        if update_data:
            update_data['update_by'] = username
            crud_intent_node.update(db, node_id, update_data)

            logger.info(f"更新意图节点成功: id={node_id}")

        db.commit()

    except ClientException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"更新意图节点失败: {e}")
        raise ClientException(f"更新意图节点失败: {str(e)}")


def delete_node(db: Session, node_id: str, username: str) -> None:
    """删除意图节点（软删除，同时删除子节点）

    Args:
        db: 数据库会话
        node_id: 节点ID
        username: 用户名
    """
    try:
        # 查询节点
        model = crud_intent_node.get_by_id(db, node_id)

        if not model:
            raise ClientException(f"节点 '{node_id}' 不存在")

        # 递归查找所有子节点
        nodes_to_delete = crud_intent_node.find_descendant_ids(db, model.intent_code)
        nodes_to_delete.append(node_id)

        # 软删除所有节点
        crud_intent_node.soft_delete_by_ids(db, nodes_to_delete, username)
        db.commit()

        logger.info(f"删除意图节点成功: id={node_id}, 共删除 {len(nodes_to_delete)} 个节点")

    except ClientException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"删除意图节点失败: {e}")
        raise ClientException(f"删除意图节点失败: {str(e)}")


def batch_delete_nodes(db: Session, ids: List[str], username: str) -> None:
    """批量删除节点

    Args:
        db: 数据库会话
        ids: 节点ID列表
        username: 用户名
    """
    try:
        crud_intent_node.soft_delete_by_ids(db, ids, username)
        db.commit()

        logger.info(f"批量删除节点成功: count={len(ids)}")

    except Exception as e:
        db.rollback()
        logger.exception(f"批量删除节点失败: {e}")
        raise ClientException(f"批量删除节点失败: {str(e)}")


def _model_to_tree_response(model: IntentNodeModel) -> IntentNodeTreeResponse:
    """将数据库模型转换为树响应对象"""
    return IntentNodeTreeResponse(
        id=model.id,
        intent_code=model.intent_code,
        name=model.name,
        level=model.level,
        parent_code=model.parent_code,
        description=model.description,
        examples=model.examples,
        collection_name=model.collection_name,
        kind=model.kind,
        children=[]
    )


def _sort_children(nodes: List[IntentNodeTreeResponse]) -> None:
    """递归排序子节点"""
    for node in nodes:
        if node.children:
            node.children.sort(key=lambda x: x.name or "")
            _sort_children(node.children)


__all__ = [
    "get_intent_tree",
    "create_node",
    "update_node",
    "delete_node",
    "batch_delete_nodes",
]
