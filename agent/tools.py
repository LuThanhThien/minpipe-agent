from pathlib import Path
import subprocess
from loguru import logger


def read_file(path: str) -> str:
    """Read UTF-8 text content from a source file path."""
    logger.debug(f"Reading file: {path}")
    return Path(path).read_text(encoding="utf-8")


def run_pytest(path: str) -> dict:
    """Run pytest with verbose output on the specified file path and return the result."""
    cmd = ["pytest", "-vv", path]
    logger.debug(f"Running command: {" ".join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def apply_changes(changes: list[dict], boundaries: list[str]) -> list[str]:
    """Apply file changes only when every path is inside an edit boundary."""
    resolved_boundaries = [Path(boundary).resolve() for boundary in boundaries]
    changed_files = []

    for change in changes:
        path = change["path"]
        file_path = Path(path).resolve()

        if not any(
            file_path == boundary or boundary in file_path.parents
            for boundary in resolved_boundaries
        ):
            raise RuntimeError(
                f"Model attempted to modify a file outside edit boundaries: {path}"
            )

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(change["content"], encoding="utf-8")
        changed_files.append(path)

    return changed_files
