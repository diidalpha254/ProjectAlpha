"""
Unit tests for Visualization Engine
"""

import unittest
import numpy as np
from datetime import datetime
from decimal import Decimal

from app.visualization.charts import ChartBuilder
from app.visualization.dashboards import DashboardBuilder
from app.visualization.theme import ThemeManager
from app.core.types import Tick
from app.core.constants import MarketState


class TestChartBuilder(unittest.TestCase):
    """Test cases for ChartBuilder."""
    
    def setUp(self):
        self.builder = ChartBuilder()
        
        # Create test ticks
        self.ticks = []
        for i in range(50):
            tick = Tick(
                tick_id=f"tick_{i}",
                symbol="R_10",
                price=Decimal(str(100 + i * 0.01)),
                last_digit=i % 10,
                timestamp=datetime.now()
            )
            self.ticks.append(tick)
    
    def test_create_frequency_histogram(self):
        """Test frequency histogram creation."""
        frequencies = {i: 0.1 for i in range(10)}
        fig = self.builder.create_frequency_histogram(frequencies, 100)
        
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 1)
    
    def test_create_transition_heatmap(self):
        """Test transition heatmap creation."""
        matrix = np.random.rand(10, 10)
        fig = self.builder.create_transition_heatmap(matrix)
        
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 1)
    
    def test_create_price_chart(self):
        """Test price chart creation."""
        fig = self.builder.create_price_chart(self.ticks)
        
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 3)  # Price, Mean, Digits
    
    def test_create_confidence_gauge(self):
        """Test confidence gauge creation."""
        fig = self.builder.create_confidence_gauge(0.75)
        
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 1)
    
    def test_create_volatility_gauge(self):
        """Test volatility gauge creation."""
        fig = self.builder.create_volatility_gauge(0.03)
        
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 1)
    
    def test_create_market_state_indicator(self):
        """Test market state indicator creation."""
        fig = self.builder.create_market_state_indicator("trending", 0.8)
        
        self.assertIsNotNone(fig)
        self.assertTrue(len(fig.layout.annotations) > 0)
    
    def test_create_digit_timeline(self):
        """Test digit timeline creation."""
        fig = self.builder.create_digit_timeline(self.ticks)
        
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 1)
    
    def test_create_digit_distribution_donut(self):
        """Test digit distribution donut creation."""
        frequencies = {i: 0.1 for i in range(10)}
        fig = self.builder.create_digit_distribution_donut(frequencies)
        
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 1)
    
    def test_empty_figure(self):
        """Test empty figure creation."""
        fig = self.builder._empty_figure("No data")
        
        self.assertIsNotNone(fig)
        self.assertTrue(len(fig.layout.annotations) > 0)


class TestThemeManager(unittest.TestCase):
    """Test cases for ThemeManager."""
    
    def setUp(self):
        self.manager = ThemeManager()
    
    def test_apply_theme(self):
        """Test theme application."""
        self.manager.apply_theme('dark')
        self.assertEqual(self.manager.get_current_theme(), 'dark')
        
        self.manager.apply_theme('light')
        self.assertEqual(self.manager.get_current_theme(), 'light')
    
    def test_toggle_theme(self):
        """Test theme toggling."""
        initial = self.manager.get_current_theme()
        new_theme = self.manager.toggle_theme()
        
        self.assertNotEqual(initial, new_theme)
    
    def test_get_theme_config(self):
        """Test getting theme configuration."""
        config = self.manager.get_theme_config()
        
        self.assertIn('background', config)
        self.assertIn('text', config)
        self.assertIn('primary', config)
    
    def test_generate_css(self):
        """Test CSS generation."""
        theme = self.manager.get_theme_config()
        css = self.manager._generate_css(theme)
        
        self.assertTrue(len(css) > 0)
        self.assertIn('--bg-color', css)
        self.assertIn('--text-color', css)


if __name__ == "__main__":
    unittest.main()