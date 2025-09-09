import os
import json
import yaml
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass

class ConfigLoader:
    """Configuration loader that supports multiple formats and sources."""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        env_prefix: str = "",
        default_config: Optional[Dict[str, Any]] = None,
        auto_reload: bool = False,
        config_model: Optional[type] = None
    ):
        self.config_path = config_path
        self.env_prefix = env_prefix
        self.default_config = default_config or {}
        self.auto_reload = auto_reload
        self.config_model = config_model
        self._config: Dict[str, Any] = {}
        self._last_load_time = 0
        
        # Load configuration immediately
        self.reload()
    
    def reload(self) -> None:
        """Reload configuration from all sources."""
        # Start with default configuration
        config = self.default_config.copy()
        
        # Load from file if specified
        if self.config_path:
            file_config = self._load_from_file(self.config_path)
            if file_config:
                self._deep_update(config, file_config)
        
        # Override with environment variables
        env_config = self._load_from_env()
        if env_config:
            self._deep_update(config, env_config)
        
        # Validate against model if provided
        if self.config_model:
            try:
                validated_config = self.config_model(**config)
                config = validated_config.dict()
            except Exception as e:
                raise ConfigurationError(f"Configuration validation failed: {str(e)}")
        
        self._config = config
        self._last_load_time = os.path.getmtime(self.config_path) if self.config_path and os.path.exists(self.config_path) else 0
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        # Check if auto-reload is enabled and file has changed
        if self.auto_reload and self.config_path and os.path.exists(self.config_path):
            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self._last_load_time:
                self.reload()
        
        # Handle nested keys with dot notation
        if '.' in key:
            parts = key.split('.')
            value = self._config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        
        return self._config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        # Check if auto-reload is enabled and file has changed
        if self.auto_reload and self.config_path and os.path.exists(self.config_path):
            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self._last_load_time:
                self.reload()
                
        return self._config.copy()
    
    def _load_from_file(self, path: str) -> Dict[str, Any]:
        """Load configuration from a file.
        
        Supports JSON, YAML, and Python files.
        """
        if not os.path.exists(path):
            logger.warning(f"Configuration file not found: {path}")
            return {}
        
        try:
            _, ext = os.path.splitext(path)
            with open(path, 'r') as f:
                if ext.lower() in ('.json'):
                    return json.load(f)
                elif ext.lower() in ('.yaml', '.yml'):
                    return yaml.safe_load(f)
                elif ext.lower() in ('.py'):
                    # This is less secure but sometimes needed
                    # Consider using a safer approach in production
                    config_dict = {}
                    exec(f.read(), {}, config_dict)
                    return config_dict
                else:
                    logger.warning(f"Unsupported configuration file format: {ext}")
                    return {}
        except Exception as e:
            logger.error(f"Error loading configuration from {path}: {str(e)}")
            return {}
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables.
        
        Environment variables are converted to nested dictionary structure.
        For example, APP_DB_HOST becomes {"app": {"db": {"host": value}}}
        """
        config = {}
        prefix = self.env_prefix.upper() + '_' if self.env_prefix else ''
        
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            
            # Remove prefix and convert to lowercase
            if prefix:
                key = key[len(prefix):]
            
            # Split by underscore to create nested structure
            parts = key.lower().split('_')
            
            # Convert value to appropriate type
            if value.lower() in ('true', 'yes', 'y', '1'):
                value = True
            elif value.lower() in ('false', 'no', 'n', '0'):
                value = False
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                value = float(value)
            
            # Build nested dictionary
            current = config
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    current[part] = value
                else:
                    if part not in current:
                        current[part] = {}
                    # Make sure current[part] is a dictionary before proceeding
                    if not isinstance(current[part], dict):
                        current[part] = {}
                    current = current[part]
        
        return config
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep update a nested dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value

# Example configuration model
class DatabaseConfig(BaseModel):
    """Database configuration model."""
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    username: str
    password: str
    database: str
    pool_size: int = Field(default=5)
    ssl_mode: Optional[str] = Field(default=None)

class RedisConfig(BaseModel):
    """Redis configuration model."""
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    password: Optional[str] = Field(default=None)
    db: int = Field(default=0)

class LoggingConfig(BaseModel):
    """Logging configuration model."""
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file: Optional[str] = Field(default=None)

class AppConfig(BaseModel):
    """Application configuration model."""
    debug: bool = Field(default=False)
    secret_key: str
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"])
    database: DatabaseConfig
    redis: Optional[RedisConfig] = Field(default=None)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    class Config:
        extra = "allow"  # Allow extra fields