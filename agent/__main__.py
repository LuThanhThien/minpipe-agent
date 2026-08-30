import argparse
from typing import Any, Dict

from .config import load_config
from .graph import build_graph


def run(file_path: str, config: Dict[str, Any]) -> str:
    graph = build_graph(config)
    response = graph.invoke({"file": file_path})
    return response["response"]


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
        "file",
        help="Source file to explain.",
    )

    args = parser.parse_args()

    config = load_config(args.config)
    print(run(file_path=args.file, config=config))


if __name__ == "__main__":
    main()
