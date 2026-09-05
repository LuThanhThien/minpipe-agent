import torch

from minpipe import build, run


class Model(torch.nn.Module):
    def forward(self, x):
        return torch.cos(x)


def test_minpipe():
    model = Model()
    values = torch.tensor([-2.0, -1.0, 0.0, 1.0, 2.0])
    expected = model(values)
    pipeline = build(model, values)
    actual = run(pipeline, values)

    assert pipeline.ops[0].name == "cos"
    assert torch.equal(actual, expected)
