import shutil
import json
from datetime import datetime
from pathlib import Path
from logging import Logger
from typing import Optional
from enum import Enum


class OperationType(str, Enum):
    RM = "rm"
    MV = "mv"
    MKDIR = "mkdir"
    TOUCH = "touch"
    CP = "cp"
    ZIP = "zip"
    UNZIP = "unzip"
    TAR = "tar"
    UNTAR = "untar"


class UndoOperation:
    def __init__(
        self,
        operation_type: OperationType,
        source: Path,
        destination: Optional[Path] = None,
        backup_path: Optional[Path] = None,
        metadata: Optional[dict] = None
    ):
        self.operation_type = operation_type
        self.source = source
        self.destination = destination
        self.backup_path = backup_path
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class UndoManager:
    
    def __init__(self, logger: Logger, undo_file: Path | None = None, max_undo: int = 100):
        self._logger = logger
        self.undo_file = undo_file or Path.home() / ".console_app_undo.json"
        self.max_undo = max_undo
        self._undo_stack: list[UndoOperation] = []
        self._backup_dir = Path.home() / ".console_app_backups"
        self._backup_dir.mkdir(exist_ok=True)
        self._load_undo_stack()
    
    def _load_undo_stack(self):
        if self.undo_file.exists():
            try:
                with open(self.undo_file, 'r') as f:
                    data = json.load(f)
                    operations = data.get('operations', [])
                    for op_data in operations:
                        op = UndoOperation(
                            operation_type=OperationType(op_data['operation_type']),
                            source=Path(op_data['source']),
                            destination=Path(op_data['destination']) if op_data.get('destination') else None,
                            backup_path=Path(op_data['backup_path']) if op_data.get('backup_path') else None,
                            metadata=op_data.get('metadata', {})
                        )
                        self._undo_stack.append(op)
                    if len(self._undo_stack) > self.max_undo:
                        self._undo_stack = self._undo_stack[-self.max_undo:]
            except Exception as e:
                self._logger.error(f"Failed to load undo stack: {e}")
                self._undo_stack = []
        else:
            self._undo_stack = []
    
    def _save_undo_stack(self):
        try:
            operations = []
            for op in self._undo_stack[-self.max_undo:]:
                operations.append({
                    "operation_type": op.operation_type.value,
                    "source": str(op.source),
                    "destination": str(op.destination) if op.destination else None,
                    "backup_path": str(op.backup_path) if op.backup_path else None,
                    "metadata": op.metadata,
                    "timestamp": op.timestamp.isoformat()
                })
            with open(self.undo_file, 'w') as f:
                json.dump({"operations": operations}, f, indent=2)
        except Exception as e:
            self._logger.error(f"Failed to save undo stack: {e}")
    
    def _create_backup(self, path: Path) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"{path.name}_{timestamp}"
        backup_path = self._backup_dir / backup_name
        
        if path.is_file():
            shutil.copy2(path, backup_path)
        elif path.is_dir():
            shutil.copytree(path, backup_path, dirs_exist_ok=True)
        
        return backup_path
    
    def register_rm(self, path: Path, recursive: bool = False) -> bool:
        if not path.exists():
            return False
        
        try:
            backup_path = self._create_backup(path)
            op = UndoOperation(
                operation_type=OperationType.RM,
                source=path,
                backup_path=backup_path,
                metadata={"recursive": recursive}
            )
            self._undo_stack.append(op)
            self._save_undo_stack()
            return True
        except Exception as e:
            self._logger.error(f"Failed to register rm operation: {e}")
            return False
    
    def register_mv(self, source: Path, destination: Path) -> bool:
        if not source.exists():
            return False
        
        try:
            backup_path = self._create_backup(source)
            op = UndoOperation(
                operation_type=OperationType.MV,
                source=source,
                destination=destination,
                backup_path=backup_path
            )
            self._undo_stack.append(op)
            self._save_undo_stack()
            return True
        except Exception as e:
            self._logger.error(f"Failed to register mv operation: {e}")
            return False
    
    def register_mkdir(self, path: Path) -> bool:
        op = UndoOperation(
            operation_type=OperationType.MKDIR,
            source=path
        )
        self._undo_stack.append(op)
        self._save_undo_stack()
        return True
    
    def register_touch(self, path: Path) -> bool:
        op = UndoOperation(
            operation_type=OperationType.TOUCH,
            source=path
        )
        self._undo_stack.append(op)
        self._save_undo_stack()
        return True
    
    def register_cp(self, source: Path, destination: Path) -> bool:
        op = UndoOperation(
            operation_type=OperationType.CP,
            source=source,
            destination=destination
        )
        self._undo_stack.append(op)
        self._save_undo_stack()
        return True
    
    def register_archive(self, operation_type: OperationType, source: Path, destination: Path) -> bool:
        if not source.exists():
            return False
        
        try:
            backup_path = self._create_backup(source)
            op = UndoOperation(
                operation_type=operation_type,
                source=source,
                destination=destination,
                backup_path=backup_path
            )
            self._undo_stack.append(op)
            self._save_undo_stack()
            return True
        except Exception as e:
            self._logger.error(f"Failed to register archive operation: {e}")
            return False
    
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0
    
    def undo_last(self) -> Optional[str]:
        if not self._undo_stack:
            return "No operations to undo"
        
        op = self._undo_stack.pop()
        self._save_undo_stack()
        
        try:
            if op.operation_type == OperationType.RM:
                if op.backup_path and op.backup_path.exists():
                    if op.source.exists():
                        if op.source.is_dir():
                            shutil.rmtree(op.source)
                        else:
                            op.source.unlink()
                    op.source.parent.mkdir(parents=True, exist_ok=True)
                    if op.backup_path.is_file():
                        shutil.copy2(op.backup_path, op.source)
                    else:
                        shutil.copytree(op.backup_path, op.source, dirs_exist_ok=True)
                    return f"Restored {op.source} from backup"
                else:
                    return f"Cannot undo: backup not found for {op.source}"
            
            elif op.operation_type == OperationType.MV:
                if op.destination and op.destination.exists():
                    if op.source.exists():
                        op.source.unlink()
                    op.destination.rename(op.source)
                    return f"Moved {op.destination} back to {op.source}"
                else:
                    return f"Cannot undo: destination not found {op.destination}"
            
            elif op.operation_type == OperationType.MKDIR:
                if op.source.exists() and op.source.is_dir():
                    shutil.rmtree(op.source)
                    return f"Removed directory {op.source}"
                else:
                    return f"Cannot undo: directory not found {op.source}"
            
            elif op.operation_type == OperationType.TOUCH:
                if op.source.exists() and op.source.is_file():
                    op.source.unlink()
                    return f"Removed file {op.source}"
                else:
                    return f"Cannot undo: file not found {op.source}"
            
            elif op.operation_type == OperationType.CP:
                if op.destination and op.destination.exists():
                    if op.destination.is_file():
                        op.destination.unlink()
                    else:
                        shutil.rmtree(op.destination)
                    return f"Removed copied file/directory {op.destination}"
                else:
                    return f"Cannot undo: copied file not found {op.destination}"
            
            elif op.operation_type in (OperationType.ZIP, OperationType.TAR):
                if op.destination and op.destination.exists():
                    op.destination.unlink()
                    return f"Removed archive {op.destination}"
                else:
                    return f"Cannot undo: archive not found {op.destination}"
            
            elif op.operation_type in (OperationType.UNZIP, OperationType.UNTAR):
                if op.destination and op.destination.exists():
                    if op.destination.is_dir():
                        shutil.rmtree(op.destination)
                    else:
                        op.destination.unlink()
                    return f"Removed extracted directory {op.destination}"
                else:
                    return f"Cannot undo: extracted directory not found {op.destination}"
            
            return "Unknown operation type"
        except Exception as e:
            self._logger.error(f"Failed to undo operation: {e}")
            return f"Error undoing operation: {e}"

