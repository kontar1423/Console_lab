from logging import Logger
import shutil
import os
import stat
from datetime import datetime
from os import PathLike, remove
from pathlib import Path
from typing import Literal

from src.enums.file_mode import FileReadMode
from src.enums.list_mode import ListMode
from src.services.workspace_manager import WorkspaceManager
from src.services.base import OSConsoleServiceBase


class WindowsConsoleService(OSConsoleServiceBase):
    
    INVALID_FILENAME_CHARS = set('<>:"|?*\\')
    
    def __init__(self, logger: Logger):
        self._logger = logger
        self._workspace_manager = WorkspaceManager(logger)
    
    def _validate_filename(self, path: Path) -> None:
        filename = path.name
        invalid_chars = [char for char in filename if char in self.INVALID_FILENAME_CHARS]
        
        if invalid_chars:
            invalid_chars_str = ', '.join(invalid_chars)
            error_msg = f"Invalid filename: '{filename}' contains forbidden characters: {invalid_chars_str}"
            self._logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _format_permissions(self, file_stat: os.stat_result) -> str:
        mode = file_stat.st_mode
        perms = []
        perms.append('d' if stat.S_ISDIR(mode) else '-')
        perms.append('r' if mode & stat.S_IRUSR else '-')
        perms.append('w' if mode & stat.S_IWUSR else '-')
        perms.append('x' if mode & stat.S_IXUSR else '-')
        perms.append('r' if mode & stat.S_IRGRP else '-')
        perms.append('w' if mode & stat.S_IWGRP else '-')
        perms.append('x' if mode & stat.S_IXGRP else '-')
        perms.append('r' if mode & stat.S_IROTH else '-')
        perms.append('w' if mode & stat.S_IWOTH else '-')
        perms.append('x' if mode & stat.S_IXOTH else '-')
        return ''.join(perms)
    
    def ls(self, path: PathLike[str] | str, list_mode: ListMode = ListMode.short) -> list[str]:
        path = self._workspace_manager.resolve_path(path)
        if not path.exists(follow_symlinks=True):
            self._logger.error(f"Folder not found: {path}")
            raise FileNotFoundError(path)
        if not path.is_dir(follow_symlinks=True):
            self._logger.error(f"You entered {path} is not a directory")
            raise NotADirectoryError(path)
        self._logger.info(f"Listing {path} in {list_mode.value} mode")
        
        if list_mode == ListMode.long:
            entries = sorted(path.iterdir(), key=lambda p: p.name)
            return self._format_long_lines(entries)
        else:
            return [entry.name + "\n" for entry in path.iterdir()]
    
    def _format_long_lines(self, entries: list[Path]) -> list[str]:
        if not entries:
            return []
        
        file_info = []
        for entry in entries:
            try:
                file_stat = entry.stat(follow_symlinks=False)
                permissions = self._format_permissions(file_stat)
                nlinks = file_stat.st_nlink
                try:
                    owner = entry.owner()
                except (KeyError, OSError, NotImplementedError):
                    owner = str(file_stat.st_uid)
                try:
                    group = entry.group()
                except (KeyError, OSError, NotImplementedError):
                    group = str(file_stat.st_gid)
                size = file_stat.st_size
                mtime = datetime.fromtimestamp(file_stat.st_mtime)
                date_str = mtime.strftime('%b %d %H:%M')
                if (datetime.now() - mtime).days > 365:
                    date_str = mtime.strftime('%b %d  %Y')
                name = entry.name
                if entry.is_symlink():
                    try:
                        target = entry.readlink()
                        name = f"{name} -> {target}"
                    except OSError:
                        pass
                file_info.append({
                    'permissions': permissions,
                    'nlinks': nlinks,
                    'owner': owner,
                    'group': group,
                    'size': size,
                    'date': date_str,
                    'name': name
                })
            except OSError as e:
                self._logger.warning(f"Failed to stat {entry}: {e}")
                file_info.append({
                    'permissions': '-',
                    'nlinks': 1,
                    'owner': '-',
                    'group': '-',
                    'size': 0,
                    'date': '-',
                    'name': entry.name
                })
        
        max_owner_width = max(len(info['owner']) for info in file_info)
        max_links_width = max(len(str(info['nlinks'])) for info in file_info)
        max_size_width = max(len(str(info['size'])) for info in file_info)
        
        result = []
        for info in file_info:
            line = f"{info['permissions']} {info['nlinks']:{max_links_width}d} {info['owner']:<{max_owner_width}} {info['group']}  {info['size']:>{max_size_width}} {info['date']} {info['name']}"
            result.append(line)
        
        return result
    
    def cat(
        self,
        filename: PathLike[str] | str,
        mode: Literal[FileReadMode.string, FileReadMode.bytes] = FileReadMode.string,
    ) -> str | bytes:
        path = Path(filename)
        if not path.exists(follow_symlinks=True):
            self._logger.error(f"File not found: {filename}")
            raise FileNotFoundError(filename)
        if path.is_dir(follow_symlinks=True):
            self._logger.error(f"You entered {filename} is not a file")
            raise IsADirectoryError(f"You entered {filename} is not a file")
        try:
            self._logger.info(f"Reading file {filename} in mode {mode}")
            match mode:
                case FileReadMode.string:
                    return path.read_text(encoding="utf-8")
                case FileReadMode.bytes:
                    return path.read_bytes()
        except OSError as e:
            self._logger.exception(f"Error reading {filename}: {e}")
            raise
    
    def rm(self, path: PathLike[str] | str, recursive: bool = False) -> None:
        path = self._workspace_manager.resolve_path(path)
        path_resolved = path.resolve()
        
        if path_resolved.is_absolute() and len(path_resolved.parts) == 1:
            self._logger.error(f"Cannot remove root directory '{path_resolved}'")
            raise PermissionError(f"Cannot remove root directory '{path_resolved}'")
        
        if not path.exists(follow_symlinks=True):
            self._logger.error(f"Folder not found: {path}")
            raise FileNotFoundError(path)
        if path.is_file(follow_symlinks=True):
            remove(path)
            self._logger.info(f"Removed file: {path}")
            return None
        if recursive and path.is_dir(follow_symlinks=True):
            shutil.rmtree(path)
            self._logger.info(f"Removed directory recursively: {path}")
            return None
        else:
            self._logger.error(f"You entered {path} is not a directory")
            raise IsADirectoryError(path)
    
    def cd(self, path: PathLike[str] | str) -> Path:
        resolved_path = self._workspace_manager.resolve_path(path)
        if not resolved_path.exists(follow_symlinks=True):
            self._logger.error(f"Folder not found: {resolved_path}")
            raise FileNotFoundError(resolved_path)
        if not resolved_path.is_dir(follow_symlinks=True):
            self._logger.error(f"You entered {resolved_path} is not a directory")
            raise NotADirectoryError(resolved_path)
        resolved_path = resolved_path.resolve()
        self._workspace_manager.set_current_path(resolved_path)
        self._logger.info(f"Changed directory to: {resolved_path}")
        return resolved_path
    
    def mkdir(self, path: PathLike[str] | str) -> None:
        path = self._workspace_manager.resolve_path(path)
        self._validate_filename(path)
        if path.exists(follow_symlinks=True):
            self._logger.error(f"Folder already exists: {path}")
            raise FileExistsError(path)
        path.mkdir(parents=True, exist_ok=True)
        self._logger.info(f"Created directory: {path}")
        return None
    
    def touch(self, path: PathLike[str] | str) -> None:
        path = self._workspace_manager.resolve_path(path)
        self._validate_filename(path)
        if path.exists(follow_symlinks=True):
            self._logger.error(f"File already exists: {path}")
            raise FileExistsError(path)
        path.touch()
        self._logger.info(f"Created file: {path}")
        return None
    
    def mv(self, source: PathLike[str] | str, destination: PathLike[str] | str) -> None:
        source = self._workspace_manager.resolve_path(source)
        destination = self._workspace_manager.resolve_path(destination)
        if not source.exists(follow_symlinks=True):
            self._logger.error(f"File not found: {source}")
            raise FileNotFoundError(source)
        self._validate_filename(destination)
        source.rename(destination)
        self._logger.info(f"Moved file: {source} to {destination}")
        return None
    
    def cp(self, source: PathLike[str] | str, destination: PathLike[str] | str, recursive: bool = False) -> None:
        source = self._workspace_manager.resolve_path(source)
        destination = Path(destination)
        
        if not source.exists():
            self._logger.error(f"Source not found: {source}")
            raise FileNotFoundError(f"Source not found: {source}")
        
        if destination.exists() and destination.is_dir():
            destination = destination / source.name
        
        self._validate_filename(destination)
        
        if source.is_file():
            shutil.copy2(source, destination)
            self._logger.info(f"Copied file: {source} -> {destination}")
        elif source.is_dir():
            if recursive:
                shutil.copytree(source, destination, dirs_exist_ok=True)
                self._logger.info(f"Copied directory: {source} -> {destination}")
            else:
                self._logger.error(f"Cannot copy directory without -r flag: {source}")
                raise IsADirectoryError(f"Cannot copy directory without -r flag: {source}")
        else:
            raise ValueError(f"Unknown source type: {source}")
        return None

