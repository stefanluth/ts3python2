PYTHON ?= python3.14
PYTEST := .venv/bin/python -m pytest
RUFF := .venv/bin/python -m ruff
TY := .venv/bin/ty
JOBS ?= 4
TS3_TEST_IMAGE ?= teamspeak:3.13.9

.venv/bin/python:
	$(PYTHON) -m venv .venv

dependencies: .venv/bin/python
	.venv/bin/python -m pip install -r requirements.dev.txt

lint: dependencies
	$(RUFF) check --fix .
	$(RUFF) format .

lint-check: dependencies
	$(RUFF) check .
	$(RUFF) format --check .

typecheck: dependencies
	$(TY) check .

test-unit: dependencies
	$(PYTEST) -m "not integration"

test-integration: dependencies
	@TS3_INTEGRATION=1 QUERY_ADMIN_PASSWORD="IntegrationAdmin123" \
		TS3_MANAGE_CONTAINER=1 TS3_TEST_IMAGE="$(TS3_TEST_IMAGE)" \
		$(PYTEST) -m integration -n $(JOBS) -v; \
	STATUS=$$?; \
	if [ $$STATUS -eq 0 ]; then echo "integration verification passed"; fi; \
	exit $$STATUS

test: test-unit test-integration
