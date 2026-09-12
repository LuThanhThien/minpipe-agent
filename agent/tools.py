from pathlib import Path
import subprocess
import sys
import tempfile

from loguru import logger

# repo-root/
# ├── agent/
# │   └── tools.py
# │   └── templates/
# └── ...
REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_ROOT = Path(__file__).resolve().parent / "templates"
PROMPTS_ROOT = TEMPLATES_ROOT / "prompts"
SCRIPTS_ROOT = TEMPLATES_ROOT / "scripts"


def resolve_repo_path(repo_root: str, path: str) -> Path:
    """Resolve a repository-relative path."""
    root = Path(repo_root).resolve()
    resolved = (root / path).resolve()

    if resolved != root and root not in resolved.parents:
        raise RuntimeError(f"Path escapes repository root: {path}")

    return resolved


def read_file(
    repo_root: str,
    path: str,
) -> str:
    """Read a UTF-8 source file relative to repo_root."""
    file_path = resolve_repo_path(
        repo_root,
        path,
    )

    logger.debug("Reading file: {}", file_path)

    return file_path.read_text(
        encoding="utf-8",
    )


def read_prompt(name: str) -> str:
    path = PROMPTS_ROOT / name

    return path.read_text(
        encoding="utf-8",
    )


def read_script(name: str) -> str:
    path = SCRIPTS_ROOT / name

    return path.read_text(
        encoding="utf-8",
    )


def run_pytest(
    repo_root: str,
    path: str,
) -> dict:
    """Run pytest from repo_root on the specified test path."""
    cmd = [
        "pytest",
        "-vv",
        path,
    ]

    logger.debug(
        "Running command: {}",
        " ".join(cmd),
    )

    result = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def format_python_files(
    repo_root: str,
    format_dir: list[str],
) -> dict:
    """Format Python files within repository-relative directory format_dir."""
    root = Path(repo_root).resolve()
    format_paths = []

    for format in format_dir:
        format_path = resolve_repo_path(repo_root, format)

        if not format_path.is_dir():
            raise RuntimeError(f"Formatter format is not a directory: {format}")

        format_paths.append(str(format_path.relative_to(root)))

    cmd = [
        sys.executable,
        "-m",
        "black",
        "--quiet",
        *format_paths,
    ]

    logger.debug(
        "Running command: {}",
        " ".join(cmd),
    )

    result = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def write_file_preserve_eol(
    path: Path,
    content: str,
) -> None:
    newline = "\n"

    if path.exists():
        raw = path.read_bytes()

        if b"\r\n" in raw:
            newline = "\r\n"

    # Normalize model output first
    content = content.replace("\r\n", "\n")

    if newline == "\r\n":
        content = content.replace("\n", "\r\n")

    path.write_bytes(content.encode("utf-8"))


def apply_changes(
    repo_root: str,
    changes: list[dict],
    boundaries: list[str],
) -> list[str]:
    """Apply model changes relative to repo_root within allowed boundaries."""
    root = Path(repo_root).resolve()

    resolved_boundaries = [
        resolve_repo_path(
            repo_root,
            boundary,
        )
        for boundary in boundaries
    ]

    changed_files = []

    for change in changes:
        path = change["path"]

        file_path = resolve_repo_path(
            repo_root,
            path,
        )

        if not any(
            file_path == boundary or boundary in file_path.parents
            for boundary in resolved_boundaries
        ):
            raise RuntimeError(
                "Model attempted to modify a file " f"outside edit boundaries: {path}"
            )

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        write_file_preserve_eol(
            file_path,
            change["content"],
        )

        changed_files.append(path)

    return changed_files


def git_stash(
    repo_root: str,
    message: str = "minpipe-agent pre-run",
    boundaries: list[str] | None = None,
) -> dict:
    boundaries = boundaries or []

    cmd = [
        "git",
        "stash",
        "push",
        "-u",
        "-m",
        message,
    ]

    if boundaries:
        cmd.append("--")
        cmd.extend(boundaries)

    logger.debug(
        "Running command: {}",
        " ".join(cmd),
    )

    result = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def git_create_worktree(
    repo_root: str,
    base_ref: str = "origin/main",
) -> str:
    worktree_root = tempfile.mkdtemp(prefix="minpipe-agent-")

    # git worktree expects to create the directory itself.
    Path(worktree_root).rmdir()

    cmd = [
        "git",
        "worktree",
        "add",
        "--detach",
        worktree_root,
        base_ref,
    ]

    logger.debug(
        "Running command: {}",
        " ".join(cmd),
    )

    result = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to create worktree:\n" f"{result.stderr}")

    return worktree_root


def git_remove_worktree(
    repo_root: str,
    worktree_root: str,
) -> None:
    cmd = [
        "git",
        "worktree",
        "remove",
        "--force",
        worktree_root,
    ]

    logger.debug(
        "Running command: {}",
        " ".join(cmd),
    )

    result = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to remove worktree:\n" f"{result.stderr}")


def git_fetch_main(
    repo_root: str,
) -> None:
    cmd = [
        "git",
        "fetch",
        "origin",
        "main",
    ]

    logger.debug(
        "Running command: {}",
        " ".join(cmd),
    )

    result = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch origin/main:\n" f"{result.stderr}")


def git_create_patch(
    repo_root: str,
    patch_path: str,
) -> str:
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_root,
        capture_output=True,
        check=True,
    )

    result = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--binary",
            "--full-index",
            "HEAD",
        ],
        cwd=repo_root,
        capture_output=True,
        check=True,
    )

    patch_file = Path(patch_path)
    patch_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    patch_file.write_bytes(result.stdout)

    return str(patch_file)
