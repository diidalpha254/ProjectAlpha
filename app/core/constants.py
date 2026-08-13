"""
Constants and Enums for Project Alpha
Defines system-wide constants, enumerations, and configuration values.
"""

from enum import Enum, auto
from typing import Dict, Any


class MarketState(Enum):
    """Market state classifications"""
    CALM = "calm"
    RANDOM = "random"
    TRENDING = "trending"
    VOLATILE = "volatile"
    CHAOTIC = "chaotic"
    MEAN_REVERTING = "mean_reverting"
    MOMENTUM_DRIVEN = "momentum_driven"


class RiskLevel(Enum):
    """Risk level classifications"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Digit(Enum):
    """Last digit values (0-9)"""
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9


class WindowSize(Enum):
    """Rolling window sizes"""
    WINDOW_100 = 100
    WINDOW_500 = 500
    WINDOW_1000 = 1000
    WINDOW_5000 = 5000
    WINDOW_10000 = 10000


class DerivSymbol(Enum):
    """Supported Deriv symbols"""
    R_10 = "R_10"
    R_25 = "R_25"
    R_50 = "R_50"
    R_75 = "R_75"
    R_100 = "R_100"
    BOOM_1000 = "BOOM_1000"
    BOOM_500 = "BOOM_500"
    BOOM_300 = "BOOM_300"
    BOOM_200 = "BOOM_200"
    BOOM_100 = "BOOM_100"


class NotificationType(Enum):
    """Notification types"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    ALERT = "alert"


# Configuration constants
DEFAULT_CONFIG: Dict[str, Any] = {
    "websocket": {
        "url": "wss://ws.binaryws.com/websockets/v3",
        "reconnect_delay": 5,
        "max_reconnect_attempts": 10,
        "heartbeat_interval": 30,
    },
    "data": {
        "windows": [100, 500, 1000, 5000, 10000],
        "max_buffer_size": 50000,
        "update_interval": 1.0,
    },
    "analytics": {
        "confidence_threshold": 0.65,
        "markov_order": 1,
        "entropy_bins": 10,
        "cycle_min_length": 5,
    },
    "market_state": {
        "calm_threshold": 0.2,
        "volatile_threshold": 0.7,
        "trend_threshold": 0.6,
        "random_threshold": 0.4,
    },
    "ui": {
        "refresh_rate": 1.0,
        "max_chart_points": 500,
        "dark_mode": True,
    },
    "storage": {
        "database_path": "data/project_alpha.db",
        "max_sessions": 1000,
        "export_format": "csv",
    },
    "api": {
        "deriv_app_id": 1089,  # Default Deriv test app ID
    }
}


# Statistical thresholds
STATISTICAL_THRESHOLDS = {
    "hot_digit_z_score": 1.5,
    "cold_digit_z_score": -1.5,
    "significant_deviation": 0.2,
    "trend_strength_min": 0.6,
    "entropy_threshold_low": 2.0,
    "entropy_threshold_high": 3.5,
    "confidence_high": 0.8,
    "confidence_medium": 0.6,
    "confidence_low": 0.4,
}


# Digit display names and colors
DIGIT_NAMES = {
    0: "Zero",
    1: "One",
    2: "Two",
    3: "Three",
    4: "Four",
    5: "Five",
    6: "Six",
    7: "Seven",
    8: "Eight",
    9: "Nine",
}

DIGIT_COLORS = {
    0: "#FF6B6B",
    1: "#4ECDC4",
    2: "#45B7D1",
    3: "#96CEB4",
    4: "#FFEAA7",
    5: "#DDA0DD",
    6: "#FFA07A",
    7: "#87CEEB",
    8: "#98D8C8",
    9: "#F7DC6F",
}


# Market state descriptions
MARKET_STATE_DESCRIPTIONS = {
    MarketState.CALM: {
        "emoji": "🌊",
        "color": "#2ECC71",
        "risk_level": RiskLevel.VERY_LOW,
        "description": "Market is exhibiting low volatility and stable patterns",
    },
    MarketState.RANDOM: {
        "emoji": "🎲",
        "color": "#3498DB",
        "risk_level": RiskLevel.MODERATE,
        "description": "Market shows random behavior with no clear patterns",
    },
    MarketState.TRENDING: {
        "emoji": "📈",
        "color": "#E67E22",
        "risk_level": RiskLevel.MODERATE,
        "description": "Market is following a clear directional trend",
    },
    MarketState.VOLATILE: {
        "emoji": "🌪️",
        "color": "#E74C3C",
        "risk_level": RiskLevel.HIGH,
        "description": "Market is experiencing high volatility and rapid changes",
    },
    MarketState.CHAOTIC: {
        "emoji": "🌀",
        "color": "#8E44AD",
        "risk_level": RiskLevel.VERY_HIGH,
        "description": "Market behavior is highly unpredictable and chaotic",
    },
    MarketState.MEAN_REVERTING: {
        "emoji": "↔️",
        "color": "#1ABC9C",
        "risk_level": RiskLevel.LOW,
        "description": "Market shows tendency to revert to the mean",
    },
    MarketState.MOMENTUM_DRIVEN: {
        "emoji": "⚡",
        "color": "#F39C12",
        "risk_level": RiskLevel.MODERATE,
        "description": "Market is driven by strong momentum",
    },
}