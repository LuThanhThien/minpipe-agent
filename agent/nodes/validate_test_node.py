from typing import TypedDict
from loguru import logger

from .base_node import BaseNode
from ..tools import run_pytest


class ValidateTestNode(BaseNode):
    def __init__(
        self,
        k_current_unsup_op_test: str,
        k_current_unsup_op: str,
        k_op_validation_passed: str,
        k_op_validation_output: str,
    ):
        super().__init__()
        self.k_current_unsup_op_test = k_current_unsup_op_test
        self.k_current_unsup_op = k_current_unsup_op
        self.k_op_validation_passed = k_op_validation_passed
        self.k_op_validation_output = k_op_validation_output

    def invoke(self, state: TypedDict):
        test = state.get(self.k_current_unsup_op_test, None)

        if test is None:
            return {}

        result = run_pytest(path=test)

        output = result["stdout"] + result["stderr"]

        return {
            self.k_op_validation_passed: result["returncode"] == 0,
            self.k_op_validation_output: output,
        }

    def print_result(self, result: TypedDict):
        test = result.get(self.k_current_unsup_op_test, "")
        op = result.get(self.k_current_unsup_op, "")
        passed = result.get(self.k_op_validation_passed, False)

        if passed:
            logger.success(
                f"Validation passed for op '{op}' with test: {test}",
            )
        else:
            logger.error(f"Validation failed for op '{op}' with test: {test}")

            output = result.get(self.k_op_validation_output, "")
            if output:
                logger.error("Test output:\n{}", output)
