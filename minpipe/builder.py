import torch

from .ir.pipe import Pipe, Pipeline


def build(model: torch.nn.Module, input: torch.Tensor) -> Pipeline:
    """Convert a traced torch graph into a minpipe pipeline.

    The model is executed once with sample input under torch FX tracing, and the
    resulting graph is used to create one Pipe per captured op in order.
    """
    if not isinstance(model, torch.nn.Module):
        raise TypeError(f"Expected a torch.nn.Module, got {type(model)}")

    model.eval()
    traced = torch.fx.symbolic_trace(model)
    pipeline = Pipeline()

    for node in traced.graph.nodes:
        if node.op == "call_module":
            module = traced.get_submodule(node.target)
            op_name = module.__class__.__name__.lower()
            pipeline.add(Pipe(name=op_name))
        elif node.op == "call_function":
            op_name = getattr(node.target, "__name__", str(node.target)).lower()
            pipeline.add(Pipe(name=op_name))
        elif node.op == "call_method":
            pipeline.add(Pipe(name=str(node.target).lower()))

    return pipeline
