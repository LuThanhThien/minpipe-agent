from dataclasses import dataclass, field
from typing import List


@dataclass
class Pipe:
    name: str = None
    args: dict = field(default_factory=dict)

    def __repr__(self):
        return self.name or "Pipe()"


class Pipeline:
    def __init__(self):
        self.ops: List[Pipe] = []

    def __repr__(self):
        if not self.ops:
            return "Pipeline()"

        names = []
        for op in self.ops:
            if isinstance(op, str):
                names.append(op)
            elif hasattr(op, "name"):
                names.append(op.name)
            else:
                names.append(str(op))

        lines = ["Pipeline("]
        lines.extend(f"  {name}" for name in names)
        lines.append(")")
        return "\n".join(lines)

    __str__ = __repr__

    def add(self, op: Pipe) -> "Pipeline":
        if isinstance(op, str):
            op = Pipe(op)
        assert isinstance(op, Pipe)
        self.ops.append(op)
        return self
