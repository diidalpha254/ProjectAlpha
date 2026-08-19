"""
Confidence Scoring Module
Calculates confidence scores for statistical analysis and market insights.
"""

from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime

from core.logger import get_logger


logger = get_logger(__name__)


class ConfidenceScorer:
    """
    Calculates confidence scores for various analyses.
    Combines multiple factors to produce reliable confidence metrics.
    """
    
    def __init__(self):
        """Initialize the confidence scorer."""
        logger.info("ConfidenceScorer initialized")
    
    def calculate_confidence(
        self,
        analysis_type: str,
        data: Dict[str, Any],
        sample_size: int,
        window_size: int
    ) -> float:
        """
        Calculate confidence score for a specific analysis.
        
        Args:
            analysis_type: Type of analysis (e.g., 'frequency', 'markov', 'trend')
            data: Analysis results
            sample_size: Number of samples used
            window_size: Window size used
            
        Returns:
            float: Confidence score (0-1)
        """
        if analysis_type == 'frequency':
            return self._frequency_confidence(data, sample_size, window_size)
        elif analysis_type == 'markov':
            return self._markov_confidence(data, sample_size, window_size)
        elif analysis_type == 'trend':
            return self._trend_confidence(data, sample_size, window_size)
        elif analysis_type == 'pattern':
            return self._pattern_confidence(data, sample_size, window_size)
        else:
            return self._generic_confidence(data, sample_size, window_size)
    
    def _frequency_confidence(self, data: Dict[str, Any], sample_size: int, window_size: int) -> float:
        """Calculate confidence for frequency analysis."""
        confidence = 0.0
        
        # Sample size factor
        sample_score = min(sample_size / window_size, 1.0)
        confidence += sample_score * 0.3
        
        # Deviation from expected
        if 'z_scores' in data:
            z_scores = list(data['z_scores'].values())
            avg_z = np.mean([abs(z) for z in z_scores])
            deviation_score = min(avg_z / 2.0, 1.0)
            confidence += deviation_score * 0.4
        
        # Consistency factor
        if 'digit_counts' in data:
            counts = list(data['digit_counts'].values())
            if counts:
                max_count = max(counts)
                min_count = min(counts)
                if max_count > 0:
                    consistency = 1 - (max_count - min_count) / max_count
                    confidence += consistency * 0.3
        
        return min(confidence, 1.0)
    
    def _markov_confidence(self, data: Dict[str, Any], sample_size: int, window_size: int) -> float:
        """Calculate confidence for Markov analysis."""
        confidence = 0.0
        
        # Sample size factor
        sample_score = min(sample_size / (window_size * 0.5), 1.0)
        confidence += sample_score * 0.3
        
        # Matrix stability
        if 'matrix' in data:
            matrix = np.array(data['matrix'])
            if matrix.size > 0:
                # Check for zero rows
                row_sums = matrix.sum(axis=1)
                nonzero_rows = np.sum(row_sums > 0)
                stability = nonzero_rows / matrix.shape[0]
                confidence += stability * 0.3
        
        # Entropy factor
        if 'entropy_rate' in data:
            entropy = data['entropy_rate']
            max_entropy = np.log2(10)  # 10 digits
            entropy_score = 1 - min(entropy / max_entropy, 1.0)
            confidence += entropy_score * 0.4
        
        return min(confidence, 1.0)
    
    def _trend_confidence(self, data: Dict[str, Any], sample_size: int, window_size: int) -> float:
        """Calculate confidence for trend analysis."""
        confidence = 0.0
        
        # Sample size factor
        sample_score = min(sample_size / (window_size * 0.3), 1.0)
        confidence += sample_score * 0.2
        
        # R-squared factor
        if 'r_squared' in data:
            r2 = data['r_squared']
            confidence += r2 * 0.4
        
        # Trend strength
        if 'trend_strength' in data:
            strength = data['trend_strength']
            confidence += strength * 0.3
        
        # Direction confidence
        if 'direction' in data and data['direction'] != 'neutral':
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _pattern_confidence(self, data: Dict[str, Any], sample_size: int, window_size: int) -> float:
        """Calculate confidence for pattern analysis."""
        confidence = 0.0
        
        # Pattern frequency
        if 'repeated_patterns' in data:
            patterns = data['repeated_patterns']
            pattern_score = min(len(patterns) / 5.0, 1.0)
            confidence += pattern_score * 0.4
        
        # Longest streak
        if 'longest_streak' in data:
            streak_len = data['longest_streak'][1]
            streak_score = min(streak_len / 10.0, 1.0)
            confidence += streak_score * 0.3
        
        # Cycle detection
        if 'cycle_lengths' in data:
            cycles = data['cycle_lengths']
            cycle_score = min(len(cycles) / 3.0, 1.0)
            confidence += cycle_score * 0.3
        
        return min(confidence, 1.0)
    
    def _generic_confidence(self, data: Dict[str, Any], sample_size: int, window_size: int) -> float:
        """Calculate generic confidence."""
        confidence = 0.0
        
        # Sample size factor
        sample_score = min(sample_size / window_size, 1.0)
        confidence += sample_score * 0.5
        
        # Data completeness
        if data:
            completeness = min(len(data) / 10.0, 1.0)
            confidence += completeness * 0.5
        
        return min(confidence, 1.0)
    
    def combine_confidences(self, confidences: List[float], weights: Optional[List[float]] = None) -> float:
        """
        Combine multiple confidence scores.
        
        Args:
            confidences: List of confidence scores
            weights: Optional weights for each score
            
        Returns:
            float: Combined confidence score
        """
        if not confidences:
            return 0.0
        
        if weights is None:
            weights = [1.0 / len(confidences)] * len(confidences)
        
        # Ensure weights sum to 1
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        # Calculate weighted average
        combined = np.average(confidences, weights=weights)
        
        return min(combined, 1.0)
    
    def get_confidence_level(self, confidence: float) -> str:
        """
        Get a confidence level description.
        
        Args:
            confidence: Confidence score (0-1)
            
        Returns:
            str: Confidence level description
        """
        if confidence >= 0.8:
            return "Very High"
        elif confidence >= 0.6:
            return "High"
        elif confidence >= 0.4:
            return "Moderate"
        elif confidence >= 0.2:
            return "Low"
        else:
            return "Very Low"
    
    def get_confidence_color(self, confidence: float) -> str:
        """
        Get a color for the confidence level.
        
        Args:
            confidence: Confidence score (0-1)
            
        Returns:
            str: Hex color code
        """
        if confidence >= 0.8:
            return "#2ECC71"  # Green
        elif confidence >= 0.6:
            return "#F1C40F"  # Yellow
        elif confidence >= 0.4:
            return "#E67E22"  # Orange
        else:
            return "#E74C3C"  # Red
