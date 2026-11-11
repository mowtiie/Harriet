import logging
from pathlib import Path

VOICE_ENCRYPTION_PREFIXES = (
    "Preparing for DAVE",
    "Executing DAVE",
    "Set MLS",
    "MLS ",
    "Voice websocket binary frame",
    "Sending voice websocket binary frame",
)

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "bot.log"

_FORMAT = "[{asctime}] [{levelname:<8}] {name}: {message}"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


class VoiceEncryptionFilter(logging.Filter):
    """Shows voice encryption debug lines from the gateway logger, which also carries chat payloads."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.WARNING or record.getMessage().startswith(
            VOICE_ENCRYPTION_PREFIXES
        )


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
    gateway_logger = logging.getLogger("discord.gateway")
    if root.level == logging.DEBUG:
        gateway_logger.setLevel(logging.DEBUG)
        gateway_logger.addFilter(VoiceEncryptionFilter())
    else:
        gateway_logger.setLevel(logging.WARNING)
