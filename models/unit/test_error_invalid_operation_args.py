import torch

from minpipe import build, run
from minpipe.ir.pipe import Pipe


class Model(torch.nn.Module):
    def forward(self, x):
        return torch.square(x)


def test_minpipe():
    model = Model()
    values = torch.tensor([-1.0, 1.0])
    pipeline = build(model, values)
    pipeline.ops[0] = Pipe(name="square", args={"unexpected": True})

    run(pipeline, values)
