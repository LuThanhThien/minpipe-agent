from typing import TypedDict

from loguru import logger

from .base_node import BaseNode
from ..tools import git_stash


class PrepareRepoNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.boundaries = ["./minpipe"]

    def invoke(self, state: TypedDict):
        result = git_stash(boundaries=self.boundaries)

        output = result["stdout"] + result["stderr"]
        succeeded = result["returncode"] == 0

        return {
            "repo_prepare_succeeded": succeeded,
            "repo_prepare_output": output,
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
                logger.info(output.strip())
        else:
            logger.error(
                "Failed to prepare repository:\n{}",
                output,
            )
