"""
Explanation Module
Provides detailed explanations of statistical findings and market behavior.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np

from core.logger import get_logger


logger = get_logger(__name__)


class ExplanationGenerator:
    """
    Generates detailed explanations of statistical findings.
    Focuses on making complex analysis understandable.
    """
    
    def __init__(self):
        """Initialize the explanation generator."""
        self._explanation_cache = {}
        logger.info("ExplanationGenerator initialized")
    
    def explain_frequency_analysis(self, frequency_data: Dict[str, Any]) -> str:
        """
        Generate explanation for frequency analysis.
        
        Args:
            frequency_data: Frequency analysis results
            
        Returns:
            str: Human-readable explanation
        """
        explanation_parts = []
        
        try:
            # Total ticks
            total = frequency_data.get('total_counts', 0)
            explanation_parts.append(f"Analysis of {total} ticks")
            
            # Hot digits
            hot = frequency_data.get('hot_digits', [])
            if hot:
                explanation_parts.append(f"Hot digits: {hot} appear more frequently than expected")
            
            # Cold digits
            cold = frequency_data.get('cold_digits', [])
            if cold:
                explanation_parts.append(f"Cold digits: {cold} appear less frequently than expected")
            
            # Z-scores
            z_scores = frequency_data.get('z_scores', {})
            if z_scores:
                significant = [d for d, z in z_scores.items() if abs(z) > 2]
                if significant:
                    explanation_parts.append(f"Significant deviations: digits {significant} show strong bias")
            
            # Distribution summary
            frequencies = frequency_data.get('frequencies', {})
            if frequencies:
                max_digit = max(frequencies, key=frequencies.get)
                max_freq = frequencies[max_digit]
                min_digit = min(frequencies, key=frequencies.get)
                min_freq = frequencies[min_digit]
                
                explanation_parts.append(
                    f"Most common: digit {max_digit} ({max_freq:.1%}), "
                    f"Least common: digit {min_digit} ({min_freq:.1%})"
                )
                
                # Uniformity check
                expected = 0.1
                deviations = [abs(f - expected) for f in frequencies.values()]
                avg_deviation = np.mean(deviations) if deviations else 0
                
                if avg_deviation < 0.02:
                    explanation_parts.append("Distribution is close to uniform (no strong bias)")
                elif avg_deviation < 0.05:
                    explanation_parts.append("Moderate deviation from uniform distribution")
                else:
                    explanation_parts.append("Significant deviation from uniform distribution")
            
        except Exception as e:
            logger.warning(f"Error explaining frequency analysis: {e}")
            explanation_parts.append("Frequency analysis in progress")
        
        return ". ".join(explanation_parts) if explanation_parts else "No frequency analysis available"
    
    def explain_markov_analysis(self, markov_data: Dict[str, Any]) -> str:
        """
        Generate explanation for Markov analysis.
        
        Args:
            markov_data: Markov analysis results
            
        Returns:
            str: Human-readable explanation
        """
        explanation_parts = []
        
        try:
            # Transition matrix
            matrix = markov_data.get('transition_matrix')
            if matrix is not None and isinstance(matrix, np.ndarray):
                # Find strongest transitions
                max_transitions = []
                for i in range(min(10, matrix.shape[0])):
                    row = matrix[i]
                    if row.size > 0:
                        max_idx = np.argmax(row)
                        max_val = row[max_idx]
                        if max_val > 0.2 and max_idx != i:
                            max_transitions.append(f"{i}→{max_idx} ({max_val:.1%})")
                
                if max_transitions:
                    explanation_parts.append(f"Strongest transitions: {', '.join(max_transitions[:3])}")
            
            # Stationary distribution
            stationary = markov_data.get('stationary_distribution')
            if stationary is not None and isinstance(stationary, np.ndarray):
                max_digit = np.argmax(stationary)
                max_prob = stationary[max_digit]
                explanation_parts.append(f"Stationary distribution favors digit {max_digit} ({max_prob:.1%})")
            
            # Entropy rate
            entropy_rate = markov_data.get('entropy_rate')
            if entropy_rate is not None:
                max_entropy = np.log2(10)
                if entropy_rate < max_entropy * 0.3:
                    explanation_parts.append("Low entropy rate suggests predictable patterns")
                elif entropy_rate < max_entropy * 0.6:
                    explanation_parts.append("Moderate entropy rate suggests some predictability")
                else:
                    explanation_parts.append("High entropy rate suggests random behavior")
            
            # Mixing time
            mixing_time = markov_data.get('mixing_time')
            if mixing_time is not None and mixing_time > 0:
                if mixing_time < 10:
                    explanation_parts.append("Fast mixing - market adapts quickly to changes")
                else:
                    explanation_parts.append(f"Slow mixing ({mixing_time} steps) - market has memory")
            
        except Exception as e:
            logger.warning(f"Error explaining Markov analysis: {e}")
            explanation_parts.append("Markov analysis in progress")
        
        return ". ".join(explanation_parts) if explanation_parts else "No Markov analysis available"
    
    def explain_pattern_analysis(self, pattern_data: Dict[str, Any]) -> str:
        """
        Generate explanation for pattern analysis.
        
        Args:
            pattern_data: Pattern analysis results
            
        Returns:
            str: Human-readable explanation
        """
        explanation_parts = []
        
        try:
            # Repeated patterns
            repeated = pattern_data.get('repeated_patterns', [])
            if repeated:
                top_patterns = []
                for pattern, count in repeated[:3]:
                    top_patterns.append(f"{pattern} (appeared {count} times)")
                explanation_parts.append(f"Repeated patterns: {', '.join(top_patterns)}")
            else:
                explanation_parts.append("No significant repeating patterns detected")
            
            # Longest streak
            longest = pattern_data.get('longest_streak', (0, 0))
            if longest[1] > 2:
                explanation_parts.append(f"Longest streak: {longest[1]} consecutive {longest[0]}s")
            
            # Current streak
            current = pattern_data.get('current_streak', (0, 0))
            if current[1] > 1:
                explanation_parts.append(f"Current streak: {current[1]} {current[0]}s in a row")
            
            # Cycles
            cycles = pattern_data.get('cycle_lengths', [])
            if cycles:
                explanation_parts.append(f"Detected cycles: {cycles[:3]}")
            
            # Dominant pattern
            dominant = pattern_data.get('dominant_pattern', [])
            if dominant:
                explanation_parts.append(f"Dominant pattern: {dominant}")
            
            # Confidence
            confidence = pattern_data.get('confidence', 0)
            if confidence > 0.7:
                explanation_parts.append("High confidence in pattern detection")
            elif confidence > 0.4:
                explanation_parts.append("Moderate confidence in pattern detection")
            else:
                explanation_parts.append("Low confidence in pattern detection")
            
        except Exception as e:
            logger.warning(f"Error explaining pattern analysis: {e}")
            explanation_parts.append("Pattern analysis in progress")
        
        return ". ".join(explanation_parts) if explanation_parts else "No pattern analysis available"
    
    def explain_transition_probabilities(self, transition_data: Dict[str, float]) -> str:
        """
        Generate explanation for transition probabilities.
        
        Args:
            transition_data: Transition probability data
            
        Returns:
            str: Human-readable explanation
        """
        explanation_parts = []
        
        try:
            # Match probability
            match_prob = transition_data.get('match_probability', 0)
            if match_prob > 0:
                explanation_parts.append(f"Match probability: {match_prob:.1%}")
            
            # Differ probability
            differ_prob = transition_data.get('differ_probability', 0)
            if differ_prob > 0:
                explanation_parts.append(f"Differ probability: {differ_prob:.1%}")
            
            # Consecutive probabilities
            consecutive_match = transition_data.get('consecutive_match', 0)
            if consecutive_match > 0:
                explanation_parts.append(f"Consecutive matches: {consecutive_match:.1%}")
            
            consecutive_differ = transition_data.get('consecutive_differ', 0)
            if consecutive_differ > 0:
                explanation_parts.append(f"Consecutive differs: {consecutive_differ:.1%}")
            
            # Interpretation
            if match_prob > 0.25:
                explanation_parts.append("Higher match probability suggests repeated digit patterns")
            elif match_prob < 0.05:
                explanation_parts.append("Very low match probability suggests alternating digits")
            
        except Exception as e:
            logger.warning(f"Error explaining transition probabilities: {e}")
            explanation_parts.append("Transition analysis in progress")
        
        return ". ".join(explanation_parts) if explanation_parts else "No transition analysis available"
