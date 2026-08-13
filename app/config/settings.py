"""
Settings management for Project Alpha
Loads and manages configuration from YAML file and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, List
import yaml
from dotenv import load_dotenv

from ..core.exceptions import ConfigurationError
from ..core.logger import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv()


class Settings:
    """Centralized settings management"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._config: Dict[str, Any] = {}
        self._config_path = Path(__file__).parent / "config.yaml"
        self._load_config()
        self._apply_env_overrides()
        self._initialized = True
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            if not self._config_path.exists():
                raise ConfigurationError(f"Configuration file not found: {self._config_path}")
            
            with open(self._config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            
            logger.info(f"Loaded configuration from {self._config_path}")
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration"""
        # WebSocket URL
        if ws_url := os.getenv("DERIV_WS_URL"):
            self._config["websocket"]["url"] = ws_url
        
        # Database path
        if db_path := os.getenv("PROJECT_ALPHA_DB"):
            self._config["storage"]["database_path"] = db_path
        
        # Log level
        if log_level := os.getenv("LOG_LEVEL"):
            self._config["logging"]["level"] = log_level
        
        # Deriv App ID
        if app_id := os.getenv("DERIV_APP_ID"):
            try:
                self._config["api"]["deriv_app_id"] = int(app_id)
            except ValueError:
                logger.warning(f"Invalid DERIV_APP_ID: {app_id}")
        
        # Dark mode
        if dark_mode := os.getenv("DARK_MODE"):