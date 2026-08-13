"""
Unit tests for Statistical Analytics Engine
"""

import unittest
import numpy as np
from datetime import datetime
from decimal import Decimal

from app.analytics.frequency import FrequencyAnalyzer
from app.analytics.markov import MarkovAnalyzer
from app.analytics.entropy import EntropyAnalyzer
from app.analytics.volatility import VolatilityAnalyzer
from app.analytics.patterns import PatternAnalyzer
from app.analytics.confidence import ConfidenceScorer
from app.analytics.engine import AnalyticsEngine
from app.core.types import Tick


class TestFrequencyAnalyzer(unittest.TestCase):
    """Test cases for FrequencyAnalyzer."""
    
    def setUp(self):
        self.analyzer = FrequencyAnalyzer()
    
    def test_analyze_uniform_distribution(self):
        """Test analysis of uniform distribution."""
        digits = [i % 10 for i in range(100)]
        result = self.analyzer.analyze(digits)
        
        # Each digit should appear ~10 times
        for digit in range(10):
            self.assertAlmostEqual(result.digit_counts[digit], 10, delta=3)
        
        # Hot and cold digits should be empty for uniform distribution
        self.assertEqual(len(result.hot_digits), 0)
        self.assertEqual(len(result.cold_digits), 0)
    
    def test_analyze_biased_distribution(self):
        """Test analysis of biased distribution."""
        digits = [0] * 50 + [i for i in range(1, 10) for _ in range(5)]
        result = self.analyzer.analyze(digits)
        
        # Digit 0 should be hot
        self.assertIn(0, result.hot_digits)
        
        # Other digits should be cold or normal
        self.assertTrue(len(result.cold_digits) > 0)
    
    def test_compare_windows(self):
        """Test window comparison."""
        window1 = [i % 10 for i in range(50)]
        window2 = [0] * 50  # All zeros
        
        comparison = self.analyzer.compare_windows(window1, window2)
        
        self.assertIn('differences', comparison)
        self.assertIn('similarity', comparison)
        self.assertLess(comparison['similarity'], 0.5)  # Should be quite different
    
    def test_confidence_score(self):
        """Test confidence score calculation."""
        digits = [i % 10 for i in range(100)]
        result = self.analyzer.analyze(digits)
        confidence = self.analyzer.get_confidence_score(result)
        
        # Uniform distribution should have low confidence
        self.assertLess(confidence, 0.5)


class TestMarkovAnalyzer(unittest.TestCase):
    """Test cases for MarkovAnalyzer."""
    
    def setUp(self):
        self.analyzer = MarkovAnalyzer(order=1)
    
    def test_transition_matrix(self):
        """Test transition matrix calculation."""
        # Create sequence with clear transitions
        digits = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
        result = self.analyzer.analyze(digits)
        
        matrix = result.transition_matrix
        self.assertEqual(matrix.shape, (10, 10))
        
        # 0 should transition to 1 with high probability
        self.assertGreater(matrix[0][1], 0.8)
        
        # 1 should transition to 0 with high probability
        self.assertGreater(matrix[1][0], 0.8)
    
    def test_stationary_distribution(self):
        """Test stationary distribution calculation."""
        digits = [i % 10 for i in range(200)]
        result = self.analyzer.analyze(digits)
        
        dist = result.stationary_distribution
        self.assertEqual(len(dist), 10)
        
        # For uniform sequence, stationary distribution should be uniform
        for p in dist:
            self.assertAlmostEqual(p, 0.1, delta=0.05)
    
    def test_predict_next_digit(self):
        """Test next digit prediction."""
        digits = [0, 1, 0, 1, 0, 1, 0, 1, 0]
        probs = self.analyzer.predict_next_digit(digits)
        
        # Should predict 1 with high probability
        self.assertGreater(probs[1], 0.5)
    
    def test_entropy_rate(self):
        """Test entropy rate calculation."""
        # Deterministic sequence should have low entropy
        digits = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
        result = self.analyzer.analyze(digits)
        self.assertLess(result.entropy_rate, 1.0)
        
        # Random sequence should have high entropy
        import random
        digits = [random.randint(0, 9) for _ in range(100)]
        result = self.analyzer.analyze(digits)
        self.assertGreater(result.entropy_rate, 2.0)


