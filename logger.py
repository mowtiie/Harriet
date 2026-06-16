import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "bot.log"

_FORMAT = "[{asctime}] [{levelname:<8}] {name}: {message}"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO") -> None:
    LOG_DIR.mkdir(exist_ok=True)
    formatter = logging.Formatter(fmt=_FORMAT, datefmt=_DATEFMT, style="{")

    file_handler = logging.FileHandler(
        filename=LOG_FILE,
        mode="w",
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
