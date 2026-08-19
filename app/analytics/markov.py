"""
Markov Chain Analysis Module
Implements Markov chain analysis for digit transitions and predictions.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime
from dataclasses import dataclass

from core.types import TransitionMatrix
from core.logger import get_logger


logger = get_logger(__name__)


@dataclass
class MarkovResult:
    """Results from Markov chain analysis."""
    transition_matrix: np.ndarray
    stationary_distribution: np.ndarray
    entropy_rate: float
    mixing_time: int
    eigenvalues: np.ndarray
    confidence: float
    timestamp: datetime


class MarkovAnalyzer:
    """
    Performs Markov chain analysis on digit sequences.
    Calculates transition probabilities, stationary distributions,
    and entropy rates.
    """
    
    def __init__(self, order: int = 1):
        """
        Initialize the Markov analyzer.
        
        Args:
            order: Markov order (1 = first-order Markov)
        """
        self.order = order
        self._cache = {}
        logger.info(f"MarkovAnalyzer initialized with order {order}")
    
    def analyze(self, digits: List[int]) -> MarkovResult:
        """
        Perform Markov chain analysis on digit sequence.
        
        Args:
            digits: List of digit values
            
        Returns:
            MarkovResult: Complete Markov analysis results
        """
        if len(digits) < self.order + 1:
            return self._empty_result()
        
        # Build transition matrix
        matrix = self._build_transition_matrix(digits)
        
        # Calculate stationary distribution
        stationary = self._calculate_stationary_distribution(matrix)
        
        # Calculate entropy rate
        entropy_rate = self._calculate_entropy_rate(matrix, stationary)
        
        # Calculate mixing time
        mixing_time = self._calculate_mixing_time(matrix)
        
        # Calculate eigenvalues
        eigenvalues = self._calculate_eigenvalues(matrix)
        
        # Calculate confidence
        confidence = self._calculate_confidence(matrix, len(digits))
        
        return MarkovResult(
            transition_matrix=matrix,
            stationary_distribution=stationary,
            entropy_rate=entropy_rate,
            mixing_time=mixing_time,
            eigenvalues=eigenvalues,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    def _build_transition_matrix(self, digits: List[int]) -> np.ndarray:
        """
        Build the transition probability matrix from digit sequence.
        
        Args:
            digits: List of digits
            
        Returns:
            np.ndarray: 10x10 transition matrix
        """
        matrix = np.zeros((10, 10))
        
        for i in range(len(digits) - self.order):
            # Get current state (digit or sequence of digits)
            current = digits[i:i + self.order]
            next_digit = digits[i + self.order]
            
            # For order > 1, we need to handle multi-digit states
            if self.order == 1:
                from_state = current[0]
                matrix[from_state][next_digit] += 1
            else:
                # For higher orders, we flatten the state
                # This is a simplified approach; for production, we'd use a more
                # sophisticated state representation
                from_state = self._state_to_index(current)
                if from_state < 10:  # Only handle order 1 for simplicity in this version
                    matrix[from_state][next_digit] += 1
                else:
                    # For order > 1, we just use the last digit as state
                    matrix[current[-1]][next_digit] += 1
        
        # Normalize rows
        row_sums = matrix.sum(axis=1, keepdims=True)
        matrix = np.divide(matrix, row_sums, where=row_sums != 0)
        
        return matrix
    
    def _state_to_index(self, state: List[int]) -> int:
        """
        Convert a multi-digit state to an index.
        
        Args:
            state: List of digits
            
        Returns:
            int: Index representing the state
        """
        if len(state) == 1:
            return state[0]
        else:
            # For order > 1, we return a value > 9 to indicate higher order
            return 10 + sum(state)  # Simplified mapping
    
    def _calculate_stationary_distribution(self, matrix: np.ndarray) -> np.ndarray:
        """
        Calculate the stationary distribution using power iteration.
        
        Args:
            matrix: Transition matrix
            
        Returns:
            np.ndarray: Stationary distribution
        """
        # Check if matrix is valid
        if matrix.shape[0] != matrix.shape[1]:
            return np.zeros(matrix.shape[0])
        
        # Power iteration
        dist = np.ones(matrix.shape[0]) / matrix.shape[0]
        
        for _ in range(1000):
            new_dist = dist @ matrix
            if np.linalg.norm(new_dist - dist) < 1e-6:
                break
            dist = new_dist
        
        # Normalize
        dist = dist / dist.sum()
        return dist
    
    def _calculate_entropy_rate(self, matrix: np.ndarray, stationary: np.ndarray) -> float:
        """
        Calculate the entropy rate of the Markov chain.
        
        Args:
            matrix: Transition matrix
            stationary: Stationary distribution
            
        Returns:
            float: Entropy rate in bits
        """
        entropy = 0.0
        
        for i in range(len(stationary)):
            if stationary[i] > 0:
                for j in range(matrix.shape[1]):
                    if matrix[i][j] > 0:
                        entropy += stationary[i] * matrix[i][j] * np.log2(1.0 / matrix[i][j])
        
        return entropy
    
    def _calculate_mixing_time(self, matrix: np.ndarray, tolerance: float = 0.01) -> int:
        """
        Calculate the mixing time of the Markov chain.
        
        Args:
            matrix: Transition matrix
            tolerance: Tolerance for convergence
            
        Returns:
            int: Mixing time in steps
        """
        # Calculate eigenvalues
        eigenvalues = np.linalg.eigvals(matrix)
        
        # Find second largest eigenvalue magnitude
        sorted_eigenvalues = np.sort(np.abs(eigenvalues))[::-1]
        
        if len(sorted_eigenvalues) < 2:
            return 0
        
        second_largest = sorted_eigenvalues[1]
        
        # Calculate mixing time
        if second_largest < 1.0:
            mixing_time = int(np.log(tolerance) / np.log(second_largest))
            return max(mixing_time, 0)
        
        return 0
    
    def _calculate_eigenvalues(self, matrix: np.ndarray) -> np.ndarray:
        """
        Calculate eigenvalues of the transition matrix.
        
        Args:
            matrix: Transition matrix
            
        Returns:
            np.ndarray: Eigenvalues
        """
        try:
            eigenvalues = np.linalg.eigvals(matrix)
            return eigenvalues
        except:
            return np.array([])
    
    def _calculate_confidence(self, matrix: np.ndarray, sample_size: int) -> float:
        """
        Calculate confidence in the Markov analysis.
        
        Args:
            matrix: Transition matrix
            sample_size: Number of samples
            
        Returns:
            float: Confidence score (0-1)
        """
        confidence = 0.0
        
        # Sample size factor
        sample_score = min(sample_size / 100.0, 1.0)
        confidence += sample_score * 0.3
        
        # Matrix stability factor
        row_sums = matrix.sum(axis=1)
        stable_rows = np.sum(row_sums > 0.5)  # Rows with some probability mass
        stability_score = stable_rows / matrix.shape[0]
        confidence += stability_score * 0.4
        
        # Entropy factor (higher entropy = more random = less confidence)
        entropy = self._calculate_entropy_rate(matrix, np.ones(matrix.shape[0]) / matrix.shape[0])
        entropy_score = 1.0 - min(entropy / 3.32, 1.0)  # 3.32 = max entropy for 10 digits
        confidence += entropy_score * 0.3
        
        return min(confidence, 1.0)
    
    def _empty_result(self) -> MarkovResult:
        """Return an empty analysis result."""
        return MarkovResult(
            transition_matrix=np.zeros((10, 10)),
            stationary_distribution=np.zeros(10),
            entropy_rate=0.0,
            mixing_time=0,
            eigenvalues=np.array([]),
            confidence=0.0,
            timestamp=datetime.now()
        )
    
    def predict_next_digit(self, digits: List[int]) -> Dict[int, float]:
        """
        Predict the next digit probabilities based on Markov chain.
        
        Args:
            digits: Recent digits
            
        Returns:
            Dict[int, float]: Probability for each next digit
        """
        if len(digits) < self.order:
            return {i: 0.1 for i in range(10)}
        
        # Get current state
        recent_digits = digits[-self.order:]
        
        # Get transition probabilities
        analysis = self.analyze(digits)
        
        if self.order == 1:
            current = recent_digits[-1]
            probs = analysis.transition_matrix[current]
        else:
            # For higher order, use last digit
            current = recent_digits[-1]
            probs = analysis.transition_matrix[current]
        
        return {i: probs[i] for i in range(10)}
    
    def get_transition_probability(self, from_digit: int, to_digit: int, digits: List[int]) -> float:
        """
        Get the probability of transitioning from one digit to another.
        
        Args:
            from_digit: Source digit
            to_digit: Target digit
            digits: Historical digits
            
        Returns:
            float: Transition probability
        """
        analysis = self.analyze(digits)
        return analysis.transition_matrix[from_digit][to_digit]
