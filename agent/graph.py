from enum import StrEnum, auto
from typing import Annotated, Any, Dict, TypedDict

from langgraph.graph import END as END_GRAPH
from langgraph.graph import START as START_GRAPH
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

from .config import resolve_node_provider_config
from .providers import ModelProvider, ProviderRegistry
from .nodes import *


class GraphState(TypedDict, total=False):
    # Test suite
    test_folder: str
    passed_tests: list[str]
    failed_tests: list[str]
    test_output: str
    test_passed: bool

    # Unsupported ops
    unsup_ops: list[str]
    unsup_ops_tests: list[str]
    current_unsup_op_index: int
    current_unsup_op: str
    current_unsup_op_test: str

    # Enable op
    op_enable_attempts: int
    max_op_enable_attempts: int
    op_enable_succeeded: bool
    op_enable_error: str
    changed_files: list[str]

    # Validation
    op_validation_passed: bool
    op_validation_output: str

    # Code context / generation
    file: str
    response: str
    refined_code: str
    code_diff: str

    messages: Annotated[list, add_messages]


class NodeType(StrEnum):
    START = START_GRAPH
    END = END_GRAPH

    RUN_TEST = auto()
    IDENTIFY_OPS = auto()
    NEXT_OP = auto()
    RESET_STATE = auto()
    INSPECT_OP = auto()
    CODEGEN = auto()
    VALIDATE_OP = auto()
    ENABLE_OP = auto()


class RouteType(StrEnum):
    AFTER_RUN_TEST = auto()
    AFTER_NEXT_OP = auto()
    AFTER_ENABLE_OP = auto()
    AFTER_VALIDATE_OP = auto()


# Short alias
NoT = NodeType
RoT = RouteType


def build_provider(
    config: Dict[str, Any],
    node: NodeType,
) -> ModelProvider:
    node_config = resolve_node_provider_config(
        config,
        node_name=node,
    )
    return ProviderRegistry.create(config=node_config)


def after_run_test_route(k_failed_tests: str):
    def _route(state: GraphState):
        if state.get(k_failed_tests, []):
            return NoT.IDENTIFY_OPS

        return NoT.END

    return _route


def after_next_op_route(k_current_op: str):
    def _route(state: GraphState):
        if state.get(k_current_op) is None:
            return NoT.END

        return NoT.INSPECT_OP

    return _route


def after_enable_op_route(
    k_succeeded: str,
    k_attempts: str,
    k_max_attempts: str,
):
    def _route(state: GraphState):
        if state.get(k_succeeded, False):
            return NoT.VALIDATE_OP

        attempts = state.get(k_attempts, 0)
        max_attempts = state.get(k_max_attempts, 5)

        if attempts < max_attempts:
            return NoT.ENABLE_OP

        return NoT.VALIDATE_OP

    return _route


def after_validate_op_route(
    k_passed: str,
    k_attempts: str,
    k_max_attempts: str,
):
    def _route(state: GraphState):
        if state.get(k_passed, False):
            return NoT.NEXT_OP

        attempts = state.get(k_attempts, 0)
        max_attempts = state.get(k_max_attempts, 5)

        if attempts < max_attempts:
            return NoT.ENABLE_OP

        return NoT.END

    return _route


def build_graph(config):
    graph = StateGraph(GraphState)

    # Providers
    inspect_provider = build_provider(
        config,
        NoT.INSPECT_OP,
    )
    enable_provider = build_provider(config, NoT.ENABLE_OP)

    # Nodes
    nodes = {
        NoT.RUN_TEST: RunTestNode(
            "test_folder",
            "test_output",
            "test_passed",
            "passed_tests",
            "failed_tests",
        ),
        NoT.IDENTIFY_OPS: IdentifyUnsupportedOpsNode(
            "test_output",
            "unsup_ops",
            "unsup_ops_tests",
            "current_unsup_op_index",
        ),
        NoT.NEXT_OP: NextTestNode(
            "unsup_ops_tests",
            "unsup_ops",
            "current_unsup_op_test",
            "current_unsup_op",
            "current_unsup_op_index",
            "file",
        ),
        NoT.RESET_STATE: SetStateNode(
            {
                "op_enable_attempts": 0,
            }
        ),
        NoT.INSPECT_OP: ExplainCodeNode(
            inspect_provider,
            "file",
            "response",
        ),
        NoT.VALIDATE_OP: ValidateTestNode(
            "current_unsup_op_test",
            "current_unsup_op",
            "op_validation_passed",
            "op_validation_output",
        ),
        NoT.ENABLE_OP: EnableOpNode(
            enable_provider,
            "current_unsup_op",
            "current_unsup_op_test",
            "response",
            "op_validation_output",
            "changed_files",
            "response",
            "op_enable_succeeded",
            "op_enable_error",
            "op_enable_attempts",
        ),
    }

    routes = {
        RoT.AFTER_RUN_TEST: after_run_test_route("failed_tests"),
        RoT.AFTER_NEXT_OP: after_next_op_route("current_unsup_op"),
        RoT.AFTER_ENABLE_OP: after_enable_op_route(
            "op_enable_succeeded",
            "op_enable_attempts",
            "max_op_enable_attempts",
        ),
        RoT.AFTER_VALIDATE_OP: after_validate_op_route(
            "op_validation_passed",
            "op_enable_attempts",
            "max_op_enable_attempts",
        ),
    }

    for name, node in nodes.items():
        graph.add_node(name, node)

    # Edges
    graph.add_edge(NoT.START, NoT.RUN_TEST)
    graph.add_conditional_edges(NoT.RUN_TEST, routes[RoT.AFTER_RUN_TEST])
    graph.add_edge(NoT.IDENTIFY_OPS, NoT.NEXT_OP)
    graph.add_conditional_edges(NoT.NEXT_OP, routes[RoT.AFTER_NEXT_OP])
    graph.add_edge(NoT.INSPECT_OP, NoT.ENABLE_OP)
    graph.add_conditional_edges(NoT.ENABLE_OP, routes[RoT.AFTER_ENABLE_OP])
    graph.add_conditional_edges(NoT.VALIDATE_OP, routes[RoT.AFTER_VALIDATE_OP])

    return graph.compile()
