"""
Market Indicators Module
Provides specialized indicators for market state classification.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime
from collections import Counter

from ..core.logger import get_logger

logger = get_logger(__name__)


class MarketIndicators:
    """
    Calculates specialized market indicators for state classification.
    """
    
    def __init__(self):
        """Initialize the market indicators calculator."""
        logger.info("MarketIndicators initialized")
    
    def calculate_indicators(self, ticks: List[Any]) -> Dict[str, Any]:
        """
        Calculate all market indicators.
        
        Args:
            ticks: List of tick objects
            
        Returns:
            Dict[str, Any]: Calculated indicators
        """
        if not ticks or len(ticks) < 10:
            return self._empty_indicators()
        
        try:
            prices = [float(t.price) for t in ticks]
            digits = [t.last_digit for t in ticks]
            
            indicators = {
                'timestamp': datetime.now(),
                'sample_size': len(ticks),
                'price_metrics': self._calculate_price_metrics(prices),
                'digit_metrics': self._calculate_digit_metrics(digits),
                'volatility_metrics': self._calculate_volatility_metrics(prices),
                'trend_metrics': self._calculate_trend_metrics(prices),
                'momentum_metrics': self._calculate_momentum_metrics(prices),
                'pattern_metrics': self._calculate_pattern_metrics(digits),
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return self._empty_indicators()
    
    def _calculate_price_metrics(self, prices: List[float]) -> Dict[str, float]:
        """Calculate price-based metrics."""
        if not prices:
            return {}
        prices = np.array(prices)
        return {
            'mean': float(np.mean(prices)),
            'median': float(np.median(prices)),
            'std': float(np.std(prices)),
            'min': float(np.min(prices)),
            'max': float(np.max(prices)),
            'range': float(np.max(prices) - np.min(prices)),
            'change': float(prices[-1] - prices[0]),
            'change_pct': float((prices[-1] - prices[0]) / prices[0] * 100) if prices[0] > 0 else 0,
        }
    
    def _calculate_digit_metrics(self, digits: List[int]) -> Dict[str, Any]:
        """Calculate digit-based metrics."""
        if not digits:
            return {}
        counts = Counter(digits)
        total = len(digits)
        frequencies = {i: counts.get(i, 0) / total for i in range(10)}
        probs = [freq for freq in frequencies.values() if freq > 0]
        entropy = -sum(p * np.log2(p) for p in probs) if probs else 0
        expected = 0.1
        hot_digits = [i for i, freq in frequencies.items() if freq > expected * 1.5]
        cold_digits = [i for i, freq in frequencies.items() if freq < expected * 0.5]
        streaks = self._calculate_digit_streaks(digits)
        return {
            'counts': dict(counts),
            'frequencies': frequencies,
            'entropy': entropy,
            'hot_digits': hot_digits,
            'cold_digits': cold_digits,
            'most_common': max(counts.items(), key=lambda x: x[1])[0] if counts else None,
            'least_common': min(counts.items(), key=lambda x: x[1])[0] if counts else None,
            'max_streak': max(streaks.values()) if streaks else 0,
            'current_streak': self._calculate_current_streak(digits),
        }
    
    def _calculate_digit_streaks(self, digits: List[int]) -> Dict[int, int]:
        """Calculate consecutive streaks for each digit."""
        if not digits:
            return {}
        streaks = {i: 0 for i in range(10)}
        current_digit = digits[0]
        current_streak = 1
        for digit in digits[1:]:
            if digit == current_digit:
                current_streak += 1
            else:
                streaks[current_digit] = max(streaks[current_digit], current_streak)
                current_digit = digit
                current_streak = 1
        streaks[current_digit] = max(streaks[current_digit], current_streak)
        return streaks
    
    def _calculate_current_streak(self, digits: List[int]) -> int:
        """Calculate current consecutive streak."""
        if not digits:
            return 0
        current_digit = digits[-1]
        streak = 1
        for i in range(len(digits) - 2, -1, -1):
            if digits[i] == current_digit:
                streak += 1
            else:
                break
        return streak
    
    def _calculate_volatility_metrics(self, prices: List[float]) -> Dict[str, float]:
        """Calculate volatility metrics."""
        if len(prices) < 2:
            return {}
        prices = np.array(prices)
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns) * np.sqrt(252)
        high = np.max(prices)
        low = np.min(prices)
        range_volatility = (high - low) / np.mean(prices) if np.mean(prices) != 0 else 0
        if len(prices) > 1:
            true_ranges = []
            for i in range(1, len(prices)):
                h = prices[i]
                l = prices[i]
                pc = prices[i-1]
                tr = max(h - l, abs(h - pc), abs(l - pc))
                true_ranges.append(tr)
            atr = np.mean(true_ranges)
        else:
            atr = 0
        return {
            'volatility': volatility,
            'range_volatility': range_volatility,
            'average_true_range': atr,
            'returns_std': np.std(returns),
            'returns_mean': np.mean(returns),
        }
    
    def _calculate_trend_metrics(self, prices: List[float]) -> Dict[str, float]:
        """Calculate trend metrics."""
        if len(prices) < 3:
            return {}
        x = np.arange(len(prices))
        y = np.array(prices)
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        ss_res = np.sum((y - y_pred) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        trend_strength = min(abs(slope) * 100, 1.0)
        direction = 'up' if slope > 0.001 else 'down' if slope < -0.001 else 'neutral'
        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_squared,
            'trend_strength': trend_strength,
            'direction': direction,
        }
    
    def _calculate_momentum_metrics(self, prices: List[float]) -> Dict[str, float]:
        """Calculate momentum metrics."""
        if len(prices) < 5:
            return {}
        prices = np.array(prices)
        short_returns = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        mid_returns = (prices[-1] - prices[-20]) / prices[-20] if len(prices) >= 20 else short_returns
        long_returns = (prices[-1] - prices[-50]) / prices[-50] if len(prices) >= 50 else mid_returns
        roc = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
        momentum_strength = min(abs(short_returns) * 100, 1.0)
        direction = 'up' if short_returns > 0.001 else 'down' if short_returns < -0.001 else 'neutral'
        return {
            'short_momentum': short_returns,
            'mid_momentum': mid_returns,
            'long_momentum': long_returns,
            'roc': roc,
            'momentum_strength': momentum_strength,
            'direction': direction,
        }
    
    def _calculate_pattern_metrics(self, digits: List[int]) -> Dict[str, Any]:
        """Calculate pattern metrics."""
        if len(digits) < 5:
            return {}
        from ..analytics.patterns import PatternAnalyzer
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(digits)
        return {
            'has_patterns': len(result.repeated_patterns) > 0,
            'pattern_count': len(result.repeated_patterns),
            'pattern_confidence': result.confidence,
            'longest_streak': result.longest_streak,
            'current_streak': result.current_streak,
            'dominant_pattern': result.dominant_pattern,
        }
    
    def _empty_indicators(self) -> Dict[str, Any]:
        """Return empty indicators."""
        return {
            'timestamp': datetime.now(),
            'sample_size': 0,
            'price_metrics': {},
            'digit_metrics': {},
            'volatility_metrics': {},
            'trend_metrics': {},
            'momentum_metrics': {},
            'pattern_metrics': {},
        }
