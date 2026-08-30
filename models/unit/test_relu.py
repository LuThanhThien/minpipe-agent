import torch

from minpipe import build, run


class Model(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.relu = torch.nn.ReLU()

    def forward(self, x):
        return self.relu(x)


def test_minpipe():
    model = Model()
    values = torch.tensor([-2.0, -1.0, 0.0, 1.0, 2.0])

    expected = model(values)
    pipeline = build(model, values)
    actual = run(pipeline, values)

    assert pipeline.ops[0].name == "relu"
    assert torch.equal(actual, expected)
