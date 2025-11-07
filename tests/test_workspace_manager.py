import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest

from src.services.workspace_manager import WorkspaceManager


class TestWorkspaceManager:

    def test_init_creates_workspace_manager(self, mock_logger, temp_state_file):
        manager = WorkspaceManager(mock_logger, state_file=temp_state_file)
        assert manager._logger == mock_logger
        assert manager.state_file == temp_state_file
        assert isinstance(manager.current_path, Path)

    def test_init_loads_existing_state(self, mock_logger, temp_state_file):
        test_path = "/tmp/test_dir"
        state_data = {"current_path": test_path}
        temp_state_file.write_text(json.dumps(state_data))
        
        manager = WorkspaceManager(mock_logger, state_file=temp_state_file)
        assert manager.current_path == Path(test_path)

    def test_init_handles_corrupted_state_file(self, mock_logger, temp_state_file):
        temp_state_file.write_text("invalid json{")
        
        manager = WorkspaceManager(mock_logger, state_file=temp_state_file)
        assert manager.current_path == Path.cwd()
        mock_logger.error.assert_called_once()

    def test_set_current_path(self, mock_logger, temp_state_file):
        manager = WorkspaceManager(mock_logger, state_file=temp_state_file)
        new_path = Path("/tmp/new_dir")
        
        manager.set_current_path(new_path)
        
        assert manager.current_path == new_path
        saved_data = json.loads(temp_state_file.read_text())
        assert saved_data["current_path"] == str(new_path.absolute())

    def test_get_current_path(self, mock_logger, temp_state_file):
        manager = WorkspaceManager(mock_logger, state_file=temp_state_file)
        test_path = Path("/tmp/test")
        manager.current_path = test_path
        
        result = manager.get_current_path()
        
        assert result == test_path

    def test_resolve_path_absolute(self, mock_logger, temp_state_file):
        manager = WorkspaceManager(mock_logger, state_file=temp_state_file)
        absolute_path = "/tmp/absolute/path"
        
        result = manager.resolve_path(absolute_path)
        
        assert result == Path(absolute_path)

    def test_resolve_path_relative(self, mock_logger, temp_state_file, tmp_path):
        manager = WorkspaceManager(mock_logger, state_file=temp_state_file)
        manager.current_path = tmp_path
        relative_path = "documents/file.txt"
        
        result = manager.resolve_path(relative_path)
        
        assert result == tmp_path / "documents" / "file.txt"

    def test_save_state_handles_errors(self, mock_logger, temp_state_file):
        manager = WorkspaceManager(mock_logger, state_file=temp_state_file)
        
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            manager._save_state()
        
        mock_logger.error.assert_called()

