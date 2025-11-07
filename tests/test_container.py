from unittest.mock import Mock
import pytest

from src.dependencies.container import Container
from src.services.base import OSConsoleServiceBase
from src.services.workspace_manager import WorkspaceManager
from src.services.history_manager import HistoryManager
from src.services.undo_manager import UndoManager


class TestContainer:

    def test_container_creation(self):
        console_service = Mock(spec=OSConsoleServiceBase)
        workspace_manager = Mock(spec=WorkspaceManager)
        history_manager = Mock(spec=HistoryManager)
        undo_manager = Mock(spec=UndoManager)
        
        container = Container(
            console_service=console_service,
            workspace_manager=workspace_manager,
            history_manager=history_manager,
            undo_manager=undo_manager
        )
        
        assert container.console_service == console_service
        assert container.workspace_manager == workspace_manager
        assert container.history_manager == history_manager
        assert container.undo_manager == undo_manager

    def test_container_is_dataclass(self):
        console_service = Mock(spec=OSConsoleServiceBase)
        workspace_manager = Mock(spec=WorkspaceManager)
        history_manager = Mock(spec=HistoryManager)
        undo_manager = Mock(spec=UndoManager)
        
        container = Container(
            console_service=console_service,
            workspace_manager=workspace_manager,
            history_manager=history_manager,
            undo_manager=undo_manager
        )
        
        assert hasattr(Container, '__dataclass_fields__')

