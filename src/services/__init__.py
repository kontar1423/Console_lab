import sys
from logging import Logger

from src.services.base import OSConsoleServiceBase
from src.services.linux_console import LinuxConsoleService
from src.services.macos_console import MacOSConsoleService
from src.services.windows_console import WindowsConsoleService


def create_console_service(logger: Logger) -> OSConsoleServiceBase:
    """
    Factory function to create the appropriate console service based on OS.
    
    Args:
        logger: Logger instance
        
    Returns:
        OSConsoleServiceBase: Platform-specific console service implementation
    """
    platform = sys.platform
    
    if platform == "darwin":  # macOS
        return MacOSConsoleService(logger=logger)
    elif platform.startswith("linux"):  # Linux
        return LinuxConsoleService(logger=logger)
    elif platform == "win32" or platform == "cygwin":  # Windows
        return WindowsConsoleService(logger=logger)
    else:
        # Fallback to Linux for other Unix-like systems
        logger.warning(f"Unknown platform {platform}, using LinuxConsoleService")
        return LinuxConsoleService(logger=logger)

