import torch
from .operation import Operation


@Operation.register
class Square(Operation):
    name = "square"

    def execute(self, x: torch.Tensor) -> torch.Tensor:
        return torch.square(x)
