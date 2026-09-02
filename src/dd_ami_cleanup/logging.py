import logging

from rich.logging import RichHandler

from .console import log_console


def configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(console=log_console, show_path=False, rich_tracebacks=True)
        ],
    )
