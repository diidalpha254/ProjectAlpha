"""
Logging configuration for Project Alpha
Provides configurable logging with different output formats and levels.
"""

import logging
import sys
from typing import Optional
from pathlib import Path
from datetime import datetime
import json


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class ColoredConsoleFormatter(logging.Formatter):
    """Custom formatter with color codes for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        log_message = (
            f"{color}[{timestamp}] "
            f"{record.levelname:<8} "
            f"{record.name:<15} "
            f"{record.getMessage()}{self.RESET}"
        )
        
        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"
        
        return log_message


class Logger:
    """Main logger class for Project Alpha"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._loggers = {}
        self._log_dir = Path("logs")
        self._log_dir.mkdir(exist_ok=True)
        self._setup_root_logger()
        self._initialized = True
    
    def _setup_root_logger(self):
        """Setup the root logger with handlers"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredConsoleFormatter())
        root_logger.addHandler(console_handler)
        
        # File handler - all logs
        file_handler = logging.FileHandler(
            self._log_dir / "project_alpha.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.FileHandler(
            self._log_dir / "errors.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific module"""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]
    
    @staticmethod
    def log_function_call(logger: logging.Logger):
        """Decorator to log function calls"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
                try:
                    result = func(*args, **kwargs)
                    logger.debug(f"{func.__name__} completed successfully")
                    return result
                except Exception as e:
                    logger.error(f"{func.__name__} failed: {str(e)}", exc_info=True)
                    raise
            return wrapper
        return decorator


# Global logger instance
logger = Logger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logger.get_logger(name)
