"""
Type definitions for Project Alpha
Strong typing for all data structures used in the application.
"""

from typing import List, Dict, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
import numpy as np
from .constants import MarketState, RiskLevel


@dataclass
class Tick:
    """Represents a single tick data point"""
    timestamp: datetime
    symbol: str
    price: Decimal
    last_digit: int
    tick_id: Optional[str] = None
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    volume: Optional[int] = None
    
    def __post_init__(self):
        """Validate tick data after initialization"""
        if not 0 <= self.last_digit <= 9:
            raise ValueError("Last digit must be between 0 and 9")
        if self.price <= 0:
            raise ValueError("Price must be positive")


@dataclass
class RollingWindow:
    """Container for rolling window data"""
    size: int
    ticks: List[Tick] = field(default_factory=list)
    last_digits: List[int] = field(default_factory=list)
    prices: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    last_updated: Optional[datetime] = None
    
    def is_full(self) -> bool:
        """Check if window has reached its size limit"""
        return len(self.ticks) >= self.size
    
    def is_empty(self) -> bool:
        """Check if window is empty"""
        return len(self.ticks) == 0
    
    def get_last_n_digits(self, n: int) -> List[int]:
        """Get last n digits from the window"""
        return self.last_digits[-n:] if n <= len(self.last_digits) else self.last_digits


@dataclass
class FrequencyAnalysis:
    """Frequency analysis results"""
    digit_counts: Dict[int, int]
    total_counts: int
    expected_frequency: float
    frequencies: Dict[int, float]
    z_scores: Dict[int, float]
    hot_digits: List[int]
    cold_digits: List[int]
    rarity_scores: Dict[int, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TransitionMatrix:
    """Transition probability matrix results"""
    matrix: np.ndarray
    from_digits: List[int]
    to_digits: List[int]
    counts: Dict[Tuple[int, int], int]
    probabilities: Dict[Tuple[int, int], float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConsecutiveStreak:
    """Consecutive streak analysis results"""
    current_digit: int
    current_streak: int
    max_streak: int
    digit_streaks: Dict[int, List[int]]
    average_streaks: Dict[int, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EntropyAnalysis:
    """Entropy and randomness analysis"""
    entropy: float
    normalized_entropy: float
    randomness_score: float
    is_random: bool
    distribution: Dict[int, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VolatilityMetrics:
    """Volatility measurement results"""
    standard_deviation: float
    variance: float
    range: float
    mean: float
    median: float
    coefficient_of_variation: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketStateAnalysis:
    """Complete market state analysis"""
    state: MarketState
    confidence: float
    risk_level: RiskLevel
    indicators: Dict[str, float]
    evidence: List[str]
    explanation: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MatchDifferInsight:
    """Match/Differ intelligence insights"""
    market_condition: str
    observations: List[str]
    digit_distribution: Dict[int, float]
    transition_probabilities: Dict[str, float]
    confidence_indicators: Dict[str, float]
    pattern_summary: str
    historical_context: str
    explanation: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AIInsight:
    """AI Market Analyst insights"""
    what_is_happening: str
    why_classified: str
    statistical_factors: List[str]
    market_differences: str
    risks: List[str]
    confidence_level: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SessionStats:
    """Session statistics"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_ticks: int = 0
    symbol: str = ""
    average_price: float = 0.0
    max_price: float = 0.0
    min_price: float = 0.0
    digit_counts: Dict[int, int] = field(default_factory=dict)
    most_common_digit: Optional[int] = None
    volatility: float = 0.0
    entropy: float = 0.0
    market_states: List[MarketState] = field(default_factory=list)


@dataclass
class Notification:
    """System notification"""
    id: str
    type: str  # info, warning, error, success, alert
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    read: bool = False
    action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class Configuration:
    """Application configuration"""
    websocket_url: str
    reconnect_delay: int
    max_reconnect_attempts: int
    windows: List[int]
    max_buffer_size: int
    update_interval: float
    confidence_threshold: float
    database_path: str
    max_sessions: int
    export_format: str
    dark_mode: bool
    deriv_app_id: int