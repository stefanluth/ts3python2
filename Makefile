dependencies:
	python3 -m venv .venv
	. ./.venv/bin/activate
	python3 -m pip install -r requirements.txt
	python3 -m pip install -r requirements.dev.txt

lint: dependencies
	black .
	isort --profile black .
	autoflake -r -i --ignore-init-module-imports .
