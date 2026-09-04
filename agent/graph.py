from typing import Any, Dict

from langgraph.graph import START, END, StateGraph

from .config import resolve_node_provider_config
from .providers import ModelProvider, ProviderRegistry
from .state import GraphState
from .nodes import *
from .routes import *


def build_provider(
    config: Dict[str, Any],
    node: str,
) -> ModelProvider:
    node_config = resolve_node_provider_config(
        config,
        node_name=node,
    )
    return ProviderRegistry.create(config=node_config)


def build_graph(config):
    graph = StateGraph(GraphState)

    # Providers
    generate_provider = build_provider(config, "generate_op")

    # Nodes
    graph.add_node("reset_state", SetStateNode({"attempts": 0, "max_attempts": 3}))
    graph.add_node("prepare_repo", PrepareRepoNode())
    graph.add_node(
        "generate_op",
        GenerateOpNode(
            generate_provider,
        ),
    )

    # Edges
    graph.add_edge(START, "reset_state")
    graph.add_edge(START, "prepare_repo")
    graph.add_edge("prepare_repo", "generate_op")
    graph.add_conditional_edges(
        "generate_op",
        after_generate_op_route(),
        {
            "success": END,
            "retry": "generate_op",
            "failed": END,
        },
    )

    return graph.compile()
