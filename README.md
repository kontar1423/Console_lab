# Console App

Utility for working with files

## Install

```bash
uv sync
```

## Run

```bash
uv run app <command> [arguments]
```

## Main commands

- ls [-l] `path`
- cat [-b] `file`
- rm [--recursive] `path`
- cd `path`
- mkdir `path`
- touch `path`
- mv `src` `dst`
- cp [-r] `src` `dst`
- zip `src` `archive.zip`
- unzip `archive.zip` `dst`
- tar [--compress] `src` `archive.tar[.gz]`
- untar `archive.tar[.gz]` `dst`
- history [--limit N]
- undo

## Examples

```bash
uv run app ls -l .
uv run app cp -r folder backup/
uv run app rm --recursive backup/
uv run app undo
```

## Steps of programm processing

```text
console_app.py (app())
    ↓
src/main.py (main callback)
    ↓
create_console_service() → MacOSConsoleService.__init__()
    ↓
Container is creating
    ↓
User: ls /path --long
    ↓
src/main.py (ls command)
    ↓
container.console_service.ls()
    ↓
MacOSConsoleService.ls()
    ↓
_workspace_manager.resolve_path()
    ↓
Checking and formating
    ↓
Return result -> output
```

## Project Structure

```text
Console-App-Sample/
├── console_app.py              # Entry point
├── pyproject.toml              # Project configuration
├── pytest.ini                  # Pytest configuration
├── uv.lock                     # Dependency lock file
│
├── src/                        # Source code
│   ├── main.py                 # CLI commands (Typer app)
│   ├── common/                 # Common utilities
│   │   └── config.py           # Logging configuration
│   ├── dependencies/           # Dependency injection
│   │   └── container.py        # DI container
│   ├── enums/                  # Enumerations
│   │   ├── file_mode.py        # File read modes
│   │   └── list_mode.py        # List display modes
│   └── services/               # Business logic services
│       ├── base.py             # Base console service interface
│       ├── workspace_manager.py # Current directory management
│       ├── history_manager.py  # Command history
│       ├── undo_manager.py     # Undo operations
│       ├── macos_console.py    # macOS implementation
│       ├── linux_console.py    # Linux implementation
│       └── windows_console.py  # Windows implementation
│
└── tests/                      # Test suite
    ├── conftest.py             # Pytest fixtures
    ├── test_cli_commands.py    # CLI integration tests
    ├── test_container.py       # DI container tests
    ├── test_workspace_manager.py
    ├── test_history_manager.py
    ├── test_undo_manager.py
    └── test_macos_console_service.py
```

## Testing

```bash
# Install test dependencies
uv sync --extra test

# Run all tests
uv run pytest
```

## Also

- History of commands: ~/.history
- Backups for undo: ~/.trash
