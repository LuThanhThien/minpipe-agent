from pathlib import Path

from langchain_core.tools import tool


@tool
def read_file(path: str) -> str:
    """Read UTF-8 text content from a source file path."""
    return Path(path).read_text(encoding="utf-8")
