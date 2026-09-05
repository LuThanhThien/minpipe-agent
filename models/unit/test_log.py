import torch

from minpipe import build, run


class Model(torch.nn.Module):
    def forward(self, x):
        return torch.log(x)


def test_minpipe():
    model = Model()
    values = torch.tensor([0.25, 0.5, 1.0, 2.0, 4.0])
    expected = model(values)
    pipeline = build(model, values)
    actual = run(pipeline, values)

    assert pipeline.ops[0].name == "log"
    assert torch.equal(actual, expected)
