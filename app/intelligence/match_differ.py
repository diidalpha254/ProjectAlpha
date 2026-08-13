"""
Match/Differ Intelligence Module
Provides specialized analysis for Match/Differ contracts based on market conditions.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass

from ..core.types import Tick, MatchDifferInsight
from ..core.constants import MarketState
from ..core.logger import get_logger
from ..analytics.engine import AnalyticsEngine
from ..market_state.classifier import MarketClassifier

logger = get_logger(__name__)


@dataclass
class MatchDifferAnalysis:
    """Comprehensive Match/Differ analysis results."""
    market_condition: str
    digit_distribution: Dict[int, float]
    transition_probabilities: Dict[str, float]
    confidence_indicators: Dict[str, float]
    pattern_summary: str
    historical_context: str
    explanation: str
    recommendations: List[str]
    risk_assessment: Dict[str, Any]
    timestamp: datetime


class MatchDifferIntelligence:
    """
    Provides specialized intelligence for Match/Differ trading.
    Analyzes digit patterns, transitions, and market conditions.
    """
    
    def __init__(self):
        """Initialize the Match/Differ intelligence module."""
        self.analytics_engine = AnalyticsEngine()
        self.market_classifier = MarketClassifier()
        self._last_analysis: Optional[MatchDifferAnalysis] = None
        self._analysis_history: List[MatchDifferAnalysis] = []
        self._max_history = 500
        
        logger.info("MatchDifferIntelligence initialized")
    
    def analyze(self, ticks: List[Tick]) -> MatchDifferInsight:
        """
        Perform comprehensive Match/Differ analysis.
        
        Args:
            ticks: List of tick objects
            
        Returns:
            MatchDifferInsight: Complete Match/Differ analysis
        """
        if not ticks or len(ticks) < 10:
            return self._empty_insight()
        
        try:
            # Get market state
            market_analysis = self.market_classifier.classify(ticks)
            
            # Perform comprehensive statistical analysis
            stats_analysis = self.analytics_engine.analyze_tick_data(ticks)
            
            # Extract digit distribution
            digit_distribution = self._extract_digit_distribution(stats_analysis)
            
            # Calculate transition probabilities
            transition_probs = self._calculate_transition_probabilities(ticks)
            
            # Generate confidence indicators
            confidence_indicators = self._generate_confidence_indicators(
                market_analysis, stats_analysis
            )
            
            # Generate pattern summary
            pattern_summary = self._generate_pattern_summary(stats_analysis)
            
            # Generate historical context
            historical_context = self._generate_historical_context(ticks)
            
            # Generate explanation
            explanation = self._generate_explanation(
                market_analysis, stats_analysis, digit_distribution
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                market_analysis, stats_analysis, digit_distribution
            )
            
            # Assess risk
            risk_assessment = self._assess_risk(
                market_analysis, stats_analysis, digit_distribution
            )
            
            # Create insight
            insight = MatchDifferInsight(
                market_condition=market_analysis.state.value,
                observations=self._generate_observations(
                    market_analysis, stats_analysis, digit_distribution
                ),
                digit_distribution=digit_distribution,
                transition_probabilities=transition_probs,
                confidence_indicators=confidence_indicators,
                pattern_summary=pattern_summary,
                historical_context=historical_context,
                explanation=explanation,
                timestamp=datetime.now()
            )
            
            # Store history
            self._analysis_history.append(insight)
            if len(self._analysis_history) > self._max_history:
                self._analysis_history = self._analysis_history[-self._max_history:]
            
            self._last_analysis = insight
            logger.info("Match/Differ analysis completed")
            
            return insight
            
        except Exception as e:
            logger.error(f"Error in Match/Differ analysis: {e}", exc_info=True)
            return self._empty_insight()
    
    def _extract_digit_distribution(self, analysis: Any) -> Dict[int, float]:
        """Extract digit distribution from analysis."""
        distribution = {}
        
        try:
            if hasattr(analysis, 'frequency') and analysis.frequency:
                frequencies = analysis.frequency.get('frequencies', {})
                total = sum(frequencies.values()) if frequencies else 0
                
                if total > 0:
                    for digit in range(10):
                        distribution[digit] = frequencies.get(digit, 0) / total
                else:
                    distribution = {i: 0.1 for i in range(10)}
            else:
                distribution = {i: 0.1 for i in range(10)}
                
        except Exception as e:
            logger.warning(f"Error extracting digit distribution: {e}")
            distribution = {i: 0.1 for i in range(10)}
        
        return distribution
    
    def _calculate_transition_probabilities(self, ticks: List[Tick]) -> Dict[str, float]:
        """
        Calculate key transition probabilities for Match/Differ.
        
        Returns:
            Dict[str, float]: Key transition probabilities
        """
        if len(ticks) < 2:
            return {
                'match_probability': 0.1,
                'differ_probability': 0.9,
                'digits_same': 0.1,
                'digits_different': 0.9,
                'consecutive_match': 0.1,
                'consecutive_differ': 0.9,
                'trend_match': 0.5,
                'trend_differ': 0.5
            }
        
        digits = [t.last_digit for t in ticks]
        
        # Calculate match probability (same digit appears)
        matches = 0
        for i in range(len(digits) - 1):
            if digits[i] == digits[i + 1]:
                matches += 1
        
        total_transitions = len(digits) - 1
        match_prob = matches / total_transitions if total_transitions > 0 else 0.1
        
        # Calculate differ probability
        differ_prob = 1 - match_prob
        
        # Calculate consecutive matches
        consecutive_matches = 0
        for i in range(len(digits) - 2):
            if digits[i] == digits[i+1] == digits[i+2]:
                consecutive_matches += 1
        consecutive_match_prob = consecutive_matches / (total_transitions - 1) if total_transitions > 1 else 0.1
        
        # Calculate consecutive differs
        consecutive_differs = 0
        for i in range(len(digits) - 2):
            if digits[i] != digits[i+1] != digits[i+2]:
                consecutive_differs += 1
        consecutive_differ_prob = consecutive_differs / (total_transitions - 1) if total_transitions > 1 else 0.1
        
        return {
            'match_probability': match_prob,
            'differ_probability': differ_prob,
            'digits_same': match_prob,
            'digits_different': differ_prob,
            'consecutive_match': consecutive_match_prob,
            'consecutive_differ': consecutive_differ_prob,
            'trend_match': match_prob * 1.2 if match_prob > 0.3 else match_prob * 0.8,
            'trend_differ': differ_prob * 1.2 if differ_prob > 0.3 else differ_prob * 0.8
        }
    
    def _generate_confidence_indicators(self, market_analysis: Any, stats_analysis: Any) -> Dict[str, float]:
        """Generate confidence indicators for Match/Differ analysis."""
        indicators = {}
        
        try:
            # Market confidence
            indicators['market_confidence'] = market_analysis.confidence
            
            # Statistical confidence
            if hasattr(stats_analysis, 'confidence'):
                indicators['statistical_confidence'] = stats_analysis.confidence.get('overall', 0.5)
            else:
                indicators['statistical_confidence'] = 0.5
            
            # Pattern confidence
            if hasattr(stats_analysis, 'patterns'):
                indicators['pattern_confidence'] = stats_analysis.patterns.get('confidence', 0.5)
            else:
                indicators['pattern_confidence'] = 0.5
            
            # Entropy confidence
            if hasattr(stats_analysis, 'entropy'):
                entropy = stats_analysis.entropy.get('entropy', 0)
                max_entropy = np.log2(10)
                indicators['entropy_confidence'] = 1 - (entropy / max_entropy)
            else:
                indicators['entropy_confidence'] = 0.5
            
            # Overall confidence
            indicators['overall_confidence'] = np.mean([
                indicators['market_confidence'],
                indicators['statistical_confidence'],
                indicators['pattern_confidence']
            ])
            
        except Exception as e:
            logger.warning(f"Error generating confidence indicators: {e}")
            indicators = {
                'market_confidence': 0.5,
                'statistical_confidence': 0.5,
                'pattern_confidence': 0.5,
                'entropy_confidence': 0.5,
                'overall_confidence': 0.5
            }
        
        return indicators
    
    def _generate_pattern_summary(self, stats_analysis: Any) -> str:
        """Generate a summary of detected patterns."""
        summary_parts = []
        
        try:
            # Check for repeated patterns
            if hasattr(stats_analysis, 'patterns'):
                patterns = stats_analysis.patterns
                repeated_patterns = patterns.get('repeated_patterns', [])
                
                if repeated_patterns:
                    top_pattern = repeated_patterns[0]
                    summary_parts.append(f"Detected pattern: {top_pattern[0]} (appeared {top_pattern[1]} times)")
                else:
                    summary_parts.append("No significant repeating patterns detected")
                
                # Check for streaks
                longest_streak = patterns.get('longest_streak', (0, 0))
                if longest_streak[1] > 2:
                    summary_parts.append(f"Longest streak: {longest_streak[1]} consecutive {longest_streak[0]}s")
            
            # Check for cycles
            if hasattr(stats_analysis, 'patterns') and 'cycle_lengths' in stats_analysis.patterns:
                cycles = stats_analysis.patterns['cycle_lengths']
                if cycles:
                    summary_parts.append(f"Detected cycles: {cycles[:3]}")
            
            # Check for hot/cold digits
            if hasattr(stats_analysis, 'frequency'):
                freq = stats_analysis.frequency
                hot_digits = freq.get('hot_digits', [])
                cold_digits = freq.get('cold_digits', [])
                
                if hot_digits:
                    summary_parts.append(f"Hot digits: {hot_digits}")
                if cold_digits:
                    summary_parts.append(f"Cold digits: {cold_digits}")
            
            # Check for randomness
            if hasattr(stats_analysis, 'entropy'):
                if stats_analysis.entropy.get('is_random', False):
                    summary_parts.append("Market appears random (no strong patterns)")
                else:
                    summary_parts.append("Non-random behavior detected")
            
        except Exception as e:
            logger.warning(f"Error generating pattern summary: {e}")
            summary_parts = ["Pattern analysis unavailable"]
        
        return " | ".join(summary_parts) if summary_parts else "No patterns detected"
    
    def _generate_historical_context(self, ticks: List[Tick]) -> str:
        """Generate historical context for the current market."""
        if len(ticks) < 20:
            return "Insufficient historical data for context"
        
        try:
            # Calculate recent vs historical metrics
            recent = ticks[-20:]
            historical = ticks[:-20] if len(ticks) > 40 else ticks
            
            recent_digits = [t.last_digit for t in recent]
            hist_digits = [t.last_digit for t in historical]
            
            # Compare distributions
            from collections import Counter
            
            recent_counts = Counter(recent_digits)
            hist_counts = Counter(hist_digits)
            
            # Calculate changes
            changes = []
            for digit in range(10):
                recent_freq = recent_counts.get(digit, 0) / len(recent_digits) if recent_digits else 0
                hist_freq = hist_counts.get(digit, 0) / len(hist_digits) if hist_digits else 0
                changes.append(abs(recent_freq - hist_freq))
            
            avg_change = np.mean(changes) if changes else 0
            
            if avg_change > 0.1:
                context = "Significant shift in digit distribution compared to historical patterns"
            elif avg_change > 0.05:
                context = "Moderate change in digit distribution from historical patterns"
            else:
                context = "Digit distribution consistent with historical patterns"
            
            # Add trend context
            if len(ticks) > 50:
                recent_prices = [float(t.price) for t in ticks[-20:]]
                hist_prices = [float(t.price) for t in ticks[:-20]] if len(ticks) > 40 else recent_prices
                
                recent_mean = np.mean(recent_prices) if recent_prices else 0
                hist_mean = np.mean(hist_prices) if hist_prices else 0
                
                if abs(recent_mean - hist_mean) / hist_mean > 0.01:
                    context += f" (price level changed {((recent_mean - hist_mean) / hist_mean * 100):.1f}%)"
            
            return context
            
        except Exception as e:
            logger.warning(f"Error generating historical context: {e}")
            return "Historical context unavailable"
    
    def _generate_explanation(
        self, 
        market_analysis: Any, 
        stats_analysis: Any,
        digit_distribution: Dict[int, float]
    ) -> str:
        """Generate an explanation of the current market behavior."""
        explanation_parts = []
        
        try:
            # Market state explanation
            explanation_parts.append(f"The market is currently {market_analysis.state.value.upper()}")
            
            # Digit distribution explanation
            max_digit = max(digit_distribution, key=digit_distribution.get)
            min_digit = min(digit_distribution, key=digit_distribution.get)
            
            explanation_parts.append(
                f"Digit {max_digit} is most frequent ({digit_distribution[max_digit]:.1%}), "
                f"while {min_digit} is least frequent ({digit_distribution[min_digit]:.1%})"
            )
            
            # Transition explanation
            if hasattr(self, '_last_transition_probs'):
                probs = self._last_transition_probs
                if probs['match_probability'] > 0.2:
                    explanation_parts.append(
                        f"There is a {probs['match_probability']:.1%} chance of digits matching consecutively"
                    )
                
                if probs['consecutive_match'] > 0.1:
                    explanation_parts.append(
                        f"Consecutive matches occur {probs['consecutive_match']:.1%} of the time"
                    )
            
            # Pattern explanation
            if hasattr(stats_analysis, 'patterns'):
                patterns = stats_analysis.patterns
                if patterns.get('repeated_patterns'):
                    top = patterns['repeated_patterns'][0]
                    explanation_parts.append(
                        f"The pattern {top[0]} repeats, indicating some structure in the market"
                    )
                else:
                    explanation_parts.append("No clear patterns detected in recent data")
            
            # Randomness explanation
            if hasattr(stats_analysis, 'entropy'):
                entropy = stats_analysis.entropy
                if entropy.get('is_random', False):
                    explanation_parts.append("The market appears random, with unpredictable digit sequences")
                else:
                    explanation_parts.append("Non-random patterns suggest potential trading opportunities")
            
            # Confidence explanation
            if hasattr(market_analysis, 'confidence'):
                confidence = market_analysis.confidence
                if confidence > 0.7:
                    explanation_parts.append("High confidence in this analysis")
                elif confidence > 0.4:
                    explanation_parts.append("Moderate confidence in this analysis")
                else:
                    explanation_parts.append("Low confidence - market conditions may be changing")
            
        except Exception as e:
            logger.warning(f"Error generating explanation: {e}")
            explanation_parts = ["Analysis currently unavailable"]
        
        return " ".join(explanation_parts)
    
    def _generate_observations(
        self,
        market_analysis: Any,
        stats_analysis: Any,
        digit_distribution: Dict[int, float]
    ) -> List[str]:
        """Generate observations about the current market."""
        observations = []
        
        try:
            # Market state observation
            observations.append(f"Market state: {market_analysis.state.value.upper()}")
            observations.append(f"State confidence: {market_analysis.confidence:.1%}")
            
            # Digit distribution observation
            max_digit = max(digit_distribution, key=digit_distribution.get)
            min_digit = min(digit_distribution, key=digit_distribution.get)
            
            observations.append(f"Most frequent digit: {max_digit} ({digit_distribution[max_digit]:.1%})")
            observations.append(f"Least frequent digit: {min_digit} ({digit_distribution[min_digit]:.1%})")
            
            # Deviation observation
            expected = 0.1
            deviations = [abs(freq - expected) for freq in digit_distribution.values()]
            avg_deviation = np.mean(deviations)
            
            if avg_deviation > 0.05:
                observations.append(f"Significant deviation from uniform distribution ({avg_deviation:.2%})")
            elif avg_deviation > 0.02:
                observations.append(f"Moderate deviation from uniform distribution ({avg_deviation:.2%})")
            else:
                observations.append("Distribution is close to uniform (no strong bias)")
            
            # Transition observations
            if hasattr(self, '_last_transition_probs'):
                probs = self._last_transition_probs
                if probs['match_probability'] > 0.2:
                    observations.append(f"High match probability: {probs['match_probability']:.1%}")
                else:
                    observations.append(f"Low match probability: {probs['match_probability']:.1%}")
            
            # Pattern observations
            if hasattr(stats_analysis, 'patterns'):
                patterns = stats_analysis.patterns
                if patterns.get('longest_streak', (0, 0))[1] > 3:
                    digit, length = patterns['longest_streak']
                    observations.append(f"Long streak detected: {length} consecutive {digit}s")
            
            # Volatility observation
            if hasattr(stats_analysis, 'volatility'):
                metrics = stats_analysis.volatility.get('metrics', {})
                if 'standard_deviation' in metrics:
                    vol = metrics['standard_deviation']
                    if vol > 0.05:
                        observations.append(f"High volatility detected: {vol:.3f}")
                    elif vol > 0.02:
                        observations.append(f"Moderate volatility: {vol:.3f}")
                    else:
                        observations.append(f"Low volatility: {vol:.3f}")
            
            # Risk observation
            observations.append(f"Risk level: {market_analysis.risk_level.value.upper()}")
            
        except Exception as e:
            logger.warning(f"Error generating observations: {e}")
            observations = ["Analysis currently unavailable"]
        
        return observations
    
    def _generate_recommendations(
        self,
        market_analysis: Any,
        stats_analysis: Any,
        digit_distribution: Dict[int, float]
    ) -> List[str]:
        """Generate trading recommendations based on analysis."""
        recommendations = []
        
        try:
            # State-based recommendations
            state = market_analysis.state
            
            if state == MarketState.CALM:
                recommendations.append("Low volatility suggests Match contracts may have higher probability")
                recommendations.append("Consider smaller position sizes due to low market activity")
            
            elif state == MarketState.RANDOM:
                recommendations.append("Random market suggests no clear advantage for Match or Differ")
                recommendations.append("Consider waiting for clearer patterns to emerge")
            
            elif state == MarketState.TRENDING:
                recommendations.append("Trending market suggests following the trend direction")
                recommendations.append("Differ contracts may have advantage if trend is strong")
            
            elif state == MarketState.VOLATILE:
                recommendations.append("High volatility suggests increased risk and opportunity")
                recommendations.append("Consider shorter timeframes for Match/Differ contracts")
            
            elif state == MarketState.CHAOTIC:
                recommendations.append("Chaotic market suggests avoiding high-risk positions")
                recommendations.append("Wait for market to stabilize before trading")
            
            elif state == MarketState.MEAN_REVERTING:
                recommendations.append("Mean reversion suggests fading extreme moves")
                recommendations.append("Match contracts may perform well in reverting markets")
            
            elif state == MarketState.MOMENTUM_DRIVEN:
                recommendations.append("Momentum suggests following the current direction")
                recommendations.append("Differ contracts may be favorable in strong momentum")
            
            # Digit-based recommendations
            max_digit = max(digit_distribution, key=digit_distribution.get)
            min_digit = min(digit_distribution, key=digit_distribution.get)
            
            if digit_distribution[max_digit] > 0.15:
                recommendations.append(f"Digit {max_digit} is currently overrepresented")
            
            if digit_distribution[min_digit] < 0.05:
                recommendations.append(f"Digit {min_digit} is currently underrepresented")
            
            # Confidence-based recommendations
            if market_analysis.confidence < 0.5:
                recommendations.append("Low confidence suggests careful position sizing")
            
            # Risk-based recommendations
            if market_analysis.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
                recommendations.append("High risk level suggests reduced position sizes")
            
            if not recommendations:
                recommendations.append("Neutral market conditions - maintain normal position sizing")
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            recommendations = ["Consult market analysis for guidance"]
        
        return recommendations
    
    def _assess_risk(
        self,
        market_analysis: Any,
        stats_analysis: Any,
        digit_distribution: Dict[int, float]
    ) -> Dict[str, Any]:
        """Assess risk for Match/Differ trading."""
        risk = {
            'overall_risk': 0.5,
            'market_risk': 0.5,
            'pattern_risk': 0.5,
            'volatility_risk': 0.5,
            'confidence_risk': 0.5,
            'risk_level': 'MODERATE'
        }
        
        try:
            # Market risk
            market_risk_map = {
                MarketState.CALM: 0.2,
                MarketState.RANDOM: 0.4,
                MarketState.TRENDING: 0.4,
                MarketState.VOLATILE: 0.7,
                MarketState.CHAOTIC: 0.9,
                MarketState.MEAN_REVERTING: 0.3,
                MarketState.MOMENTUM_DRIVEN: 0.5
            }
            risk['market_risk'] = market_risk_map.get(market_analysis.state, 0.5)
            
            # Pattern risk
            if hasattr(stats_analysis, 'patterns'):
                pattern_conf = stats_analysis.patterns.get('confidence', 0.5)
                risk['pattern_risk'] = 1 - pattern_conf  # Lower pattern confidence = higher risk
            
            # Volatility risk
            if hasattr(stats_analysis, 'volatility'):
                metrics = stats_analysis.volatility.get('metrics', {})
                vol = metrics.get('standard_deviation', 0)
                risk['volatility_risk'] = min(vol * 10, 1.0)  # Scale volatility
            
            # Confidence risk
            risk['confidence_risk'] = 1 - market_analysis.confidence
            
            # Overall risk
            risk['overall_risk'] = np.mean([
                risk['market_risk'],
                risk['pattern_risk'],
                risk['volatility_risk'],
                risk['confidence_risk']
            ])
            
            # Risk level
            if risk['overall_risk'] < 0.3:
                risk['risk_level'] = 'LOW'
            elif risk['overall_risk'] < 0.5:
                risk['risk_level'] = 'MODERATE'
            elif risk['overall_risk'] < 0.7:
                risk['risk_level'] = 'HIGH'
            else:
                risk['risk_level'] = 'VERY_HIGH'
            
        except Exception as e:
            logger.warning(f"Error assessing risk: {e}")
        
        return risk
    
    def _empty_insight(self) -> MatchDifferInsight:
        """Return an empty insight."""
        return MatchDifferInsight(
            market_condition="unknown",
            observations=["Insufficient data for analysis"],
            digit_distribution={i: 0.1 for i in range(10)},
            transition_probabilities={},
            confidence_indicators={},
            pattern_summary="No data available",
            historical_context="No historical data",
            explanation="Insufficient data for meaningful analysis",
            timestamp=datetime.now()
        )