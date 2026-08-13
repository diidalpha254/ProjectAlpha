"""
Unit tests for the Data Processing Pipeline
"""

import unittest
import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

from app.data.processor import DataProcessor
from app.data.data_normalizer import DataNormalizer
from app.data.rolling_window import RollingWindowManager
from app.data.event_bus import event_bus
from app.core.types import Tick


class TestDataNormalizer(unittest.TestCase):
    """Test cases for DataNormalizer."""
    
    def setUp(self):
        self.normalizer = DataNormalizer()
    
    def test_normalize_valid_tick(self):
        """Test normalizing a valid tick."""
        raw_data = {
            "symbol": "R_10",
            "tick": 1234.56,
            "epoch": 1700000000
        }
        
        tick = self.normalizer.normalize_tick(raw_data)
        
        self.assertIsNotNone(tick)
        self.assertEqual(tick.symbol, "R_10")
        self.assertEqual(tick.price, Decimal("1234.56"))
        self.assertEqual(tick.last_digit, 6)  # Last digit of 1234.56 is 6
        self.assertEqual(tick.epoch, 1700000000)
    
    def test_normalize_invalid_symbol(self):
        """Test normalizing with invalid symbol."""
        raw_data = {
            "symbol": "INVALID",
            "tick": 1234.56,
            "epoch": 1700000000
        }
        
        tick = self.normalizer.normalize_tick(raw_data)
        
        # Should still work with unknown symbol (flexible)
        self.assertIsNotNone(tick)
        self.assertEqual(tick.symbol, "INVALID")
    
    def test_normalize_missing_fields(self):
        """Test normalizing with missing fields."""
        raw_data = {
            "symbol": "R_10"
        }
        
        tick = self.normalizer.normalize_tick(raw_data)
        self.assertIsNone(tick)  # Missing price should return None
    
    def test_normalize_price_formats(self):
        """Test different price formats."""
        test_cases = [
            {"tick": 1234.56, "expected": 6},  # Float
            {"tick": "1234.56", "expected": 6},  # String
            {"price": 1234.56, "expected": 6},  # Different field name
            {"quote": 1234.56, "expected": 6},  # Different field name
        ]
        
        for case in test_cases:
            raw_data = {
                "symbol": "R_10",
                "epoch": 1700000000,
                **case
            }
            
            tick = self.normalizer.normalize_tick(raw_data)
            self.assertIsNotNone(tick)
            self.assertEqual(tick.last_digit, case["expected"])
    
    def test_extract_last_digit(self):
        """Test last digit extraction."""
        test_cases = [
            (Decimal("1234.56"), 6),
            (Decimal("1234.50"), 0),
            (Decimal("1234.99"), 9),
            (Decimal("1234.01"), 1),
            (Decimal("1000.00"), 0),
        ]
        
        for price, expected in test_cases:
            digit = self.normalizer._extract_last_digit(price)
            self.assertEqual(digit, expected)
    
    def test_get_stats(self):
        """Test getting validation statistics."""
        stats = self.normalizer.get_stats()
        self.assertIn("total_validated", stats)
        self.assertIn("total_invalid", stats)
        self.assertIn("error_rate", stats)


class TestRollingWindowManager(unittest.TestCase):
    """Test cases for RollingWindowManager."""
    
    def setUp(self):
        self.window_sizes = [10, 20, 50]
        self.manager = RollingWindowManager(self.window_sizes)
    
    def test_add_tick(self):
        """Test adding ticks to windows."""
        for i in range(25):
            tick = Tick(
                tick_id=f"tick_{i}",
                symbol="R_10",
                price=Decimal(str(100 + i)),
                last_digit=i % 10,
                timestamp=datetime.now()
            )
            self.manager.add_tick(tick)
        
        # Check window sizes
        self.assertEqual(len(self.manager.get_window(10)), 10)
        self.assertEqual(len(self.manager.get_window(20)), 20)
        self.assertEqual(len(self.manager.get_window(50)), 25)
    
    def test_window_stats(self):
        """Test window statistics calculation."""
        # Add ticks with known values
        for i in range(100):
            tick = Tick(
                tick_id=f"tick_{i}",
                symbol="R_10",
                price=Decimal(str(100 + i)),
                last_digit=i % 10,
                timestamp=datetime.now()
            )
            self.manager.add_tick(tick)
        
        stats = self.manager.get_window_stats(50)
        self.assertIsNotNone(stats)
        self.assertTrue(stats.is_full)
        self.assertEqual(stats.count, 50)
        self.assertEqual(stats.mean_price, 125)  # Average of 100-149
        self.assertEqual(stats.min_price, 100)
        self.assertEqual(stats.max_price, 149)
    
    def test_digit_frequency(self):
        """Test digit frequency calculation."""
        # Add ticks with known digits
        for i in range(100):
            digit = i % 10
            tick = Tick(
                tick_id=f"tick_{i}",
                symbol="R_10",
                price=Decimal(str(100 + i)),
                last_digit=digit,
                timestamp=datetime.now()
            )
            self.manager.add_tick(tick)
        
        freq = self.manager.get_digit_frequency(100)
        for digit in range(10):
            self.assertEqual(freq[digit], 10)  # Each digit appears 10 times
    
    def test_transition_matrix(self):
        """Test transition matrix calculation."""
        # Add ticks with sequential digits
        for i in range(100):
            digit = i % 10
            tick = Tick(
                tick_id=f"tick_{i}",
                symbol="R_10",
                price=Decimal(str(100 + i)),
                last_digit=digit,
                timestamp=datetime.now()
            )
            self.manager.add_tick(tick)
        
        matrix = self.manager.get_transition_matrix(100)
        self.assertEqual(matrix.shape, (10, 10))
        
        # Each digit should transition to the next digit 10 times
        for i in range(10):
            total = matrix[i].sum()
            self.assertAlmostEqual(total, 1.0)  # Row sums to 1
    
    def test_get_overall_stats(self):
        """Test getting overall statistics."""
        for i in range(50):
            tick = Tick(
                tick_id=f"tick_{i}",
                symbol="R_10",
                price=Decimal(str(100 + i)),
                last_digit=i % 10,
                timestamp=datetime.now()
            )
            self.manager.add_tick(tick)
        
        stats = self.manager.get_overall_stats()
        self.assertEqual(stats["total_ticks"], 50)
        self.assertEqual(stats["mean_price"], 124.5)  # Average of 100-149


