import sys
from os import environ
from os.path import isfile

import typed_settings as ts
from attrs import frozen
from loguru import logger


DEV = "--dev" in sys.argv


def is_containerized() -> bool:
    if "CONTAINER_FLAG" in environ:
        logger.debug("Container environment detected by: FLAG")
        return True

    if isfile("~/.dockerenv"):
        logger.debug("Container environment detected by: .dockerenv")
        return True

    return False


@frozen
class Settings:
    database: str

    api_id: int
    api_hash: ts.SecretStr
    bot_token: ts.SecretStr

    log_level: str = "DEBUG" if DEV else "INFO"


settings = ts.load(
    Settings,
    appname="weathergram",
    config_files=["./config.toml"],
    *({"env_prefix": None} if is_containerized() else ()),
)

logger.remove(0)  # Clear defaults
logger.add(sys.stderr, level=settings.log_level, diagnose=DEV, enqueue=True)
