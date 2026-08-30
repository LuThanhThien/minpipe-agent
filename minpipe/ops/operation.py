import torch
from abc import ABC, abstractmethod


class OperationRegistry:
    _registry = {}

    @classmethod
    def register(cls, op_cls):
        cls._registry[op_cls.name] = op_cls
        return op_cls

    @classmethod
    def get(cls, name: str):
        if name not in cls._registry:
            raise KeyError(f"Unknown operation: {name}")
        return cls._registry[name]

    @classmethod
    def create(cls, name: str, args: dict) -> "Operation":
        op_cls = cls.get(name)
        return op_cls(**args)

    @classmethod
    def all(cls):
        return cls._registry.copy()


class Operation(ABC):
    name: str

    @abstractmethod
    def execute(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError(f"NIY for {self.name}")

    @staticmethod
    def register(cls):
        return OperationRegistry.register(cls)
