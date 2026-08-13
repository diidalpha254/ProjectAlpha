"""
Unit tests for Match/Differ Intelligence module
"""

import unittest
import numpy as np
from datetime import datetime
from decimal import Decimal

from app.intelligence.match_differ import MatchDifferIntelligence
from app.intelligence.context import HistoricalContext
from app.core.types import Tick


class TestMatchDifferIntelligence(unittest.TestCase):
    """Test cases for MatchDifferIntelligence."""
    
    def setUp(self):
        self.intelligence = MatchDifferIntelligence()
        
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
    
    def test_analyze(self):
        """Test comprehensive analysis."""
        result = self.intelligence.analyze(self.ticks)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result.market_condition, str)
        self.assertIsInstance(result.digit_distribution, dict)
        self.assertIsInstance(result.transition_probabilities, dict)
        self.assertIsInstance(result.confidence_indicators, dict)
        self.assertIsInstance(result.pattern_summary, str)
        self.assertIsInstance(result.historical_context, str)
        self.assertIsInstance(result.explanation, str)
    
    def test_empty_data(self):
        """Test analysis with empty data."""
        result = self.intelligence.analyze([])
        self.assertEqual(result.market_condition, "unknown")
        self.assertIn("Insufficient data", result.explanation)
    
    def test_transition_probabilities(self):
        """Test transition probability calculation."""
        # Test with deterministic sequence
        digits = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
        ticks = []
        for i, digit in enumerate(digits):
            tick = Tick(
                tick_id=f"tick_{i}",
                symbol="R_10",
                price=Decimal("100.00"),
                last_digit=digit,
                timestamp=datetime.now()
            )
            ticks.append(tick)
        
        # Get transition probabilities through analyze
        result = self.intelligence.analyze(ticks)
        probs = result.transition_probabilities
        
        # Check that probabilities exist
        self.assertIn('match_probability', probs)
        self.assertIn('differ_probability', probs)
    
    def test_confidence_indicators(self):
        """Test confidence indicator generation."""
        result = self.intelligence.analyze(self.ticks)
        
        self.assertIn('market_confidence', result.confidence_indicators)
        self.assertIn('statistical_confidence', result.confidence_indicators)
        self.assertIn('overall_confidence', result.confidence_indicators)
        
        # All confidence should be between 0 and 1
        for value in result.confidence_indicators.values():
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 1)
    
    def test_observations_generation(self):
        """Test observation generation."""
        result = self.intelligence.analyze(self.ticks)
        
        self.assertTrue(len(result.observations) > 0)
        self.assertTrue(any("Market state" in obs for obs in result.observations))
        self.assertTrue(any("digit" in obs.lower() for obs in result.observations))
    
    def test_pattern_summary(self):
        """Test pattern summary generation."""
        result = self.intelligence.analyze(self.ticks)
        
        self.assertTrue(len(result.pattern_summary) > 0)
        self.assertIsInstance(result.pattern_summary, str)
    
    def test_historical_context(self):
        """Test historical context generation."""
        result = self.intelligence.analyze(self.ticks)
        
        self.assertTrue(len(result.historical_context) > 0)
        self.assertIsInstance(result.historical_context, str)
    
    def test_explanation(self):
        """Test explanation generation."""
        result = self.intelligence.analyze(self.ticks)
        
        self.assertTrue(len(result.explanation) > 0)
        self.assertIsInstance(result.explanation, str)
    
    def test_analysis_history(self):
        """Test analysis history tracking."""
        # Run multiple analyses
        for i in range(5):
            self.intelligence.analyze(self.ticks)
        
        self.assertEqual(len(self.intelligence._analysis_history), 5)
    
    def test_digit_distribution(self):
        """Test digit distribution extraction."""
        # Create biased distribution
        ticks = []
        for i in range(100):
            digit = 0 if i < 30 else (i % 10)  # 0 appears 30 times
            tick = Tick(
                tick_id=f"tick_{i}",
                symbol="R_10",
                price=Decimal("100.00"),
                last_digit=digit,
                timestamp=datetime.now()
            )
            ticks.append(tick)
        
        result = self.intelligence.analyze(ticks)
        distribution = result.digit_distribution
        
        # Digit 0 should have higher frequency
        self.assertGreater(distribution[0], 0.1)
        
        # Sum should be approximately 1
        self.assertAlmostEqual(sum(distribution.values()), 1.0, places=1)
    
    def test_risk_assessment(self):
        """Test risk assessment through private method."""
        from app.intelligence.match_differ import RiskLevel
        
        # Create a risk assessment using the private method
        # We test this through the analyze method indirectly
        result = self.intelligence.analyze(self.ticks)
        
        # Check that observations include risk level
        self.assertTrue(any("Risk level" in obs for obs in result.observations))


