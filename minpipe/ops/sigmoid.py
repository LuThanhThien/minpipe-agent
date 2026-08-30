import torch
from .operation import Operation


@Operation.register
class Sigmoid(Operation):
    name = "sigmoid"

    def execute(self, x: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(x)
