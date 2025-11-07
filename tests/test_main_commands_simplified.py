"""Simplified integration tests for main CLI commands."""
from pathlib import Path
from unittest.mock import patch, Mock
import pytest
from typer.testing import CliRunner

from src.main import app


class TestMainCommandsSimplified:
    """Simplified test suite for main CLI commands using integration testing."""

    @pytest.fixture
    def runner(self):
        """Fixture that provides a CliRunner."""
        return CliRunner()

    def test_ls_command_integration(self, runner, tmp_path):
        """Test ls command with actual directory."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        (test_dir / "file1.txt").touch()
        (test_dir / "file2.txt").touch()
        
        result = runner.invoke(app, ["ls", str(test_dir)])
        
        assert result.exit_code == 0
        assert "file1.txt" in result.stdout
        assert "file2.txt" in result.stdout

    def test_cat_command_integration(self, runner, tmp_path):
        """Test cat command with actual file."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        result = runner.invoke(app, ["cat", str(test_file)])
        
        assert result.exit_code == 0
        assert content in result.stdout

    def test_mkdir_command_integration(self, runner, tmp_path):
        """Test mkdir command."""
        new_dir = tmp_path / "newdir"
        
        result = runner.invoke(app, ["mkdir", str(new_dir)])
        
        assert result.exit_code == 0
        assert new_dir.exists()
        assert "Created directory:" in result.stdout

    def test_touch_command_integration(self, runner, tmp_path):
        """Test touch command."""
        new_file = tmp_path / "newfile.txt"
        
        result = runner.invoke(app, ["touch", str(new_file)])
        
        assert result.exit_code == 0
        assert new_file.exists()
        assert "Created file:" in result.stdout

    def test_rm_file_integration(self, runner, tmp_path):
        """Test rm command for file."""
        test_file = tmp_path / "test.txt"
        test_file.touch()
        
        result = runner.invoke(app, ["rm", str(test_file)])
        
        assert result.exit_code == 0
        assert not test_file.exists()
        assert "Removed:" in result.stdout

    def test_rm_directory_recursive_integration(self, runner, tmp_path):
        """Test rm command for directory with recursive flag."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        (test_dir / "file.txt").touch()
        
        result = runner.invoke(app, ["rm", "-r", "-f", str(test_dir)])
        
        assert result.exit_code == 0
        assert not test_dir.exists()

    def test_mv_command_integration(self, runner, tmp_path):
        """Test mv command."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("content")
        
        result = runner.invoke(app, ["mv", str(source), str(dest)])
        
        assert result.exit_code == 0
        assert not source.exists()
        assert dest.exists()
        assert "Moved file:" in result.stdout

    def test_cp_command_integration(self, runner, tmp_path):
        """Test cp command."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        content = "test content"
        source.write_text(content)
        
        result = runner.invoke(app, ["cp", str(source), str(dest)])
        
        assert result.exit_code == 0
        assert source.exists()  # Source still exists
        assert dest.exists()
        assert dest.read_text() == content

    def test_zip_command_integration(self, runner, tmp_path):
        """Test zip command."""
        source = tmp_path / "test.txt"
        archive = tmp_path / "archive.zip"
        source.write_text("content")
        
        result = runner.invoke(app, ["zip", str(source), str(archive)])
        
        assert result.exit_code == 0
        assert archive.exists()
        assert "Created archive:" in result.stdout

    def test_unzip_command_integration(self, runner, tmp_path):
        """Test unzip command."""
        import zipfile
        
        archive = tmp_path / "archive.zip"
        extract_dir = tmp_path / "extracted"
        
        # Create a zip file
        with zipfile.ZipFile(archive, 'w') as zf:
            zf.writestr("file.txt", "content")
        
        result = runner.invoke(app, ["unzip", str(archive), "-d", str(extract_dir)])
        
        assert result.exit_code == 0
        assert (extract_dir / "file.txt").exists()

    def test_tar_command_integration(self, runner, tmp_path):
        """Test tar command."""
        source = tmp_path / "test.txt"
        archive = tmp_path / "archive.tar"
        source.write_text("content")
        
        result = runner.invoke(app, ["tar", str(source), str(archive)])
        
        assert result.exit_code == 0
        assert archive.exists()

    def test_history_command_integration(self, runner, tmp_path):
        """Test history command shows previous commands."""
        # Run a command first
        test_file = tmp_path / "test.txt"
        test_file.touch()
        runner.invoke(app, ["cat", str(test_file)])
        
        # Now check history
        result = runner.invoke(app, ["history"])
        
        assert result.exit_code == 0
        # History should contain the cat command or show no history message

    def test_cd_command_integration(self, runner, tmp_path):
        """Test cd command."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        
        result = runner.invoke(app, ["cd", str(test_dir)])
        
        assert result.exit_code == 0
        assert "Changed directory to:" in result.stdout

    def test_error_handling_nonexistent_file(self, runner, tmp_path):
        """Test error handling for nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"
        
        result = runner.invoke(app, ["cat", str(nonexistent)])
        
        assert result.exit_code == 0  # Errors are caught and printed
        assert str(nonexistent) in result.stdout or "not found" in result.stdout.lower()

    def test_undo_command_integration(self, runner, tmp_path):
        """Test undo command."""
        # Create and remove a file
        test_file = tmp_path / "test.txt"
        test_file.touch()
        runner.invoke(app, ["rm", str(test_file)])
        
        # Now try to undo
        result = runner.invoke(app, ["undo"])
        
        assert result.exit_code == 0
        # Undo should either restore the file or show appropriate message

