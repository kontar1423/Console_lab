"""Фикстуры для тестов. Позволяет не писать всё это руками в каждом тесте."""
import logging
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
import pytest
from typer.testing import CliRunner


@pytest.fixture
def mock_logger():
    logger = Mock(spec=logging.Logger)
    logger.info = MagicMock()  # Для функций, которые есть у logger, мы можем использовать MagicMock
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.exception = MagicMock()
    return logger


@pytest.fixture
def temp_state_file(tmp_path):
    return tmp_path / ".console_app_state.json"


@pytest.fixture
def temp_history_file(tmp_path):
    return tmp_path / ".console_app_history.json"


@pytest.fixture
def temp_undo_file(tmp_path):
    return tmp_path / ".console_app_undo.json"


@pytest.fixture
def temp_backup_dir(tmp_path):
    backup_dir = tmp_path / ".console_app_backups"
    backup_dir.mkdir(exist_ok=True)
    return backup_dir

@pytest.fixture(autouse=True)
def mock_logging():
    with patch('src.main.logging.config.dictConfig'):
        yield

@pytest.fixture
def runner():
    return CliRunner()