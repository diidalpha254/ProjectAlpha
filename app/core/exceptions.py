"""
Custom exceptions for Project Alpha
Provides specific exception types for different error scenarios.
"""

from typing import Optional, Any


class ProjectAlphaError(Exception):
    """Base exception class for Project Alpha"""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)


class ConnectionError(ProjectAlphaError):
    """Exception raised for WebSocket connection issues"""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(f"Connection error: {message}", code, details)


class DataValidationError(ProjectAlphaError):
    """Exception raised for data validation failures"""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(f"Data validation error: {message}", code, details)


class StorageError(ProjectAlphaError):
    """Exception raised for database/storage issues"""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(f"Storage error: {message}", code, details)


class AnalyticsError(ProjectAlphaError):
    """Exception raised for analytics computation issues"""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(f"Analytics error: {message}", code, details)


class ConfigurationError(ProjectAlphaError):
    """Exception raised for configuration issues"""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(f"Configuration error: {message}", code, details)


class WebsocketError(ProjectAlphaError):
    """Exception raised for WebSocket errors"""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(f"WebSocket error: {message}", code, details)


class MarketStateError(ProjectAlphaError):
    """Exception raised for market state classification issues"""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(f"Market state error: {message}", code, details)


class FeatureError(ProjectAlphaError):
    """Exception raised for feature-related issues (replay, export, etc.)"""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(f"Feature error: {message}", code, details)