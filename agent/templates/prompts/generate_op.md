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

PREVIOUS GENERATION ERROR
{previous_generate_error}

MINPIPE ARCHITECTURE RULES

- Operations register themselves through @Operation.register.
- The decorator executes only when the Python module defining the operation is imported.
- minpipe/ops/__init__.py imports supported operation modules.
- If an operation module is not imported, its registration decorator does not execute.
- Runtime execution resolves operations through the operation registry.

Creating the operation implementation alone is NOT sufficient.
You must verify the complete integration path:

```
implementation
    -> module import
    -> decorator execution
    -> registry entry
    -> runtime lookup
```

DIAGNOSIS CHECKLIST

Before generating changes, determine:

1. Does minpipe/ops/{op}.py exist?
1. If it exists, is its implementation correct?
1. Is the {op} module imported by minpipe/ops/__init__.py?
1. Will importing minpipe.ops execute @Operation.register for {op}?
1. Will the runtime operation registry resolve "{op}"?

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
1. Importing minpipe.ops loads the target operation module.
1. The target operation's registration decorator executes.
1. Runtime lookup resolves "{op}" successfully.

EDITING RULES

- Preserve all unrelated existing code, imports, formatting, and behavior.
- Make only the minimal changes required for the requested operation.
- Do not remove, rewrite, or reorganize existing code unless directly necessary.
- When updating registration files such as `minpipe/ops/__init__.py`, add the required import while preserving all existing imports and registrations.

OUTPUT FORMAT

Return ONLY valid JSON in this format:

```json
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
```

Do not use markdown code fences.
Do not include explanations outside the JSON.
