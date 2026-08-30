from abc import ABC, abstractmethod


class ModelProvider(ABC):
    @abstractmethod
    def invoke(self, prompt: str) -> str:
        raise NotImplementedError
