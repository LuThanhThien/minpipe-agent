import re
from typing import TypedDict

from loguru import logger

from .base_node import BaseNode


class IdentifyUnsupportedOpsNode(BaseNode):
    OP_PATTERNS = [
        r"Unknown operation:\s*(?:torch\.)?([A-Za-z0-9_]+)",
    ]

    def __init__(
        self,
        k_targeted_test_output: str,
        k_unsup_ops: str,
        k_unsup_ops_tests: str,
        k_current_unsup_op_id: str,
    ):
        super().__init__()
        self.k_targeted_test_output = k_targeted_test_output
        self.k_unsup_ops = k_unsup_ops
        self.k_unsup_ops_tests = k_unsup_ops_tests
        self.k_current_unsup_op_id = k_current_unsup_op_id

    def _identify_op(self, text: str) -> str | None:
        for pattern in self.OP_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def invoke(self, state: TypedDict):
        output = state.get(self.k_targeted_test_output, "")

        unsup_ops = []
        unsup_ops_tests = []

        for line in output.splitlines():
            if not line.startswith("FAILED "):
                continue

            # Example:
            # FAILED models/unit/test_exp.py::test_exp - RuntimeError:
            # Unsupported operation: exp

            match = re.match(
                r"FAILED\s+(\S+)",
                line,
            )

            if not match:
                continue

            test_id = match.group(1)
            op = self._identify_op(line)

            print(f"line: {line}")
            print(f"Identified op: {op}")

            if op is None:
                continue

            # Avoid duplicate op entries.
            if op in unsup_ops:
                continue

            unsup_ops.append(op)
            unsup_ops_tests.append(test_id)

        return {
            self.k_unsup_ops: unsup_ops,
            self.k_unsup_ops_tests: unsup_ops_tests,
            self.k_current_unsup_op_id: 0,
        }

    def print_result(self, result: TypedDict):
        ops = result.get(self.k_unsup_ops, [])
        tests = result.get(self.k_unsup_ops_tests, [])

        if not ops:
            logger.info("No unsupported ops identified")
            return

        logger.info("Identified {} unsupported ops:", len(ops))

        for op, test in zip(ops, tests):
            logger.info(
                "  {} -> {}",
                op,
                test,
            )
