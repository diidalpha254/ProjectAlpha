"""
Data Buffer Manager
Manages buffering of incoming tick data with configurable window sizes.
"""

from typing import Dict, List, Optional, Any
from collections import deque
from datetime import datetime
import threading

from core.types import Tick, RollingWindow
from core.constants import WindowSize
from core.logger import get_logger
from core.exceptions import DataValidationError


logger = get_logger(__name__)


class DataBuffer:
    """
    Manages multiple rolling windows of tick data with different sizes.
    Thread-safe implementation for real-time data processing.
    """
    
    def __init__(self):
        """Initialize the data buffer with configured window sizes."""
        self._lock = threading.RLock()
        self._windows: Dict[int, RollingWindow] = {}
        self._all_ticks: deque = deque(maxlen=50000)
        self._last_digit_history: deque = deque(maxlen=50000)
        
        # Initialize windows
        window_sizes = [100, 500, 1000, 5000, 10000]
        for size in window_sizes:
            self._windows[size] = RollingWindow(
                size=size,
                ticks=[],
                last_digits=[],
                prices=[],
                timestamps=[]
            )
        
        logger.info(f"Initialized DataBuffer with windows: {window_sizes}")
    
    def add_tick(self, tick: Tick) -> None:
        """
        Add a tick to the buffer and update all windows.
        
        Args:
            tick: Tick object to add
        """
        with self._lock:
            # Validate tick
            if not isinstance(tick, Tick):
                raise DataValidationError("Invalid tick object")
            
            # Add to global buffer
            self._all_ticks.append(tick)
            self._last_digit_history.append(tick.last_digit)
            
            # Update each window
            for window in self._windows.values():
                window.ticks.append(tick)
                window.last_digits.append(tick.last_digit)
                window.prices.append(float(tick.price))
                window.timestamps.append(tick.timestamp)
                window.last_updated = datetime.now()
                
                # Maintain window size
                if len(window.ticks) > window.size:
                    window.ticks = window.ticks[-window.size:]
                    window.last_digits = window.last_digits[-window.size:]
                    window.prices = window.prices[-window.size:]
                    window.timestamps = window.timestamps[-window.size:]
            
            logger.debug(f"Added tick: {tick.symbol} @ {tick.price} (digit: {tick.last_digit})")
    
    def get_window(self, size: int) -> Optional[RollingWindow]:
        """
        Get a specific rolling window.
        
        Args:
            size: Window size (100, 500, 1000, 5000, 10000)
            
        Returns:
            Optional[RollingWindow]: The window or None if not found
        """
        with self._lock:
            return self._windows.get(size)
    
    def get_all_windows(self) -> Dict[int, RollingWindow]:
        """
        Get all rolling windows.
        
        Returns:
            Dict[int, RollingWindow]: Dictionary of windows by size
        """
        with self._lock:
            return self._windows.copy()
    
    def get_last_digits(self, count: int = 100) -> List[int]:
        """
        Get the last N digits from the buffer.
        
        Args:
            count: Number of digits to retrieve
            
        Returns:
            List[int]: List of last digits
        """
        with self._lock:
            if count > len(self._last_digit_history):
                return list(self._last_digit_history)
            return list(self._last_digit_history)[-count:]
    
    def get_all_ticks(self, count: Optional[int] = None) -> List[Tick]:
        """
        Get all ticks or last N ticks from the buffer.
        
        Args:
            count: Optional number of ticks to retrieve
            
        Returns:
            List[Tick]: List of ticks
        """
        with self._lock:
            if count is None:
                return list(self._all_ticks)
            return list(self._all_ticks)[-count:]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get buffer statistics.
        
        Returns:
            Dict[str, Any]: Statistics about the buffer
        """
        with self._lock:
            return {
                "total_ticks": len(self._all_ticks),
                "last_digit_history_length": len(self._last_digit_history),
                "windows": {
                    size: {
                        "size": window.size,
                        "ticks": len(window.ticks),
                        "is_full": window.is_full()
                    }
                    for size, window in self._windows.items()
                },
                "last_updated": max(
                    (w.last_updated for w in self._windows.values() if w.last_updated),
                    default=None
                )
            }
    
    def clear(self) -> None:
        """Clear all buffers and windows."""
        with self._lock:
            self._all_ticks.clear()
            self._last_digit_history.clear()
            for window in self._windows.values():
                window.ticks.clear()
                window.last_digits.clear()
                window.prices.clear()
                window.timestamps.clear()
                window.last_updated = None
            
            logger.info("Data buffer cleared")
    
    def get_digit_frequency(self, window_size: int = 100) -> Dict[int, int]:
        """
        Calculate digit frequency for a specific window.
        
        Args:
            window_size: Size of the window to analyze
            
        Returns:
            Dict[int, int]: Frequency count for each digit (0-9)
        """
        with self._lock:
            window = self._windows.get(window_size)
            if not window:
                return {}
            
            frequency = {i: 0 for i in range(10)}
            for digit in window.last_digits:
                frequency[digit] = frequency.get(digit, 0) + 1
            
            return frequency
    
    def get_digit_probability(self, window_size: int = 100) -> Dict[int, float]:
        """
        Calculate digit probability for a specific window.
        
        Args:
            window_size: Size of the window to analyze
            
        Returns:
            Dict[int, float]: Probability for each digit (0-9)
        """
        frequency = self.get_digit_frequency(window_size)
        total = sum(frequency.values())
        
        if total == 0:
            return {i: 0.0 for i in range(10)}
        
        return {digit: count / total for digit, count in frequency.items()}
