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
    ctx.obj = Container(
        console_service=create_console_service(logger=logger),
        workspace_manager=workspace_manager,
    )


@app.command()
def ls(
    ctx: Context,
    path: Path = typer.Argument(
        ..., exists=False, readable=False, help="File to print"
    ),
    mode: bool = typer.Option(False, "--long", "-l", help="List in long format"),
) -> None:
    """
    List all files in a directory.
    :param ctx:   typer context object for imitating di container
    :param path:  path to directory to list
    :return: content of directory
    """
    try:
        container: Container = get_container(ctx)
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
    """
    Cat a file
    :param ctx: typer context object for imitating di container
    :param filename: Filename to cat
    :param mode: Mode to read the file in
    :return:
    """
    try:
        container: Container = get_container(ctx)
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
        # Запрет удаления критичных путей
        path_str = str(path)
        if path_str == '/' or path_str == '..' or path_str.endswith('/..') or path_str.endswith('\\..'):
            typer.echo("❌ Error: Cannot remove root directory '/' or parent directory '..'")
            return
        
        # Запросить подтверждение для рекурсивного удаления
        if recursive and not force:
            confirmation = typer.confirm(f"Remove '{path}' and all its contents?")
            if not confirmation:
                typer.echo("Removal cancelled")
                return
        
        container: Container = get_container(ctx)
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
        container.console_service.cp(source, destination, recursive=recursive)
        typer.echo(f"Copied file: {source} to {destination}")
    except FileExistsError as e:
        typer.echo(e)
    except OSError as e:
        typer.echo(e)
if __name__ == "__main__":
    app()
