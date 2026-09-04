from typing import TypedDict
from loguru import logger

from .base_node import BaseNode


class NextTestNode(BaseNode):
    def __init__(
        self,
        k_tests: str,
        k_ops: str,
        k_current_test: str,
        k_current_op: str,
        k_current_id: str,
        k_file: str,
    ):
        super().__init__()
        self.k_tests = k_tests
        self.k_ops = k_ops
        self.k_current_test = k_current_test
        self.k_current_op = k_current_op
        self.k_current_id = k_current_id
        self.k_file = k_file

    def invoke(self, state: TypedDict):
        tests = state.get(self.k_tests, [])
        ops = state.get(self.k_ops, [])
        index = state.get(self.k_current_id, 0)

        if index >= len(tests) or index >= len(ops):
            return {
                self.k_file: None,
                self.k_current_test: None,
                self.k_current_op: None,
                self.k_current_id: None,
            }

        current_test = tests[index]
        current_op = ops[index]
        file_path = current_test.split("::", 1)[0]

        return {
            self.k_file: file_path,
            self.k_current_test: current_test,
            self.k_current_op: current_op,
            self.k_current_id: index + 1,
        }

    def print_result(self, result: TypedDict):
        cid = result.get(self.k_current_id, "N/A")
        file = result.get(self.k_file, "N/A")
        logger.info(f"Next test {cid} {file}")
