import json
from typing import TypedDict
import re

from loguru import logger

from .base_node import BaseNode
from ..providers import ModelProvider
from ..tools import apply_changes

ENABLE_OP_INSTRUCTIONS = """
You are implementing operation support in MinPipe.

Unsupported operation:
{}

Reproducer test:
{}

Repository context:
{}

Previous validation output:
{}

Your task:
- Enable support for the operation.
- Follow the existing MinPipe operation implementation pattern.
- Make the minimum necessary changes.
- Do not modify tests.
- Do not weaken validation.
- Do not modify unrelated files.

Return ONLY valid JSON in this format:

{{
  "changes": [
    {{
      "path": "path/to/file.py",
      "content": "complete new file content"
    }}
  ]
}}

Do not use markdown code fences.
"""


class EnableOpNode(BaseNode):
    def __init__(
        self,
        provider: ModelProvider,
        k_op: str,
        k_test: str,
        k_context: str,
        k_validation_output: str,
        k_changed_files: str,
        k_response: str,
        k_succeeded: str,
        k_error: str,
        k_attempts: str,
    ):
        super().__init__()

        self.provider = provider

        self.k_op = k_op
        self.k_test = k_test
        self.k_context = k_context
        self.k_validation_output = k_validation_output

        self.k_changed_files = k_changed_files
        self.k_response = k_response
        self.k_succeeded = k_succeeded
        self.k_error = k_error
        self.k_attempts = k_attempts

        self.boundaries = ["./minpipe"]

    def invoke(self, state: TypedDict):
        op = state[self.k_op]
        test = state[self.k_test]

        context = state.get(self.k_context, "")
        validation_output = state.get(self.k_validation_output, "")

        response = ""
        changed_files = []

        cur_attempts = state.get(self.k_attempts, 0) + 1

        try:
            prompt = self._build_prompt(
                op,
                test,
                context,
                validation_output,
            )

            response = self.provider.invoke(prompt)

            logger.info(f"Response:\n{response}")

            changes = self._parse_response(response)
            self._validate_changes(changes)
            changed_files = apply_changes(changes, self.boundaries)

            return {
                self.k_changed_files: changed_files,
                self.k_response: response,
                self.k_succeeded: True,
                self.k_error: "",
                self.k_attempts: cur_attempts,
            }

        except Exception as exc:
            return {
                self.k_changed_files: changed_files,
                self.k_response: response,
                self.k_succeeded: False,
                self.k_error: str(exc),
                self.k_attempts: cur_attempts,
            }

    def _build_prompt(
        self,
        op: str,
        test: str,
        context: str,
        validation_output: str,
    ) -> str:
        return ENABLE_OP_INSTRUCTIONS.format(op, test, context, validation_output)

    def _parse_response(self, response: str) -> list[dict]:
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
                f"EnableOpNode received invalid JSON:\n{response}"
            ) from exc

        changes = data.get("changes")

        if not isinstance(changes, list):
            raise RuntimeError("Model response does not contain a valid 'changes' list")

        return changes

    def _validate_changes(self, changes: list[dict]):
        for change in changes:
            path = change.get("path", "")
            content = change.get("content", "")

            if not path or not content:
                raise RuntimeError("Invalid change entry")

            if "\n" not in content:
                raise RuntimeError(
                    f"Generated content does not look like source code: {path}"
                )

    def print_result(self, result: TypedDict):
        changed_files = result.get(
            self.k_changed_files,
            [],
        )
        succeeded = result.get(self.k_succeeded, False)
        error = result.get(self.k_error, "")

        if not succeeded:
            logger.error("EnableOpNode failed: {}", error)
            return

        if not changed_files:
            logger.warning("EnableOpNode made no changes")
            return

        logger.success("EnableOpNode completed successfully")
        logger.info(f"Changed {len(changed_files)} file(s):")

        for file in changed_files:
            logger.info(f"  {file}")
