import torch

from .ir.pipe import Pipeline
from .ops.operation import OperationRegistry


class Runner:
    def __init__(self):
        pass

    def _eval(self, value):
        if isinstance(value, torch.Tensor):
            return value
        if isinstance(value, (tuple, list)):
            if len(value) != 1:
                raise ValueError(
                    f"Expected a single tensor input, got {len(value)} values"
                )
            return self._eval(value[0])
        raise RuntimeError(f"NIY: {type(value)}")

    def run(self, pipeline: Pipeline, input_value):
        value = self._eval(input_value)
        for pipe in pipeline.ops:
            op = OperationRegistry.create(pipe.name, pipe.args)
            value = op.execute(value)
        return value


def run(pipeline: Pipeline, input: torch.Tensor) -> torch.Tensor:
    from .runner import Runner

    return Runner().run(pipeline, input)
