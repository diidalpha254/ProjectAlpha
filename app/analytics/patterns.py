"""
Pattern Recognition Module
Detects patterns, cycles, and streaks in digit sequences.
"""

from typing import List, Dict, Tuple, Optional, Set
from collections import Counter, defaultdict
from dataclasses import dataclass
import numpy as np
from datetime import datetime

from app.core.types import ConsecutiveStreak
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PatternResult:
    """Results from pattern analysis."""
    repeated_patterns: List[Tuple[List[int], int]]  # Pattern and frequency
    longest_streak: Tuple[int, int]  # (digit, length)
    current_streak: Tuple[int, int]  # (digit, length)
    cycle_lengths: List[int]
    dominant_pattern: List[int]
    confidence: float
    timestamp: datetime


class PatternAnalyzer:
    """
    Detects patterns, cycles, and streaks in digit sequences.
    Uses various pattern recognition techniques.
    """
    
    def __init__(self, min_pattern_length: int = 2, max_pattern_length: int = 5):
        """
        Initialize the pattern analyzer.
        
        Args:
            min_pattern_length: Minimum pattern length to detect
            max_pattern_length: Maximum pattern length to detect
        """
        self.min_pattern_length = min_pattern_length
        self.max_pattern_length = max_pattern_length
        self._cache = {}
        logger.info(f"PatternAnalyzer initialized (min_len={min_pattern_length}, max_len={max_pattern_length})")
    
    def analyze(self, digits: List[int]) -> PatternResult:
        """
        Perform comprehensive pattern analysis.
        
        Args:
            digits: List of digits
            
        Returns:
            PatternResult: Pattern analysis results
        """
        if len(digits) < 2:
            return self._empty_result()
        
        # Find repeated patterns
        repeated_patterns = self._find_repeated_patterns(digits)
        
        # Find longest streak
        longest_streak = self._find_longest_streak(digits)
        
        # Find current streak
        current_streak = self._find_current_streak(digits)
        
        # Find cycles
        cycle_lengths = self._find_cycles(digits)
        
        # Find dominant pattern
        dominant_pattern = self._find_dominant_pattern(digits)
        
        # Calculate confidence
        confidence = self._calculate_confidence(repeated_patterns, longest_streak, cycle_lengths)
        
        return PatternResult(
            repeated_patterns=repeated_patterns,
            longest_streak=longest_streak,
            current_streak=current_streak,
            cycle_lengths=cycle_lengths,
            dominant_pattern=dominant_pattern,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    def _find_repeated_patterns(self, digits: List[int]) -> List[Tuple[List[int], int]]:
        """
        Find repeated patterns in the digit sequence.
        
        Args:
            digits: List of digits
            
        Returns:
            List[Tuple[List[int], int]]: Patterns and their frequencies
        """
        patterns = defaultdict(int)
        
        # Search for patterns of different lengths
        for length in range(self.min_pattern_length, min(self.max_pattern_length, len(digits)) + 1):
            for i in range(len(digits) - length + 1):
                pattern = tuple(digits[i:i + length])
                patterns[pattern] += 1
        
        # Filter patterns that appear more than once
        repeated = [(list(pattern), count) for pattern, count in patterns.items() if count > 1]
        
        # Sort by frequency (descending) and then by length (descending)
        repeated.sort(key=lambda x: (x[1], len(x[0])), reverse=True)
        
        # Return top 10 patterns
        return repeated[:10]
    
    def _find_longest_streak(self, digits: List[int]) -> Tuple[int, int]:
        """
        Find the longest consecutive streak in the digit sequence.
        
        Args:
            digits: List of digits
            
        Returns:
            Tuple[int, int]: (digit, streak_length)
        """
        if not digits:
            return (0, 0)
        
        current_digit = digits[0]
        current_streak = 1
        max_streak = 1
        max_digit = digits[0]
        
        for digit in digits[1:]:
            if digit == current_digit:
                current_streak += 1
                if current_streak > max_streak:
                    max_streak = current_streak
                    max_digit = current_digit
            else:
                current_digit = digit
                current_streak = 1
        
        return (max_digit, max_streak)
    
    def _find_current_streak(self, digits: List[int]) -> Tuple[int, int]:
        """
        Find the current consecutive streak.
        
        Args:
            digits: List of digits
            
        Returns:
            Tuple[int, int]: (digit, streak_length)
        """
        if not digits:
            return (0, 0)
        
        current_digit = digits[-1]
        streak = 1
        
        for i in range(len(digits) - 2, -1, -1):
            if digits[i] == current_digit:
                streak += 1
            else:
                break
        
        return (current_digit, streak)
    
    def _find_cycles(self, digits: List[int]) -> List[int]:
        """
        Detect cycles in the digit sequence using autocorrelation.
        
        Args:
            digits: List of digits
            
        Returns:
            List[int]: Detected cycle lengths
        """
        if len(digits) < 10:
            return []
        
        # Convert digits to numeric values
        arr = np.array(digits)
        
        # Calculate autocorrelation for different lags
        cycles = []
        for lag in range(1, min(50, len(digits) // 2)):
            corr = np.corrcoef(arr[:-lag], arr[lag:])[0, 1]
            if not np.isnan(corr) and corr > 0.3:  # Threshold for significant correlation
                cycles.append(lag)
        
        # Remove duplicates and sort
        cycles = sorted(set(cycles))
        
        # Return cycles with significant correlation
        return cycles[:5]  # Return top 5 cycles
    
    def _find_dominant_pattern(self, digits: List[int]) -> List[int]:
        """
        Find the most dominant pattern in the sequence.
        
        Args:
            digits: List of digits
            
        Returns:
            List[int]: Dominant pattern
        """
        if len(digits) < 3:
            return []
        
        # Look for the most frequent 2-3 digit pattern
        patterns = defaultdict(int)
        
        for length in [2, 3]:
            for i in range(len(digits) - length + 1):
                pattern = tuple(digits[i:i + length])
                patterns[pattern] += 1
        
        if not patterns:
            return []
        
        # Find pattern with highest frequency
        most_common = max(patterns.items(), key=lambda x: x[1])
        
        # If frequency is too low, return empty
        if most_common[1] < 2:
            return []
        
        return list(most_common[0])
    
    def _calculate_confidence(self, repeated_patterns: List, longest_streak: Tuple[int, int], cycle_lengths: List[int]) -> float:
        """
        Calculate confidence in pattern analysis.
        
        Args:
            repeated_patterns: Found repeated patterns
            longest_streak: Longest streak found
            cycle_lengths: Detected cycle lengths
            
        Returns:
            float: Confidence score (0-1)
        """
        confidence = 0.0
        
        # Factor 1: Number of repeated patterns
        if repeated_patterns:
            pattern_score = min(len(repeated_patterns) / 5.0, 1.0)
            confidence += pattern_score * 0.4
        
        # Factor 2: Longest streak significance
        if longest_streak[1] > 3:
            streak_score = min(longest_streak[1] / 10.0, 1.0)
            confidence += streak_score * 0.3
        
        # Factor 3: Cycles detected
        if cycle_lengths:
            cycle_score = min(len(cycle_lengths) / 3.0, 1.0)
            confidence += cycle_score * 0.3
        
        return min(confidence, 1.0)
    
    def _empty_result(self) -> PatternResult:
        """Return empty pattern result."""
        return PatternResult(
            repeated_patterns=[],
            longest_streak=(0, 0),
            current_streak=(0, 0),
            cycle_lengths=[],
            dominant_pattern=[],
            confidence=0.0,
            timestamp=datetime.now()
        )
    
    def analyze_streaks(self, digits: List[int]) -> ConsecutiveStreak:
        """
        Analyze consecutive streaks for all digits.
        
        Args:
            digits: List of digits
            
        Returns:
            ConsecutiveStreak: Streak analysis
        """
        if not digits:
            return ConsecutiveStreak(
                current_digit=0,
                current_streak=0,
                max_streak=0,
                digit_streaks={i: [] for i in range(10)},
                average_streaks={i: 0.0 for i in range(10)},
                timestamp=datetime.now()
            )
        
        # Find current streak
        current_digit, current_streak = self._find_current_streak(digits)
        
        # Find max streak
        max_digit, max_streak = self._find_longest_streak(digits)
        
        # Find streaks for each digit
        digit_streaks = {i: [] for i in range(10)}
        
        if len(digits) > 1:
            current = digits[0]
            streak = 1
            
            for digit in digits[1:]:
                if digit == current:
                    streak += 1
                else:
                    digit_streaks[current].append(streak)
                    current = digit
                    streak = 1
            
            # Add last streak
            digit_streaks[current].append(streak)
        
        # Calculate average streaks
        average_streaks = {
            i: sum(streaks) / len(streaks) if streaks else 0.0
            for i, streaks in digit_streaks.items()
        }
        
        return ConsecutiveStreak(
            current_digit=current_digit,
            current_streak=current_streak,
            max_streak=max_streak,
            digit_streaks=digit_streaks,
            average_streaks=average_streaks,
            timestamp=datetime.now()
        )
