import logging
import os
import sys
import io
from logging.handlers import RotatingFileHandler


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[90m",   # light gray
        "INFO": "\033[97m",    # white
        "WARNING": "\033[93m", # yellow/orange
        "ERROR": "\033[91m",   # red
        "CRITICAL": "\033[41m" # red background
    }
    RESET = "\033[0m"

    def format(self, record):
        log_msg = super().format(record)
        color = self.COLORS.get(record.levelname, self.RESET)
        return f"{color}{log_msg}{self.RESET}"


class AppLogger:
    _initialized = False
    _base_logger_name = "genai_logger"

    def __init__(self, log_dir="logs", log_file="app.log"):
        self.log_dir = log_dir
        self.log_file = log_file

        self.logger = logging.getLogger(self._base_logger_name)
        self.logger.setLevel(logging.DEBUG)

        if not AppLogger._initialized:
            self._ensure_log_dir()
            self._clear_log_file()
            self._setup_handlers()
            AppLogger._initialized = True

    def _ensure_log_dir(self):
        os.makedirs(self.log_dir, exist_ok=True)

    def _clear_log_file(self):
        log_path = os.path.join(self.log_dir, self.log_file)
        try:
            with open(log_path, "w", encoding="utf-8"):
                pass
        except Exception as e:
            print(f"Warning: Could not clear log file '{log_path}': {e}")

    def _setup_handlers(self):
        if self.logger.hasHandlers():
            return

        base_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(filename)s:%(lineno)d]"

        # Console handler with colors
        try:
            stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
            console_handler = logging.StreamHandler(stream)
        except Exception:
            console_handler = logging.StreamHandler(sys.stdout)

        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(ColoredFormatter(base_format))
        self.logger.addHandler(console_handler)

        # File handler (no colors, just plain text)
        file_handler = RotatingFileHandler(
            os.path.join(self.log_dir, self.log_file),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(base_format))
        self.logger.addHandler(file_handler)

    def get_logger(self, name=None):
        if name:
            return self.logger.getChild(name)
        return self.logger


# Global logger
LOGGER = AppLogger().get_logger()

if __name__ == "__main__":
    log = AppLogger().get_logger("Test")
    log.debug("This is a DEBUG message")
    log.info("This is an INFO message")
    log.warning("This is a WARNING message")
    log.error("This is an ERROR message")
    log.critical("This is a CRITICAL message")
