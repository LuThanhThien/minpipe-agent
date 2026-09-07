from typing import TypedDict


class GraphState(TypedDict):
    # Consts - init
    max_attempts: int
    boundaries: list[str]
    repo_root: str

    # Share
    op: str
    test: str
    artifact_dir: str
    worktree_root: str

    # Prepare repo
    repo_prepare_succeeded: bool
    repo_prepare_output: str

    # Generate op
    generate_attempts: int
    generate_succeeded: bool
    generate_error: str
    generate_changed_files: list[str]
    generate_response: str

    # Formatting
    formatting_succeeded: bool
    formatting_output: str
    formatting_error: str

    # Validate op
    validation_succeeded: bool
    validation_output: str
    validation_error: str

    # Patch
    patch_path: str
    patch_succeeded: bool
    patch_error: str

    # Cleanup
    repo_cleanup_succeeded: bool
    repo_cleanup_output: str
