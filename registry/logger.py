import logging
import logging.config
import logging.handlers
import pathlib

LOG_FORMAT = "[%(asctime)s] %(levelname)s %(module)s:%(lineno)d %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 4  # plus the current log file -> 50 MiB total, by default


def configure_logging(filename: pathlib.Path) -> None:
    filename.parent.mkdir(parents=True, exist_ok=True)

    # We configure logging to the WSGI error stream to be more conservative
    # than the rotating file because the error stream can end up in the web
    # server's log files.

    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {"format": LOG_FORMAT, "datefmt": LOG_DATE_FORMAT}
            },
            "handlers": {
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "default",
                    "filename": filename,
                    "maxBytes": LOG_MAX_BYTES,
                    "backupCount": LOG_BACKUP_COUNT,
                },
                "wsgi_stream": {
                    "class": "logging.StreamHandler",
                    "level": "WARNING",
                    "formatter": "default",
                    "stream": "ext://flask.logging.wsgi_errors_stream",
                },
            },
            "root": {
                "level": "DEBUG",
                "handlers": ["rotating_file", "wsgi_stream"],
            },
        }
    )
