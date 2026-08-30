cfg:
	bash ./scripts/configure.sh

build:
	bash ./scripts/activate && bash ./scripts/build.sh

test:
	pytest -m models