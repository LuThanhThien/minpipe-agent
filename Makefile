.PHONY: cfg build test agent

cfg:
	bash ./scripts/configure.sh

build:
	bash ./scripts/activate && bash ./scripts/build.sh

test:
	pytest -m models

agent:
	python -m agent \
		--config ./agent/configs/ollama_qwen.py \
		--op floor \
		--test ./models/unit/test_floor.py

tu:
	pytest -sv models/unit/test_floor.py
