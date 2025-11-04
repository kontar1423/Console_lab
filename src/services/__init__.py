import sys
from logging import Logger

from src.services.base import OSConsoleServiceBase
from src.services.linux_console import LinuxConsoleService
from src.services.macos_console import MacOSConsoleService
from src.services.windows_console import WindowsConsoleService


def create_console_service(logger: Logger) -> OSConsoleServiceBase:
    platform = sys.platform
    
    if platform == "darwin":
        return MacOSConsoleService(logger=logger)
    elif platform.startswith("linux"):
        return LinuxConsoleService(logger=logger)
    elif platform == "win32" or platform == "cygwin":
        return WindowsConsoleService(logger=logger)
    else:
        logger.warning(f"Unknown platform {platform}, using LinuxConsoleService")
        return LinuxConsoleService(logger=logger)

