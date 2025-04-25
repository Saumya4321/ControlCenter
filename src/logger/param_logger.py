import logging
import os
from datetime import datetime

class ParamLogger:
    def __init__(self, name="TextLogger", log_dir=None):
        # Create a logger with a custom name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)  # You can change this to INFO or WARNING

        # Avoid duplicate handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Prevent propagation to the root logger
        self.logger.propagate = False

        # Setup log directory
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(__file__), "text_logs")
        os.makedirs(log_dir, exist_ok=True)

        # Create a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = os.path.join(log_dir, f"log_{timestamp}.txt")

        # Create a file handler
        file_handler = logging.FileHandler(self.log_file_path, mode="a", encoding="utf-8")
        formatter = logging.Formatter(
            fmt="[{asctime}] [{levelname}] {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        # Add the handler to the logger
        self.logger.addHandler(file_handler)

    def debug(self, msg):
        self.logger.debug(msg)
    
    def info(self, msg):
        self.logger.info(msg)
    
    def warning(self, msg):
        self.logger.warning(msg)
    
    def error(self, msg):
        self.logger.error(msg)
    
    def critical(self, msg):
        self.logger.critical(msg)
