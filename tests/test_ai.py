"""
Unit tests for AI Insights Engine
"""

import unittest
import numpy as np
from datetime import datetime
from decimal import Decimal

from app.ai.insights import AIInsightsEngine
from app.ai.explanation import ExplanationGenerator
from app.ai.risk import RiskCommunicator
from app.core.types import Tick
from app.core.constants import MarketState, RiskLevel


class TestAIInsightsEngine(unittest.TestCase):
    """Test cases for AIInsightsEngine."""
    
    def setUp(self):
        self.engine = AIInsightsEngine()
        
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
    
    def test_generate_insights(self):
        """Test insight generation."""
        insight = self.engine.generate_insights(self.ticks)
        
        self.assertIsNotNone(insight)
        self.assertIsInstance(insight.what_is_happening, str)
        self.assertIsInstance(insight.why_classified, str)
        self.assertIsInstance(insight.statistical_factors, list)
        self.assertIsInstance(insight.market_differences, str)
        self.assertIsInstance(insight.risks, list)
        self.assertIsInstance(insight.confidence_level, float)
    
    def test_empty_data(self):
        """Test insight generation with empty data."""
        insight = self.engine.generate_insights([])
        
        self.assertIn("Insufficient data", insight.what_is_happening)
        self.assertEqual(insight.confidence_level, 0.0)
    
    def test_market_description(self):
        """Test market description generation."""
        insight = self.engine.generate_insights(self.ticks)
        
        self.assertTrue(len(insight.what_is_happening) > 0)
        self.assertIsInstance(insight.what_is_happening, str)
    
    def test_classification_explanation(self):
        """Test classification explanation generation."""
        insight = self.engine.generate_insights(self.ticks)
        
        self.assertTrue(len(insight.why_classified) > 0)
        self.assertIsInstance(insight.why_classified, str)
    
    def test_statistical_factors(self):
        """Test statistical factors generation."""
        insight = self.engine.generate_insights(self.ticks)
        
        self.assertTrue(len(insight.statistical_factors) > 0)
        self.assertIsInstance(insight.statistical_factors, list)
    
    def test_market_differences(self):
        """Test market differences generation."""
        insight = self.engine.generate_insights(self.ticks)
        
        self.assertTrue(len(insight.market_differences) > 0)
        self.assertIsInstance(insight.market_differences, str)
    
    def test_risk_insights(self):
        """Test risk insights generation."""
        insight = self.engine.generate_insights(self.ticks)
        
        self.assertTrue(len(insight.risks) > 0)
        self.assertIsInstance(insight.risks, list)
        
        # Check for transparency disclaimer
        self.assertTrue(any("No prediction" in risk for risk in insight.risks))
    
    def test_insight_history(self):
        """Test insight history tracking."""
        # Generate multiple insights
        for i in range(5):
            self.engine.generate_insights(self.ticks)
        
        history = self.engine.get_insight_history()
        self.assertEqual(len(history), 5)
    
    def test_recent_insight(self):
        """Test getting the most recent insight."""
        insight = self.engine.generate_insights(self.ticks)
        recent = self.engine.get_recent_insight()
        
        self.assertIsNotNone(recent)
        self.assertEqual(recent, insight)
    
    def test_confidence_level_consistency(self):
        """Test confidence level consistency."""
        insight = self.engine.generate_insights(self.ticks)
        
        # Confidence should be between 0 and 1
        self.assertGreaterEqual(insight.confidence_level, 0)
        self.assertLessEqual(insight.confidence_level, 1)


