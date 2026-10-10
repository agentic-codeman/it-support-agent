"""
RAG 对话相关的数据传输对象（DTO）
"""
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class RewriteResult:
    """查询改写结果"""
    rewritten_question: str  # 改写后的问题


@dataclass
class IntentNode:
    """意图节点"""
    id: str
    name: str
    kind: str = "KB"  # "KB", "SYSTEM"
    level: int = 0  # 0=DOMAIN, 1=CATEGORY, 2=TOPIC
    kb_id: Optional[str] = None
    parent_id: Optional[str] = None
    description: str = ""
    full_path: str = ""
    examples: List[str] = field(default_factory=list)
    collection_name: Optional[str] = None
    children: List['IntentNode'] = field(default_factory=list)

    def is_leaf(self) -> bool:
        """是否为叶子节点"""
        return len(self.children) == 0

    def is_kb(self) -> bool:
        """是否为 KB 类型节点"""
        return self.kind in ["KB", None]

    def is_system(self) -> bool:
        """是否为 SYSTEM 类型节点"""
        return self.kind == "SYSTEM"


@dataclass
class NodeScore:
    """意图节点评分"""
    node: Optional[IntentNode]  # 完整的意图节点对象
    score: float


@dataclass
class QuestionIntent:
    """问题意图"""
    question: str
    node_scores: List[NodeScore] = field(default_factory=list)


@dataclass
class GuidanceDecision:
    """引导式问答决策结果"""
    action: str = "NONE"  # "NONE" or "PROMPT"
    prompt: Optional[str] = None

    @classmethod
    def none(cls):
        """创建无引导决策"""
        return cls(action="NONE", prompt=None)

    @classmethod
    def prompt(cls, prompt_text: str):
        """创建引导决策"""
        return cls(action="PROMPT", prompt=prompt_text)

    def is_prompt(self) -> bool:
        """是否需要引导"""
        return self.action == "PROMPT"
