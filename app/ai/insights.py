"""
AI Insights Engine
Generates natural language insights, explanations, and risk communications
based on statistical analysis and market conditions.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import random

from core.types import Tick, AIInsight, MarketStateAnalysis
from core.constants import MarketState, RiskLevel
from core.logger import get_logger
from analytics.engine import AnalyticsEngine
from market_state.classifier import MarketClassifier
from intelligence.match_differ import MatchDifferIntelligence


logger = get_logger(__name__)


class AIInsightsEngine:
    """
    Generates human-readable insights and explanations from market data.
    Focuses on transparency, explainability, and risk communication.
    """
    
    def __init__(self):
        """Initialize the AI Insights Engine."""
        self.analytics_engine = AnalyticsEngine()
        self.market_classifier = MarketClassifier()
        self.match_differ_intelligence = MatchDifferIntelligence()
        
        self._insight_history: List[AIInsight] = []
        self._max_history = 500
        
        # Templates for different insights
        self._templates = self._initialize_templates()
        
        logger.info("AIInsightsEngine initialized")
    
    def _initialize_templates(self) -> Dict[str, Any]:
        """Initialize templates for different insight types."""
        return {
            'market_state': {
                'calm': [
                    "The market is currently showing low volatility with stable patterns.",
                    "Market conditions are calm with predictable price movements.",
                    "Low market activity suggests a stable trading environment."
                ],
                'random': [
                    "The market appears to be behaving randomly with no clear patterns.",
                    "Random market conditions make it difficult to identify trends.",
                    "Market movements are unpredictable and lacking clear direction."
                ],
                'trending': [
                    "A clear market trend is developing with consistent directional movement.",
                    "The market is trending strongly in one direction.",
                    "Trending conditions indicate sustained directional momentum."
                ],
                'volatile': [
                    "High volatility is creating significant price swings in the market.",
                    "The market is experiencing rapid and unpredictable price changes.",
                    "Volatile conditions require careful risk management."
                ],
                'chaotic': [
                    "Extreme market chaos with highly unpredictable behavior.",
                    "The market is in a chaotic state with no clear patterns.",
                    "Chaotic conditions indicate high risk and uncertainty."
                ],
                'mean_reverting': [
                    "The market is showing mean-reverting behavior, pulling back to averages.",
                    "Price movements are reverting to the mean, suggesting range-bound conditions.",
                    "Mean-reverting patterns indicate potential reversal opportunities."
                ],
                'momentum_driven': [
                    "Strong momentum is driving the market in a clear direction.",
                    "The market is momentum-driven with sustained directional pressure.",
                    "Momentum conditions suggest following the current trend."
                ]
            },
            'risk': {
                'very_low': [
                    "Risk levels are very low, indicating a stable trading environment.",
                    "Minimal risk exposure is recommended in current conditions.",
                    "Very low risk suggests normal position sizing."
                ],
                'low': [
                    "Low risk levels suggest favorable trading conditions.",
                    "Limited risk exposure is recommended for current market conditions.",
                    "Low risk suggests maintaining moderate position sizes."
                ],
                'moderate': [
                    "Moderate risk levels require careful position management.",
                    "Balanced risk management is advised in current conditions.",
                    "Moderate risk suggests adjusting position sizes accordingly."
                ],
                'high': [
                    "High risk levels require cautious trading approach.",
                    "Significant risk exposure should be avoided in current conditions.",
                    "High risk suggests reducing position sizes."
                ],
                'very_high': [
                    "Very high risk levels indicate extremely cautious trading required.",
                    "Maximum caution advised due to elevated risk levels.",
                    "Very high risk suggests minimal or no position exposure."
                ]
            },
            'digit_pattern': {
                'hot': [
                    "Hot digits are appearing more frequently than expected.",
                    "Certain digits are showing higher than normal frequency.",
                    "Hot digit activity suggests potential pattern opportunities."
                ],
                'cold': [
                    "Cold digits are appearing less frequently than expected.",
                    "Certain digits are showing lower than normal frequency.",
                    "Cold digit activity suggests potential reversal opportunities."
                ],
                'streak': [
                    "Consecutive digit streaks are forming in the market.",
                    "Streak patterns indicate potential momentum in digit movements.",
                    "Current streaks suggest attention to similar digit sequences."
                ],
                'transition': [
                    "Digit transitions show interesting patterns for Match/Differ.",
                    "Transition probabilities are indicating potential opportunities.",
                    "Changing digit patterns suggest adaptation of trading strategy."
                ]
            }
        }
    
    def generate_insights(self, ticks: List[Tick]) -> AIInsight:
        """
        Generate comprehensive AI insights from tick data.
        
        Args:
            ticks: List of tick objects
            
        Returns:
            AIInsight: Complete AI insights
        """
        if not ticks or len(ticks) < 10:
            return self._empty_insight()
        
        try:
            # Perform analyses
            market_analysis = self.market_classifier.classify(ticks)
            stats_analysis = self.analytics_engine.analyze_tick_data(ticks)
            md_analysis = self.match_differ_intelligence.analyze(ticks)
            
            # Generate insights
            what_is_happening = self._generate_market_description(market_analysis, stats_analysis)
            why_classified = self._generate_classification_explanation(market_analysis)
            statistical_factors = self._generate_statistical_factors(stats_analysis)
            market_differences = self._generate_market_differences(ticks, stats_analysis)
            risks = self._generate_risk_insights(market_analysis)
            confidence_level = market_analysis.confidence
            
            # Create insight
            insight = AIInsight(
                what_is_happening=what_is_happening,
                why_classified=why_classified,
                statistical_factors=statistical_factors,
                market_differences=market_differences,
                risks=risks,
                confidence_level=confidence_level,
                timestamp=datetime.now()
            )
            
            # Store history
            self._insight_history.append(insight)
            if len(self._insight_history) > self._max_history:
                self._insight_history = self._insight_history[-self._max_history:]
            
            logger.info("AI insights generated successfully")
            return insight
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}", exc_info=True)
            return self._empty_insight()
    
    def _generate_market_description(self, market_analysis: MarketStateAnalysis, stats_analysis: Any) -> str:
        """Generate a description of what is happening in the market."""
        description_parts = []
        
        try:
            # Market state description
            state = market_analysis.state
            state_templates = self._templates['market_state'].get(state.value, [])
            if state_templates:
                description_parts.append(random.choice(state_templates))
            
            # Add volatility context
            if 'volatility' in market_analysis.indicators:
                vol = market_analysis.indicators['volatility']
                if vol > 0.05:
                    description_parts.append(f"Volatility is elevated at {vol:.3f}, indicating larger price swings.")
                elif vol > 0.02:
                    description_parts.append(f"Volatility is moderate at {vol:.3f}.")
                else:
                    description_parts.append(f"Volatility is low at {vol:.3f}, suggesting stable conditions.")
            
            # Add trend context
            if 'trend_strength' in market_analysis.indicators:
                trend = market_analysis.indicators['trend_strength']
                if trend > 0.6:
                    direction = "upward" if market_analysis.indicators.get('trend_direction', 0) > 0 else "downward"
                    description_parts.append(f"A {direction} trend is strengthening with {trend:.2f} strength.")
            
            # Add digit distribution context
            if hasattr(stats_analysis, 'summary'):
                summary = stats_analysis.summary
                if 'most_common_digit' in summary:
                    most_common = summary['most_common_digit']
                    description_parts.append(f"Digit {most_common} is appearing most frequently.")
                
                if 'hot_digits' in summary and summary['hot_digits']:
                    description_parts.append(f"Hot digits {summary['hot_digits']} are showing increased frequency.")
            
            # Add randomness context
            if hasattr(stats_analysis, 'entropy'):
                if stats_analysis.entropy.get('is_random', False):
                    description_parts.append("The market appears random with no clear patterns.")
                else:
                    description_parts.append("Non-random patterns are detectable in the market.")
            
        except Exception as e:
            logger.warning(f"Error generating market description: {e}")
            description_parts.append("Market conditions are currently being analyzed.")
        
        return " ".join(description_parts) if description_parts else "Market analysis in progress."
    
    def _generate_classification_explanation(self, market_analysis: MarketStateAnalysis) -> str:
        """Generate an explanation of why the market was classified as such."""
        explanation_parts = []
        
        try:
            # State explanation
            state = market_analysis.state
            state_desc = self._get_state_description(state)
            explanation_parts.append(state_desc)
            
            # Key indicators
            indicators = market_analysis.indicators
            evidence = market_analysis.evidence
            
            if indicators:
                # Add key indicator explanations
                if 'volatility' in indicators:
                    vol = indicators['volatility']
                    explanation_parts.append(
                        f"Volatility of {vol:.3f} indicates {self._get_volatility_level(vol)}."
                    )
                
                if 'entropy' in indicators:
                    entropy = indicators['entropy']
                    explanation_parts.append(
                        f"Entropy of {entropy:.2f} suggests {self._get_entropy_level(entropy)}."
                    )
                
                if 'trend_strength' in indicators:
                    trend = indicators['trend_strength']
                    explanation_parts.append(
                        f"Trend strength of {trend:.2f} indicates {self._get_trend_level(trend)}."
                    )
                
                if 'momentum_strength' in indicators:
                    momentum = indicators['momentum_strength']
                    explanation_parts.append(
                        f"Momentum of {momentum:.2f} suggests {self._get_momentum_level(momentum)}."
                    )
            
            # Add evidence
            if evidence:
                explanation_parts.append("Supporting evidence includes:")
                for ev in evidence[:3]:
                    explanation_parts.append(f"• {ev}")
            
            # Confidence explanation
            confidence = market_analysis.confidence
            explanation_parts.append(
                f"This classification has {self._get_confidence_level(confidence)} confidence."
            )
            
        except Exception as e:
            logger.warning(f"Error generating classification explanation: {e}")
            explanation_parts.append("Classification based on comprehensive market analysis.")
        
        return " ".join(explanation_parts) if explanation_parts else "Market classification in progress."
    
    def _generate_statistical_factors(self, stats_analysis: Any) -> List[str]:
        """Generate list of statistical factors that influenced the analysis."""
        factors = []
        
        try:
            # Frequency factors
            if hasattr(stats_analysis, 'frequency'):
                freq = stats_analysis.frequency
                if freq.get('hot_digits'):
                    factors.append(f"Hot digits: {freq['hot_digits']} (appearing more frequently)")
                if freq.get('cold_digits'):
                    factors.append(f"Cold digits: {freq['cold_digits']} (appearing less frequently)")
                
                # Deviation from uniform
                frequencies = freq.get('frequencies', {})
                if frequencies:
                    expected = 0.1
                    deviations = [abs(f - expected) for f in frequencies.values()]
                    avg_deviation = np.mean(deviations) if deviations else 0
                    if avg_deviation > 0.02:
                        factors.append(f"Significant deviation from uniform distribution ({avg_deviation:.2%})")
            
            # Entropy factors
            if hasattr(stats_analysis, 'entropy'):
                entropy = stats_analysis.entropy
                if entropy.get('is_random'):
                    factors.append("High randomness detected in digit sequences")
                else:
                    factors.append("Non-random patterns detected")
                factors.append(f"Entropy: {entropy.get('entropy', 0):.2f} bits")
            
            # Volatility factors
            if hasattr(stats_analysis, 'volatility'):
                metrics = stats_analysis.volatility.get('metrics', {})
                if metrics.get('standard_deviation'):
                    factors.append(f"Volatility: {metrics['standard_deviation']:.3f}")
                if metrics.get('coefficient_of_variation'):
                    factors.append(f"Variation coefficient: {metrics['coefficient_of_variation']:.3f}")
            
            # Pattern factors
            if hasattr(stats_analysis, 'patterns'):
                patterns = stats_analysis.patterns
                if patterns.get('longest_streak', (0, 0))[1] > 3:
                    digit, length = patterns['longest_streak']
                    factors.append(f"Longest consecutive streak: {length} of digit {digit}")
                
                if patterns.get('repeated_patterns'):
                    factors.append(f"Repeated patterns detected: {len(patterns['repeated_patterns'])} patterns found")
            
            # Momentum factors
            if hasattr(stats_analysis, 'volatility'):
                momentum = stats_analysis.volatility.get('momentum', {})
                if momentum.get('direction'):
                    factors.append(f"Momentum direction: {momentum['direction']}")
                if momentum.get('strength'):
                    factors.append(f"Momentum strength: {momentum['strength']:.2f}")
            
            # Confidence factors
            if hasattr(stats_analysis, 'confidence'):
                confidence = stats_analysis.confidence
                factors.append(f"Overall confidence: {confidence.get('overall', 0):.2%}")
            
        except Exception as e:
            logger.warning(f"Error generating statistical factors: {e}")
            factors.append("Various statistical factors analyzed")
        
        return factors if factors else ["Statistical analysis in progress"]
    
    def _generate_market_differences(self, ticks: List[Tick], stats_analysis: Any) -> str:
        """
        Generate description of how current market differs from previous periods.
        """
        try:
            if len(ticks) < 50:
                return "Insufficient data to identify differences from previous periods."
            
            # Compare recent vs older data
            recent = ticks[-20:]
            older = ticks[:-20] if len(ticks) > 40 else ticks
            
            recent_digits = [t.last_digit for t in recent]
            older_digits = [t.last_digit for t in older]
            
            # Calculate differences
            from collections import Counter
            recent_counts = Counter(recent_digits)
            older_counts = Counter(older_digits)
            
            # Find significant changes
            changes = []
            for digit in range(10):
                recent_freq = recent_counts.get(digit, 0) / len(recent_digits) if recent_digits else 0
                older_freq = older_counts.get(digit, 0) / len(older_digits) if older_digits else 0
                diff = recent_freq - older_freq
                if abs(diff) > 0.02:
                    direction = "increased" if diff > 0 else "decreased"
                    changes.append(f"digit {digit} {direction} by {abs(diff):.1%}")
            
            # Compare price levels
            recent_prices = [float(t.price) for t in recent]
            older_prices = [float(t.price) for t in older] if len(ticks) > 40 else recent_prices
            
            price_change = 0
            if older_prices and recent_prices:
                older_mean = np.mean(older_prices)
                recent_mean = np.mean(recent_prices)
                if older_mean > 0:
                    price_change = (recent_mean - older_mean) / older_mean * 100
            
            # Generate description
            description_parts = []
            
            if changes:
                description_parts.append(f"The most notable differences are: {', '.join(changes[:3])}")
            else:
                description_parts.append("Digit distribution is relatively stable compared to previous periods.")
            
            if abs(price_change) > 0.5:
                description_parts.append(f"Price level has changed by {price_change:.1f}%.")
            
            # Check for pattern changes
            if hasattr(stats_analysis, 'patterns'):
                patterns = stats_analysis.patterns
                if patterns.get('repeated_patterns'):
                    description_parts.append("New patterns may be emerging in recent data.")
            
            return ". ".join(description_parts) if description_parts else "No significant differences detected."
            
        except Exception as e:
            logger.warning(f"Error generating market differences: {e}")
            return "Market differences are being analyzed."
    
    def _generate_risk_insights(self, market_analysis: MarketStateAnalysis) -> List[str]:
        """
        Generate risk-related insights and warnings.
        """
        risks = []
        
        try:
            risk_level = market_analysis.risk_level
            
            # Risk level warnings
            risk_templates = self._templates['risk'].get(risk_level.value, [])
            if risk_templates:
                risks.append(random.choice(risk_templates))
            
            # State-specific risks
            state = market_analysis.state
            
            if state == MarketState.VOLATILE:
                risks.append("High volatility increases risk of sudden price movements.")
                risks.append("Consider tighter stop-loss positions.")
            
            elif state == MarketState.CHAOTIC:
                risks.append("Chaotic conditions make risk management essential.")
                risks.append("Avoid aggressive position sizing in current conditions.")
            
            elif state == MarketState.TRENDING:
                risks.append("Trending conditions require attention to trend reversals.")
                risks.append("Monitor for signs of trend exhaustion.")
            
            elif state == MarketState.RANDOM:
                risks.append("Random conditions increase uncertainty in predictions.")
                risks.append("Avoid overcommitting to any single direction.")
            
            elif state == MarketState.MEAN_REVERTING:
                risks.append("Mean reversion may lead to false breakouts.")
                risks.append("Be cautious of overextended positions.")
            
            elif state == MarketState.MOMENTUM_DRIVEN:
                risks.append("Momentum can reverse quickly.")
                risks.append("Monitor momentum indicators for signs of exhaustion.")
            
            # Confidence-based risks
            confidence = market_analysis.confidence
            if confidence < 0.5:
                risks.append("Low confidence suggests careful position management.")
            
            # Specific risk factors
            if 'volatility' in market_analysis.indicators:
                vol = market_analysis.indicators['volatility']
                if vol > 0.08:
                    risks.append(f"Extreme volatility ({vol:.3f}) requires maximum caution.")
            
            if 'entropy' in market_analysis.indicators:
                entropy = market_analysis.indicators['entropy']
                if entropy > 3.0:
                    risks.append("High entropy indicates unpredictable market behavior.")
            
            # Add general risk warning
            if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
                risks.append("Risk management should be the top priority.")
            
            # Add transparency note
            risks.append("No prediction of future outcomes is implied. Use this analysis as one of many tools.")
            
        except Exception as e:
            logger.warning(f"Error generating risk insights: {e}")
            risks.append("Risk assessment in progress. Exercise caution in all trading decisions.")
        
        return risks if risks else ["Risk analysis in progress. Trade responsibly."]
    
    def _get_state_description(self, state: MarketState) -> str:
        """Get a description of the market state."""
        descriptions = {
            MarketState.CALM: "The market is classified as CALM due to low volatility and stable patterns.",
            MarketState.RANDOM: "The market is classified as RANDOM due to unpredictable behavior and lack of patterns.",
            MarketState.TRENDING: "The market is classified as TRENDING due to strong directional movement.",
            MarketState.VOLATILE: "The market is classified as VOLATILE due to high price swings and uncertainty.",
            MarketState.CHAOTIC: "The market is classified as CHAOTIC due to extreme unpredictability.",
            MarketState.MEAN_REVERTING: "The market is classified as MEAN REVERTING due to tendency to return to averages.",
            MarketState.MOMENTUM_DRIVEN: "The market is classified as MOMENTUM DRIVEN due to strong directional pressure."
        }
        return descriptions.get(state, "Market classification based on comprehensive analysis.")
    
    def _get_volatility_level(self, volatility: float) -> str:
        """Get a description of volatility level."""
        if volatility < 0.02:
            return "very low volatility"
        elif volatility < 0.05:
            return "moderate volatility"
        elif volatility < 0.08:
            return "high volatility"
        else:
            return "extreme volatility"
    
    def _get_entropy_level(self, entropy: float) -> str:
        """Get a description of entropy level."""
        if entropy < 2.0:
            return "low randomness (patterned)"
        elif entropy < 3.0:
            return "moderate randomness"
        else:
            return "high randomness (unpredictable)"
    
    def _get_trend_level(self, trend: float) -> str:
        """Get a description of trend level."""
        if trend < 0.3:
            return "weak or no trend"
        elif trend < 0.6:
            return "moderate trend"
        else:
            return "strong trend"
    
    def _get_momentum_level(self, momentum: float) -> str:
        """Get a description of momentum level."""
        if momentum < 0.3:
            return "weak momentum"
        elif momentum < 0.6:
            return "moderate momentum"
        else:
            return "strong momentum"
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get a description of confidence level."""
        if confidence >= 0.8:
            return "very high"
        elif confidence >= 0.6:
            return "high"
        elif confidence >= 0.4:
            return "moderate"
        elif confidence >= 0.2:
            return "low"
        else:
            return "very low"
    
    def _empty_insight(self) -> AIInsight:
        """Return an empty insight."""
        return AIInsight(
            what_is_happening="Insufficient data for market analysis.",
            why_classified="Classification pending sufficient data.",
            statistical_factors=["Waiting for more data points"],
            market_differences="Insufficient data for comparison.",
            risks=["Data collection in progress. Please wait for analysis."],
            confidence_level=0.0,
            timestamp=datetime.now()
        )
    
    def get_insight_history(self, limit: int = 100) -> List[AIInsight]:
        """
        Get historical insights.
        
        Args:
            limit: Maximum number of insights to return
            
        Returns:
            List[AIInsight]: Historical insights
        """
        return self._insight_history[-limit:]
    
    def get_recent_insight(self) -> Optional[AIInsight]:
        """
        Get the most recent insight.
        
        Returns:
            Optional[AIInsight]: Latest insight or None
        """
        return self._insight_history[-1] if self._insight_history else None
