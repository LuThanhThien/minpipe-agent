CONFIG = dict(
    nodes=dict(
        explain_code=dict(
            name="OllamaProvider",
            init_config=dict(
                model="qwen2.5-coder:0.5b",
                base_url="http://localhost:11434",
            ),
        ),
    ),
)
