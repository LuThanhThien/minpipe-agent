from abc import ABC, abstractmethod
from typing import TypedDict
from loguru import logger


class BaseNode(ABC):
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__

    def __call__(self, state):
        logger.info(f"Running node: {self.name}")
        result = self.invoke(state)
        logger.info(f"Finished node: {self.name}")
        self.print_result(result)
        return result

    def print_result(self, result: TypedDict):
        pass

    @abstractmethod
    def invoke(self, state: TypedDict):
        pass
