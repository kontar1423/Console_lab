from dataclasses import dataclass
from pathlib import Path

from src.services.base import OSConsoleServiceBase
from src.services.workspace_manager import WorkspaceManager
from src.services.history_manager import HistoryManager
from src.services.undo_manager import UndoManager


@dataclass
class Container:
    console_service: OSConsoleServiceBase
    workspace_manager: 'WorkspaceManager'
    history_manager: 'HistoryManager'
    undo_manager: 'UndoManager'