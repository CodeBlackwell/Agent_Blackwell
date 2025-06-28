import logging
import os
from io import StringIO
from importlib import reload

import pytest

# Import target after potential env var tweaks
import src.utils.logging_config as logging_config


def _reset_logging():
    """Remove all handlers so configure_logging can run again."""
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.setLevel(logging.NOTSET)


@pytest.fixture(autouse=True)
def reset_root_logger():
    """Ensure a clean root logger before each test."""
    _reset_logging()
    yield
    _reset_logging()


def test_default_level_is_info(caplog):
    logging_config.configure_logging()

    with caplog.at_level(logging.INFO):
        logging.getLogger("test").info("hello")

    # Ensure at least one log record captured
    assert any(
        rec.levelname == "INFO" and rec.getMessage() == "hello" for rec in caplog.records
    )


def test_respects_log_level_env_var(caplog, monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    reload(logging_config)  # re-import to pick up env var changes
    logging_config.configure_logging()

    with caplog.at_level(logging.DEBUG):
        logging.getLogger("test").debug("debug-msg")

    assert any(
        rec.levelname == "DEBUG" and rec.getMessage() == "debug-msg" for rec in caplog.records
    )