class TestDataProcessor(unittest.TestCase):
    """Test cases for DataProcessor."""
    
    def setUp(self):
        self.processor = DataProcessor(window_sizes=[10, 20, 50])
    
    def test_process_valid_tick(self):
        """Test processing a valid tick."""
        raw_data = {
            "symbol": "R_10",
            "tick": 1234.56,
            "epoch": 1700000000
        }
        
        tick = self.processor.process_tick_sync(raw_data)
        self.assertIsNotNone(tick)
        self.assertEqual(tick.last_digit, 6)
    
    def test_process_multiple_ticks(self):
        """Test processing multiple ticks."""
        for i in range(30):
            raw_data = {
                "symbol": "R_10",
                "tick": 100 + i,
                "epoch": 1700000000 + i
            }
            tick = self.processor.process_tick_sync(raw_data)
            self.assertIsNotNone(tick)
        
        stats = self.processor.get_processor_stats()
        self.assertEqual(stats["ticks_processed"], 30)
        self.assertEqual(stats["ticks_rejected"], 0)
    
    def test_process_invalid_tick(self):
        """Test processing invalid tick."""
        raw_data = {
            "symbol": "R_10"
            # Missing price
        }
        
        tick = self.processor.process_tick_sync(raw_data)
        self.assertIsNone(tick)
        
        stats = self.processor.get_processor_stats()
        self.assertEqual(stats["ticks_rejected"], 1)
    
    def test_get_window_stats(self):
        """Test getting window statistics."""
        for i in range(100):
            raw_data = {
                "symbol": "R_10",
                "tick": 100 + i,
                "epoch": 1700000000 + i
            }
            self.processor.process_tick_sync(raw_data)
        
        stats = self.processor.get_window_stats(50)
        self.assertIsNotNone(stats)
        self.assertEqual(stats["count"], 50)
        self.assertTrue(stats["is_full"])
    
    def test_clear(self):
        """Test clearing the processor."""
        for i in range(10):
            raw_data = {
                "symbol": "R_10",
                "tick": 100 + i,
                "epoch": 1700000000 + i
            }
            self.processor.process_tick_sync(raw_data)
        
        self.processor.clear()
        
        stats = self.processor.get_processor_stats()
        self.assertEqual(stats["ticks_processed"], 0)
        self.assertEqual(stats["ticks_rejected"], 0)
    
    def test_async_processing(self):
        """Test asynchronous processing."""
        # Start processor thread
        self.processor.start()
        
        # Publish raw ticks via event bus
        for i in range(10):
            raw_data = {
                "symbol": "R_10",
                "tick": 100 + i,
                "epoch": 1700000000 + i
            }
            event_bus.publish("raw_tick", raw_data, "Test")
        
        # Wait for processing
        import time
        time.sleep(1)
        
        stats = self.processor.get_processor_stats()
        self.assertEqual(stats["ticks_processed"], 10)
        
        self.processor.stop()


class TestEventBus(unittest.TestCase):
    """Test cases for EventBus."""
    
    def setUp(self):
        self.event_bus = event_bus
        self.handler_called = False
        self.handler_data = None
    
    def test_publish_subscribe(self):
        """Test publish/subscribe pattern."""
        def handler(event):
            self.handler_called = True
            self.handler_data = event.data
        
        self.event_bus.subscribe("test_event", handler)
        self.event_bus.publish("test_event", {"test": "data"}, "Test")
        
        self.assertTrue(self.handler_called)
        self.assertEqual(self.handler_data["test"], "data")
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event."""
        counter = 0
        
        def handler1(event):
            nonlocal counter
            counter += 1
        
        def handler2(event):
            nonlocal counter
            counter += 1
        
        self.event_bus.subscribe("test_event", handler1)
        self.event_bus.subscribe("test_event", handler2)
        self.event_bus.publish("test_event", {"test": "data"}, "Test")
        
        self.assertEqual(counter, 2)
    
    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        def handler(event):
            self.handler_called = True
        
        self.event_bus.subscribe("test_event", handler)
        self.event_bus.unsubscribe("test_event", handler)
        self.event_bus.publish("test_event", {"test": "data"}, "Test")
        
        self.assertFalse(self.handler_called)
    
    def test_event_history(self):
        """Test event history tracking."""
        for i in range(5):
            self.event_bus.publish("test_event", {"index": i}, "Test")
        
        history = self.event_bus.get_event_history("test_event", limit=3)
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0].data["index"], 4)  # Latest first


if __name__ == "__main__":
    unittest.main()