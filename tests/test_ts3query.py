import os
from ts3client.ts3query import TS3Query
from ts3client.utils.logger import create_logger

logger = create_logger("TS3Query", "./tests/test.log")


def test_ts3query_login():
    login = "serveradmin"
    password = os.getenv("QUERY_ADMIN_PASSWORD")
    assert password is not None
    ts3query = TS3Query("localhost", 10011)
    login_response = ts3query.login(login, password)
    assert login_response.error_id == 0
    assert login_response.msg == "ok"


def test_ts3query_use():
    login = "serveradmin"
    password = os.getenv("QUERY_ADMIN_PASSWORD")
    assert password is not None
    logger.info("Starting test_ts3query_use")
    ts3query = TS3Query("localhost", 10011)
    login_response = ts3query.login(login, password)
    assert login_response.error_id == 0
    assert login_response.msg == "ok"
    use_response = ts3query.commands.use(1)
    assert use_response.error_id == 0
    assert use_response.msg == "ok"


def test_ts3query_login_fail():
    login = "serveradmin"
    password = "wrong_password"
    logger.info("Starting test_ts3query_login_fail")
    ts3query = TS3Query("localhost", 10011)
    login_response = ts3query.login(login, password)
    assert login_response.error_id == 520
    assert login_response.msg == "invalid loginname or password"


def test_ts3query_logout():
    login = "serveradmin"
    password = os.getenv("QUERY_ADMIN_PASSWORD")
    assert password is not None
    logger.info("Starting test_ts3query_logout")
    ts3query = TS3Query("localhost", 10011, login, password)
    logout_response = ts3query.logout()
    assert logout_response.error_id == 0
    assert logout_response.msg == "ok"


def test_ts3query_logout_fail():
    logger.info("Starting test_ts3query_logout_fail")
    ts3query = TS3Query("localhost", 10011)
    logout_response = ts3query.logout()
    assert logout_response.error_id == 518
    assert logout_response.msg == "not logged in"
