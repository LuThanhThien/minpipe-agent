from typing import TypedDict


class GraphState(TypedDict):
    op: str
    test: str

    # Prepare repo
    repo_prepare_succeeded: bool
    repo_prepare_output: str

    # Generate op
    attempts: int
    max_attempts: int
    success: bool
    error: str
    file_changes: list[str]
    response: str
