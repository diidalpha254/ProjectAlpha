"""
Data Processing Pipeline
Orchestrates the entire data processing flow from raw data to analytics-ready ticks.
"""

from typing import Optional, Dict, Any, Callable, List
import asyncio
import threading
from datetime import datetime
import queue
import time
import numpy as np

from core.types import Tick
from core.exceptions import DataValidationError
from core.logger import get_logger
from .data_normalizer import DataNormalizer
from .rolling_window import RollingWindowManager
from .event_bus import event_bus

logger = get_logger(__name__)


class DataProcessor:
    """
    Main data processing pipeline that normalizes, validates, and distributes ticks.
    Implements an event-driven architecture for downstream processing.
    """
    
    def __init__(self, window_sizes: List[int] = None):
        """
        Initialize the data processor.
        
        Args:
            window_sizes: List of window sizes to maintain
        """
        if window_sizes is None:
            window_sizes = [50, 100, 500, 1000, 5000, 10000]
        
        self.normalizer = DataNormalizer()
        self.window_manager = RollingWindowManager(window_sizes)
        
        # Processing queue for async processing
        self._processing_queue = queue.Queue(maxsize=10000)
        self._is_processing = False
        self._processor_thread: Optional[threading.Thread] = None
        self._stop_processing = threading.Event()
        
        # Statistics
        self.stats = {
            "ticks_processed": 0,
            "ticks_rejected": 0,
            "last_processed": None,
            "processing_rate": 0.0,
            "queue_size": 0,
            "start_time": datetime.now(),
            "total_processing_time": 0.0,
            "avg_processing_time": 0.0
        }
        
        # Processing time tracking
        self._processing_times = []
        self._max_processing_times = 100
        
        # Register event handlers
        self._register_event_handlers()
        
        logger.info("DataProcessor initialized")
        self._start_processor_thread()
    
    def _register_event_handlers(self):
        """Register event handlers for the processing pipeline."""
        # Subscribe to raw tick events
        event_bus.subscribe("raw_tick", self.process_tick, async_handler=False)
        
        # Subscribe to system events
        event_bus.subscribe("system_stop", self._handle_system_stop, async_handler=False)
        event_bus.subscribe("system_start", self._handle_system_start, async_handler=False)
        
        logger.info("Event handlers registered")
    
    def _start_processor_thread(self):
        """Start the background processor thread."""
        if self._processor_thread is None or not self._processor_thread.is_alive():
            self._stop_processing.clear()
            self._is_processing = True
            self._processor_thread = threading.Thread(
                target=self._processor_loop,
                name="DataProcessor",
                daemon=True
            )
            self._processor_thread.start()
            logger.info("Processor thread started")
    
    def _processor_loop(self):
        """Main processing loop running in background thread."""
        logger.info("Processor loop started")
        last_stats_time = datetime.now()
        processed_count = 0
        
        while not self._stop_processing.is_set():
            try:
                # Process items from queue with timeout
                try:
                    tick_data = self._processing_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Track processing time
                start_time = time.perf_counter()
                
                # Process the tick
                processed_tick = self._process_tick_sync(tick_data)
                
                # Calculate processing time
                processing_time = time.perf_counter() - start_time
                self._track_processing_time(processing_time)
                
                if processed_tick:
                    processed_count += 1
                    self.stats["ticks_processed"] += 1
                    self.stats["last_processed"] = datetime.now()
                    
                    # Emit processed tick event
                    event_bus.publish("processed_tick", processed_tick, "DataProcessor")
                    
                    # Emit window update event
                    stats = self.window_manager.get_all_stats()
                    event_bus.publish("window_updated", stats, "DataProcessor")
                else:
                    self.stats["ticks_rejected"] += 1
                
                self._processing_queue.task_done()
                self.stats["queue_size"] = self._processing_queue.qsize()
                
                # Update processing rate
                now = datetime.now()
                if (now - last_stats_time).total_seconds() >= 5:
                    rate = processed_count / 5.0
                    self.stats["processing_rate"] = rate
                    processed_count = 0
                    last_stats_time = now
                    
                    # Emit processing stats event
                    event_bus.publish("processing_stats", self.stats, "DataProcessor")
                
            except Exception as e:
                logger.error(f"Error in processor loop: {e}", exc_info=True)
                time.sleep(0.1)
        
        logger.info("Processor loop stopped")
    
    def _track_processing_time(self, processing_time: float):
        """Track processing times for performance monitoring."""
        self._processing_times.append(processing_time)
        if len(self._processing_times) > self._max_processing_times:
            self._processing_times = self._processing_times[-self._max_processing_times:]
        
        self.stats["total_processing_time"] += processing_time
        if self.stats["ticks_processed"] > 0:
            self.stats["avg_processing_time"] = (
                self.stats["total_processing_time"] / self.stats["ticks_processed"]
            )
    
    def _process_tick_sync(self, raw_data: Dict[str, Any]) -> Optional[Tick]:
        """
        Process a tick synchronously.
        
        Args:
            raw_data: Raw tick data
            
        Returns:
            Optional[Tick]: Processed tick or None
        """
        try:
            # Normalize the tick
            tick = self.normalizer.normalize_tick(raw_data)
            
            if not tick:
                logger.warning("Tick rejected by normalizer")
                return None
            
            # Add to rolling windows
            self.window_manager.add_tick(tick)
            
            return tick
            
        except Exception as e:
            logger.error(f"Error processing tick: {e}", exc_info=True)
            return None
    
    def process_tick(self, raw_data: Dict[str, Any]):
        """
        Process a tick asynchronously by adding to the processing queue.
        
        Args:
            raw_data: Raw tick data from WebSocket
        """
        try:
            # Check if queue is full
            if self._processing_queue.qsize() >= self._processing_queue.maxsize - 100:
                logger.warning("Processing queue is nearly full, consider increasing capacity")
            
            # Add to queue
            self._processing_queue.put(raw_data)
            
        except Exception as e:
            logger.error(f"Error queuing tick for processing: {e}", exc_info=True)
    
    def process_tick_sync(self, raw_data: Dict[str, Any]) -> Optional[Tick]:
        """
        Process a tick synchronously (for testing or immediate processing).
        
        Args:
            raw_data: Raw tick data
            
        Returns:
            Optional[Tick]: Processed tick or None
        """
        return self._process_tick_sync(raw_data)
    
    def _handle_system_stop(self, event):
        """Handle system stop event."""
        logger.info("Received system stop event, stopping processor...")
        self.stop()
    
    def _handle_system_start(self, event):
        """Handle system start event."""
        logger.info("Received system start event, starting processor...")
        self.start()
    
    def start(self):
        """Start the processing pipeline."""
        if not self._is_processing:
            self._start_processor_thread()
            logger.info("Processing pipeline started")
    
    def stop(self):
        """Stop the processing pipeline gracefully."""
        self._stop_processing.set()
        self._is_processing = False
        
        if self._processor_thread and self._processor_thread.is_alive():
            self._processor_thread.join(timeout=5)
        
        # Process remaining items in queue
        remaining = self._processing_queue.qsize()
        if remaining > 0:
            logger.info(f"Processing {remaining} remaining items in queue...")
            while not self._processing_queue.empty():
                try:
                    tick_data = self._processing_queue.get(timeout=0.1)
                    self._process_tick_sync(tick_data)
                    self._processing_queue.task_done()
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"Error processing remaining items: {e}")
        
        logger.info("Processing pipeline stopped")
    
    def get_window(self, size: int) -> List[Tick]:
        """
        Get a specific rolling window.
        
        Args:
            size: Window size
            
        Returns:
            List[Tick]: Window contents
        """
        return self.window_manager.get_window(size)
    
    def get_window_stats(self, size: int) -> Dict[str, Any]:
        """
        Get statistics for a specific window.
        
        Args:
            size: Window size
            
        Returns:
            Dict[str, Any]: Window statistics
        """
        return self.window_manager.get_window_summary(size)
    
    def get_all_windows_stats(self) -> Dict[int, Dict[str, Any]]:
        """
        Get statistics for all windows.
        
        Returns:
            Dict[int, Dict[str, Any]]: Statistics for all windows
        """
        stats = {}
        for size in self.window_manager.window_sizes:
            stats[size] = self.window_manager.get_window_summary(size)
        return stats
    
    def get_processor_stats(self) -> Dict[str, Any]:
        """
        Get processor statistics.
        
        Returns:
            Dict[str, Any]: Processor statistics
        """
        return {
            **self.stats,
            "queue_size": self._processing_queue.qsize(),
            "is_processing": self._is_processing,
            "window_sizes": self.window_manager.window_sizes,
            "normalizer_stats": self.normalizer.get_stats(),
            "overall_stats": self.window_manager.get_overall_stats(),
            "uptime": (datetime.now() - self.stats["start_time"]).total_seconds(),
            "performance": {
                "avg_processing_time_ms": self.stats["avg_processing_time"] * 1000,
                "processing_rate_per_sec": self.stats["processing_rate"]
            }
        }
    
    def get_transition_matrix(self, window_size: int = 100) -> np.ndarray:
        """
        Get transition probability matrix for a window.
        
        Args:
            window_size: Window size
            
        Returns:
            np.ndarray: 10x10 transition matrix
        """
        return self.window_manager.get_transition_matrix(window_size)
    
    def get_digit_frequency(self, window_size: int = 100) -> Dict[int, int]:
        """
        Get digit frequency for a window.
        
        Args:
            window_size: Window size
            
        Returns:
            Dict[int, int]: Digit frequencies
        """
        return self.window_manager.get_digit_frequency(window_size)
    
    def get_digit_probability(self, window_size: int = 100) -> Dict[int, float]:
        """
        Get digit probability for a window.
        
        Args:
            window_size: Window size
            
        Returns:
            Dict[int, float]: Digit probabilities
        """
        return self.window_manager.get_digit_probability(window_size)
    
    def get_last_digits(self, count: int = 100) -> List[int]:
        """
        Get the last N digits.
        
        Args:
            count: Number of digits to retrieve
            
        Returns:
            List[int]: List of last digits
        """
        return self.window_manager.get_last_digits(count)
    
    def clear(self):
        """Clear all data from the processor."""
        self.window_manager.clear()
        self.stats["ticks_processed"] = 0
        self.stats["ticks_rejected"] = 0
        self.stats["total_processing_time"] = 0.0
        self.stats["avg_processing_time"] = 0.0
        self._processing_times.clear()
        logger.info("Data processor cleared")
    
    def reset_stats(self):
        """Reset processor statistics."""
        self.stats = {
            "ticks_processed": 0,
            "ticks_rejected": 0,
            "last_processed": None,
            "processing_rate": 0.0,
            "queue_size": 0,
            "start_time": datetime.now(),
            "total_processing_time": 0.0,
            "avg_processing_time": 0.0
        }
        self._processing_times.clear()
        self.normalizer.reset_stats()
        logger.info("Processor statistics reset")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop()
