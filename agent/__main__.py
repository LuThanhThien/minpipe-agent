import argparse
from typing import Any, Dict

from .config import load_config
from .graph import build_graph


def run(args: argparse.Namespace, config: Dict[str, Any]) -> str:
    graph = build_graph(config)
    response = graph.invoke({"test_folder": args.test_folder})

    lines = ["Test run completed."]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Explain source code with a LangGraph agent."
    )

    parser.add_argument(
        "--config",
        default="configs/monkey.py",
        help="Python config file defining a CONFIG dictionary.",
    )
    parser.add_argument(
        "--test-folder",
        default="./models",
        help="Test folder to run tests for.",
    )

    args = parser.parse_args()

    config = load_config(args.config)
    print(run(args=args, config=config))


if __name__ == "__main__":
    main()
