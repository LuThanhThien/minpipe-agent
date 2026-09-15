import re

from loguru import logger

from .base_node import BaseNode
from ..providers import ModelProvider
from ..state import GraphState
from ..tools import read_file


class OpContextNode(BaseNode):
    def __init__(self):
        super().__init__()

    def invoke(self, state: GraphState):
        worktree_root = state.get("worktree_root")
        if not worktree_root:
            return {
                "op_context_result": context,
                "op_context_succeeded": False,
                "op_context_error": "worktree_root is not available in graph state",
            }

        op = state.get("op")
        test = state.get("test")

        if not op or not test:
            logger.warning("Op/test are not found in the state")
            return {
                "op_context_result": context,
                "op_context_succeeded": False,
                "op_context_error": "op/test are not available in graph state",
            }

        try:
            context = self._build_context(
                op=op,
                test=test,
                worktree_root=worktree_root,
                validation_output=state.get(
                    "validation_output",
                    "",
                ),
                generate_error=state.get(
                    "generate_error",
                    "",
                ),
                generate_changed_files=state.get("generate_changed_files", ""),
            )

            return {
                "op_context_result": context,
                "op_context_succeeded": True,
                "op_context_error": "",
            }

        except Exception as exc:
            return {
                "op_context_result": "",
                "op_context_succeeded": False,
                "op_context_error": str(exc),
            }

    def _build_context(
        self,
        op: str,
        test: str,
        worktree_root: str,
        validation_output: str,
        generate_error: str,
        generate_changed_files: str,
    ) -> dict:
        return {
            "failure": self._extract_failure(
                validation_output,
                op,
            ),
            "test_source": self._read_optional(
                worktree_root,
                test,
            ),
            "existing_op_source": self._read_optional(
                worktree_root,
                f"minpipe/ops/{op}.py",
                default="Not found",
            ),
            "registry_source": self._read_optional(
                worktree_root,
                "minpipe/ops/operation.py",
            ),
            "ops_init_source": self._read_optional(
                worktree_root,
                "minpipe/ops/__init__.py",
            ),
            "similar_ops": self._build_similar_ops_context(
                op=op,
                worktree_root=worktree_root,
            ),
            "previous_validation_output": (
                validation_output
                if validation_output
                else "No previous targeted validation output."
            ),
            "previous_generate_error": (
                generate_error if generate_error else "No previous generation error."
            ),
            "previous_generate_changed_files": (
                generate_changed_files
                if generate_changed_files
                else "No previous changed found."
            ),
        }

    def _build_similar_ops_context(
        self,
        op: str,
        worktree_root: str,
    ) -> str:
        candidates = [
            "relu",
            "sigmoid",
            "square",
        ]

        sections = []

        for candidate in candidates:
            if candidate == op:
                continue

            path = f"minpipe/ops/{candidate}.py"

            source = self._read_optional(
                worktree_root,
                path,
                default="",
            )

            if not source:
                continue

            sections.append(f"# {path}\n\n{source}")

        if not sections:
            return "No similar working operations found."

        return "\n\n".join(sections)

    def _read_optional(
        self,
        worktree_root: str,
        path: str,
        default: str = "",
    ) -> str:
        try:
            return read_file(
                repo_root=worktree_root,
                path=path,
            )
        except (FileNotFoundError, OSError):
            return default

    def _extract_failure(
        self,
        output: str,
        op: str,
    ) -> str:
        if not output:
            return f"Unknown operation: {op}"

        patterns = [
            rf"KeyError:\s*['\"]Unknown operation:\s*{re.escape(op)}['\"]",
            rf"Unknown operation:\s*{re.escape(op)}",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                output,
                re.IGNORECASE,
            )

            if match:
                return match.group(0)

        return output[-2000:]

    def print_result(
        self,
        result: GraphState,
    ):
        succeeded = result.get(
            "op_context_succeeded",
            False,
        )

        error = result.get(
            "op_context_error",
            "",
        )

        context = result.get(
            "op_context_result",
            {},
        )

        if not succeeded:
            logger.error(
                "OpContextNode failed: {}",
                error or "unknown error",
            )
            return

        if not context:
            logger.warning("OpContextNode produced no context")
            return

        logger.success("OpContextNode assembled operation context")

        failure = context.get("failure", "")
        if failure:
            logger.info(
                "Failure context:\n{}",
                failure.strip(),
            )

        test_source = context.get("test_source", "")
        if test_source:
            logger.info(
                "Test source:\n{}",
                test_source.strip()[:2000],
            )

        similar_ops = context.get("similar_ops", "")
        if similar_ops and similar_ops != "No similar working operations found.":
            logger.info(
                "Similar operations:\n{}",
                similar_ops.strip()[:2000],
            )
