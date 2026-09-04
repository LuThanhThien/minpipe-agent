from typing import Annotated, Any, Dict, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition

from .config import resolve_node_provider_config
from .providers import ProviderRegistry, ModelProvider
from .nodes import *


class AgentState(TypedDict):
    file: str
    messages: Annotated[list[AnyMessage], add_messages]
    response: str


def create_provider(config: Dict[str, Any], name: str) -> ModelProvider:
    node_config = resolve_node_provider_config(config, node_name=name)
    provider = ProviderRegistry.create(config=node_config)
    return provider


def build_graph(config):

    graph = StateGraph(AgentState)

    explain_code_provider = create_provider(config, "explain_code")
    graph.add_node(
        "explain_code",
        ExplainCodeNode(explain_code_provider),
    )

    graph.add_edge(START, "explain_code")
    graph.add_edge("explain_code", END)

    return graph.compile()
