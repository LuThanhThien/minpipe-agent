from abc import ABC, abstractmethod
from typing import TypedDict


class BaseNode(ABC):
    def __init__(self, provider):
        self.provider = provider

    @abstractmethod
    def __call__(self, state):
        pass
