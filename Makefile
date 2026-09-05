.PHONY: cfg build test agent

cfg:
	bash ./scripts/configure.sh

build:
	bash ./scripts/activate && bash ./scripts/build.sh

test:
	pytest -m models

agent:
	python -m agent --config ./agent/configs/ollama_qwen.py
