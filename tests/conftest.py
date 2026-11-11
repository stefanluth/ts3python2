"""Test bootstrap for isolated per-worker log directories."""

import os

_integration = os.getenv("TS3_INTEGRATION") == "1"
_worker = os.getenv("PYTEST_XDIST_WORKER")

if _integration and _worker:
    os.environ.setdefault("TS3_LOG_DIR", os.path.join("logs", _worker))
