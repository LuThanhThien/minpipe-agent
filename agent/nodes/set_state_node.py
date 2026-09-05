from typing import Any, TypedDict

from loguru import logger

from .base_node import BaseNode


class SetStateNode(BaseNode):
    def __init__(self, defaults: dict[str, Any]):
        super().__init__()
        self.defaults = defaults

    def invoke(self, state: TypedDict):
        return self.defaults.copy()

    def print_result(self, result: TypedDict):
        logger.info(
            "Reset state: {}",
            ", ".join(result.keys()),
        )
