from abc import ABC, abstractmethod
from os import PathLike
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
    def cd(self, path: PathLike[str] | str) -> None: ...
    
    @abstractmethod
    def mkdir(self, path: PathLike[str] | str) -> None: ...
    
    @abstractmethod
    def touch(self, path: PathLike[str] | str) -> None: ...
    
    @abstractmethod
    def mv(self, source: PathLike[str] | str, destination: PathLike[str] | str) -> None: ...
    
    @abstractmethod
    def cp(self, source: PathLike[str] | str, destination: PathLike[str] | str, recursive: bool = False) -> None: ...