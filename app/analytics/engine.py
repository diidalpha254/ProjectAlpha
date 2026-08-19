"""
Statistical Analytics Engine
Orchestrates all statistical analyses and provides a unified interface.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass

from core.types import Tick
from core.logger import get_logger
from core.exceptions import AnalyticsError
from .frequency import FrequencyAnalyzer
from .markov import MarkovAnalyzer
from .entropy import EntropyAnalyzer
from .volatility import VolatilityAnalyzer
from .patterns import PatternAnalyzer
from .confidence import ConfidenceScorer

logger = get_logger(__name__)


@dataclass
class ComprehensiveAnalysis:
    """Complete analysis results from all analyzers."""
    frequency: Dict[str, Any]
    markov: Dict[str, Any]
    entropy: Dict[str, Any]
    volatility: Dict[str, Any]
    patterns: Dict[str, Any]
    confidence: Dict[str, Any]
    summary: Dict[str, Any]
    timestamp: datetime


class AnalyticsEngine:
    """
    Orchestrates all statistical analyses.
    Provides a unified interface for comprehensive market analysis.
    """
    
    def __init__(self):
        """Initialize the analytics engine with all analyzers."""
        self.frequency_analyzer = FrequencyAnalyzer()
        self.markov_analyzer = MarkovAnalyzer(order=1)
        self.entropy_analyzer = EntropyAnalyzer()
        self.volatility_analyzer = VolatilityAnalyzer()
        self.pattern_analyzer = PatternAnalyzer()
        self.confidence_scorer = ConfidenceScorer()
        
        self._cache = {}
        self._last_analysis: Optional[ComprehensiveAnalysis] = None
        
        logger.info("AnalyticsEngine initialized")
    
    def analyze_tick_data(self, ticks: List[Tick]) -> ComprehensiveAnalysis:
        """
        Perform comprehensive analysis on tick data.
        
        Args:
            ticks: List of tick objects
            
        Returns:
            ComprehensiveAnalysis: Complete analysis results
        """
        if not ticks:
            return self._empty_analysis()
        
        try:
            # Extract data from ticks
            prices = [float(t.price) for t in ticks]
            digits = [t.last_digit for t in ticks]
            
            # Perform analyses
            frequency_result = self.frequency_analyzer.analyze(digits)
            markov_result = self.markov_analyzer.analyze(digits)
            entropy_result = self.entropy_analyzer.analyze(digits)
            volatility_result = self.volatility_analyzer.analyze_volatility(prices)
            momentum_result = self.volatility_analyzer.analyze_momentum(prices)
            pattern_result = self.pattern_analyzer.analyze(digits)
            
            # Calculate confidence scores
            confidence_scores = {
                'frequency': self.confidence_scorer.calculate_confidence(
                    'frequency', 
                    frequency_result.__dict__, 
                    len(digits), 
                    100
                ),
                'markov': self.confidence_scorer.calculate_confidence(
                    'markov',
                    {'matrix': markov_result.transition_matrix, 'entropy_rate': markov_result.entropy_rate},
                    len(digits),
                    100
                ),
                'pattern': self.confidence_scorer.calculate_confidence(
                    'pattern',
                    {'repeated_patterns': pattern_result.repeated_patterns, 
                     'longest_streak': pattern_result.longest_streak,
                     'cycle_lengths': pattern_result.cycle_lengths},
                    len(digits),
                    100
                )
            }
            
            # Calculate overall confidence
            overall_confidence = self.confidence_scorer.combine_confidences(
                list(confidence_scores.values())
            )
            
            # Create comprehensive analysis
            analysis = ComprehensiveAnalysis(
                frequency=frequency_result.__dict__,
                markov=markov_result.__dict__,
                entropy=entropy_result.__dict__,
                volatility={
                    'metrics': volatility_result.__dict__,
                    'momentum': momentum_result.__dict__,
                    'trend': self.volatility_analyzer.analyze_trend(prices),
                    'mean_reversion': self.volatility_analyzer.measure_mean_reversion(prices)
                },
                patterns=pattern_result.__dict__,
                confidence={
                    'scores': confidence_scores,
                    'overall': overall_confidence,
                    'level': self.confidence_scorer.get_confidence_level(overall_confidence),
                    'color': self.confidence_scorer.get_confidence_color(overall_confidence)
                },
                summary=self._generate_summary(
                    frequency_result, markov_result, entropy_result,
                    volatility_result, momentum_result, pattern_result,
                    overall_confidence
                ),
                timestamp=datetime.now()
            )
            
            self._last_analysis = analysis
            return analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}", exc_info=True)
            raise AnalyticsError(f"Analysis failed: {e}")
    
    def _generate_summary(
        self,
        frequency_result,
        markov_result,
        entropy_result,
        volatility_result,
        momentum_result,
        pattern_result,
        overall_confidence
    ) -> Dict[str, Any]:
        """Generate a human-readable summary of the analysis."""
        summary = {
            'total_ticks': frequency_result.total_counts,
            'most_common_digit': max(frequency_result.frequencies.items(), key=lambda x: x[1])[0],
            'least_common_digit': min(frequency_result.frequencies.items(), key=lambda x: x[1])[0],
            'hot_digits': frequency_result.hot_digits,
            'cold_digits': frequency_result.cold_digits,
            'is_random': entropy_result.is_random,
            'entropy_score': entropy_result.entropy,
            'volatility_score': volatility_result.standard_deviation,
            'momentum_direction': momentum_result.direction,
            'momentum_strength': momentum_result.strength,
            'trend_direction': self.volatility_analyzer.analyze_trend(
                []  # This will be filled from the actual analysis
            )['direction'] if hasattr(self, '_last_analysis') else 'neutral',
            'has_patterns': len(pattern_result.repeated_patterns) > 0,
            'longest_streak': pattern_result.longest_streak,
            'overall_confidence': overall_confidence,
            'confidence_level': self.confidence_scorer.get_confidence_level(overall_confidence)
        }
        
        # Add trend analysis if available
        if hasattr(self, '_last_analysis') and self._last_analysis:
            if 'trend' in self._last_analysis.volatility:
                summary['trend_direction'] = self._last_analysis.volatility['trend']['direction']
                summary['trend_strength'] = self._last_analysis.volatility['trend']['trend_strength']
        
        return summary
    
    def _empty_analysis(self) -> ComprehensiveAnalysis:
        """Return an empty analysis result."""
        empty_result = {
            'total_counts': 0,
            'frequencies': {i: 0.0 for i in range(10)},
            'hot_digits': [],
            'cold_digits': []
        }
        return ComprehensiveAnalysis(
            frequency=empty_result,
            markov={'transition_matrix': np.zeros((10, 10))},
            entropy={'entropy': 0.0, 'is_random': False},
            volatility={'metrics': {}, 'momentum': {}, 'trend': {}, 'mean_reversion': {}},
            patterns={'repeated_patterns': [], 'longest_streak': (0, 0)},
            confidence={'scores': {}, 'overall': 0.0, 'level': 'Very Low', 'color': '#E74C3C'},
            summary={'total_ticks': 0, 'overall_confidence': 0.0},
            timestamp=datetime.now()
        )
    
    def get_digit_frequency(self, ticks: List[Tick]) -> Dict[int, int]:
        """Get digit frequency from ticks."""
        digits = [t.last_digit for t in ticks]
        return self.frequency_analyzer.analyze(digits).digit_counts
    
    def get_transition_matrix(self, ticks: List[Tick]) -> np.ndarray:
        """Get transition matrix from ticks."""
        digits = [t.last_digit for t in ticks]
        return self.markov_analyzer.analyze(digits).transition_matrix
    
    def get_entropy(self, ticks: List[Tick]) -> float:
        """Get entropy score from ticks."""
        digits = [t.last_digit for t in ticks]
        return self.entropy_analyzer.analyze(digits).entropy
    
    def get_volatility(self, ticks: List[Tick]) -> float:
        """Get volatility from ticks."""
        prices = [float(t.price) for t in ticks]
        return self.volatility_analyzer.analyze_volatility(prices).standard_deviation
    
    def get_momentum(self, ticks: List[Tick]) -> Dict[str, Any]:
        """Get momentum analysis from ticks."""
        prices = [float(t.price) for t in ticks]
        result = self.volatility_analyzer.analyze_momentum(prices)
        return {
            'direction': result.direction,
            'strength': result.strength,
            'score': result.momentum_score,
            'confidence': result.confidence
        }
    
    def get_patterns(self, ticks: List[Tick]) -> Dict[str, Any]:
        """Get pattern analysis from ticks."""
        digits = [t.last_digit for t in ticks]
        result = self.pattern_analyzer.analyze(digits)
        return {
            'repeated_patterns': result.repeated_patterns,
            'longest_streak': result.longest_streak,
            'current_streak': result.current_streak,
            'dominant_pattern': result.dominant_pattern,
            'confidence': result.confidence
        }
    
    def get_streak_analysis(self, ticks: List[Tick]) -> Dict[str, Any]:
        """Get streak analysis from ticks."""
        digits = [t.last_digit for t in ticks]
        result = self.pattern_analyzer.analyze_streaks(digits)
        return result.__dict__
    
    def clear_cache(self):
        """Clear the analysis cache."""
        self._cache.clear()
        self._last_analysis = None
        logger.info("Analytics cache cleared")
