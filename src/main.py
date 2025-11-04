from src.common.config import LOGGING_CONFIG

import logging
import sys
from pathlib import Path

import typer
from typer import Typer, Context

from src.dependencies.container import Container
from src.enums.file_mode import FileReadMode
from src.services import create_console_service
from src.services.workspace_manager import WorkspaceManager
from src.services.history_manager import HistoryManager
from src.services.undo_manager import UndoManager
from src.enums.list_mode import ListMode
app = Typer()


def get_container(ctx: Context) -> Container:
    container = ctx.obj
    if not isinstance(container, Container):
        raise RuntimeError("DI container is not initialized")
    return container


@app.callback()
def main(ctx: Context):
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    workspace_manager = WorkspaceManager(logger)
    history_manager = HistoryManager(logger)
    undo_manager = UndoManager(logger)
    ctx.obj = Container(
        console_service=create_console_service(logger=logger),
        workspace_manager=workspace_manager,
        history_manager=history_manager,
        undo_manager=undo_manager,
    )


@app.command()
def ls(
    ctx: Context,
    path: Path = typer.Argument(
        ..., exists=False, readable=False, help="File to print"
    ),
    mode: bool = typer.Option(False, "--long", "-l", help="List in long format"),
) -> None:
    try:
        container: Container = get_container(ctx)
        args = [str(path)]
        if mode:
            args.append("-l")
        container.history_manager.add_command("ls", args)
        
        content = container.console_service.ls(path, list_mode=ListMode.long if mode else ListMode.short)
        if mode:
            for item in content:
                typer.echo(item)
        else:
            sys.stdout.writelines(content)
    except OSError as e:
        typer.echo(e)


@app.command()
def cat(
    ctx: Context,
    filename: Path = typer.Argument(
        ..., exists=False, readable=False, help="File to print"
    ),
    mode: bool = typer.Option(False, "--bytes", "-b", help="Read as bytes"),
):
    try:
        container: Container = get_container(ctx)
        args = [str(filename)]
        if mode:
            args.append("-b")
        container.history_manager.add_command("cat", args)
        
        mode = FileReadMode.bytes if mode else FileReadMode.string
        data = container.console_service.cat(
            filename,
            mode=mode,
        )
        if isinstance(data, bytes):
            sys.stdout.buffer.write(data)
        else:
            sys.stdout.write(data)
    except OSError as e:
        typer.echo(e)

@app.command()
def rm(
    ctx: Context,
    path: Path = typer.Argument(
        ..., exists=False, readable=False, help="File to print"
    ),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Remove directory recursively"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation"),
) -> None:
    try:
        container: Container = get_container(ctx)
        args = [str(path)]
        if recursive:
            args.append("-r")
        if force:
            args.append("-f")
        container.history_manager.add_command("rm", args)
        
        path_str = str(path)
        if path_str == '/' or path_str == '..' or path_str.endswith('/..') or path_str.endswith('\\..'):
            typer.echo("❌ Error: Cannot remove root directory '/' or parent directory '..'")
            return
        
        resolved_path = container.workspace_manager.resolve_path(path)
        if resolved_path.exists():
            container.undo_manager.register_rm(resolved_path, recursive=recursive)
        
        if recursive and not force:
            confirmation = typer.confirm(f"Remove '{path}' and all its contents?")
            if not confirmation:
                typer.echo("Removal cancelled")
                return
        
        container.console_service.rm(path, recursive=recursive)
        typer.echo(f"Removed: {path}")
    except PermissionError as e:
        typer.echo(f"❌ Error: {e}")
    except OSError as e:
        typer.echo(e)

@app.command()
def cd(
    ctx: Context,
    path: Path = typer.Argument(
        ..., exists=False, readable=False, help="File to print"
    ),
) -> None:
    try:
        container: Container = get_container(ctx)
        container.history_manager.add_command("cd", [str(path)])
        
        resolved_path = container.console_service.cd(path)
        typer.echo(f"Changed directory to: {resolved_path}")
    except OSError as e:
        typer.echo(e)

@app.command()
def mkdir(
    ctx: Context,
    path: Path = typer.Argument(
        ..., exists=False, readable=False, help="File to print"
    ),
) -> None:
    try:
        container: Container = get_container(ctx)
        container.history_manager.add_command("mkdir", [str(path)])
        
        resolved_path = container.workspace_manager.resolve_path(path)
        container.undo_manager.register_mkdir(resolved_path)
        
        container.console_service.mkdir(path)
        typer.echo(f"Created directory: {path}")
    except OSError as e:
        typer.echo(e)

@app.command()
def touch(
    ctx: Context,
    path: Path = typer.Argument(
        ..., exists=False, readable=False, help="File to print"
    ),
) -> None:
    try:
        container: Container = get_container(ctx)
        container.history_manager.add_command("touch", [str(path)])
        
        resolved_path = container.workspace_manager.resolve_path(path)
        container.undo_manager.register_touch(resolved_path)
        
        container.console_service.touch(path)
        typer.echo(f"Created file: {path}")
    except OSError as e:
        typer.echo(e)

@app.command()
def mv(
    ctx: Context,
    source: Path = typer.Argument(
        ..., exists=False, readable=False, help="File to print"
    ),
    destination: Path = typer.Argument(
        ..., exists=False, readable=False, help="File to print"
    ),
) -> None:
    try:
        container: Container = get_container(ctx)
        container.history_manager.add_command("mv", [str(source), str(destination)])
        
        resolved_source = container.workspace_manager.resolve_path(source)
        resolved_dest = container.workspace_manager.resolve_path(destination)
        container.undo_manager.register_mv(resolved_source, resolved_dest)
        
        container.console_service.mv(source, destination)
        typer.echo(f"Moved file: {source} to {destination}")
    except OSError as e:
        typer.echo(e)

