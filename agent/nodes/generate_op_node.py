import json
import re

from loguru import logger

from .base_node import BaseNode
from ..providers import ModelProvider
from ..state import GraphState
from ..tools import apply_changes, read_prompt


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
            context = state.get("op_context_result")

            if not context:
                return {
                    "generate_succeeded": False,
                    "generate_error": "op context is not available",
                    "generate_attempts": attempts,
                }

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
            previous_generate_changed_files=context["previous_generate_changed_files"],
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
