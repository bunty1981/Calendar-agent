"""Shared logging setup so the CLI and web app log consistently.

Each app calls `setup_logging` once at startup with its own log file path,
so their logs stay separate while sharing the same format.
"""
import logging


def setup_logging(name: str, log_file: str, level: int = logging.DEBUG) -> logging.Logger:
    """Configure logging to write to `log_file` and return a logger for `name`.

    The root logger (and therefore any third-party library logger that
    hasn't set its own level, e.g. requests_oauthlib/urllib3) is kept at
    WARNING regardless of `level` — their DEBUG output includes full OAuth
    request/response bodies (access tokens, refresh tokens, client secrets),
    which must never land in a log file on disk. Only the named logger
    returned here is set to `level`, so the app's own debug/info logging
    still works as before.
    """
    logging.basicConfig(
        level=logging.WARNING,
        filename=log_file,
        filemode="w",
        format="%(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger
