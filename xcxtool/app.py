"""Custom application class for xcxtool apps

The main objective is to have built-in logging and output methods to allow for
variable output levels.
"""

import logging
from typing import Any

import rich.console
import rich.logging
import plumbum.cli as cli

CRITICAL = 50
ERROR = 40
WARNING = 30
SUCCESS = 25
INFO = 20
DEBUG = 10

LOGGER_NAME = "XCXToolApplicationLog"

logging.addLevelName(35, "SUCCESS")

_log_config = {}


class XCXToolApplication(cli.Application):

    _level: int = SUCCESS
    log: logging.Logger
    output_console: rich.console.Console

    def __init__(self, executable):
        super().__init__(executable)
        self.output_console = rich.console.Console()
        setup_console_log()
        self._log = logging.getLogger(LOGGER_NAME)

    @property
    def message_level(self) -> int:
        return self._level

    @message_level.setter
    def message_level(self, level: int | str) -> None:
        """Set the program's message level"""
        if isinstance(level, str):
            # self.message_level = _name_to_level.get(level.upper(), SUCCESS)
            self._log.setLevel(level.upper())
            return
        if level > 50:
            self._level = 50
        elif level < 10:
            self._level = 10
        else:
            self._level = level
        self._log.setLevel(self._level)

    def out(self, *output: Any, highlight: bool = False, markup: bool = True) -> None:
        """Send program output to stdout"""
        self.output_console.print(*output, markup=markup, highlight=highlight)

    def log(
        self,
        level: int,
        message: str,
        *args: object,
        extra: dict[str, object] | None = None,
    ) -> None:
        """Send an informational message to stderr.

        For actual program output, use the out() method.
        """
        self._log.log(level, message, *args, extra=extra)

    def error(
        self, message, *args, markup: bool = True, rich_highlight: bool = False
    ) -> None:
        """Log a message at ERROR level"""
        self._log.log(
            ERROR, message, *args, extra={"markup": markup, "highlight": rich_highlight}
        )

    def warning(
        self, message, *args, markup: bool = True, rich_highlight: bool = False
    ) -> None:
        """Log a message at WARNING level"""
        self._log.log(
            WARNING,
            message,
            *args,
            extra={"markup": markup, "highlight": rich_highlight},
        )

    def success(
        self, message, *args, markup: bool = True, rich_highlight: bool = False
    ) -> None:
        """Log a message at SUCCESS level"""
        self._log.log(
            SUCCESS,
            message,
            *args,
            extra={"markup": markup, "highlight": rich_highlight},
        )

    def info(
        self, message, *args, markup: bool = True, rich_highlight: bool = False
    ) -> None:
        """Log a message at INFO level"""
        self._log.log(
            INFO, message, *args, extra={"markup": markup, "highlight": rich_highlight}
        )

    def debug(
        self, message, *args, markup: bool = True, rich_highlight: bool = False
    ) -> None:
        """Log a message at DEBUG level"""
        self._log.log(
            DEBUG, message, *args, extra={"markup": markup, "highlight": rich_highlight}
        )


def setup_console_log():
    """Setup the logging module for console logging"""
    log = logging.getLogger(LOGGER_NAME)
    if "console_handler" in _log_config:
        log.debug("console_log already configured")
        return
    console_handler = rich.logging.RichHandler(
        console=rich.console.Console(stderr=True),
        level=logging.NOTSET,
        show_time=False,
        show_level=False,
        show_path=False,
        rich_tracebacks=True,
        markup=True,
    )
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(console_handler)
    log.setLevel(SUCCESS)
    _log_config["console_handler"] = console_handler


if __name__ == "__main__":

    class TestApp(XCXToolApplication):
        verbose = cli.Flag(["v", "verbose"], excludes=["quiet"])
        quiet = cli.Flag(["q", "quiet"], excludes=["verbose"])

        def main(self):
            if self.verbose:
                self.message_level = "INFO"
            if self.quiet:
                self.message_level = "WARNING"
            self.warning("This is a [bold red]WARNING[/] message")
            self.success("This is a [bold green]SUCCESS[/] message")
            self.info("This is an [bold]INFO[/] message")
            self.debug("This is a [blue]DEBUG[/] message")

    TestApp.run()
