import torch

from minpipe import build, run


class Model(torch.nn.Module):
    def forward(self, x):
        return torch.sigmoid(x)


def test_minpipe():
    model = Model()
    values = torch.tensor([-1.0, 1.0])
    pipeline = build(model, values)

    run(pipeline, (values, values))
