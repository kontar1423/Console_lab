import os
import stat
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, PropertyMock
import pytest

from src.services.macos_console import MacOSConsoleService
from src.enums.list_mode import ListMode
from src.enums.file_mode import FileReadMode


class TestMacOSConsoleService:

    @pytest.fixture
    def mock_workspace_manager(self, tmp_path):
        manager = Mock()
        manager.current_path = tmp_path
        manager.resolve_path = lambda p: tmp_path / p if not Path(p).is_absolute() else Path(p)
        return manager

    @pytest.fixture
    def console_service(self, mock_logger):
        with patch('src.services.macos_console.WorkspaceManager'):
            service = MacOSConsoleService(mock_logger)
            return service

    def test_init_creates_service(self, mock_logger):
        with patch('src.services.macos_console.WorkspaceManager'):
            service = MacOSConsoleService(mock_logger)
            assert service._logger == mock_logger
            assert service._workspace_manager is not None

    def test_ls_short_mode(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        (test_dir / "file1.txt").touch()
        (test_dir / "file2.txt").touch()
        
        result = console_service.ls(test_dir, list_mode=ListMode.short)
        
        assert len(result) == 2
        assert any("file1.txt" in line for line in result)
        assert any("file2.txt" in line for line in result)

    def test_ls_long_mode(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        test_file = test_dir / "file.txt"
        test_file.write_text("content")
        
        result = console_service.ls(test_dir, list_mode=ListMode.long)
        
        assert len(result) >= 1
        assert any("file.txt" in line for line in result)
        assert any(line.startswith('-') or line.startswith('d') for line in result)

    def test_ls_nonexistent_directory(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        nonexistent = tmp_path / "nonexistent"
        
        with pytest.raises(FileNotFoundError):
            console_service.ls(nonexistent)

    def test_ls_file_not_directory(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_file = tmp_path / "file.txt"
        test_file.touch()
        
        with pytest.raises(NotADirectoryError):
            console_service.ls(test_file)

    def test_cat_string_mode(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        result = console_service.cat(test_file, mode=FileReadMode.string)
        
        assert result == content
        assert isinstance(result, str)

    def test_cat_bytes_mode(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_file = tmp_path / "test.bin"
        content = b"Binary content"
        test_file.write_bytes(content)
        
        result = console_service.cat(test_file, mode=FileReadMode.bytes)
        
        assert result == content
        assert isinstance(result, bytes)

    def test_cat_nonexistent_file(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        nonexistent = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            console_service.cat(nonexistent)

    def test_cat_directory(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        
        with pytest.raises(IsADirectoryError):
            console_service.cat(test_dir)

    def test_rm_file(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_file = tmp_path / "test.txt"
        test_file.touch()
        
        console_service.rm(test_file, recursive=False)
        
        assert not test_file.exists()

    def test_rm_directory_recursive(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        (test_dir / "file.txt").touch()
        
        console_service.rm(test_dir, recursive=True)
        
        assert not test_dir.exists()

    def test_rm_directory_without_recursive_flag(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        
        with pytest.raises(IsADirectoryError):
            console_service.rm(test_dir, recursive=False)

    def test_rm_root_directory(self, console_service, mock_workspace_manager):
        console_service._workspace_manager = mock_workspace_manager
        console_service._workspace_manager.resolve_path = lambda p: Path('/')
        
        with pytest.raises(PermissionError):
            console_service.rm('/', recursive=True)

    def test_rm_nonexistent_file(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        nonexistent = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            console_service.rm(nonexistent)

    def test_cd_existing_directory(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        
        result = console_service.cd(test_dir)
        
        assert result == test_dir.resolve()
        mock_workspace_manager.set_current_path.assert_called_once()

    def test_cd_nonexistent_directory(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        nonexistent = tmp_path / "nonexistent"
        
        with pytest.raises(FileNotFoundError):
            console_service.cd(nonexistent)

    def test_cd_file(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_file = tmp_path / "file.txt"
        test_file.touch()
        
        with pytest.raises(NotADirectoryError):
            console_service.cd(test_file)

    def test_mkdir_new_directory(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        new_dir = tmp_path / "newdir"
        
        console_service.mkdir(new_dir)
        
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_mkdir_existing_directory(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        
        with pytest.raises(FileExistsError):
            console_service.mkdir(test_dir)

    def test_mkdir_nested_directories(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        nested_dir = tmp_path / "parent" / "child" / "grandchild"
        
        console_service.mkdir(nested_dir)
        
        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_touch_new_file(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        new_file = tmp_path / "newfile.txt"
        
        console_service.touch(new_file)
        
        assert new_file.exists()
        assert new_file.is_file()

    def test_touch_existing_file(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        test_file = tmp_path / "test.txt"
        test_file.touch()
        
        with pytest.raises(FileExistsError):
            console_service.touch(test_file)

    def test_mv_file(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("content")
        
        console_service.mv(source, dest)
        
        assert not source.exists()
        assert dest.exists()
        assert dest.read_text() == "content"

    def test_mv_nonexistent_file(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        source = tmp_path / "nonexistent.txt"
        dest = tmp_path / "dest.txt"
        
        with pytest.raises(FileNotFoundError):
            console_service.mv(source, dest)

    def test_cp_file(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        content = "test content"
        source.write_text(content)
        
        console_service.cp(source, dest, recursive=False)
        
        assert source.exists()
        assert dest.exists()
        assert dest.read_text() == content

    def test_cp_directory_recursive(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        source_dir = tmp_path / "source"
        dest_dir = tmp_path / "dest"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("content")
        
        console_service.cp(source_dir, dest_dir, recursive=True)
        
        assert source_dir.exists()
        assert dest_dir.exists()
        assert (dest_dir / "file.txt").exists()

    def test_cp_directory_without_recursive_flag(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        source_dir = tmp_path / "source"
        dest_dir = tmp_path / "dest"
        source_dir.mkdir()
        
        with pytest.raises(IsADirectoryError):
            console_service.cp(source_dir, dest_dir, recursive=False)

    def test_cp_nonexistent_source(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        source = tmp_path / "nonexistent.txt"
        dest = tmp_path / "dest.txt"
        
        with pytest.raises(FileNotFoundError):
            console_service.cp(source, dest)

    def test_zip_file(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        source = tmp_path / "test.txt"
        archive = tmp_path / "archive.zip"
        source.write_text("content")
        
        console_service.zip(source, archive)
        
        assert archive.exists()
        import zipfile
        with zipfile.ZipFile(archive, 'r') as zf:
            assert "test.txt" in zf.namelist()

    def test_zip_directory(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        source_dir = tmp_path / "testdir"
        archive = tmp_path / "archive.zip"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.txt").write_text("content2")
        
        console_service.zip(source_dir, archive)
        
        assert archive.exists()
        import zipfile
        with zipfile.ZipFile(archive, 'r') as zf:
            names = zf.namelist()
            assert "file1.txt" in names
            assert "file2.txt" in names

    def test_zip_nonexistent_source(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        source = tmp_path / "nonexistent.txt"
        archive = tmp_path / "archive.zip"
        
        with pytest.raises(FileNotFoundError):
            console_service.zip(source, archive)

    def test_unzip_archive(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        archive = tmp_path / "archive.zip"
        extract_dir = tmp_path / "extracted"
        
        import zipfile
        with zipfile.ZipFile(archive, 'w') as zf:
            zf.writestr("file.txt", "content")
        
        console_service.unzip(archive, extract_dir)
        
        assert extract_dir.exists()
        assert (extract_dir / "file.txt").exists()

    def test_unzip_invalid_archive(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        invalid_archive = tmp_path / "invalid.zip"
        invalid_archive.write_text("not a zip file")
        
        with pytest.raises(ValueError):
            console_service.unzip(invalid_archive)

    def test_tar_file(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        source = tmp_path / "test.txt"
        archive = tmp_path / "archive.tar"
        source.write_text("content")
        
        console_service.tar(source, archive, compress=False)
        
        assert archive.exists()

    def test_tar_with_compression(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        source = tmp_path / "test.txt"
        archive = tmp_path / "archive.tar.gz"
        source.write_text("content")
        
        console_service.tar(source, archive, compress=True)
        
        assert archive.exists()

    def test_untar_archive(self, console_service, mock_workspace_manager, tmp_path):
        console_service._workspace_manager = mock_workspace_manager
        archive = tmp_path / "archive.tar"
        extract_dir = tmp_path / "extracted"
        
        import tarfile
        source_file = tmp_path / "test.txt"
        source_file.write_text("content")
        with tarfile.open(archive, 'w') as tar:
            tar.add(source_file, arcname="test.txt")
        
        console_service.untar(archive, extract_dir)
        
        assert extract_dir.exists()
        assert (extract_dir / "test.txt").exists()

    def test_format_permissions(self, console_service, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.touch()
        file_stat = test_file.stat()
        
        result = console_service._format_permissions(file_stat)
        
        assert len(result) == 10
        assert result[0] in ['-', 'd']
        assert all(c in ['r', 'w', 'x', '-'] for c in result[1:])

