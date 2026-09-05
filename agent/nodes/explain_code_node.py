from typing import TypedDict

from .base_node import BaseNode
from ..tools import read_file

CODE_EXPLAINER_INSTRUCTIONS = """You are a code analysis assistant.

Your task is to explain source code clearly and concisely.

When given code, explain:
1. What the code does.
2. The important classes and functions.
3. How the execution flow works.
4. Any important dependencies or relationships.

Do not modify the code.
Do not generate replacement code unless explicitly asked.

Code:
{}
"""


class ExplainCodeNode(BaseNode):
    def __init__(self, provider, k_file: str, k_response: str):
        super().__init__()
        self.provider = provider
        self.k_file = k_file
        self.k_response = k_response

    def invoke(self, state: TypedDict):
        file = state.get(self.k_file, None)

        if file is None:
            return {}

        code = read_file(path=file)

        prompt = self._build_prompt(code)
        text = self.provider.invoke(prompt)

        return {
            self.k_response: text,
        }

    def _build_prompt(self, code: str) -> str:
        return CODE_EXPLAINER_INSTRUCTIONS.format(code)

    def print_result(self, result: TypedDict):
        print("Code Explanation:")
        print(result[self.k_response])
