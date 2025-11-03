# src/services/workspace_manager.py
import json
from pathlib import Path
from logging import Logger


class WorkspaceManager:
    """Управление рабочим пространством между сессиями"""
    
    def __init__(self, logger: Logger, state_file: Path | None = None):
        self._logger = logger
        self.state_file = state_file or Path.home() / ".console_app_state.json"
        self._load_state()
    
    def _load_state(self):
        """Загрузить состояние из файла"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.current_path = Path(data.get('current_path', '.'))
            except Exception as e:
                self._logger.error(f"Failed to load state: {e}")
                self.current_path = Path.cwd()
        else:
            self.current_path = Path.cwd()
    
    def _save_state(self):
        """Сохранить состояние в файл"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    "current_path": str(self.current_path.absolute())
                }, f)
        except Exception as e:
            self._logger.error(f"Failed to save state: {e}")
    
    def set_current_path(self, path: Path):
        """Установить текущую директорию"""
        self.current_path = path
        self._save_state()
    
    def get_current_path(self) -> Path:
        """Получить текущую директорию"""
        return self.current_path
    
    def resolve_path(self, user_input: str) -> Path:
        """Разрешить путь относительно текущей директории"""
        input_path = Path(user_input)
        if input_path.is_absolute():
            return input_path
        return (self.current_path / input_path).resolve()