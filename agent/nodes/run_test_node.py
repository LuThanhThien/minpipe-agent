import re
from typing import Any, Dict, List, Tuple, TypedDict
from loguru import logger

from ..tools import run_pytest
from .base_node import BaseNode


class RunTestNode(BaseNode):
    def __init__(
        self,
        k_test_folder: str,
        k_targeted_test_output: str,
        k_targeted_test_passed: str,
        k_passed_tests: str,
        k_failed_tests: str,
    ):
        super().__init__()
        self.k_test_folder = k_test_folder
        self.k_targeted_test_output = k_targeted_test_output
        self.k_targeted_test_passed = k_targeted_test_passed
        self.k_passed_tests = k_passed_tests
        self.k_failed_tests = k_failed_tests

    def _parse_test_results(self, output: str) -> Tuple[List[str], List[str]]:
        passed_tests: List[str] = []
        failed_tests: List[str] = []

        # Normal verbose test result:
        # models/unit/test_relu.py::test_minpipe PASSED
        # models/unit/test_sqrt.py::test_minpipe FAILED
        test_pattern = re.compile(
            r"^(?P<test>\S+::\S+)\s+"
            r"(?P<status>PASSED|FAILED|ERROR|XPASS|XFAIL|SKIPPED)\b",
            re.MULTILINE,
        )

        # Collection error summary:
        # ERROR models/unit/test_sqrt.py
        collection_error_pattern = re.compile(
            r"^ERROR\s+(?P<test>\S+\.py)\s*$",
            re.MULTILINE,
        )

        for match in test_pattern.finditer(output):
            test_name = match.group("test")
            status = match.group("status")

            if status == "PASSED":
                passed_tests.append(test_name)

            elif status in {"FAILED", "ERROR", "XPASS"}:
                failed_tests.append(test_name)

        for match in collection_error_pattern.finditer(output):
            test_name = match.group("test")

            if test_name not in failed_tests:
                failed_tests.append(test_name)

        return passed_tests, failed_tests

    def invoke(self, state: TypedDict):
        test_folder = state[self.k_test_folder]
        result: Dict[str, Any] = run_pytest(path=test_folder)

        combined_output = result["stdout"] + result["stderr"]
        passed_tests, failed_tests = self._parse_test_results(combined_output)

        return {
            self.k_targeted_test_output: combined_output,
            self.k_targeted_test_passed: result["returncode"] == 0,
            self.k_passed_tests: passed_tests,
            self.k_failed_tests: failed_tests,
        }

    def print_result(self, result: TypedDict):
        cmd_outs = result.get(self.k_targeted_test_output, "")
        logger.debug(f"Test outputs:\n{cmd_outs}")

        failed_tests = result.get(self.k_failed_tests, [])
        test_failed_str = "\n".join(failed_tests)
        logger.info(f"Total test failed: {len(failed_tests)}")
        print(test_failed_str)

        passed_tests = result.get(self.k_passed_tests, [])
        test_passed_str = "\n".join(passed_tests)
        logger.info(f"Total test passed: {len(passed_tests)}")
        print(test_passed_str)
