from loguru import logger

from .base_node import BaseNode
from ..state import GraphState
from ..tools import format_python_files


class FileFormatterNode(BaseNode):
    def invoke(self, state: GraphState):
        worktree_root = state.get("worktree_root")
        boundaries = state.get("boundaries", [])

        if not worktree_root:
            return {
                "formatting_succeeded": False,
                "formatting_output": "",
                "formatting_error": "worktree_root is not available in graph state",
            }

        if not boundaries:
            return {
                "formatting_succeeded": False,
                "formatting_output": "",
                "formatting_error": "boundaries are not available in graph state",
            }

        try:
            result = format_python_files(
                repo_root=worktree_root,
                format_dir=boundaries,
            )

            output = result["stdout"] + result["stderr"]
            succeeded = result["returncode"] == 0

            return {
                "formatting_succeeded": succeeded,
                "formatting_output": output,
                "formatting_error": (
                    "" if succeeded else f"black exited with code {result.returncode}"
                ),
            }

        except Exception as exc:
            return {
                "formatting_succeeded": False,
                "formatting_output": "",
                "formatting_error": str(exc),
            }

    def print_result(self, result: GraphState):
        if result.get("formatting_succeeded", False):
            logger.success("Formatting completed successfully")
        else:
            logger.error(
                "Formatting failed: {}",
                result.get("formatting_error", ""),
            )

        output = result.get("formatting_output", "")
        if output:
            logger.info("Formatting output:\n{}", output.strip())