@app.command()
def cp(
    ctx: Context,
    source: Path = typer.Argument(
        ..., exists=False, readable=False, help="File to print"
    ),
    destination: Path = typer.Argument(
        ..., exists=False, readable=False, help="File to print"
    ),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Copy directory recursively"),
) -> None:
    try:
        container: Container = get_container(ctx)
        args = [str(source), str(destination)]
        if recursive:
            args.append("-r")
        container.history_manager.add_command("cp", args)
        
        resolved_source = container.workspace_manager.resolve_path(source)
        resolved_dest = container.workspace_manager.resolve_path(destination)
        if resolved_dest.exists() and resolved_dest.is_dir():
            resolved_dest = resolved_dest / resolved_source.name
        container.undo_manager.register_cp(resolved_source, resolved_dest)
        
        container.console_service.cp(source, destination, recursive=recursive)
        typer.echo(f"Copied file: {source} to {destination}")
    except FileExistsError as e:
        typer.echo(e)
    except OSError as e:
        typer.echo(e)

@app.command()
def zip(
    ctx: Context,
    source: Path = typer.Argument(..., exists=False, help="File or directory to zip"),
    destination: Path = typer.Argument(..., exists=False, help="Archive file path"),
) -> None:
    try:
        container: Container = get_container(ctx)
        container.history_manager.add_command("zip", [str(source), str(destination)])
        
        resolved_source = container.workspace_manager.resolve_path(source)
        resolved_dest = container.workspace_manager.resolve_path(destination)
        from src.services.undo_manager import OperationType
        container.undo_manager.register_archive(OperationType.ZIP, resolved_source, resolved_dest)
        
        container.console_service.zip(source, destination)
        typer.echo(f"Created archive: {destination}")
    except OSError as e:
        typer.echo(e)

@app.command()
def unzip(
    ctx: Context,
    archive: Path = typer.Argument(..., exists=False, help="Archive file to extract"),
    destination: Path = typer.Option(None, "--destination", "-d", help="Destination directory"),
) -> None:
    try:
        container: Container = get_container(ctx)
        args = [str(archive)]
        if destination:
            args.extend(["-d", str(destination)])
        container.history_manager.add_command("unzip", args)
        
        resolved_archive = container.workspace_manager.resolve_path(archive)
        if destination:
            resolved_dest = container.workspace_manager.resolve_path(destination)
        else:
            resolved_dest = resolved_archive.parent
        from src.services.undo_manager import OperationType
        container.undo_manager.register_archive(OperationType.UNZIP, resolved_archive, resolved_dest)
        
        container.console_service.unzip(archive, destination)
        dest_path = destination if destination else archive.parent
        typer.echo(f"Extracted to: {dest_path}")
    except OSError as e:
        typer.echo(e)
    except ValueError as e:
        typer.echo(e)

@app.command()
def tar(
    ctx: Context,
    source: Path = typer.Argument(..., exists=False, help="File or directory to archive"),
    destination: Path = typer.Argument(..., exists=False, help="Archive file path"),
    compress: bool = typer.Option(False, "--compress", "-z", help="Compress with gzip"),
) -> None:
    try:
        container: Container = get_container(ctx)
        args = [str(source), str(destination)]
        if compress:
            args.append("-z")
        container.history_manager.add_command("tar", args)
        
        resolved_source = container.workspace_manager.resolve_path(source)
        resolved_dest = container.workspace_manager.resolve_path(destination)
        from src.services.undo_manager import OperationType
        container.undo_manager.register_archive(OperationType.TAR, resolved_source, resolved_dest)
        
        container.console_service.tar(source, destination, compress=compress)
        typer.echo(f"Created archive: {destination}")
    except OSError as e:
        typer.echo(e)

@app.command()
def untar(
    ctx: Context,
    archive: Path = typer.Argument(..., exists=False, help="Archive file to extract"),
    destination: Path = typer.Option(None, "--destination", "-d", help="Destination directory"),
) -> None:
    try:
        container: Container = get_container(ctx)
        args = [str(archive)]
        if destination:
            args.extend(["-d", str(destination)])
        container.history_manager.add_command("untar", args)
        
        resolved_archive = container.workspace_manager.resolve_path(archive)
        if destination:
            resolved_dest = container.workspace_manager.resolve_path(destination)
        else:
            resolved_dest = resolved_archive.parent
        from src.services.undo_manager import OperationType
        container.undo_manager.register_archive(OperationType.UNTAR, resolved_archive, resolved_dest)
        
        container.console_service.untar(archive, destination)
        dest_path = destination if destination else archive.parent
        typer.echo(f"Extracted to: {dest_path}")
    except OSError as e:
        typer.echo(e)

@app.command()
def history(
    ctx: Context,
    limit: int = typer.Option(50, "--limit", "-n", help="Number of commands to show"),
) -> None:
    try:
        container: Container = get_container(ctx)
        history = container.history_manager.get_history(limit=limit)
        if not history:
            typer.echo("No command history")
            return
        
        for i, entry in enumerate(reversed(history), 1):
            timestamp = entry.get('timestamp', '')
            command = entry.get('command', '')
            args = entry.get('args', [])
            args_str = ' '.join(args) if args else ''
            typer.echo(f"{i:4d}  {timestamp}  {command} {args_str}")
    except Exception as e:
        typer.echo(f"Error: {e}")

@app.command()
def undo(ctx: Context) -> None:
    try:
        container: Container = get_container(ctx)
        container.history_manager.add_command("undo", [])
        if not container.undo_manager.can_undo():
            typer.echo("No operations to undo")
            return
        
        result = container.undo_manager.undo_last()
        typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}")

if __name__ == "__main__":
    app()