class TestHistoricalContext(unittest.TestCase):
    """Test cases for HistoricalContext."""
    
    def setUp(self):
        self.context = HistoricalContext(max_history=1000)
        
        # Create test ticks
        self.ticks = []
        for i in range(200):
            tick = Tick(
                tick_id=f"tick_{i}",
                symbol="R_10",
                price=Decimal(str(100 + i * 0.01)),
                last_digit=i % 10,
                timestamp=datetime.now()
            )
            self.ticks.append(tick)
        
        self.context.add_ticks(self.ticks[:100])  # Add historical data
    
    def test_add_ticks(self):
        """Test adding ticks to context."""
        self.context.add_ticks(self.ticks[100:])
        
        # Should have all ticks (limited by max_history)
        self.assertEqual(len(self.context._ticks), 200)
    
    def test_historical_comparison(self):
        """Test historical comparison."""
        comparison = self.context.get_historical_comparison(self.ticks[100:150])
        
        self.assertIn('similarity_score', comparison)
        self.assertIn('differences', comparison)
        self.assertIn('historical_context', comparison)
        self.assertIn('anomaly_score', comparison)
        self.assertIn('confidence', comparison)
    
    def test_similarity_score(self):
        """Test similarity score calculation."""
        # Compare identical sets
        comparison1 = self.context.get_historical_comparison(self.ticks[:50])
        self.assertGreater(comparison1['similarity_score'], 0.5)
        
        # Compare different sets
        different_ticks = []
        for i in range(50):
            tick = Tick(
                tick_id=f"diff_{i}",
                symbol="R_10",
                price=Decimal(str(200 + i)),
                last_digit=5 if i < 25 else i % 10,
                timestamp=datetime.now()
            )
            different_ticks.append(tick)
        
        comparison2 = self.context.get_historical_comparison(different_ticks)
        self.assertLess(comparison2['similarity_score'], 0.8)
    
    def test_anomaly_score(self):
        """Test anomaly score calculation."""
        # Normal comparison
        comparison1 = self.context.get_historical_comparison(self.ticks[50:100])
        self.assertLess(comparison1['anomaly_score'], 0.5)
        
        # Anomalous data
        anomalous_ticks = []
        for i in range(50):
            tick = Tick(
                tick_id=f"anomaly_{i}",
                symbol="R_10",
                price=Decimal(str(1000 + i * 10)),  # Price spike
                last_digit=i % 10,
                timestamp=datetime.now()
            )
            anomalous_ticks.append(tick)
        
        comparison2 = self.context.get_historical_comparison(anomalous_ticks)
        self.assertGreater(comparison2['anomaly_score'], 0.3)
    
    def test_take_snapshot(self):
        """Test taking snapshots."""
        self.context.take_snapshot()
        self.context.take_snapshot()
        self.context.take_snapshot()
        
        snapshots = self.context.get_snapshots()
        self.assertEqual(len(snapshots), 3)
    
    def test_empty_comparison(self):
        """Test comparison with empty context."""
        empty_context = HistoricalContext()
        comparison = empty_context.get_historical_comparison(self.ticks[:50])
        
        self.assertEqual(comparison['similarity_score'], 0.0)
        self.assertEqual(comparison['confidence'], 0.0)
        self.assertIn('Insufficient historical data', comparison['historical_context'])
    
    def test_clear(self):
        """Test clearing historical context."""
        self.context.clear()
        self.assertEqual(len(self.context._ticks), 0)
        self.assertEqual(len(self.context._snapshots), 0)


if __name__ == "__main__":
    unittest.main()