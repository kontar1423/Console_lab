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

```bash
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

## Also

- History of commands: ~/.history
- Backups for undo: ~/.trash