class TestEntropyAnalyzer(unittest.TestCase):
    """Test cases for EntropyAnalyzer."""
    
    def setUp(self):
        self.analyzer = EntropyAnalyzer()
    
    def test_entropy_calculation(self):
        """Test entropy calculation."""
        # Uniform distribution should have maximum entropy
        digits = [i % 10 for i in range(100)]
        result = self.analyzer.analyze(digits)
        
        max_entropy = np.log2(10)
        self.assertAlmostEqual(result.entropy, max_entropy, delta=0.2)
    
    def test_randomness_detection(self):
        """Test randomness detection."""
        # Random sequence
        import random
        digits = [random.randint(0, 9) for _ in range(100)]
        result = self.analyzer.analyze(digits)
        self.assertTrue(result.is_random)
        
        # Deterministic sequence
        digits = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] * 10
        result = self.analyzer.analyze(digits)
        self.assertFalse(result.is_random)
    
    def test_chi_square_test(self):
        """Test chi-square test."""
        # Uniform distribution should pass chi-square test
        digits = [i % 10 for i in range(100)]
        chi_square, p_value = self.analyzer.chi_square_test(digits)
        
        # p-value should be high (fail to reject null hypothesis)
        self.assertGreater(p_value, 0.05)
    
    def test    def test_runs_test(self):
        """Test runs test for randomness."""
        # Random sequence should pass runs test
        import random
        digits = [random.randint(0, 9) for _ in range(100)]
        p_value = self.analyzer.runs_test(digits)
        
        # p-value should be high (fail to reject null hypothesis of randomness)
        self.assertGreater(p_value, 0.05)
        
        # Highly patterned sequence should fail runs test
        digits = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1] * 10
        p_value = self.analyzer.runs_test(digits)
        
        # p-value should be low (reject null hypothesis)
        self.assertLess(p_value, 0.05)
    
    def test_auto_correlation(self):
        """Test auto-correlation calculation."""
        # Random sequence should have low auto-correlation
        import random
        digits = [random.randint(0, 9) for _ in range(100)]
        correlations = self.analyzer.auto_correlation(digits, max_lag=5)
        
        for corr in correlations:
            self.assertLess(abs(corr), 0.3)  # Low correlation for random data
        
        # Patterned sequence should have high auto-correlation at specific lags
        digits = [i % 10 for i in range(100)]
        correlations = self.analyzer.auto_correlation(digits, max_lag=10)
        
        # Should have correlation at lag 10 (cycle length)
        self.assertGreater(abs(correlations[9]), 0.5)
    
    def test_get_entropy_confidence(self):
        """Test entropy confidence calculation."""
        # High entropy should give high confidence in randomness
        import random
        digits = [random.randint(0, 9) for _ in range(100)]
        result = self.analyzer.analyze(digits)
        confidence = self.analyzer.get_entropy_confidence(result)
        self.assertGreater(confidence, 0.5)
        
        # Low entropy should give high confidence in patterns
        digits = [0] * 50 + [1] * 50
        result = self.analyzer.analyze(digits)
        confidence = self.analyzer.get_entropy_confidence(result)
        self.assertGreater(confidence, 0.6)


