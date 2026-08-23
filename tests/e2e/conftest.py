from __future__ import annotations

import subprocess
import time

import pytest


@pytest.fixture(scope="session")
def app_server():
    proc = subprocess.Popen(
        ["python", "main.py"],
        env={
            "PYTHONPATH": "src",
            "SMTP_CONFIG_DIR": "/tmp/smtp_tool_e2e_test",
            "SESSION_SECRET": "e2e-test-secret",
            "LOG_LEVEL": "WARNING",
            "PYTHONUNBUFFERED": "1",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)
    yield "http://localhost:5000"
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def page(app_server, browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
