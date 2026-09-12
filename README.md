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

## Model Providers

### Ollama Provider

Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Copilot Provider

First install/login:

```bash
npm install -g @github/copilot
```

Then 

```bash
copilot login
```

You can test programmatic invocation:

```bash
copilot -p "Write a Python function that adds two numbers" -s
```