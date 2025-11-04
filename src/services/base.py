from abc import ABC, abstractmethod
from os import PathLike
from pathlib import Path
from typing import Literal

from src.enums.file_mode import FileReadMode
from src.enums.list_mode import ListMode


class OSConsoleServiceBase(ABC):
    @abstractmethod
    def ls(self, path: PathLike[str] | str, list_mode: ListMode = ListMode.short) -> list[str]: ...

    @abstractmethod
    def cat(
        self,
        filename: PathLike | str,
        mode: Literal[FileReadMode.string, FileReadMode.bytes] = FileReadMode.string,
    ) -> str | bytes: ...

    @abstractmethod
    def rm(self, path: PathLike[str] | str, recursive: bool = False) -> None: ...

    @abstractmethod
    def cd(self, path: PathLike[str] | str) -> Path: ...
    
    @abstractmethod
    def mkdir(self, path: PathLike[str] | str) -> None: ...
    
    @abstractmethod
    def touch(self, path: PathLike[str] | str) -> None: ...
    
    @abstractmethod
    def mv(self, source: PathLike[str] | str, destination: PathLike[str] | str) -> None: ...
    
    @abstractmethod
    def cp(self, source: PathLike[str] | str, destination: PathLike[str] | str, recursive: bool = False) -> None: ...

    @abstractmethod
    def zip(self, source: PathLike[str] | str, destination: PathLike[str] | str) -> None: ...

    @abstractmethod
    def unzip(self, archive: PathLike[str] | str, destination: PathLike[str] | str | None = None) -> None: ...

    @abstractmethod
    def tar(self, source: PathLike[str] | str, destination: PathLike[str] | str, compress: bool = False) -> None: ...

    @abstractmethod
    def untar(self, archive: PathLike[str] | str, destination: PathLike[str] | str | None = None) -> None: ...

    def get_history(self) -> list[dict]:
        """Get command history. Override if needed."""
        return []

    def undo_last(self) -> str:
        """Undo last operation. Override if needed."""
        return "Undo not implemented"