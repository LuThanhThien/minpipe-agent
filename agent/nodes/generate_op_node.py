import json
import re
from typing import TypedDict

from loguru import logger

from .base_node import BaseNode
from ..providers import ModelProvider
from ..tools import apply_changes, read_file

GENERATE_OP_INSTRUCTIONS = GENERATE_OP_INSTRUCTIONS = """
You are implementing one missing or incorrect operation in MinPipe.

TARGET OPERATION
{op}

REPRODUCER TEST
{test}

CURRENT FAILURE
{failure}

TEST SOURCE
{test_source}

EXISTING IMPLEMENTATION FOR CURRENT OP
{existing_op_source}

OPERATION FRAMEWORK / REGISTRY
{registry_source}

OPERATION PACKAGE REGISTRATION
{ops_init_source}

WORKING OPERATION EXAMPLES
{similar_ops}

PREVIOUS VALIDATION OUTPUT
{previous_validation_output}


MINPIPE ARCHITECTURE RULES

- Operations register themselves through @Operation.register.
- The decorator executes only when the Python module defining the operation is imported.
- minpipe/ops/__init__.py imports supported operation modules.
- If an operation module is not imported, its registration decorator does not execute.
- Runtime execution resolves operations through the operation registry.

Creating the operation implementation alone is NOT sufficient.
You must verify the complete integration path:

    implementation
        -> module import
        -> decorator execution
        -> registry entry
        -> runtime lookup


DIAGNOSIS CHECKLIST

Before generating changes, determine:

1. Does minpipe/ops/{op}.py exist?
2. If it exists, is its implementation correct?
3. Is the {op} module imported by minpipe/ops/__init__.py?
4. Will importing minpipe.ops execute @Operation.register for {op}?
5. Will the runtime operation registry resolve "{op}"?

Do not assume registration is complete merely because
@Operation.register appears in the implementation file.


TASK

Enable support for the target operation.

Requirements:
- Diagnose whether the operation is missing, incorrectly implemented,
  incorrectly imported, or incorrectly registered.
- Make the minimum necessary source changes.
- Follow existing MinPipe patterns shown in the context.
- Do not modify tests.
- Do not weaken validation.
- Do not modify unrelated files.
- If an implementation already exists, fix it instead of creating a duplicate.
- Include ALL required files in "changes".
- Do not return a partial implementation.

When modifying an existing file:
- Preserve its current import style and structure.
- Make the smallest possible diff.
- Do not refactor unrelated existing code.

SUCCESS CONDITION

The change is complete only if:

1. The reproducer test can pass.
2. Importing minpipe.ops loads the target operation module.
3. The target operation's registration decorator executes.
4. Runtime lookup resolves "{op}" successfully.

EDITING RULES

- Preserve all unrelated existing code, imports, formatting, and behavior.
- Make only the minimal changes required for the requested operation.
- Do not remove, rewrite, or reorganize existing code unless directly necessary.
- When updating registration files such as `minpipe/ops/__init__.py`, add the required import while preserving all existing imports and registrations.

OUTPUT FORMAT 

Return ONLY valid JSON in this format:

{{
  "diagnosis": {{
    "implementation_exists": "...",
    "implementation_correct": "...",
    "module_imported": "...",
    "registration_triggered": "...",
    "runtime_lookup_available": "..."
  }},
  "changes": [
    {{
      "path": "path/to/file.py",
      "content": "complete new file content"
    }}
  ]
}}

Do not use markdown code fences.
Do not include explanations outside the JSON.
"""


class GenerateOpNode(BaseNode):
    def __init__(
        self,
        provider: ModelProvider,
    ):
        super().__init__()

        self.provider = provider
        self.boundaries = ["./minpipe"]

    def invoke(self, state: TypedDict):
        attempts = state.get("attempts", 0)

        # Temporary hardcoded values.
        # Later replace these with state values.
        op = state.get("op", None)
        test = state.get("test", None)
        if op is None or test is None:
            logger.warning(f"Op/test are not found in the state")
            return {}

        response = ""
        changed_files = []

        try:
            context = self._build_context(
                op=op,
                test=test,
                validation_output=state.get(
                    "validation_output",
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
                changes,
                self.boundaries,
            )

            return {
                "changed_files": changed_files,
                "response": response,
                "success": True,
                "error": "",
                "attempts": attempts,
            }

        except Exception as exc:
            return {
                "changed_files": changed_files,
                "response": response,
                "success": False,
                "error": str(exc),
                "attempts": attempts,
            }

    def _build_context(
        self,
        op: str,
        test: str,
        validation_output: str,
    ) -> dict:
        return {
            "failure": self._extract_failure(
                validation_output,
                op,
            ),
            "test_source": self._read_optional(test),
            "existing_op_source": self._read_optional(
                f"minpipe/ops/{op}.py",
                default="Not found",
            ),
            "registry_source": self._read_optional(
                "minpipe/ops/operation.py",
            ),
            "ops_init_source": self._read_optional(
                "minpipe/ops/__init__.py",
            ),
            "similar_ops": self._build_similar_ops_context(
                op,
            ),
            "previous_validation_output": (
                validation_output
                if validation_output
                else "No previous targeted validation output."
            ),
        }

    def _build_similar_ops_context(
        self,
        op: str,
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
        path: str,
        default: str = "",
    ) -> str:
        try:
            return read_file(path)
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
        return GENERATE_OP_INSTRUCTIONS.format(
            op=op,
            test=test,
            failure=context["failure"],
            test_source=context["test_source"],
            existing_op_source=context["existing_op_source"],
            registry_source=context["registry_source"],
            ops_init_source=context["ops_init_source"],
            similar_ops=context["similar_ops"],
            previous_validation_output=context["previous_validation_output"],
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
                f"GenerateOpNode received invalid JSON:\n{response}"
            ) from exc

        changes = data.get("changes")

        if not isinstance(changes, list):
            raise RuntimeError("Model response does not contain a valid 'changes' list")

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
                raise RuntimeError(f"Model attempted to modify test file: {path}")

            if "\n" not in content:
                raise RuntimeError(
                    f"Generated content does not look like source code: {path}"
                )

    def print_result(
        self,
        result: TypedDict,
    ):
        changed_files = result.get(
            "changed_files",
            [],
        )

        succeeded = result.get(
            "success",
            False,
        )

        error = result.get(
            "error",
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
            logger.info("  {}", file)
