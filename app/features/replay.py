"""
Historical Replay Module
Enables replay of historical tick data for analysis and testing.
"""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import time
import threading
import queue

from ..core.types import Tick
from ..core.logger import get_logger
from ..storage.database import DatabaseManager
from ..data.event_bus import event_bus

logger = get_logger(__name__)


class HistoricalReplay:
    """
    Replays historical tick data with configurable speed.
    Supports pause, resume, and speed control.
    """
    
    def __init__(self):
        """Initialize the historical replay engine."""
        self.database = DatabaseManager()
        self._replay_thread: Optional[threading.Thread] = None
        self._replay_queue: queue.Queue = queue.Queue()
        self._is_replaying = False
        self._is_paused = False
        self._replay_speed = 1.0
        self._replay_ticks: List[Tick] = []
        self._current_index = 0
        self._start_time: Optional[datetime] = None
        self._callback: Optional[Callable] = None
        self._stop_replay = threading.Event()
        
        logger.info("HistoricalReplay initialized")
    
    def load_session(self, session_id: str) -> bool:
        """
        Load a session for replay.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            bool: True if successful
        """
        try:
            ticks_data = self.database.get_ticks(session_id=session_id, limit=1000000)
            if not ticks_data:
                logger.warning(f"No ticks found for session {session_id}")
                return False
            
            # Convert to Tick objects
            self._replay_ticks = []
            for data in ticks_data:
                tick = Tick(
                    tick_id=data['tick_id'],
                    symbol=data['symbol'],
                    price=data['price'],
                    last_digit=data['last_digit'],
                    timestamp=datetime.fromtimestamp(data['timestamp'])
                )
                self._replay_ticks.append(tick)
            
            logger.info(f"Loaded {len(self._replay_ticks)} ticks for replay")
            return True
            
        except Exception as e:
            logger.error(f"Error loading session for replay: {e}")
            return False
    
    def load_ticks(self, ticks: List[Tick]) -> bool:
        """
        Load ticks for replay.
        
        Args:
            ticks: List of tick objects
            
        Returns:
            bool: True if successful
        """
        self._replay_ticks = ticks
        logger.info(f"Loaded {len(ticks)} ticks for replay")
        return True
    
    def start_replay(self, speed: float = 1.0, callback: Optional[Callable] = None):
        """
        Start replaying loaded ticks.
        
        Args:
            speed: Replay speed multiplier
            callback: Callback function for each tick
        """
        if not self._replay_ticks:
            logger.warning("No ticks loaded for replay")
            return
        
        if self._is_replaying:
            logger.warning("Replay already in progress")
            return
        
        self._replay_speed = speed
        self._callback = callback
        self._is_replaying = True
        self._is_paused = False
        self._current_index = 0
        self._start_time = datetime.now()
        self._stop_replay.clear()
        
        # Start replay thread
        self._replay_thread = threading.Thread(
            target=self._replay_loop,
            name="HistoricalReplay",
            daemon=True
        )
        self._replay_thread.start()
        
        logger.info(f"Started replay with speed {speed}x")
        event_bus.publish("replay_started", {"speed": speed}, "HistoricalReplay")
    
    def _replay_loop(self):
        """Main replay loop running in background thread."""
        try:
            while not self._stop_replay.is_set() and self._current_index < len(self._replay_ticks):
                if self._is_paused:
                    time.sleep(0.1)
                    continue
                
                # Get current tick
                tick = self._replay_ticks[self._current_index]
                
                # Emit tick event
                event_bus.publish("processed_tick", tick, "HistoricalReplay")
                
                # Call callback if provided
                if self._callback:
                    try:
                        self._callback(tick)
                    except Exception as e:
                        logger.error(f"Error in replay callback: {e}")
                
                self._current_index += 1
                
                # Calculate delay based on speed
                if self._current_index < len(self._replay_ticks):
                    next_tick = self._replay_ticks[self._current_index]
                    time_diff = (next_tick.timestamp - tick.timestamp).total_seconds()
                    if time_diff > 0:
                        delay = time_diff / self._replay_speed
                        # Cap delay to prevent issues
                        if delay > 5.0:
                            delay = 5.0
                        time.sleep(delay)
            
            # Replay finished
            self._is_replaying = False
            event_bus.publish("replay_finished", {
                "total_ticks": len(self._replay_ticks),
                "duration": (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
            }, "HistoricalReplay")
            logger.info("Replay finished")
            
        except Exception as e:
            logger.error(f"Error in replay loop: {e}")
            self._is_replaying = False
    
    def pause_replay(self):
        """Pause the replay."""
        if self._is_replaying and not self._is_paused:
            self._is_paused = True
            event_bus.publish("replay_paused", {}, "HistoricalReplay")
            logger.info("Replay paused")
    
    def resume_replay(self):
        """Resume the replay."""
        if self._is_replaying and self._is_paused:
            self._is_paused = False
            event_bus.publish("replay_resumed", {}, "HistoricalReplay")
            logger.info("Replay resumed")
    
    def stop_replay(self):
        """Stop the replay."""
        if self._is_replaying:
            self._stop_replay.set()
            self._is_replaying = False
            self._is_paused = False
            
            if self._replay_thread and self._replay_thread.is_alive():
                self._replay_thread.join(timeout=5)
            
            event_bus.publish("replay_stopped", {}, "HistoricalReplay")
            logger.info("Replay stopped")
    
    def set_speed(self, speed: float):
        """
        Set replay speed.
        
        Args:
            speed: Speed multiplier
        """
        self._replay_speed = max(0.1, min(speed, 10.0))
        event_bus.publish("replay_speed_changed", {"speed": self._replay_speed}, "HistoricalReplay")
        logger.info(f"Replay speed set to {self._replay_speed}x")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get replay status.
        
        Returns:
            Dict[str, Any]: Status information
        """
        total = len(self._replay_ticks)
        progress = (self._current_index / total * 100) if total > 0 else 0
        
        return {
            'is_replaying': self._is_replaying,
            'is_paused': self._is_paused,
            'speed': self._replay_speed,
            'total_ticks': total,
            'current_index': self._current_index,
            'progress': progress,
            'duration': (datetime.now() - self._start_time).total_seconds() if self._start_time and self._is_replaying else 0,
            'start_time': self._start_time
        }
    
    def seek_to(self, position: float):
        """
        Seek to a position in the replay.
        
        Args:
            position: Position as percentage (0-100)
        """
        if not self._replay_ticks:
            return
        
        position = max(0, min(position, 100))
        self._current_index = int(len(self._replay_ticks) * position / 100)
        logger.info(f"Seeked to {position:.1f}%")