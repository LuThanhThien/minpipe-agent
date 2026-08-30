import torch
from .operation import Operation


@Operation.register
class ReLU(Operation):
    name = "relu"

    def execute(self, x: torch.Tensor) -> torch.Tensor:
        return torch.relu(x)
