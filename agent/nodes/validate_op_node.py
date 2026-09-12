from loguru import logger

from .base_node import BaseNode
from ..state import GraphState
from ..tools import run_pytest


class ValidateOpNode(BaseNode):
    def invoke(self, state: GraphState):
        worktree_root = state.get("worktree_root")
        test = state.get("test")

        if not worktree_root:
            return {
                "validation_succeeded": False,
                "validation_output": "",
                "validation_error": ("worktree_root is not available in graph state"),
            }

        if not test:
            return {
                "validation_succeeded": False,
                "validation_output": "",
                "validation_error": ("test is not available in graph state"),
            }

        try:
            result = run_pytest(
                repo_root=worktree_root,
                path=test,
            )

            output = result["stdout"] + result["stderr"]
            succeeded = result["returncode"] == 0

            return {
                "validation_succeeded": succeeded,
                "validation_output": output,
                "validation_error": (
                    ""
                    if succeeded
                    else f"pytest exited with code {result['returncode']}"
                ),
            }

        except Exception as exc:
            return {
                "validation_succeeded": False,
                "validation_output": "",
                "validation_error": str(exc),
            }

    def print_result(self, result: GraphState):
        succeeded = result.get(
            "validation_succeeded",
            False,
        )

        output = result.get(
            "validation_output",
            "",
        )

        error = result.get(
            "validation_error",
            "",
        )

        if succeeded:
            logger.success("Validation passed successfully")
        else:
            logger.error(
                "Validation failed: {}",
                error,
            )

        if output:
            logger.info(
                "Validation output:\n{}",
                output.strip(),
            )
