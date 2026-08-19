"""
Frequency Analysis Module
Provides digit frequency analysis, hot/cold detection, and rarity scoring.
"""

from typing import Dict, List, Tuple, Optional
from collections import Counter
import numpy as np
from datetime import datetime
from dataclasses import dataclass

from core.types import Tick, FrequencyAnalysis
from core.constants import STATISTICAL_THRESHOLDS
from core.logger import get_logger


logger = get_logger(__name__)


class FrequencyAnalyzer:
    """
    Analyzes digit frequencies with statistical significance testing.
    Identifies hot and cold digits based on z-scores.
    """
    
    def __init__(self):
        """Initialize the frequency analyzer."""
        self.thresholds = STATISTICAL_THRESHOLDS
        self._cache = {}
        logger.info("FrequencyAnalyzer initialized")
    
    def analyze(self, digits: List[int]) -> FrequencyAnalysis:
        """
        Perform comprehensive frequency analysis on a list of digits.
        
        Args:
            digits: List of digit values (0-9)
            
        Returns:
            FrequencyAnalysis: Complete frequency analysis results
        """
        if not digits:
            return self._empty_analysis()
        
        total = len(digits)
        expected = total / 10.0
        
        # Count frequencies
        digit_counts = Counter(digits)
        
        # Calculate frequencies and z-scores
        frequencies = {}
        z_scores = {}
        rarity_scores = {}
        
        for digit in range(10):
            count = digit_counts.get(digit, 0)
            freq = count / total if total > 0 else 0
            frequencies[digit] = freq
            
            # Calculate z-score
            std_dev = np.sqrt(total * 0.1 * 0.9)  # Binomial std deviation
            if std_dev > 0:
                z_score = (count - expected) / std_dev
            else:
                z_score = 0
            z_scores[digit] = z_score
            
            # Calculate rarity score (0-1, higher = more rare)
            rarity = abs(z_score) / 3.0  # Normalize by 3 std deviations
            rarity_scores[digit] = min(rarity, 1.0)
        
        # Identify hot and cold digits
        hot_digits = [
            digit for digit, z in z_scores.items()
            if z > self.thresholds['hot_digit_z_score']
        ]
        cold_digits = [
            digit for digit, z in z_scores.items()
            if z < self.thresholds['cold_digit_z_score']
        ]
        
        return FrequencyAnalysis(
            digit_counts=dict(digit_counts),
            total_counts=total,
            expected_frequency=0.1,
            frequencies=frequencies,
            z_scores=z_scores,
            hot_digits=hot_digits,
            cold_digits=cold_digits,
            rarity_scores=rarity_scores,
            timestamp=datetime.now()
        )
    
    def _empty_analysis(self) -> FrequencyAnalysis:
        """Return an empty analysis result."""
        return FrequencyAnalysis(
            digit_counts={i: 0 for i in range(10)},
            total_counts=0,
            expected_frequency=0.1,
            frequencies={i: 0.0 for i in range(10)},
            z_scores={i: 0.0 for i in range(10)},
            hot_digits=[],
            cold_digits=[],
            rarity_scores={i: 0.0 for i in range(10)},
            timestamp=datetime.now()
        )
    
    def compare_windows(self, window1: List[int], window2: List[int]) -> Dict[str, any]:
        """
        Compare frequency distributions between two windows.
        
        Args:
            window1: First window digits
            window2: Second window digits
            
        Returns:
            Dict: Comparison results
        """
        analysis1 = self.analyze(window1)
        analysis2 = self.analyze(window2)
        
        # Calculate distribution differences
        differences = {}
        for digit in range(10):
            diff = analysis2.frequencies[digit] - analysis1.frequencies[digit]
            differences[digit] = diff
        
        # Calculate overall similarity (cosine similarity)
        vec1 = [analysis1.frequencies[d] for d in range(10)]
        vec2 = [analysis2.frequencies[d] for d in range(10)]
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 > 0 and norm2 > 0:
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        else:
            similarity = 0.0
        
        return {
            'differences': differences,
            'similarity': similarity,
            'window1_hot': analysis1.hot_digits,
            'window2_hot': analysis2.hot_digits,
            'window1_cold': analysis1.cold_digits,
            'window2_cold': analysis2.cold_digits
        }
    
    def get_confidence_score(self, analysis: FrequencyAnalysis) -> float:
        """
        Calculate confidence score based on frequency analysis.
        
        Args:
            analysis: Frequency analysis results
            
        Returns:
            float: Confidence score (0-1)
        """
        if analysis.total_counts < 10:
            return 0.0
        
        # High confidence when:
        # 1. There are strong deviations from expected
        # 2. Hot/cold digits are clearly identified
        # 3. Z-scores are significant
        
        avg_z = np.mean([abs(z) for z in analysis.z_scores.values()])
        hot_count = len(analysis.hot_digits)
        cold_count = len(analysis.cold_digits)
        
        # More extreme deviations = higher confidence
        deviation_score = min(avg_z / 2.0, 1.0)
        
        # Presence of hot/cold digits
        pattern_score = min((hot_count + cold_count) / 4.0, 1.0)
        
        # Sample size factor
        sample_score = min(analysis.total_counts / 100.0, 1.0)
        
        confidence = (deviation_score * 0.5 + pattern_score * 0.3 + sample_score * 0.2)
        return min(confidence, 1.0)
