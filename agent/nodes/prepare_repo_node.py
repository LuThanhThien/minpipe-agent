from typing import TypedDict

from loguru import logger

from .base_node import BaseNode
from ..tools import git_create_worktree, git_fetch_main


class PrepareRepoNode(BaseNode):
    def __init__(self, base_ref: str = "origin/main"):
        super().__init__()
        self.base_ref = base_ref

    def invoke(self, state: TypedDict):
        repo_root = state["repo_root"]

        try:
            git_fetch_main(repo_root)

            worktree_root = git_create_worktree(
                repo_root=repo_root,
                base_ref=self.base_ref,
            )

            return {
                "repo_prepare_succeeded": True,
                "repo_prepare_output": (
                    f"Created worktree at {worktree_root} " f"from {self.base_ref}"
                ),
                "worktree_root": worktree_root,
            }

        except Exception as e:
            return {
                "repo_prepare_succeeded": False,
                "repo_prepare_output": str(e),
                "worktree_root": None,
            }

    def print_result(self, result: TypedDict):
        succeeded = result.get(
            "repo_prepare_succeeded",
            False,
        )

        output = result.get(
            "repo_prepare_output",
            "",
        )

        if succeeded:
            logger.success("Repository prepared successfully")

            if output:
                logger.info(output)
        else:
            logger.error(
                "Failed to prepare repository:\n{}",
                output,
            )
