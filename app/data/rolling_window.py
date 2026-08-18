"""
Rolling Window Manager
Manages efficient rolling windows with automatic updates and statistics.
"""

from typing import List, Dict, Optional, Any, Tuple
from collections import deque
from datetime import datetime
import numpy as np
from dataclasses import dataclass, field
import threading

from ..core.types import Tick
from ..core.logger import get_logger
from ..core.exceptions import DataValidationError

logger = get_logger(__name__)


@dataclass
class WindowStats:
    """Statistics for a rolling window."""
    size: int
    count: int
    is_full: bool
    first_timestamp: Optional[datetime] = None
    last_timestamp: Optional[datetime] = None
    mean_price: float = 0.0
    std_price: float = 0.0
    min_price: float = 0.0
    max_price: float = 0.0
    digit_frequencies: Dict[int, int] = field(default_factory=dict)
    digit_probabilities: Dict[int, float] = field(default_factory=dict)
    tick_rate: float = 0.0
    last_update: Optional[datetime] = None


class RollingWindowManager:
    """
    Manages multiple rolling windows with efficient storage and real-time statistics.
    Supports windows of various sizes with O(1) updates.
    """
    
    def __init__(self, window_sizes: List[int] = None):
        """
        Initialize the rolling window manager.
        
        Args:
            window_sizes: List of window sizes to maintain
        """
        if window_sizes is None:
            window_sizes = [50, 100, 500, 1000, 5000, 10000]
        
        self._lock = threading.RLock()
        self.window_sizes = sorted(window_sizes)
        
        # Main data structures
        self._ticks: deque = deque(maxlen=max(window_sizes))
        self._prices: deque = deque(maxlen=max(window_sizes))
        self._last_digits: deque = deque(maxlen=max(window_sizes))
        self._timestamps: deque = deque(maxlen=max(window_sizes))
        
        # Window-specific views
        self._windows: Dict[int, deque] = {}
        self._window_stats: Dict[int, WindowStats] = {}
        
        # Statistics tracking
        self._running_mean = 0.0
        self._running_m2 = 0.0
        self._digit_counts = {i: 0 for i in range(10)}
        self._total_ticks = 0
        
        # Initialize windows
        for size in self.window_sizes:
            self._windows[size] = deque(maxlen=size)
            self._window_stats[size] = WindowStats(
                size=size,
                count=0,
                is_full=False
            )
        
        logger.info(f"RollingWindowManager initialized with sizes: {self.window_sizes}")
    
    def add_tick(self, tick: Tick) -> Dict[int, WindowStats]:
        """
        Add a new tick to all rolling windows.
        
        Args:
            tick: Tick object to add
            
        Returns:
            Dict[int, WindowStats]: Updated statistics for all windows
        """
        with self._lock:
            try:
                # Add to main buffers
                self._ticks.append(tick)
                self._prices.append(float(tick.price))
                self._last_digits.append(tick.last_digit)
                self._timestamps.append(tick.timestamp)
                self._total_ticks += 1
                
                # Update running statistics (Welford's algorithm)
                price_float = float(tick.price)
                delta = price_float - self._running_mean
                self._running_mean += delta / self._total_ticks
                delta2 = price_float - self._running_mean
                self._running_m2 += delta * delta2
                
                # Update digit counts
                self._digit_counts[tick.last_digit] = self._digit_counts.get(tick.last_digit, 0) + 1
                
                # Update each window
                updated_stats = {}
                for size in self.window_sizes:
                    window = self._windows[size]
                    window.append(tick)
                    
                    # Update window statistics
                    stats = self._window_stats[size]
                    stats.count = len(window)
                    stats.is_full = len(window) >= size
                    
                    if stats.count > 0:
                        stats.first_timestamp = window[0].timestamp
                        stats.last_timestamp = window[-1].timestamp
                        stats.last_update = datetime.now()
                        
                        # Calculate window statistics
                        window_prices = [float(t.price) for t in window]
                        stats.mean_price = np.mean(window_prices)
                        stats.std_price = np.std(window_prices, ddof=1) if len(window_prices) > 1 else 0
                        stats.min_price = np.min(window_prices)
                        stats.max_price = np.max(window_prices)
                        
                        # Calculate digit frequencies
                        digits = [t.last_digit for t in window]
                        stats.digit_frequencies = {
                            i: digits.count(i) for i in range(10)
                        }
                        
                        # Calculate probabilities
                        total = len(digits)
                        stats.digit_probabilities = {
                            i: count / total if total > 0 else 0.0
                            for i, count in stats.digit_frequencies.items()
                        }
                        
                        # Calculate tick rate (ticks per second)
                        if len(window) > 1:
                            time_diff = (window[-1].timestamp - window[0].timestamp).total_seconds()
                            if time_diff > 0:
                                stats.tick_rate = len(window) / time_diff
                    
                    updated_stats[size] = stats
                
                logger.debug(f"Added tick {tick.tick_id}, total: {self._total_ticks}")
                return updated_stats
                
            except Exception as e:
                logger.error(f"Error adding tick to rolling windows: {e}", exc_info=True)
                raise DataValidationError(f"Failed to add tick: {e}")
    
    def get_window(self, size: int) -> List[Tick]:
        """
        Get the current contents of a specific window.
        
        Args:
            size: Window size
            
        Returns:
            List[Tick]: List of ticks in the window
        """
        with self._lock:
            if size not in self._windows:
                raise ValueError(f"Window size {size} not configured")
            return list(self._windows[size])
    
    def get_window_stats(self, size: int) -> Optional[WindowStats]:
        """
        Get statistics for a specific window.
        
        Args:
            size: Window size
            
        Returns:
            Optional[WindowStats]: Window statistics or None
        """
        with self._lock:
            return self._window_stats.get(size)
    
    def get_all_stats(self) -> Dict[int, WindowStats]:
        """
        Get statistics for all windows.
        
        Returns:
            Dict[int, WindowStats]: Statistics for all windows
        """
        with self._lock:
            return self._window_stats.copy()
    
    def get_last_digits(self, count: int = 100) -> List[int]:
        """
        Get the last N digits.
        
        Args:
            count: Number of digits to retrieve
            
        Returns:
            List[int]: List of last digits
        """
        with self._lock:
            return list(self._last_digits)[-count:]
    
    def get_prices(self, count: int = 100) -> List[float]:
        """
        Get the last N prices.
        
        Args:
            count: Number of prices to retrieve
            
        Returns:
            List[float]: List of prices
        """
        with self._lock:
            return list(self._prices)[-count:]
    
    def get_tick_rate(self) -> float:
        """
        Calculate the current tick rate (ticks per second).
        
        Returns:
            float: Ticks per second
        """
        with self._lock:
            if len(self._timestamps) < 2:
                return 0.0
            
            recent = list(self._timestamps)[-100:]
            if len(recent) < 2:
                return 0.0
            
            time_diff = (recent[-1] - recent[0]).total_seconds()
            if time_diff <= 0:
                return 0.0
            
            return (len(recent) - 1) / time_diff
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """
        Get overall statistics across all windows.
        
        Returns:
            Dict[str, Any]: Overall statistics
        """
        with self._lock:
            variance = self._running_m2 / max(1, self._total_ticks - 1)
            std_dev = np.sqrt(variance) if variance > 0 else 0.0
            
            return {
                "total_ticks": self._total_ticks,
                "mean_price": self._running_mean,
                "std_price": std_dev,
                "min_price": min(self._prices) if self._prices else 0.0,
                "max_price": max(self._prices) if self._prices else 0.0,
                "digit_counts": self._digit_counts,
                "tick_rate": self.get_tick_rate(),
                "timestamp": datetime.now()
            }
    
    def get_digit_frequency(self, window_size: int = 100) -> Dict[int, int]:
        """
        Get digit frequency for a specific window.
        
        Args:
            window_size: Window size
            
        Returns:
            Dict[int, int]: Digit frequency counts
        """
        with self._lock:
            if window_size not in self._window_stats:
                return {i: 0 for i in range(10)}
            
            return self._window_stats[window_size].digit_frequencies.copy()
    
    def get_digit_probability(self, window_size: int = 100) -> Dict[int, float]:
        """
        Get digit probability for a specific window.
        
        Args:
            window_size: Window size
            
        Returns:
            Dict[int, float]: Digit probabilities
        """
        with self._lock:
            if window_size not in self._window_stats:
                return {i: 0.0 for i in range(10)}
            
            return self._window_stats[window_size].digit_probabilities.copy()
    
    def get_transition_matrix(self, window_size: int = 100) -> np.ndarray:
        """
        Calculate the transition probability matrix for a window.
        
        Args:
            window_size: Window size
            
        Returns:
            np.ndarray: 10x10 transition matrix
        """
        with self._lock:
            if window_size not in self._windows:
                return np.zeros((10, 10))
            
            window = self._windows[window_size]
            if len(window) < 2:
                return np.zeros((10, 10))
            
            matrix = np.zeros((10, 10))
            digits = [t.last_digit for t in window]
            
            for i in range(len(digits) - 1):
                from_digit = digits[i]
                to_digit = digits[i + 1]
                matrix[from_digit][to_digit] += 1
            
            row_sums = matrix.sum(axis=1, keepdims=True)
            matrix = np.divide(matrix, row_sums, where=row_sums != 0)
            
            return matrix
    
    def get_window_summary(self, size: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a window.
        
        Args:
            size: Window size
            
        Returns:
            Dict[str, Any]: Comprehensive window summary
        """
        with self._lock:
            if size not in self._window_stats:
                return {}
            
            stats = self._window_stats[size]
            window = self._windows[size]
            
            digits = [t.last_digit for t in window]
            
            most_common = max(stats.digit_frequencies.items(), key=lambda x: x[1]) if digits else (0, 0)
            least_common = min(stats.digit_frequencies.items(), key=lambda x: x[1]) if digits else (0, 0)
            
            probs = [p for p in stats.digit_probabilities.values() if p > 0]
            entropy = -sum(p * np.log2(p) for p in probs) if probs else 0
            
            return {
                "size": size,
                "count": stats.count,
                "is_full": stats.is_full,
                "first_timestamp": stats.first_timestamp,
                "last_timestamp": stats.last_timestamp,
                "mean_price": stats.mean_price,
                "std_price": stats.std_price,
                "min_price": stats.min_price,
                "max_price": stats.max_price,
                "tick_rate": stats.tick_rate,
                "digit_frequencies": stats.digit_frequencies,
                "digit_probabilities": stats.digit_probabilities,
                "most_common_digit": most_common[0],
                "most_common_count": most_common[1],
                "least_common_digit": least_common[0],
                "least_common_count": least_common[1],
                "entropy": entropy,
                "consecutive_streaks": self._calculate_streaks(digits),
                "last_update": stats.last_update
            }
    
    def _calculate_streaks(self, digits: List[int]) -> Dict[int, List[int]]:
        """
        Calculate consecutive streaks for each digit.
        
        Args:
            digits: List of digits
            
        Returns:
            Dict[int, List[int]]: Streak lengths for each digit
        """
        streaks = {i: [] for i in range(10)}
        
        if not digits:
            return streaks
        
        current_digit = digits[0]
        current_streak = 1
        
        for digit in digits[1:]:
            if digit == current_digit:
                current_streak += 1
            else:
                streaks[current_digit].append(current_streak)
                current_digit = digit
                current_streak = 1
        
        streaks[current_digit].append(current_streak)
        
        return streaks
    
    def clear(self):
        """Clear all windows and reset statistics."""
        with self._lock:
            self._ticks.clear()
            self._prices.clear()
            self._last_digits.clear()
            self._timestamps.clear()
            self._total_ticks = 0
            self._running_mean = 0.0
            self._running_m2 = 0.0
            self._digit_counts = {i: 0 for i in range(10)}
            
            for size in self.window_sizes:
                self._windows[size].clear()
                self._window_stats[size] = WindowStats(
                    size=size,
                    count=0,
                    is_full=False
                )
            
            logger.info("Rolling windows cleared")
