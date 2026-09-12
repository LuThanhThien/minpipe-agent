from loguru import logger

from .base_node import BaseNode
from ..state import GraphState
from ..tools import git_remove_worktree


class CleanupRepoNode(BaseNode):
    def invoke(self, state: GraphState):
        repo_root = state.get("repo_root")
        worktree_root = state.get("worktree_root")

        if not repo_root or not worktree_root:
            return {
                "repo_cleanup_succeeded": True,
                "repo_cleanup_output": "No worktree to clean up.",
            }

        try:
            git_remove_worktree(
                repo_root=repo_root,
                worktree_root=worktree_root,
            )

            return {
                "repo_cleanup_succeeded": True,
                "repo_cleanup_output": (f"Removed worktree: {worktree_root}"),
            }

        except Exception as exc:
            return {
                "repo_cleanup_succeeded": False,
                "repo_cleanup_output": str(exc),
            }

    def print_result(self, result: GraphState):
        succeeded = result.get(
            "repo_cleanup_succeeded",
            False,
        )

        output = result.get(
            "repo_cleanup_output",
            "",
        )

        if succeeded:
            logger.success("Repository cleaned up successfully")

            if output:
                logger.info(output)
        else:
            logger.error(
                "Failed to clean up repository:\n{}",
                output,
            )
