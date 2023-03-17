dependencies:
	python3 -m venv .venv
	. ./.venv/bin/activate
	python3 -m pip install -r requirements.dev.txt

lint: dependencies
	black -l 120 .
	isort --profile black .
	autoflake -r -i --ignore-init-module-imports .

test: dependencies
	rm -f ./tests/test.log
	docker rm -f TS3_TEST_CONTAINER || true
	docker run -p 9987:9987/udp -p 10011:10011 -p 30033:30033 -e TS3SERVER_LICENSE=accept --name TS3_TEST_CONTAINER -d teamspeak:3.13
	sleep 1
	QUERY_ADMIN_PASSWORD=$$(docker logs TS3_TEST_CONTAINER 2>&1 | less | grep password | cut -d ',' -f 2 | cut -d '"' -f 2) pytest -s