class TestVolatilityAnalyzer(unittest.TestCase):
    """Test cases for VolatilityAnalyzer."""
    
    def setUp(self):
        self.analyzer = VolatilityAnalyzer()
    
    def test_volatility_metrics(self):
        """Test volatility metrics calculation."""
        prices = [100 + i for i in range(100)]
        metrics = self.analyzer.analyze_volatility(prices)
        
        self.assertEqual(metrics.mean, 149.5)
        self.assertEqual(metrics.min_price, 100)
        self.assertEqual(metrics.max_price, 199)
        self.assertGreater(metrics.standard_deviation, 0)
    
    def test_momentum_analysis(self):
        """Test momentum analysis."""
        # Upward trend
        prices = [100 + i * 0.1 for i in range(50)]
        result = self.analyzer.analyze_momentum(prices)
        
        self.assertEqual(result.direction, 'up')
        self.assertGreater(result.strength, 0.3)
        self.assertGreater(result.momentum_score, 0.3)
        
        # Downward trend
        prices = [100 - i * 0.1 for i in range(50)]
        result = self.analyzer.analyze_momentum(prices)
        
        self.assertEqual(result.direction, 'down')
        self.assertGreater(result.strength, 0.3)
        
        # Neutral trend
        prices = [100 + np.random.randn() * 0.1 for _ in range(50)]
        result = self.analyzer.analyze_momentum(prices)
        
        self.assertIn(result.direction, ['neutral', 'up', 'down'])
    
    def test_trend_analysis(self):
        """Test trend analysis."""
        # Upward trend
        prices = [100 + i for i in range(50)]
        trend = self.analyzer.analyze_trend(prices)
        
        self.assertEqual(trend['direction'], 'up')
        self.assertGreater(trend['trend_strength'], 0.5)
        self.assertGreater(trend['r_squared'], 0.9)  # Strong linear relationship
        
        # Downward trend
        prices = [100 - i for i in range(50)]
        trend = self.analyzer.analyze_trend(prices)
        
        self.assertEqual(trend['direction'], 'down')
        self.assertGreater(trend['trend_strength'], 0.5)
        
        # No trend
        prices = [100 + np.random.randn() * 5 for _ in range(50)]
        trend = self.analyzer.analyze_trend(prices)
        
        self.assertEqual(trend['direction'], 'neutral')
        self.assertLess(trend['trend_strength'], 0.5)
    
    def test_mean_reversion(self):
        """Test mean reversion detection."""
        # Mean reverting series
        mean = 100
        prices = [mean + np.random.randn() * 5 for _ in range(50)]
        # Add some mean reversion
        for i in range(1, len(prices)):
            prices[i] = prices[i-1] + (mean - prices[i-1]) * 0.3 + np.random.randn() * 2
        
        result = self.analyzer.measure_mean_reversion(prices)
        
        self.assertGreater(result['mean_reversion_score'], 0.3)
        self.assertLess(result['auto_correlation'], 0.5)  # Should show reversion


