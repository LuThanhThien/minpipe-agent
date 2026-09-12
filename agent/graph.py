from typing import Any, Dict
from pathlib import Path

from langgraph.graph import START, END, StateGraph

from .config import resolve_node_provider_config
from .providers import ModelProvider, ProviderRegistry
from .state import GraphState
from .nodes import *
from .routes import *
from .tools import REPO_ROOT


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
    graph.add_node(
        "reset_state",
        SetStateNode(
            {
                "attempts": 0,
                "max_attempts": 3,
                "repo_root": str(REPO_ROOT),
                "boundaries": ["./minpipe"],
            }
        ),
    )
    graph.add_node("prepare_repo", PrepareRepoNode())
    graph.add_node(
        "generate_op",
        GenerateOpNode(generate_provider),
    )
    graph.add_node(
        "format_files",
        FileFormatterNode(),
    )
    graph.add_node(
        "validate_op",
        ValidateOpNode(),
    )
    graph.add_node(
        "save_patch",
        SavePatchNode(),
    )
    graph.add_node(
        "cleanup_repo",
        CleanupRepoNode(),
    )

    # Edges
    graph.add_edge(START, "reset_state")
    graph.add_edge("reset_state", "prepare_repo")
    graph.add_edge("prepare_repo", "generate_op")
    graph.add_conditional_edges(
        "generate_op",
        after_generate_op_route(),
        {
            "success": "format_files",
            "retry": "generate_op",
            "failed": END,
        },
    )
    # NOTE: either way, goes to validation
    graph.add_conditional_edges(
        "format_files",
        after_formatting_route(),
        {
            "success": "validate_op",
            "failed": "validate_op",
        },
    )
    graph.add_conditional_edges(
        "validate_op",
        after_validate_op_route(),
        {
            "success": "save_patch",
            "retry": "generate_op",
            "failed": END,
        },
    )
    graph.add_edge(
        "save_patch",
        "cleanup_repo",
    )
    graph.add_edge(
        "cleanup_repo",
        END,
    )

    return graph.compile()
