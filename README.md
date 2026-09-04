# Minpipe Agent

LangGraph-based code explanation agent with pluggable providers.

## Setting up

Create virtual python environment:

```bash
python -m venv .venv
```

Install dependencies

```bash
uv pip install -r requirements.txt
```

## Running the agent

The runtime configuration is loaded from a Python file containing a `CONFIG` dictionary.

Run the agent with the default `configs/monkey.py` or provide another config file:

```bash
python -m agent.main path/to/source.py
python -m agent.main --config other_config.py path/to/source.py
```
