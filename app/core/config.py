"""
Configuration Module
Loads and manages application configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv()

class Config:
    """
    Application configuration manager.
    Loads from environment variables and config.yaml.
    """
    
    def __init__(self):
        self.config = {}
        self._load_config()
        self._load_env_vars()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
    
    def _load_env_vars(self):
        """Load environment variables with safe defaults."""
        # Deriv App ID - from SECRETS
        app_id_str = os.getenv("DERIV_APP_ID")
        if app_id_str is not None and app_id_str.strip():
            try:
                self.config.setdefault("api", {})["deriv_app_id"] = int(app_id_str)
            except ValueError:
                self.config.setdefault("api", {})["deriv_app_id"] = 1089
        else:
            # If not set, use default
            self.config.setdefault("api", {})["deriv_app_id"] = 1089
        
        # Deriv API Token - from SECRETS (optional)
        token = os.getenv("DERIV_TOKEN")
        if token is not None and token.strip():
            self.config.setdefault("api", {})["deriv_token"] = token
        
        # WebSocket URL
        if ws_url := os.getenv("DERIV_WS_URL"):
            self.config.setdefault("websocket", {})["url"] = ws_url
        
        # Database
        if db_path := os.getenv("PROJECT_ALPHA_DB"):
            self.config.setdefault("storage", {})["database_path"] = db_path
        
        # Logging
        if log_level := os.getenv("LOG_LEVEL"):
            self.config.setdefault("logging", {})["level"] = log_level
        
        # UI
        if dark_mode := os.getenv("DARK_MODE"):
            self.config.setdefault("ui", {})["dark_mode"] = dark_mode.lower() == "true"
    
    def get(self, key: str, default=None):
        """
        Get configuration value by dot notation.
        
        Args:
            key: Dot notation key (e.g., "websocket.url")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value):
        """
        Set configuration value.
        
        Args:
            key: Dot notation key
            value: Value to set
        """
        keys = key.split('.')
        target = self.config
        
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        target[keys[-1]] = value

# Global configuration instance
settings = Config()
