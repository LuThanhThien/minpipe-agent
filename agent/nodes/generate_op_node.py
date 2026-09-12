import json
import re

from loguru import logger

from .base_node import BaseNode
from ..providers import ModelProvider
from ..state import GraphState
from ..tools import apply_changes, read_file, read_prompt


class GenerateOpNode(BaseNode):
    def __init__(
        self,
        provider: ModelProvider,
    ):
        super().__init__()

        self.provider = provider

    def invoke(self, state: GraphState):
        attempts = state.get("generate_attempts", 0) + 1

        worktree_root = state.get("worktree_root")
        if not worktree_root:
            return {
                "generate_succeeded": False,
                "generate_error": "worktree_root is not available in graph state",
                "generate_attempts": attempts,
            }

        op = state.get("op")
        test = state.get("test")
        boundaries = state.get("boundaries", [])

        if not op or not test:
            logger.warning("Op/test are not found in the state")
            return {
                "generate_succeeded": False,
                "generate_error": "op/test are not available in graph state",
                "generate_attempts": attempts,
            }

        response = ""
        changed_files = []

        try:
            context = self._build_context(
                op=op,
                test=test,
                worktree_root=worktree_root,
                validation_output=state.get(
                    "validation_output",
                    "",
                ),
                generate_error=state.get(
                    "generate_error",
                    "",
                ),
            )

            prompt = self._build_prompt(
                op=op,
                test=test,
                context=context,
            )

            logger.debug("Prompt:\n{}", prompt)

            response = self.provider.invoke(prompt)

            logger.info("Response:\n{}", response)

            changes = self._parse_response(response)

            self._validate_changes(changes)

            changed_files = apply_changes(
                repo_root=worktree_root,
                changes=changes,
                boundaries=boundaries,
            )

            if not changes:
                return {
                    "generate_changed_files": changed_files,
                    "generate_response": response,
                    "generate_succeeded": False,
                    "generate_error": "No changes were made.",
                    "generate_attempts": attempts,
                }

            return {
                "generate_changed_files": changed_files,
                "generate_response": response,
                "generate_succeeded": True,
                "generate_error": "",
                "generate_attempts": attempts,
            }

        except Exception as exc:
            return {
                "generate_changed_files": changed_files,
                "generate_response": response,
                "generate_succeeded": False,
                "generate_error": str(exc),
                "generate_attempts": attempts,
            }

    def _build_context(
        self,
        op: str,
        test: str,
        worktree_root: str,
        validation_output: str,
        generate_error: str,
    ) -> dict:
        return {
            "failure": self._extract_failure(
                validation_output,
                op,
            ),
            "test_source": self._read_optional(
                worktree_root,
                test,
            ),
            "existing_op_source": self._read_optional(
                worktree_root,
                f"minpipe/ops/{op}.py",
                default="Not found",
            ),
            "registry_source": self._read_optional(
                worktree_root,
                "minpipe/ops/operation.py",
            ),
            "ops_init_source": self._read_optional(
                worktree_root,
                "minpipe/ops/__init__.py",
            ),
            "similar_ops": self._build_similar_ops_context(
                op=op,
                worktree_root=worktree_root,
            ),
            "previous_validation_output": (
                validation_output
                if validation_output
                else "No previous targeted validation output."
            ),
            "previous_generate_error": (
                generate_error if generate_error else "No previous generation error."
            ),
        }

    def _build_similar_ops_context(
        self,
        op: str,
        worktree_root: str,
    ) -> str:
        candidates = [
            "relu",
            "sigmoid",
            "square",
        ]

        sections = []

        for candidate in candidates:
            if candidate == op:
                continue

            path = f"minpipe/ops/{candidate}.py"

            source = self._read_optional(
                worktree_root,
                path,
                default="",
            )

            if not source:
                continue

            sections.append(f"# {path}\n\n{source}")

        if not sections:
            return "No similar working operations found."

        return "\n\n".join(sections)

    def _read_optional(
        self,
        worktree_root: str,
        path: str,
        default: str = "",
    ) -> str:
        try:
            return read_file(
                repo_root=worktree_root,
                path=path,
            )
        except (FileNotFoundError, OSError):
            return default

    def _extract_failure(
        self,
        output: str,
        op: str,
    ) -> str:
        if not output:
            return f"Unknown operation: {op}"

        patterns = [
            rf"KeyError:\s*['\"]Unknown operation:\s*{re.escape(op)}['\"]",
            rf"Unknown operation:\s*{re.escape(op)}",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                output,
                re.IGNORECASE,
            )

            if match:
                return match.group(0)

        return output[-2000:]

    def _build_prompt(
        self,
        op: str,
        test: str,
        context: dict,
    ) -> str:
        return read_prompt("generate_op.md").format(
            op=op,
            test=test,
            failure=context["failure"],
            test_source=context["test_source"],
            existing_op_source=context["existing_op_source"],
            registry_source=context["registry_source"],
            ops_init_source=context["ops_init_source"],
            similar_ops=context["similar_ops"],
            previous_validation_output=context["previous_validation_output"],
            previous_generate_error=context["previous_generate_error"],
        )

    def _parse_response(
        self,
        response: str,
    ) -> list[dict]:
        text = response.strip()

        fenced = re.search(
            r"```(?:json)?\s*(.*?)```",
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if fenced:
            text = fenced.group(1).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "GenerateOpNode received invalid JSON:\n" f"{response}"
            ) from exc

        changes = data.get("changes")

        if not isinstance(changes, list):
            raise RuntimeError(
                "Model response does not contain " "a valid 'changes' list"
            )

        return changes

    def _validate_changes(
        self,
        changes: list[dict],
    ):
        for change in changes:
            path = change.get("path", "")
            content = change.get("content", "")

            if not path or not content:
                raise RuntimeError("Invalid change entry")

            if path.startswith("models/"):
                raise RuntimeError("Model attempted to modify " f"test file: {path}")

            if "\n" not in content:
                raise RuntimeError(
                    "Generated content does not " f"look like source code: {path}"
                )

    def print_result(
        self,
        result: GraphState,
    ):
        changed_files = result.get(
            "generate_changed_files",
            [],
        )

        succeeded = result.get(
            "generate_succeeded",
            False,
        )

        error = result.get(
            "generate_error",
            "",
        )

        if not succeeded:
            logger.error(
                "GenerateOpNode failed: {}",
                error,
            )
            return

        if not changed_files:
            logger.warning("GenerateOpNode made no changes")
            return

        logger.success("GenerateOpNode completed successfully")

        logger.info(
            "Changed {} file(s):",
            len(changed_files),
        )

        for file in changed_files:
            logger.info(
                "  {}",
                file,
            )
