from dataclasses import dataclass
from pathlib import Path

from src.services.base import OSConsoleServiceBase
from src.services.workspace_manager import WorkspaceManager


@dataclass
class Container:
    console_service: OSConsoleServiceBase
    workspace_manager: 'WorkspaceManager'