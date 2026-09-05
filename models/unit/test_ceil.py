import torch

from minpipe import build, run


class Model(torch.nn.Module):
    def forward(self, x):
        return torch.ceil(x)


def test_minpipe():
    model = Model()
    values = torch.tensor([-2.5, -1.25, 0.0, 1.25, 2.5])
    expected = model(values)
    pipeline = build(model, values)
    actual = run(pipeline, values)

    assert pipeline.ops[0].name == "ceil"
    assert torch.equal(actual, expected)
