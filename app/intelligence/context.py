"""
Historical Context Module
Provides historical comparison and context for market analysis.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from collections import deque

from ..core.types import Tick
from ..core.logger import get_logger

logger = get_logger(__name__)


class HistoricalContext:
    """
    Manages historical context for market analysis.
    Compares current market conditions with historical patterns.
    """
    
    def __init__(self, max_history: int = 10000):
        """
        Initialize the historical context manager.
        
        Args:
            max_history: Maximum number of historical ticks to store
        """
        self.max_history = max_history
        self._ticks: deque = deque(maxlen=max_history)
        self._snapshots: List[Dict[str, Any]] = []
        self._max_snapshots = 100
        
        logger.info(f"HistoricalContext initialized with max_history={max_history}")
    
    def add_ticks(self, ticks: List[Tick]):
        """
        Add ticks to historical context.
        
        Args:
            ticks: List of ticks to add
        """
        for tick in ticks:
            self._ticks.append(tick)
    
    def get_historical_comparison(self, current_ticks: List[Tick]) -> Dict[str, Any]:
        """
        Compare current ticks with historical data.
        
        Args:
            current_ticks: List of current ticks
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        if len(self._ticks) < 10 or len(current_ticks) < 10:
            return self._empty_comparison()
        
        try:
            # Extract features
            current_features = self._extract_features(current_ticks)
            historical_features = self._extract_features(list(self._ticks))
            
            # Calculate similarities and differences
            comparison = {
                'timestamp': datetime.now(),
                'similarity_score': self._calculate_similarity(current_features, historical_features),
                'differences': self._calculate_differences(current_features, historical_features),
                'historical_context': self._generate_context(current_features, historical_features),
                'anomaly_score': self._calculate_anomaly_score(current_features, historical_features),
                'confidence': self._calculate_comparison_confidence(len(current_ticks), len(self._ticks))
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error in historical comparison: {e}")
            return self._empty_comparison()
    
    def _extract_features(self, ticks: List[Tick]) -> Dict[str, Any]:
        """Extract features from ticks for comparison."""
        if not ticks:
            return {}
        
        digits = [t.last_digit for t in ticks]
        prices = [float(t.price) for t in ticks]
        
        # Calculate digit distribution
        from collections import Counter
        counts = Counter(digits)
        distribution = {i: counts.get(i, 0) / len(digits) for i in range(10)}
        
        # Calculate price statistics
        price_mean = np.mean(prices)
        price_std = np.std(prices)
        
        # Calculate transition probabilities
        transitions = self._calculate_transitions(digits)
        
        # Calculate streaks
        max_streak = self._calculate_max_streak(digits)
        
        # Calculate entropy
        probs = [freq for freq in distribution.values() if freq > 0]
        entropy = -sum(p * np.log2(p) for p in probs) if probs else 0
        
        return {
            'digit_distribution': distribution,
            'price_mean': price_mean,
            'price_std': price_std,
            'transitions': transitions,
            'max_streak': max_streak,
            'entropy': entropy,
            'sample_size': len(ticks)
        }
    
    def _calculate_transitions(self, digits: List[int]) -> Dict[str, float]:
        """Calculate transition probabilities."""
        if len(digits) < 2:
            return {'match': 0.0, 'differ': 1.0}
        
        matches = 0
        total = len(digits) - 1
        
        for i in range(total):
            if digits[i] == digits[i+1]:
                matches += 1
        
        return {
            'match': matches / total if total > 0 else 0,
            'differ': (total - matches) / total if total > 0 else 1
        }
    
    def _calculate_max_streak(self, digits: List[int]) -> int:
        """Calculate maximum consecutive streak."""
        if not digits:
            return 0
        
        max_streak = 1
        current_streak = 1
        
        for i in range(1, len(digits)):
            if digits[i] == digits[i-1]:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1
        
        return max_streak
    
    def _calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between two feature sets."""
        if not features1 or not features2:
            return 0.0
        
        # Compare digit distributions
        dist1 = features1.get('digit_distribution', {})
        dist2 = features2.get('digit_distribution', {})
        
        # Cosine similarity
        vec1 = [dist1.get(i, 0) for i in range(10)]
        vec2 = [dist2.get(i, 0) for i in range(10)]
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 > 0 and norm2 > 0:
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        else:
            similarity = 0.0
        
        # Compare transition probabilities
        trans1 = features1.get('transitions', {})
        trans2 = features2.get('transitions', {})
        
        match_diff = abs(trans1.get('match', 0) - trans2.get('match', 0))
        transition_similarity = 1 - min(match_diff, 1.0)
        
        # Weighted combination
        combined = similarity * 0.7 + transition_similarity * 0.3
        
        return max(0, min(combined, 1.0))
    
    def _calculate_differences(self, features1: Dict, features2: Dict) -> Dict[str, Any]:
        """Calculate differences between feature sets."""
        if not features1 or not features2:
            return {}
        
        differences = {}
        
        # Digit distribution differences
        dist1 = features1.get('digit_distribution', {})
        dist2 = features2.get('digit_distribution', {})
        
        digit_diffs = {}
        for digit in range(10):
            digit_diffs[digit] = dist2.get(digit, 0) - dist1.get(digit, 0)
        differences['digit_distribution'] = digit_diffs
        
        # Price differences
        if 'price_mean' in features1 and 'price_mean' in features2:
            differences['price_change'] = features2['price_mean'] - features1['price_mean']
            differences['price_change_pct'] = (
                (features2['price_mean'] - features1['price_mean']) / features1['price_mean'] * 100
                if features1['price_mean'] != 0 else 0
            )
        
        # Transition differences
        if 'transitions' in features1 and 'transitions' in features2:
            trans1 = features1['transitions']
            trans2 = features2['transitions']
            differences['transition_change'] = trans2.get('match', 0) - trans1.get('match', 0)
        
        # Entropy differences
        if 'entropy' in features1 and 'entropy' in features2:
            differences['entropy_change'] = features2['entropy'] - features1['entropy']
        
        # Streak differences
        if 'max_streak' in features1 and 'max_streak' in features2:
            differences['streak_change'] = features2['max_streak'] - features1['max_streak']
        
        return differences
    
    def _generate_context(self, current: Dict, historical: Dict) -> str:
        """Generate contextual description."""
        context_parts = []
        
        # Price context
        if 'price_mean' in current and 'price_mean' in historical:
            change_pct = (
                (current['price_mean'] - historical['price_mean']) / historical['price_mean'] * 100
                if historical['price_mean'] != 0 else 0
            )
            
            if abs(change_pct) > 1:
                context_parts.append(f"Price level changed {change_pct:.1f}% from historical average")
            else:
                context_parts.append("Price level consistent with historical average")
        
        # Digit distribution context
        dist_current = current.get('digit_distribution', {})
        dist_historical = historical.get('digit_distribution', {})
        
        significant_changes = []
        for digit in range(10):
            diff = abs(dist_current.get(digit, 0) - dist_historical.get(digit, 0))
            if diff > 0.02:  # 2% difference
                significant_changes.append(f"Digit {digit} changed by {diff:.1%}")
        
        if significant_changes:
            context_parts.append(f"Notable changes: {', '.join(significant_changes[:3])}")
        else:
            context_parts.append("Digit distribution stable compared to historical patterns")
        
        # Transition context
        if 'transitions' in current and 'transitions' in historical:
            current_match = current['transitions'].get('match', 0)
            hist_match = historical['transitions'].get('match', 0)
            
            if abs(current_match - hist_match) > 0.05:
                direction = "increased" if current_match > hist_match else "decreased"
                context_parts.append(f"Match probability {direction} by {abs(current_match - hist_match):.1%}")
        
        # Randomness context
        if 'entropy' in current and 'entropy' in historical:
            if abs(current['entropy'] - historical['entropy']) > 0.5:
                direction = "increased" if current['entropy'] > historical['entropy'] else "decreased"
                context_parts.append(f"Randomness {direction} significantly")
        
        return ". ".join(context_parts) if context_parts else "Market conditions similar to historical patterns"
    
    def _calculate_anomaly_score(self, current: Dict, historical: Dict) -> float:
        """Calculate anomaly score for current conditions."""
        if not current or not historical:
            return 0.0
        
        score = 0.0
        
        # Distribution anomaly
        dist_current = current.get('digit_distribution', {})
        dist_historical = historical.get('digit_distribution', {})
        
        deviation_sum = 0
        for digit in range(10):
            diff = abs(dist_current.get(digit, 0) - dist_historical.get(digit, 0))
            deviation_sum += diff
        avg_deviation = deviation_sum / 10
        
        score += min(avg_deviation * 5, 0.5)
        
        # Transition anomaly
        trans_current = current.get('transitions', {})
        trans_historical = historical.get('transitions', {})
        
        match_diff = abs(
            trans_current.get('match', 0) - trans_historical.get('match', 0)
        )
        score += min(match_diff * 2, 0.3)
        
        # Entropy anomaly
        if 'entropy' in current and 'entropy' in historical:
            entropy_diff = abs(current['entropy'] - historical['entropy'])
            score += min(entropy_diff / 3.32, 0.2)  # Max entropy = 3.32
        
        return min(score, 1.0)
    
    def _calculate_comparison_confidence(self, current_size: int, historical_size: int) -> float:
        """Calculate confidence in the comparison."""
        confidence = 0.0
        
        # Current sample size
        current_score = min(current_size / 50, 1.0)
        confidence += current_score * 0.4
        
        # Historical sample size
        historical_score = min(historical_size / 200, 1.0)
        confidence += historical_score * 0.4
        
        # Historical diversity
        if len(self._snapshots) > 5:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _empty_comparison(self) -> Dict[str, Any]:
        """Return empty comparison."""
        return {
            'timestamp': datetime.now(),
            'similarity_score': 0.0,
            'differences': {},
            'historical_context': 'Insufficient historical data',
            'anomaly_score': 0.0,
            'confidence': 0.0
        }
    
    def take_snapshot(self):
        """
        Take a snapshot of current state for future comparison.
        """
        if len(self._ticks) > 0:
            features = self._extract_features(list(self._ticks))
            features['timestamp'] = datetime.now()
            self._snapshots.append(features)
            
            if len(self._snapshots) > self._max_snapshots:
                self._snapshots = self._snapshots[-self._max_snapshots:]
            
            logger.debug(f"Snapshot taken ({len(self._snapshots)} total)")
    
    def get_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get historical snapshots.
        
        Args:
            limit: Maximum number of snapshots
            
        Returns:
            List[Dict[str, Any]]: Historical snapshots
        """
        return self._snapshots[-limit:]
    
    def clear(self):
        """Clear all historical data."""
        self._ticks.clear()
        self._snapshots.clear()
        logger.info("Historical context cleared")