class TestPatternAnalyzer(unittest.TestCase):
    """Test cases for PatternAnalyzer."""
    
    def setUp(self):
        self.analyzer = PatternAnalyzer(min_pattern_length=2, max_pattern_length=4)
    
    def test_repeated_patterns(self):
        """Test repeated pattern detection."""
        # Create sequence with clear repeating pattern
        pattern = [0, 1, 2, 3]
        digits = pattern * 10
        result = self.analyzer.analyze(digits)
        
        # Should detect the pattern [0, 1, 2, 3]
        patterns = result.repeated_patterns
        self.assertTrue(len(patterns) > 0)
        
        # The most frequent pattern should be the one we created
        if patterns:
            most_common = patterns[0]
            self.assertIn(0, most_common[0])
            self.assertIn(1, most_common[0])
    
    def test_streak_detection(self):
        """Test streak detection."""
        digits = [0, 0, 0, 1, 1, 2, 2, 2, 2, 3, 0, 0, 0, 0, 0]
        result = self.analyzer.analyze(digits)
        
        # Longest streak should be digit 0 with length 5
        self.assertEqual(result.longest_streak[0], 0)
        self.assertEqual(result.longest_streak[1], 5)
        
        # Current streak should be 0 with length 5
        self.assertEqual(result.current_streak[0], 0)
        self.assertEqual(result.current_streak[1], 5)
    
    def test_cycle_detection(self):
        """Test cycle detection."""
        # Create a cyclic sequence
        cycle = [0, 1, 2, 3, 4]
        digits = cycle * 10
        result = self.analyzer.analyze(digits)
        
        # Should detect cycle length 5
        cycles = result.cycle_lengths
        self.assertIn(5, cycles)
    
    def test_streak_analysis(self):
        """Test comprehensive streak analysis."""
        digits = [0, 0, 0, 1, 1, 2, 2, 2, 2, 3, 0, 0, 0, 0, 0]
        result = self.analyzer.analyze_streaks(digits)
        
        self.assertEqual(result.current_digit, 0)
        self.assertEqual(result.current_streak, 5)
        self.assertEqual(result.max_streak, 5)
        
        # Check digit 2 streaks
        self.assertIn(4, result.digit_streaks[2])  # Digit 2 had a streak of 4
        
        # Check digit 0 streaks
        self.assertIn(5, result.digit_streaks[0])  # Digit 0 had a streak of 5
    
    def test_confidence_calculation(self):
        """Test confidence calculation."""
        # Clear patterns should give high confidence
        digits = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1] * 10
        result = self.analyzer.analyze(digits)
        self.assertGreater(result.confidence, 0.5)
        
        # Random sequence should give low confidence
        import random
        digits = [random.randint(0, 9) for _ in range(100)]
        result = self.analyzer.analyze(digits)
        self.assertLess(result.confidence, 0.5)


class TestConfidenceScorer(unittest.TestCase):
    """Test cases for ConfidenceScorer."""
    
    def setUp(self):
        self.scorer = ConfidenceScorer()
    
    def test_frequency_confidence(self):
        """Test frequency confidence calculation."""
        data = {
            'z_scores': {i: 1.5 for i in range(10)},
            'digit_counts': {i: 15 for i in range(10)}
        }
        confidence = self.scorer.calculate_confidence('frequency', data, 100, 100)
        self.assertGreater(confidence, 0.5)
    
    def test_markov_confidence(self):
        """Test Markov confidence calculation."""
        data = {
            'matrix': np.eye(10) * 0.9,
            'entropy_rate': 0.5
        }
        confidence = self.scorer.calculate_confidence('markov', data, 100, 100)
        self.assertGreater(confidence, 0.5)
    
    def test_trend_confidence(self):
        """Test trend confidence calculation."""
        data = {
            'r_squared': 0.9,
            'trend_strength': 0.8,
            'direction': 'up'
        }
        confidence = self.scorer.calculate_confidence('trend', data, 50, 100)
        self.assertGreater(confidence, 0.7)
    
    def test_combine_confidences(self):
        """Test confidence combination."""
        confidences = [0.8, 0.6, 0.9]
        weights = [0.5, 0.3, 0.2]
        
        combined = self.scorer.combine_confidences(confidences, weights)
        self.assertAlmostEqual(combined, 0.76, places=2)
        
        # Test without weights (equal weights)
        combined = self.scorer.combine_confidences(confidences)
        self.assertAlmostEqual(combined, 0.7667, places=2)
    
    def test_confidence_levels(self):
        """Test confidence level classification."""
        self.assertEqual(self.scorer.get_confidence_level(0.9), "Very High")
        self.assertEqual(self.scorer.get_confidence_level(0.7), "High")
        self.assertEqual(self.scorer.get_confidence_level(0.5), "Moderate")
        self.assertEqual(self.scorer.get_confidence_level(0.3), "Low")
        self.assertEqual(self.scorer.get_confidence_level(0.1), "Very Low")
    
    def test_confidence_colors(self):
        """Test confidence color mapping."""
        self.assertEqual(self.scorer.get_confidence_color(0.9), "#2ECC71")  # Green
        self.assertEqual(self.scorer.get_confidence_color(0.7), "#F1C40F")  # Yellow
        self.assertEqual(self.scorer.get_confidence_color(0.5), "#E67E22")  # Orange
        self.assertEqual(self.scorer.get_confidence_color(0.3), "#E74C3C")  # Red


