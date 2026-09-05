import torch

from minpipe import build


class Model(torch.nn.Module):
    def forward(self, x):
        return torch.relu(x)


def test_minpipe():
    values = torch.tensor([-1.0, 1.0])

    build("not a model", values)
