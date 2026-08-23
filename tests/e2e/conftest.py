from __future__ import annotations

import os
import subprocess
import time
import urllib.error
import urllib.request

import pytest


@pytest.fixture(scope="session")
def app_server():
    proc = subprocess.Popen(
        ["python", "main.py"],
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "SMTP_CONFIG_DIR": "/tmp/smtp_tool_e2e_test",
            "SESSION_SECRET": "e2e-test-secret",
            "LOG_LEVEL": "WARNING",
            "PYTHONUNBUFFERED": "1",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    url = "http://localhost:5000"
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"App process exited with code {proc.returncode}")
        try:
            urllib.request.urlopen(f"{url}/health_check", timeout=2)
            break
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError("App server did not start within 30 seconds")
    yield url
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def page(app_server, browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
