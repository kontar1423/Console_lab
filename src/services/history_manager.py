import json
from datetime import datetime
from pathlib import Path
from logging import Logger
from typing import Optional


class HistoryManager:
    
    def __init__(self, logger: Logger, history_file: Path | None = None, max_history: int = 1000):
        self._logger = logger
        self.history_file = history_file or Path.home() / ".console_app_history.json"
        self.max_history = max_history
        self._history: list[dict] = []
        self._load_history()
    
    def _load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self._history = data.get('history', [])
                    if len(self._history) > self.max_history:
                        self._history = self._history[-self.max_history:]
            except Exception as e:
                self._logger.error(f"Failed to load history: {e}")
                self._history = []
        else:
            self._history = []
    
    def _save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump({
                    "history": self._history[-self.max_history:]
                }, f, indent=2)
        except Exception as e:
            self._logger.error(f"Failed to save history: {e}")
    
    def add_command(self, command: str, args: list[str] = None, timestamp: Optional[datetime] = None):
        if timestamp is None:
            timestamp = datetime.now()
        
        entry = {
            "timestamp": timestamp.isoformat(),
            "command": command,
            "args": args or []
        }
        self._history.append(entry)
        self._save_history()
    
    def get_history(self, limit: int = 50) -> list[dict]:
        return self._history[-limit:] if limit else self._history
    
    def clear_history(self):
        self._history = []
        self._save_history()

