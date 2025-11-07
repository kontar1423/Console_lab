import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

from src.services.undo_manager import UndoManager, OperationType, UndoOperation


class TestUndoManager:

    def test_init_creates_undo_manager(self, mock_logger, temp_undo_file):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        assert manager._logger == mock_logger
        assert manager.undo_file == temp_undo_file
        assert manager._undo_stack == []
        assert manager._backup_dir.exists()

    def test_register_rm_file(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        result = manager.register_rm(test_file, recursive=False)
        
        assert result is True
        assert len(manager._undo_stack) == 1
        op = manager._undo_stack[0]
        assert op.operation_type == OperationType.RM
        assert op.source == test_file
        assert op.backup_path is not None
        assert op.backup_path.exists()

    def test_register_rm_directory(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")
        
        result = manager.register_rm(test_dir, recursive=True)
        
        assert result is True
        assert len(manager._undo_stack) == 1
        assert manager._undo_stack[0].metadata["recursive"] is True

    def test_register_rm_nonexistent_path(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        nonexistent = tmp_path / "nonexistent.txt"
        
        result = manager.register_rm(nonexistent, recursive=False)
        
        assert result is False
        assert len(manager._undo_stack) == 0

    def test_register_mv(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        source = tmp_path / "source.txt"
        source.write_text("content")
        dest = tmp_path / "dest.txt"
        
        result = manager.register_mv(source, dest)
        
        assert result is True
        assert len(manager._undo_stack) == 1
        op = manager._undo_stack[0]
        assert op.operation_type == OperationType.MV
        assert op.source == source
        assert op.destination == dest
        assert op.backup_path.exists()

    def test_register_mkdir(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        new_dir = tmp_path / "newdir"
        
        result = manager.register_mkdir(new_dir)
        
        assert result is True
        assert len(manager._undo_stack) == 1
        op = manager._undo_stack[0]
        assert op.operation_type == OperationType.MKDIR
        assert op.source == new_dir

    def test_register_touch(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        new_file = tmp_path / "newfile.txt"
        
        result = manager.register_touch(new_file)
        
        assert result is True
        assert len(manager._undo_stack) == 1
        op = manager._undo_stack[0]
        assert op.operation_type == OperationType.TOUCH
        assert op.source == new_file

    def test_register_cp(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        
        result = manager.register_cp(source, dest)
        
        assert result is True
        assert len(manager._undo_stack) == 1
        op = manager._undo_stack[0]
        assert op.operation_type == OperationType.CP
        assert op.source == source
        assert op.destination == dest

    def test_register_archive_zip(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        source = tmp_path / "source.txt"
        source.write_text("content")
        dest = tmp_path / "archive.zip"
        
        result = manager.register_archive(OperationType.ZIP, source, dest)
        
        assert result is True
        assert len(manager._undo_stack) == 1
        op = manager._undo_stack[0]
        assert op.operation_type == OperationType.ZIP
        assert op.backup_path.exists()

    def test_can_undo_empty_stack(self, mock_logger, temp_undo_file):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        assert manager.can_undo() is False

    def test_can_undo_with_operations(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        manager.register_rm(test_file)
        
        assert manager.can_undo() is True

    def test_undo_rm_operation(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")
        manager.register_rm(test_file)
        test_file.unlink()
        
        result = manager.undo_last()
        
        assert "Restored" in result
        assert test_file.exists()
        assert test_file.read_text() == "original content"

    def test_undo_mkdir_operation(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        new_dir = tmp_path / "newdir"
        manager.register_mkdir(new_dir)
        new_dir.mkdir()
        
        result = manager.undo_last()
        
        assert "Removed directory" in result
        assert not new_dir.exists()

    def test_undo_touch_operation(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        new_file = tmp_path / "newfile.txt"
        manager.register_touch(new_file)
        new_file.touch()
        
        result = manager.undo_last()
        
        assert "Removed file" in result
        assert not new_file.exists()

    def test_undo_cp_operation(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("content")
        manager.register_cp(source, dest)
        shutil.copy2(source, dest)
        
        result = manager.undo_last()
        
        assert "Removed copied" in result
        assert not dest.exists()
        assert source.exists()

    def test_undo_mv_operation(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("content")
        manager.register_mv(source, dest)
        source.rename(dest)
        
        result = manager.undo_last()
        
        assert "Moved" in result
        assert source.exists()
        assert not dest.exists()

    def test_undo_empty_stack(self, mock_logger, temp_undo_file):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        
        result = manager.undo_last()
        
        assert result == "No operations to undo"

    def test_save_and_load_undo_stack(self, mock_logger, temp_undo_file, tmp_path):
        manager1 = UndoManager(mock_logger, undo_file=temp_undo_file)
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        manager1.register_rm(test_file)
        
        manager2 = UndoManager(mock_logger, undo_file=temp_undo_file)
        
        assert len(manager2._undo_stack) == 1
        assert manager2._undo_stack[0].operation_type == OperationType.RM

    def test_max_undo_limit(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file, max_undo=5)
        
        for i in range(10):
            test_file = tmp_path / f"file{i}.txt"
            test_file.write_text("content")
            manager.register_rm(test_file)
        
        manager2 = UndoManager(mock_logger, undo_file=temp_undo_file, max_undo=5)
        assert len(manager2._undo_stack) <= 5

    def test_undo_handles_missing_backup(self, mock_logger, temp_undo_file, tmp_path):
        manager = UndoManager(mock_logger, undo_file=temp_undo_file)
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        manager.register_rm(test_file)
        
        backup_path = manager._undo_stack[0].backup_path
        if backup_path.is_file():
            backup_path.unlink()
        elif backup_path.is_dir():
            shutil.rmtree(backup_path)
        
        result = manager.undo_last()
        
        assert "Cannot undo" in result or "backup not found" in result

