from typing import Any, Dict

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
"""


def build_code_explainer_prompt(code: str) -> str:
    return f"""{CODE_EXPLAINER_INSTRUCTIONS}

Code:
{code}
"""


class ExplainCodeNode(BaseNode):
    def __call__(self, state):
        code = read_file.invoke({"path": state["file"]})

        prompt = build_code_explainer_prompt(code)
        text = self.provider.invoke(prompt)

        return {
            "response": text,
        }
