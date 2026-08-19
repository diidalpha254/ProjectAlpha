"""
Tick Recording Module
Records live tick data to storage for later analysis.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import threading

from core.types import Tick
from core.logger import get_logger
from storage.database import DatabaseManager
from data.event_bus import event_bus

logger = get_logger(__name__)


class TickRecorder:
    """
    Records incoming ticks to database with configurable options.
    Supports automatic and manual recording modes.
    """
    
    def __init__(self):
        """Initialize the tick recorder."""
        self.database = DatabaseManager()
        self._is_recording = False
        self._recording_session_id: Optional[str] = None
        self._buffer: List[Tick] = []
        self._buffer_size = 100
        self._max_duration = 3600  # 1 hour
        self._start_time: Optional[datetime] = None
        self._recorded_count = 0
        self._lock = threading.Lock()
        
        # Register event handler
        event_bus.subscribe('processed_tick', self._handle_tick, async_handler=False)
        
        logger.info("TickRecorder initialized")
    
    def start_recording(self, symbol: str, buffer_size: int = 100, max_duration: int = 3600):
        """
        Start recording ticks.
        
        Args:
            symbol: Trading symbol
            buffer_size: Number of ticks to buffer before saving
            max_duration: Maximum recording duration in seconds
        """
        with self._lock:
            if self._is_recording:
                logger.warning("Recording already in progress")
                return
            
            # Create session
            self._recording_session_id = self.database.create_session(symbol)
            self._is_recording = True
            self._buffer_size = buffer_size
            self._max_duration = max_duration
            self._start_time = datetime.now()
            self._recorded_count = 0
            self._buffer = []
            
            event_bus.publish("recording_started", {
                "session_id": self._recording_session_id,
                "symbol": symbol
            }, "TickRecorder")
            
            logger.info(f"Started recording session {self._recording_session_id}")
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording and save remaining ticks.
        
        Returns:
            Optional[str]: Session ID
        """
        with self._lock:
            if not self._is_recording:
                logger.warning("No recording in progress")
                return None
            
            # Save remaining ticks
            if self._buffer:
                self._flush_buffer()
            
            session_id = self._recording_session_id
            self._is_recording = False
            self._recording_session_id = None
            
            event_bus.publish("recording_stopped", {
                "session_id": session_id,
                "total_ticks": self._recorded_count,
                "duration": (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
            }, "TickRecorder")
            
            logger.info(f"Stopped recording session {session_id} with {self._recorded_count} ticks")
            return session_id
    
    def _handle_tick(self, event):
        """Handle incoming tick from event bus."""
        if not self._is_recording:
            return
        
        tick = event.data
        with self._lock:
            self._buffer.append(tick)
            self._recorded_count += 1
            
            # Check buffer size
            if len(self._buffer) >= self._buffer_size:
                self._flush_buffer()
            
            # Check duration
            if self._start_time and self._max_duration > 0:
                duration = (datetime.now() - self._start_time).total_seconds()
                if duration >= self._max_duration:
                    logger.info(f"Recording reached max duration ({self._max_duration}s)")
                    self.stop_recording()
    
    def _flush_buffer(self):
        """Save buffer to database."""
        if not self._buffer:
            return
        
        try:
            saved = self.database.save_ticks_batch(self._buffer, self._recording_session_id)
            self._buffer = []
            logger.debug(f"Flushed {saved} ticks to database")
            
        except Exception as e:
            logger.error(f"Error flushing buffer: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get recording status.
        
        Returns:
            Dict[str, Any]: Status information
        """
        duration = 0
        if self._start_time and self._is_recording:
            duration = (datetime.now() - self._start_time).total_seconds()
        
        return {
            'is_recording': self._is_recording,
            'session_id': self._recording_session_id,
            'recorded_count': self._recorded_count,
            'buffer_size': len(self._buffer),
            'duration': duration,
            'max_duration': self._max_duration,
            'start_time': self._start_time
        }
    
    def set_buffer_size(self, size: int):
        """
        Set buffer size.
        
        Args:
            size: Number of ticks to buffer before saving
        """
        self._buffer_size = max(10, min(size, 1000))
        logger.info(f"Buffer size set to {self._buffer_size}")
    
    def set_max_duration(self, seconds: int):
        """
        Set maximum recording duration.
        
        Args:
            seconds: Maximum duration in seconds (0 = unlimited)
        """
        self._max_duration = max(0, seconds)
        logger.info(f"Max duration set to {self._max_duration}s")
