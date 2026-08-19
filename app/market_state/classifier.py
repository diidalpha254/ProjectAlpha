"""
Market State Classifier
Classifies market conditions based on statistical analysis and indicators.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from enum import Enum

from core.constants import MarketState, RiskLevel, MARKET_STATE_DESCRIPTIONS
from core.types import MarketStateAnalysis
from core.logger import get_logger
from analytics.engine import AnalyticsEngine, ComprehensiveAnalysis

logger = get_logger(__name__)


class MarketClassifier:
    """
    Classifies market states based on comprehensive statistical analysis.
    Uses multiple indicators to determine current market conditions.
    """
    
    def __init__(self):
        """Initialize the market classifier."""
        self.analytics_engine = AnalyticsEngine()
        self._last_classification: Optional[MarketStateAnalysis] = None
        self._state_history: List[MarketStateAnalysis] = []
        self._max_history = 1000
        
        # Thresholds for classification
        self.thresholds = {
            'calm_volatility': 0.02,  # Low volatility threshold
            'volatile_volatility': 0.05,  # High volatility threshold
            'chaotic_entropy': 0.85,  # High entropy threshold
            'trend_strength': 0.6,  # Strong trend threshold
            'mean_reversion': 0.5,  # Mean reversion threshold
            'momentum_strength': 0.6,  # Strong momentum threshold
            'random_entropy_low': 0.3,  # Low entropy threshold
            'random_entropy_high': 0.7,  # High entropy threshold
        }
        
        logger.info("MarketClassifier initialized")
    
    def classify(self, ticks: List[Any]) -> MarketStateAnalysis:
        """
        Classify the current market state based on tick data.
        
        Args:
            ticks: List of tick objects
            
        Returns:
            MarketStateAnalysis: Complete market state analysis
        """
        if not ticks or len(ticks) < 10:
            return self._empty_analysis()
        
        try:
            # Perform comprehensive analysis
            analysis = self.analytics_engine.analyze_tick_data(ticks)
            
            # Extract key indicators
            indicators = self._extract_indicators(analysis)
            
            # Determine market state
            state, confidence, evidence = self._determine_state(indicators, analysis)
            
            # Calculate risk level
            risk_level = self._calculate_risk_level(state, indicators)
            
            # Generate explanation
            explanation = self._generate_explanation(state, indicators, evidence)
            
            # Create analysis result
            result = MarketStateAnalysis(
                state=state,
                confidence=confidence,
                risk_level=risk_level,
                indicators=indicators,
                evidence=evidence,
                explanation=explanation,
                timestamp=datetime.now()
            )
            
            # Store history
            self._state_history.append(result)
            if len(self._state_history) > self._max_history:
                self._state_history = self._state_history[-self._max_history:]
            
            self._last_classification = result
            logger.info(f"Market classified as: {state.value} (confidence: {confidence:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error classifying market state: {e}", exc_info=True)
            return self._empty_analysis()
    
    def _extract_indicators(self, analysis: ComprehensiveAnalysis) -> Dict[str, float]:
        """
        Extract key indicators from comprehensive analysis.
        
        Args:
            analysis: Comprehensive analysis results
            
        Returns:
            Dict[str, float]: Extracted indicators
        """
        indicators = {}
        
        try:
            # Volatility indicators
            if 'metrics' in analysis.volatility:
                metrics = analysis.volatility['metrics']
                indicators['volatility'] = metrics.get('standard_deviation', 0)
                indicators['volatility_ratio'] = metrics.get('coefficient_of_variation', 0)
            
            # Momentum indicators
            if 'momentum' in analysis.volatility:
                momentum = analysis.volatility['momentum']
                indicators['momentum_strength'] = momentum.get('strength', 0)
                indicators['momentum_direction'] = 1 if momentum.get('direction') == 'up' else -1 if momentum.get('direction') == 'down' else 0
            
            # Trend indicators
            if 'trend' in analysis.volatility:
                trend = analysis.volatility['trend']
                indicators['trend_strength'] = trend.get('trend_strength', 0)
                indicators['trend_direction'] = 1 if trend.get('direction') == 'up' else -1 if trend.get('direction') == 'down' else 0
                indicators['r_squared'] = trend.get('r_squared', 0)
            
            # Mean reversion indicators
            if 'mean_reversion' in analysis.volatility:
                mean_rev = analysis.volatility['mean_reversion']
                indicators['mean_reversion_score'] = mean_rev.get('mean_reversion_score', 0)
                indicators['half_life'] = mean_rev.get('half_life', 0)
            
            # Entropy indicators
            if 'entropy' in analysis.__dict__:
                entropy_data = analysis.entropy
                indicators['entropy'] = entropy_data.get('entropy', 0)
                indicators['randomness_score'] = entropy_data.get('randomness_score', 0)
            
            # Pattern indicators
            if 'patterns' in analysis.__dict__:
                patterns = analysis.patterns
                indicators['pattern_confidence'] = patterns.get('confidence', 0)
                if patterns.get('longest_streak'):
                    indicators['max_streak'] = patterns['longest_streak'][1]
            
            # Frequency indicators
            if 'frequency' in analysis.__dict__:
                freq = analysis.frequency
                indicators['hot_digits'] = len(freq.get('hot_digits', []))
                indicators['cold_digits'] = len(freq.get('cold_digits', []))
                
                # Calculate deviation from uniform
                frequencies = freq.get('frequencies', {})
                if frequencies:
                    expected = 0.1
                    deviations = [abs(freq - expected) for freq in frequencies.values()]
                    indicators['frequency_deviation'] = np.mean(deviations) if deviations else 0
            
            # Confidence indicators
            if 'confidence' in analysis.__dict__:
                conf = analysis.confidence
                indicators['overall_confidence'] = conf.get('overall', 0)
            
            # Summary indicators
            if 'summary' in analysis.__dict__:
                summary = analysis.summary
                indicators['total_ticks'] = summary.get('total_ticks', 0)
                indicators['is_random'] = 1 if summary.get('is_random', False) else 0
            
        except Exception as e:
            logger.warning(f"Error extracting indicators: {e}")
        
        return indicators
    
    def _determine_state(
        self, 
        indicators: Dict[str, float], 
        analysis: ComprehensiveAnalysis
    ) -> Tuple[MarketState, float, List[str]]:
        """
        Determine market state based on indicators.
        
        Args:
            indicators: Extracted indicators
            analysis: Comprehensive analysis
            
        Returns:
            Tuple[MarketState, float, List[str]]: State, confidence, evidence
        """
        evidence = []
        scores = {}
        
        # Calculate score for each state
        scores[MarketState.CALM] = self._score_calm(indicators)
        scores[MarketState.RANDOM] = self._score_random(indicators)
        scores[MarketState.TRENDING] = self._score_trending(indicators)
        scores[MarketState.VOLATILE] = self._score_volatile(indicators)
        scores[MarketState.CHAOTIC] = self._score_chaotic(indicators)
        scores[MarketState.MEAN_REVERTING] = self._score_mean_reverting(indicators)
        scores[MarketState.MOMENTUM_DRIVEN] = self._score_momentum(indicators)
        
        # Get best state
        best_state = max(scores, key=scores.get)
        confidence = scores[best_state]
        
        # Collect evidence
        evidence = self._collect_evidence(best_state, indicators, analysis)
        
        return best_state, confidence, evidence
    
    def _score_calm(self, indicators: Dict[str, float]) -> float:
        """Score for calm market state."""
        score = 0.0
        
        # Low volatility
        if indicators.get('volatility', 0) < self.thresholds['calm_volatility']:
            score += 0.4
        
        # Low entropy (predictable)
        if indicators.get('entropy', 0) < 2.0:
            score += 0.2
        
        # Weak or no trend
        if indicators.get('trend_strength', 0) < 0.3:
            score += 0.2
        
        # Low momentum
        if indicators.get('momentum_strength', 0) < 0.3:
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_random(self, indicators: Dict[str, float]) -> float:
        """Score for random market state."""
        score = 0.0
        
        # High entropy (random)
        entropy = indicators.get('entropy', 0)
        if self.thresholds['random_entropy_low'] < entropy < self.thresholds['random_entropy_high']:
            score += 0.3
        
        # High randomness score
        if indicators.get('randomness_score', 0) > 0.5:
            score += 0.2
        
        # Weak trend
        if indicators.get('trend_strength', 0) < 0.4:
            score += 0.2
        
        # No strong patterns
        if indicators.get('pattern_confidence', 0) < 0.3:
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_trending(self, indicators: Dict[str, float]) -> float:
        """Score for trending market state."""
        score = 0.0
        
        # Strong trend
        if indicators.get('trend_strength', 0) > self.thresholds['trend_strength']:
            score += 0.4
        
        # High R-squared (linear trend)
        if indicators.get('r_squared', 0) > 0.7:
            score += 0.3
        
        # Consistent direction
        if indicators.get('trend_direction', 0) != 0:
            score += 0.2
        
        # Low randomness
        if indicators.get('randomness_score', 0) < 0.4:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_volatile(self, indicators: Dict[str, float]) -> float:
        """Score for volatile market state."""
        score = 0.0
        
        # High volatility
        if indicators.get('volatility', 0) > self.thresholds['volatile_volatility']:
            score += 0.4
        
        # High volatility ratio
        if indicators.get('volatility_ratio', 0) > 0.5:
            score += 0.2
        
        # High entropy (unpredictable)
        if indicators.get('entropy', 0) > 2.5:
            score += 0.2
        
        # Mixed patterns
        if 0.3 < indicators.get('pattern_confidence', 0) < 0.7:
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_chaotic(self, indicators: Dict[str, float]) -> float:
        """Score for chaotic market state."""
        score = 0.0
        
        # Very high entropy
        if indicators.get('entropy', 0) > 3.0:
            score += 0.3
        
        # High randomness
        if indicators.get('randomness_score', 0) > self.thresholds['chaotic_entropy']:
            score += 0.3
        
        # High volatility
        if indicators.get('volatility', 0) > self.thresholds['volatile_volatility'] * 1.5:
            score += 0.2
        
        # No clear patterns
        if indicators.get('pattern_confidence', 0) < 0.2:
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_mean_reverting(self, indicators: Dict[str, float]) -> float:
        """Score for mean reverting market state."""
        score = 0.0
        
        # High mean reversion score
        if indicators.get('mean_reversion_score', 0) > self.thresholds['mean_reversion']:
            score += 0.4
        
        # Low half-life (quick reversion)
        if indicators.get('half_life', 0) < 5:
            score += 0.3
        
        # Moderate volatility
        if self.thresholds['calm_volatility'] < indicators.get('volatility', 0) < self.thresholds['volatile_volatility']:
            score += 0.2
        
        # No strong trend
        if indicators.get('trend_strength', 0) < 0.4:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_momentum(self, indicators: Dict[str, float]) -> float:
        """Score for momentum driven market state."""
        score = 0.0
        
        # Strong momentum
        if indicators.get('momentum_strength', 0) > self.thresholds['momentum_strength']:
            score += 0.4
        
        # Clear direction
        if indicators.get('momentum_direction', 0) != 0:
            score += 0.3
        
        # Moderate volatility
        if 0.02 < indicators.get('volatility', 0) < 0.08:
            score += 0.2
        
        # Low entropy (predictable direction)
        if indicators.get('entropy', 0) < 2.5:
            score += 0.1
        
        return min(score, 1.0)
    
    def _collect_evidence(
        self, 
        state: MarketState, 
        indicators: Dict[str, float],
        analysis: ComprehensiveAnalysis
    ) -> List[str]:
        """
        Collect evidence supporting the classification.
        
        Args:
            state: Classified market state
            indicators: Extracted indicators
            analysis: Comprehensive analysis
            
        Returns:
            List[str]: Evidence statements
        """
        evidence = []
        
        # State-specific evidence
        if state == MarketState.CALM:
            if indicators.get('volatility', 0) < 0.02:
                evidence.append("Very low volatility detected")
            if indicators.get('entropy', 0) < 2.0:
                evidence.append("Low entropy indicates predictable patterns")
            if indicators.get('trend_strength', 0) < 0.3:
                evidence.append("No strong trend direction")
        
        elif state == MarketState.RANDOM:
            if indicators.get('randomness_score', 0) > 0.5:
                evidence.append("High randomness score")
            if 0.3 < indicators.get('entropy', 0) < 0.7:
                evidence.append("Moderate entropy indicates random behavior")
            if indicators.get('pattern_confidence', 0) < 0.3:
                evidence.append("No strong patterns detected")
        
        elif state == MarketState.TRENDING:
            if indicators.get('trend_strength', 0) > 0.6:
                evidence.append(f"Strong trend with strength {indicators['trend_strength']:.2f}")
            if indicators.get('r_squared', 0) > 0.7:
                evidence.append("High R-squared indicates linear trend")
            direction = "up" if indicators.get('trend_direction', 0) > 0 else "down"
            evidence.append(f"Clear {direction}ward trend direction")
        
        elif state == MarketState.VOLATILE:
            if indicators.get('volatility', 0) > 0.05:
                evidence.append(f"High volatility: {indicators['volatility']:.3f}")
            if indicators.get('entropy', 0) > 2.5:
                evidence.append("High entropy indicates unpredictability")
            if 0.3 < indicators.get('pattern_confidence', 0) < 0.7:
                evidence.append("Mixed patterns detected")
        
        elif state == MarketState.CHAOTIC:
            if indicators.get('entropy', 0) > 3.0:
                evidence.append("Very high entropy (>3.0)")
            if indicators.get('randomness_score', 0) > 0.85:
                evidence.append("Very high randomness score")
            if indicators.get('pattern_confidence', 0) < 0.2:
                evidence.append("No discernible patterns")
        
        elif state == MarketState.MEAN_REVERTING:
            if indicators.get('mean_reversion_score', 0) > 0.5:
                evidence.append(f"Strong mean reversion: {indicators['mean_reversion_score']:.2f}")
            if indicators.get('half_life', 0) < 5:
                evidence.append("Rapid mean reversion detected")
        
        elif state == MarketState.MOMENTUM_DRIVEN:
            if indicators.get('momentum_strength', 0) > 0.6:
                evidence.append(f"Strong momentum: {indicators['momentum_strength']:.2f}")
            direction = "up" if indicators.get('momentum_direction', 0) > 0 else "down"
            evidence.append(f"Clear {direction}ward momentum")
        
        # Add general evidence
        if indicators.get('overall_confidence', 0) > 0.7:
            evidence.append("High overall confidence in analysis")
        
        # Add digit distribution evidence
        if 'hot_digits' in indicators and indicators['hot_digits'] > 0:
            evidence.append(f"Hot digits detected: {indicators['hot_digits']} digits appear more frequently")
        
        if 'cold_digits' in indicators and indicators['cold_digits'] > 0:
            evidence.append(f"Cold digits detected: {indicators['cold_digits']} digits appear less frequently")
        
        # Add streak evidence
        if indicators.get('max_streak', 0) > 3:
            evidence.append(f"Long streak detected: {indicators['max_streak']} consecutive identical digits")
        
        return evidence
    
    def _calculate_risk_level(self, state: MarketState, indicators: Dict[str, float]) -> RiskLevel:
        """
        Calculate risk level based on market state and indicators.
        
        Args:
            state: Market state
            indicators: Extracted indicators
            
        Returns:
            RiskLevel: Calculated risk level
        """
        # Base risk by state
        state_risk = {
            MarketState.CALM: RiskLevel.VERY_LOW,
            MarketState.RANDOM: RiskLevel.MODERATE,
            MarketState.TRENDING: RiskLevel.MODERATE,
            MarketState.VOLATILE: RiskLevel.HIGH,
            MarketState.CHAOTIC: RiskLevel.VERY_HIGH,
            MarketState.MEAN_REVERTING: RiskLevel.LOW,
            MarketState.MOMENTUM_DRIVEN: RiskLevel.MODERATE,
        }
        
        base_risk = state_risk.get(state, RiskLevel.MODERATE)
        
        # Adjust based on indicators
        risk_score = self._risk_score(base_risk)
        
        # Adjust for volatility
        volatility = indicators.get('volatility', 0)
        if volatility > 0.1:
            risk_score = min(risk_score + 0.3, 1.0)
        elif volatility > 0.05:
            risk_score = min(risk_score + 0.2, 1.0)
        
        # Adjust for entropy
        entropy = indicators.get('entropy', 0)
        if entropy > 3.0:
            risk_score = min(risk_score + 0.2, 1.0)
        
        # Adjust for trend strength
        trend = indicators.get('trend_strength', 0)
        if trend > 0.7:
            risk_score = max(risk_score - 0.1, 0.0)  # Trend reduces risk
        
        # Convert back to RiskLevel
        if risk_score < 0.2:
            return RiskLevel.VERY_LOW
        elif risk_score < 0.4:
            return RiskLevel.LOW
        elif risk_score < 0.6:
            return RiskLevel.MODERATE
        elif risk_score < 0.8:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    def _risk_score(self, risk_level: RiskLevel) -> float:
        """Convert risk level to numeric score."""
        scores = {
            RiskLevel.VERY_LOW: 0.1,
            RiskLevel.LOW: 0.3,
            RiskLevel.MODERATE: 0.5,
            RiskLevel.HIGH: 0.7,
            RiskLevel.VERY_HIGH: 0.9,
        }
        return scores.get(risk_level, 0.5)
    
    def _generate_explanation(
        self, 
        state: MarketState, 
        indicators: Dict[str, float],
        evidence: List[str]
    ) -> str:
        """
        Generate a human-readable explanation of the market state.
        
        Args:
            state: Market state
            indicators: Extracted indicators
            evidence: Evidence statements
            
        Returns:
            str: Explanation text
        """
        state_desc = MARKET_STATE_DESCRIPTIONS.get(state)
        emoji = state_desc.get('emoji', '📊') if state_desc else '📊'
        
        explanation = f"{emoji} **Market State: {state.value.upper()}**\n\n"
        
        # Add description
        if state_desc:
            explanation += f"{state_desc.get('description', '')}\n\n"
        
        # Add key indicators
        explanation += "**Key Indicators:**\n"
        if 'volatility' in indicators:
            explanation += f"• Volatility: {indicators['volatility']:.4f}\n"
        if 'entropy' in indicators:
            explanation += f"• Entropy: {indicators['entropy']:.2f}\n"
        if 'trend_strength' in indicators:
            explanation += f"• Trend Strength: {indicators['trend_strength']:.2f}\n"
        if 'momentum_strength' in indicators:
            explanation += f"• Momentum: {indicators['momentum_strength']:.2f}\n"
        if 'overall_confidence' in indicators:
            explanation += f"• Analysis Confidence: {indicators['overall_confidence']:.2%}\n\n"
        
        # Add evidence
        if evidence:
            explanation += "**Supporting Evidence:**\n"
            for ev in evidence[:5]:  # Limit to 5 evidence points
                explanation += f"• {ev}\n"
        
        # Add risk level
        risk_level = self._calculate_risk_level(state, indicators)
        explanation += f"\n**Risk Level: {risk_level.value.upper()}**"
        
        return explanation
    
    def _empty_analysis(self) -> MarketStateAnalysis:
        """Return an empty analysis result."""
        return MarketStateAnalysis(
            state=MarketState.RANDOM,
            confidence=0.0,
            risk_level=RiskLevel.MODERATE,
            indicators={},
            evidence=["Insufficient data for classification"],
            explanation="Insufficient data to classify market state. Please wait for more ticks.",
            timestamp=datetime.now()
        )
    
    def get_state_history(self, limit: int = 100) -> List[MarketStateAnalysis]:
        """
        Get historical state classifications.
        
        Args:
            limit: Maximum number of states to return
            
        Returns:
            List[MarketStateAnalysis]: Historical states
        """
        return self._state_history[-limit:]
    
    def get_state_transitions(self) -> List[Tuple[MarketState, MarketState]]:
        """
        Get state transition history.
        
        Returns:
            List[Tuple[MarketState, MarketState]]: State transitions
        """
        transitions = []
        for i in range(1, len(self._state_history)):
            transitions.append((
                self._state_history[i-1].state,
                self._state_history[i].state
            ))
        return transitions
    
    def get_state_distribution(self) -> Dict[MarketState, int]:
        """
        Get distribution of states in history.
        
        Returns:
            Dict[MarketState, int]: State distribution counts
        """
        distribution = {state: 0 for state in MarketState}
        for analysis in self._state_history:
            distribution[analysis.state] += 1
        return distribution
