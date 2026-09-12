from typing import TypedDict


def after_generate_op_route():

    def _route(state: TypedDict) -> str:
        if state.get("generate_succeeded", False):
            return "success"

        attempts = state.get("generate_attempts", 0)
        max_attempts = state.get("max_attempts", 3)

        if attempts < max_attempts:
            return "retry"

        return "failed"

    return _route


def after_validate_op_route():

    def _route(state: TypedDict) -> str:
        if state.get("validation_succeeded", False):
            return "success"

        attempts = state.get("attempts", 0)
        max_attempts = state.get("max_attempts", 3)

        if attempts < max_attempts:
            return "retry"

        return "failed"

    return _route


def after_formatting_route():

    def _route(state: TypedDict) -> str:
        if state.get("formatting_succeeded", False):
            return "success"

        return "failed"

    return _route