class TestExplanationGenerator(unittest.TestCase):
    """Test cases for ExplanationGenerator."""
    
    def setUp(self):
        self.generator = ExplanationGenerator()
    
    def test_explain_frequency_analysis(self):
        """Test frequency analysis explanation."""
        data = {
            'total_counts': 100,
            'hot_digits': [0, 1],
            'cold_digits': [8, 9],
            'z_scores': {0: 2.5, 1: 2.0, 8: -2.5, 9: -2.0},
            'frequencies': {0: 0.15, 1: 0.14, 2: 0.1, 3: 0.1, 4: 0.1,
                          5: 0.1, 6: 0.1, 7: 0.1, 8: 0.05, 9: 0.06}
        }
        
        explanation = self.generator.explain_frequency_analysis(data)
        
        self.assertTrue(len(explanation) > 0)
        self.assertIn("100 ticks", explanation)
        self.assertIn("Hot digits", explanation)
        self.assertIn("Cold digits", explanation)
    
    def test_explain_markov_analysis(self):
        """Test Markov analysis explanation."""
        data = {
            'transition_matrix': np.random.rand(10, 10),
            'stationary_distribution': np.random.rand(10),
            'entropy_rate': 2.5,
            'mixing_time': 5
        }
        
        explanation = self.generator.explain_markov_analysis(data)
        self.assertTrue(len(explanation) > 0)
    
    def test_explain_pattern_analysis(self):
        """Test pattern analysis explanation."""
        data = {
            'repeated_patterns': [([0, 1], 3), ([2, 3], 2)],
            'longest_streak': (0, 5),
            'current_streak': (1, 3),
            'cycle_lengths': [10, 20],
            'dominant_pattern': [0, 1, 2],
            'confidence': 0.8
        }
        
        explanation = self.generator.explain_pattern_analysis(data)
        self.assertTrue(len(explanation) > 0)
    
    def test_explain_transition_probabilities(self):
        """Test transition probability explanation."""
        data = {
            'match_probability': 0.3,
            'differ_probability': 0.7,
            'consecutive_match': 0.1,
            'consecutive_differ': 0.3
        }
        
        explanation = self.generator.explain_transition_probabilities(data)
        self.assertTrue(len(explanation) > 0)
        self.assertIn("Match probability", explanation)
        self.assertIn("Differ probability", explanation)


class TestRiskCommunicator(unittest.TestCase):
    """Test cases for RiskCommunicator."""
    
    def setUp(self):
        self.communicator = RiskCommunicator()
    
    def test_communicate_risk_very_high(self):
        """Test very high risk communication."""
        messages = self.communicator.communicate_risk(
            RiskLevel.VERY_HIGH,
            MarketState.CHAOTIC,
            0.3
        )
        
        self.assertTrue(len(messages) > 0)
        self.assertTrue(any("VERY HIGH" in msg for msg in messages))
        self.assertTrue(any("caution" in msg.lower() for msg in messages))
    
    def test_communicate_risk_high(self):
        """Test high risk communication."""
        messages = self.communicator.communicate_risk(
            RiskLevel.HIGH,
            MarketState.VOLATILE,
            0.5
        )
        
        self.assertTrue(len(messages) > 0)
        self.assertTrue(any("HIGH" in msg for msg in messages))
    
    def test_communicate_risk_low(self):
        """Test low risk communication."""
        messages = self.communicator.communicate_risk(
            RiskLevel.LOW,
            MarketState.CALM,
            0.8
        )
        
        self.assertTrue(len(messages) > 0)
        self.assertTrue(any("LOW" in msg for msg in messages))
    
    def test_get_detailed_risk_explanation(self):
        """Test detailed risk explanation."""
        factors = {
            'market_risk': 0.8,
            'pattern_risk': 0.6,
            'volatility_risk': 0.7,
            'confidence_risk': 0.4,
            'overall_risk': 0.65
        }
        
        explanation = self.communicator.get_detailed_risk_explanation(factors)
        self.assertTrue(len(explanation) > 0)
        self.assertIn("HIGH", explanation)
    
    def test_get_risk_mitigation_suggestions(self):
        """Test risk mitigation suggestions."""
        suggestions = self.communicator.get_risk_mitigation_suggestions(RiskLevel.HIGH)
        
        self.assertTrue(len(suggestions) > 0)
        self.assertTrue(any("reduce" in s.lower() for s in suggestions))
        
        suggestions_low = self.communicator.get_risk_mitigation_suggestions(RiskLevel.LOW)
        self.assertTrue(any("increase" in s.lower() for s in suggestions_low))
    
    def test_get_transparent_disclaimer(self):
        """Test transparent disclaimer."""
        disclaimer = self.communicator.get_transparent_disclaimer()
        
        self.assertTrue(len(disclaimer) > 0)
        self.assertIn("No prediction", disclaimer)
        self.assertIn("risk", disclaimer.lower())


if __name__ == "__main__":
    unittest.main()