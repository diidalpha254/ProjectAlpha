"""
Entropy and Randomness Analysis Module
Measures randomness, entropy, and information content in digit sequences.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from collections import Counter
from datetime import datetime
from dataclasses import dataclass

from ..core.types import EntropyAnalysis
from ..core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RandomnessResult:
    """Results from randomness analysis."""
    entropy: float
    normalized_entropy: float
    randomness_score: float
    is_random: bool
    distribution: Dict[int, float]
    chi_square_stat: float
    chi_square_p: float
    auto_correlation: List[float]
    timestamp: datetime


class EntropyAnalyzer:
    """
    Analyzes entropy and randomness in digit sequences.
    Uses Shannon entropy, chi-square tests, and auto-correlation.
    """
    
    def __init__(self):
        """Initialize the entropy analyzer."""
        self._cache = {}
        logger.info("EntropyAnalyzer initialized")
    
    def analyze(self, digits: List[int]) -> EntropyAnalysis:
        """
        Perform entropy analysis on digit sequence.
        
        Args:
            digits: List of digits
            
        Returns:
            EntropyAnalysis: Complete entropy analysis
        """
        if not digits:
            return self._empty_analysis()
        
        # Calculate distribution
        distribution = self._calculate_distribution(digits)
        
        # Calculate entropy
        entropy = self._calculate_entropy(distribution)
        
        # Calculate normalized entropy (0-1)
        max_entropy = np.log2(10)  # 10 possible digits
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        # Calculate randomness score (1 = random, 0 = deterministic)
        randomness_score = normalized_entropy
        
        # Determine if sequence appears random
        is_random = randomness_score > 0.85
        
        return EntropyAnalysis(
            entropy=entropy,
            normalized_entropy=normalized_entropy,
            randomness_score=randomness_score,
            is_random=is_random,
            distribution=distribution,
            timestamp=datetime.now()
        )
    
    def _calculate_distribution(self, digits: List[int]) -> Dict[int, float]:
        """Calculate probability distribution of digits."""
        counts = Counter(digits)
        total = len(digits)
        return {i: counts.get(i, 0) / total for i in range(10)}
    
    def _calculate_entropy(self, distribution: Dict[int, float]) -> float:
        """
        Calculate Shannon entropy.
        
        Args:
            distribution: Probability distribution
            
        Returns:
            float: Entropy in bits
        """
        entropy = 0.0
        for prob in distribution.values():
            if prob > 0:
                entropy -= prob * np.log2(prob)
        return entropy
    
    def _empty_analysis(self) -> EntropyAnalysis:
        """Return an empty analysis result."""
        return EntropyAnalysis(
            entropy=0.0,
            normalized_entropy=0.0,
            randomness_score=0.0,
            is_random=False,
            distribution={i: 0.0 for i in range(10)},
            timestamp=datetime.now()
        )
    
    def chi_square_test(self, digits: List[int]) -> Tuple[float, float]:
        """
        Perform chi-square test for uniform distribution.
        
        Args:
            digits: List of digits
            
        Returns:
            Tuple[float, float]: (chi-square statistic, p-value)
        """
        if not digits:
            return (0.0, 1.0)
        
        # Count digits
        counts = [0] * 10
        for digit in digits:
            counts[digit] += 1
        
        # Expected count for each digit
        expected = len(digits) / 10.0
        
        # Calculate chi-square
        chi_square = sum((count - expected) ** 2 / expected for count in counts)
        
        # Calculate p-value using chi-square distribution approximation
        # Degrees of freedom = 9
        p_value = self._chi_square_cdf(chi_square, 9)
        
        return (chi_square, p_value)
    
    def _chi_square_cdf(self, x: float, df: int) -> float:
        """
        Approximate chi-square CDF.
        
        Args:
            x: Chi-square value
            df: Degrees of freedom
            
        Returns:
            float: P-value
        """
        # Simplified approximation using gamma function
        # For production, use scipy.stats.chi2
        import math
        
        if x <= 0:
            return 1.0
        
        # Basic approximation
        k = df / 2.0
        h = x / 2.0
        if h > 0 and k > 0:
            # Gamma function approximation
            gamma_k = math.gamma(k)
            p = (h ** (k - 1) * math.exp(-h)) / gamma_k
            # We'll return a rough approximation
            return min(1.0, p * 10)
        
        return 0.5
    
    def auto_correlation(self, digits: List[int], max_lag: int = 10) -> List[float]:
        """
        Calculate auto-correlation for different lags.
        
        Args:
            digits: List of digits
            max_lag: Maximum lag to calculate
            
        Returns:
            List[float]: Auto-correlation for each lag
        """
        if len(digits) < 2:
            return [0.0] * max_lag
        
        # Normalize digits
        mean = np.mean(digits)
        normalized = digits - mean
        
        correlations = []
        for lag in range(1, max_lag + 1):
            if len(normalized) <= lag:
                correlations.append(0.0)
                continue
            
            # Calculate correlation
            corr = np.corrcoef(normalized[:-lag], normalized[lag:])[0, 1]
            if np.isnan(corr):
                corr = 0.0
            correlations.append(corr)
        
        return correlations
    
    def runs_test(self, digits: List[int]) -> float:
        """
        Perform runs test for randomness.
        
        Args:
            digits: List of digits
            
        Returns:
            float: P-value for runs test
        """
        if len(digits) < 2:
            return 1.0
        
        # Count runs (consecutive equal digits)
        runs = 1
        for i in range(1, len(digits)):
            if digits[i] != digits[i-1]:
                runs += 1
        
        # Expected number of runs
        n = len(digits)
        expected_runs = (2 * n - 1) / 3.0
        
        # Variance of runs
        variance = (16 * n - 29) / 90.0
        
        # Z-score
        if variance > 0:
            z_score = (runs - expected_runs) / np.sqrt(variance)
            # Convert to p-value (two-tailed)
            p_value = 2 * (1 - self._normal_cdf(abs(z_score)))
            return min(p_value, 1.0)
        
        return 1.0
    
    def _normal_cdf(self, z: float) -> float:
        """
        Approximate normal CDF.
        
        Args:
            z: Z-score
            
        Returns:
            float: Probability
        """
        # Approximation using error function
        import math
        
        # Use the error function approximation
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911
        
        # Save sign
        sign = 1 if z >= 0 else -1
        z = abs(z)
        
        t = 1.0 / (1.0 + p * z)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-z * z / 2.0)
        
        return 0.5 * (1.0 + sign * y)
    
    def get_entropy_confidence(self, analysis: EntropyAnalysis) -> float:
        """
        Calculate confidence in entropy analysis.
        
        Args:
            analysis: Entropy analysis results
            
        Returns:
            float: Confidence score (0-1)
        """
        # High entropy = high randomness = high confidence in random state
        # Low entropy = low randomness = high confidence in patterns
        
        # Entropy-based confidence
        if analysis.entropy == 0:
            return 1.0  # Highly deterministic
        
        max_entropy = np.log2(10)
        entropy_ratio = analysis.entropy / max_entropy
        
        # Confidence is highest for very high or very low entropy
        if entropy_ratio > 0.8:
            return 0.9  # Very random
        elif entropy_ratio < 0.3:
            return 0.8  # Very patterned
        else:
            return 0.5  # Unclear