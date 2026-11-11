PYTHON ?= python3.12
PYTEST := .venv/bin/python -m pytest
RUFF := .venv/bin/python -m ruff
TY := .venv/bin/ty
CONTAINER := ts3-test-$(shell echo $$$$)

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
	docker rm -f $(CONTAINER) || true
	docker run -p 127.0.0.1:10022:10022 -p 9987:9987/udp -p 30033:30033 \
		-e TS3SERVER_LICENSE=accept \
		-e TS3SERVER_QUERY_PROTOCOLS=ssh \
		-e TS3SERVER_QUERY_SSH_PORT=10022 \
		-e TS3SERVER_SERVERADMIN_PASSWORD=IntegrationAdmin123 \
		--name $(CONTAINER) -d teamspeak:3.13
	@TS3_INTEGRATION=1 QUERY_ADMIN_PASSWORD="IntegrationAdmin123" $(PYTEST) -m integration -v; \
	STATUS=$$?; docker rm -f $(CONTAINER) >/dev/null 2>&1 || true; \
	if [ $$STATUS -eq 0 ]; then echo "integration verification passed"; fi; \
	exit $$STATUS

test: test-unit test-integration
