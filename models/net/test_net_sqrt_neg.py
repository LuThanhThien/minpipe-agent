import torch

from minpipe import build, run


class Model(torch.nn.Module):
    def forward(self, x):
        x = torch.sqrt(x)
        return torch.neg(x)


def test_minpipe():
    model = Model()
    values = torch.tensor([0.25, 0.5, 1.0, 2.0, 4.0])

    expected = model(values)
    pipeline = build(model, values)
    actual = run(pipeline, values)

    assert [op.name for op in pipeline.ops] == ["sqrt", "neg"]
    assert torch.equal(actual, expected)
