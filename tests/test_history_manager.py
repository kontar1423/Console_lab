import json
from datetime import datetime
from pathlib import Path
import pytest

from src.services.history_manager import HistoryManager


class TestHistoryManager:

    def test_init_creates_history_manager(self, mock_logger, temp_history_file):
        manager = HistoryManager(mock_logger, history_file=temp_history_file)
        assert manager._logger == mock_logger
        assert manager.history_file == temp_history_file
        assert manager._history == []

    def test_init_loads_existing_history(self, mock_logger, temp_history_file):
        history_data = {
            "history": [
                {"timestamp": "2024-01-01T12:00:00", "command": "ls", "args": ["-l"]},
                {"timestamp": "2024-01-01T12:01:00", "command": "cd", "args": ["/tmp"]},
            ]
        }
        temp_history_file.write_text(json.dumps(history_data))
        
        manager = HistoryManager(mock_logger, history_file=temp_history_file)
        assert len(manager._history) == 2
        assert manager._history[0]["command"] == "ls"

    def test_init_truncates_old_history(self, mock_logger, temp_history_file):
        large_history = {
            "history": [
                {"timestamp": f"2024-01-01T{i:02d}:00:00", "command": f"cmd{i}", "args": []}
                for i in range(150)
            ]
        }
        temp_history_file.write_text(json.dumps(large_history))
        
        manager = HistoryManager(mock_logger, history_file=temp_history_file, max_history=100)
        assert len(manager._history) == 100

    def test_add_command_with_args(self, mock_logger, temp_history_file):
        manager = HistoryManager(mock_logger, history_file=temp_history_file)
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        manager.add_command("ls", ["-l", "/tmp"], timestamp=timestamp)
        
        assert len(manager._history) == 1
        entry = manager._history[0]
        assert entry["command"] == "ls"
        assert entry["args"] == ["-l", "/tmp"]
        assert entry["timestamp"] == timestamp.isoformat()

    def test_add_command_without_args(self, mock_logger, temp_history_file):
        manager = HistoryManager(mock_logger, history_file=temp_history_file)
        
        manager.add_command("pwd")
        
        assert len(manager._history) == 1
        assert manager._history[0]["args"] == []

    def test_add_command_auto_timestamp(self, mock_logger, temp_history_file):
        manager = HistoryManager(mock_logger, history_file=temp_history_file)
        before = datetime.now()
        
        manager.add_command("ls")
        
        after = datetime.now()
        entry_time = datetime.fromisoformat(manager._history[0]["timestamp"])
        assert before <= entry_time <= after

    def test_add_command_saves_to_file(self, mock_logger, temp_history_file):
        manager = HistoryManager(mock_logger, history_file=temp_history_file)
        
        manager.add_command("ls", ["-l"])
        
        assert temp_history_file.exists()
        saved_data = json.loads(temp_history_file.read_text())
        assert len(saved_data["history"]) == 1
        assert saved_data["history"][0]["command"] == "ls"

    def test_get_history_with_limit(self, mock_logger, temp_history_file):
        manager = HistoryManager(mock_logger, history_file=temp_history_file)
        for i in range(10):
            manager.add_command(f"cmd{i}")
        
        history = manager.get_history(limit=5)
        
        assert len(history) == 5
        assert history[0]["command"] == "cmd5"
        assert history[-1]["command"] == "cmd9"

    def test_get_history_without_limit(self, mock_logger, temp_history_file):
        manager = HistoryManager(mock_logger, history_file=temp_history_file)
        for i in range(10):
            manager.add_command(f"cmd{i}")
        
        history = manager.get_history(limit=0)
        
        assert len(history) == 10

    def test_clear_history(self, mock_logger, temp_history_file):
        manager = HistoryManager(mock_logger, history_file=temp_history_file)
        manager.add_command("ls")
        manager.add_command("cd")
        
        manager.clear_history()
        
        assert manager._history == []
        saved_data = json.loads(temp_history_file.read_text())
        assert saved_data["history"] == []

    def test_init_handles_corrupted_history_file(self, mock_logger, temp_history_file):
        temp_history_file.write_text("invalid json{")
        
        manager = HistoryManager(mock_logger, history_file=temp_history_file)
        assert manager._history == []
        mock_logger.error.assert_called_once()