class TestAnalyticsEngine(unittest.TestCase):
    """Test cases for AnalyticsEngine."""
    
    def setUp(self):
        self.engine = AnalyticsEngine()
        
        # Create test ticks
        self.ticks = []
        for i in range(100):
            tick = Tick(
                tick_id=f"tick_{i}",
                symbol="R_10",
                price=Decimal(str(100 + i * 0.01)),
                last_digit=i % 10,
                timestamp=datetime.now()
            )
            self.ticks.append(tick)
    
    def test_comprehensive_analysis(self):
        """Test comprehensive analysis."""
        result = self.engine.analyze_tick_data(self.ticks)
        
        self.assertIsNotNone(result)
        self.assertIn('frequency', result.__dict__)
        self.assertIn('markov', result.__dict__)
        self.assertIn('entropy', result.__dict__)
        self.assertIn('volatility', result.__dict__)
        self.assertIn('patterns', result.__dict__)
        self.assertIn('confidence', result.__dict__)
        self.assertIn('summary', result.__dict__)
    
    def test_get_digit_frequency(self):
        """Test digit frequency retrieval."""
        frequency = self.engine.get_digit_frequency(self.ticks)
        self.assertEqual(len(frequency), 10)
        
        # Each digit should appear ~10 times
        for digit in range(10):
            self.assertAlmostEqual(frequency[digit], 10, delta=2)
    
    def test_get_transition_matrix(self):
        """Test transition matrix retrieval."""
        matrix = self.engine.get_transition_matrix(self.ticks)
        self.assertEqual(matrix.shape, (10, 10))
    
    def test_get_entropy(self):
        """Test entropy retrieval."""
        entropy = self.engine.get_entropy(self.ticks)
        max_entropy = np.log2(10)
        self.assertAlmostEqual(entropy, max_entropy, delta=0.3)
    
    def test_get_volatility(self):
        """Test volatility retrieval."""
        volatility = self.engine.get_volatility(self.ticks)
        self.assertGreater(volatility, 0)
    
    def test_get_momentum(self):
        """Test momentum retrieval."""
        momentum = self.engine.get_momentum(self.ticks)
        self.assertIn('direction', momentum)
        self.assertIn('strength', momentum)
        self.assertIn('score', momentum)
        self.assertIn('confidence', momentum)
    
    def test_get_patterns(self):
        """Test pattern retrieval."""
        patterns = self.engine.get_patterns(self.ticks)
        self.assertIn('repeated_patterns', patterns)
        self.assertIn('longest_streak', patterns)
        self.assertIn('current_streak', patterns)
    
    def test_get_streak_analysis(self):
        """Test streak analysis retrieval."""
        streaks = self.engine.get_streak_analysis(self.ticks)
        self.assertIn('current_digit', streaks)
        self.assertIn('current_streak', streaks)
        self.assertIn('max_streak', streaks)
        self.assertIn('digit_streaks', streaks)
    
    def test_clear_cache(self):
        """Test cache clearing."""
        # Run analysis to populate cache
        self.engine.analyze_tick_data(self.ticks)
        self.assertIsNotNone(self.engine._last_analysis)
        
        # Clear cache
        self.engine.clear_cache()
        self.assertIsNone(self.engine._last_analysis)
    
    def test_empty_analysis(self):
        """Test analysis with empty data."""
        result = self.engine.analyze_tick_data([])
        
        self.assertEqual(result.summary['total_ticks'], 0)
        self.assertEqual(result.confidence['overall'], 0.0)
        self.assertEqual(result.confidence['level'], "Very Low")


if __name__ == "__main__":
    unittest.main()