"""
Volatility Analysis Module
Measures price volatility, momentum, and market dynamics.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from datetime import datetime
from dataclasses import dataclass

from ..core.types import VolatilityMetrics
from ..core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MomentumResult:
    """Results from momentum analysis."""
    current_momentum: float
    momentum_score: float  # 0-1, higher = stronger momentum
    direction: str  # 'up', 'down', 'neutral'
    strength: float
    acceleration: float
    confidence: float
    timestamp: datetime


class VolatilityAnalyzer:
    """
    Analyzes price volatility, momentum, and market dynamics.
    Uses statistical measures and trend indicators.
    """
    
    def __init__(self):
        """Initialize the volatility analyzer."""
        self._cache = {}
        logger.info("VolatilityAnalyzer initialized")
    
    def analyze_volatility(self, prices: List[float]) -> VolatilityMetrics:
        """
        Analyze price volatility.
        
        Args:
            prices: List of price values
            
        Returns:
            VolatilityMetrics: Volatility metrics
        """
        if not prices:
            return self._empty_metrics()
        
        # Convert to numpy array
        prices_array = np.array(prices)
        
        # Calculate metrics
        mean = np.mean(prices_array)
        median = np.median(prices_array)
        std_dev = np.std(prices_array, ddof=1) if len(prices) > 1 else 0
        variance = std_dev ** 2
        price_range = np.max(prices_array) - np.min(prices_array)
        
        # Coefficient of variation
        cv = std_dev / mean if mean != 0 else 0
        
        return VolatilityMetrics(
            standard_deviation=std_dev,
            variance=variance,
            range=price_range,
            mean=mean,
            median=median,
            coefficient_of_variation=cv,
            timestamp=datetime.now()
        )
    
    def analyze_momentum(self, prices: List[float]) -> MomentumResult:
        """
        Analyze price momentum.
        
        Args:
            prices: List of price values
            
        Returns:
            MomentumResult: Momentum analysis
        """
        if len(prices) < 2:
            return self._empty_momentum()
        
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        # Current momentum (short-term)
        recent_returns = returns[-10:] if len(returns) >= 10 else returns
        current_momentum = np.mean(recent_returns) if recent_returns.size > 0 else 0
        
        # Long-term momentum
        long_returns = returns[-50:] if len(returns) >= 50 else returns
        long_momentum = np.mean(long_returns) if long_returns.size > 0 else 0
        
        # Direction
        if current_momentum > 0.001:
            direction = 'up'
        elif current_momentum < -0.001:
            direction = 'down'
        else:
            direction = 'neutral'
        
        # Strength (0-1)
        strength = min(abs(current_momentum) * 10, 1.0)  # 0.1% = 1, 1% = max
        
        # Acceleration
        if len(returns) >= 2:
            acceleration = returns[-1] - returns[-2]
        else:
            acceleration = 0.0
        
        # Calculate momentum score (0-1)
        momentum_score = self._calculate_momentum_score(current_momentum, strength, direction)
        
        # Confidence
        confidence = self._calculate_momentum_confidence(len(prices), strength, direction)
        
        return MomentumResult(
            current_momentum=current_momentum,
            momentum_score=momentum_score,
            direction=direction,
            strength=strength,
            acceleration=acceleration,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    def _calculate_momentum_score(self, momentum: float, strength: float, direction: str) -> float:
        """Calculate overall momentum score."""
        # Base score from strength
        score = strength * 0.7
        
        # Add bonus for clear direction
        if direction != 'neutral':
            score += 0.15
        
        # Add bonus for momentum magnitude
        if abs(momentum) > 0.005:
            score += 0.15
        
        return min(score, 1.0)
    
    def _calculate_momentum_confidence(self, sample_size: int, strength: float, direction: str) -> float:
        """Calculate confidence in momentum analysis."""
        confidence = 0.0
        
        # Sample size factor
        sample_score = min(sample_size / 50.0, 1.0)
        confidence += sample_score * 0.4
        
        # Strength factor
        strength_score = strength
        confidence += strength_score * 0.3
        
        # Direction clarity factor
        if direction != 'neutral':
            confidence += 0.2
        
        # Additional factor for significant momentum
        if strength > 0.5 and direction != 'neutral':
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def analyze_trend(self, prices: List[float]) -> Dict[str, any]:
        """
        Analyze price trend using linear regression.
        
        Args:
            prices: List of prices
            
        Returns:
            Dict: Trend analysis results
        """
        if len(prices) < 3:
            return {'trend_strength': 0.0, 'slope': 0.0, 'r_squared': 0.0}
        
        # Linear regression
        x = np.arange(len(prices))
        y = np.array(prices)
        
        slope, intercept = np.polyfit(x, y, 1)
        
        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        ss_res = np.sum((y - y_pred) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Trend strength (0-1)
        trend_strength = min(abs(slope) * 100, 1.0)  # Normalize
        
        # Determine trend direction
        if slope > 0.001:
            direction = 'up'
        elif slope < -0.001:
            direction = 'down'
        else:
            direction = 'neutral'
        
        return {
            'trend_strength': trend_strength,
            'slope': slope,
            'r_squared': r_squared,
            'direction': direction,
            'intercept': intercept
        }
    
    def measure_mean_reversion(self, prices: List[float]) -> Dict[str, any]:
        """
        Measure mean reversion tendency.
        
        Args:
            prices: List of prices
            
        Returns:
            Dict: Mean reversion metrics
        """
        if len(prices) < 5:
            return {'mean_reversion_score': 0.0, 'half_life': 0}
        
        # Calculate mean
        mean_price = np.mean(prices)
        
        # Calculate deviations from mean
        deviations = prices - mean_price
        
        # Calculate auto-correlation of deviations
        if len(deviations) > 1:
            corr = np.corrcoef(deviations[:-1], deviations[1:])[0, 1]
            if np.isnan(corr):
                corr = 0
        else:
            corr = 0
        
        # Mean reversion score (0-1)
        # High negative correlation = strong mean reversion
        mean_reversion_score = max(0, -corr)  # 0 = no reversion, 1 = strong reversion
        
        # Calculate half-life (simplified)
        if corr < 0:
            half_life = int(-np.log(2) / np.log(abs(corr))) if abs(corr) > 0 else 0
        else:
            half_life = 0
        
        return {
            'mean_reversion_score': mean_reversion_score,
            'half_life': half_life,
            'auto_correlation': corr,
            'mean_price': mean_price,
            'deviation_std': np.std(deviations)
        }
    
    def _empty_metrics(self) -> VolatilityMetrics:
        """Return empty volatility metrics."""
        return VolatilityMetrics(
            standard_deviation=0.0,
            variance=0.0,
            range=0.0,
            mean=0.0,
            median=0.0,
            coefficient_of_variation=0.0,
            timestamp=datetime.now()
        )
    
    def _empty_momentum(self) -> MomentumResult:
        """Return empty momentum result."""
        return MomentumResult(
            current_momentum=0.0,
            momentum_score=0.0,
            direction='neutral',
            strength=0.0,
            acceleration=0.0,
            confidence=0.0,
            timestamp=datetime.now()
        )