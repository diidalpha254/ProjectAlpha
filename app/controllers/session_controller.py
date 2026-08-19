"""
Session Controller Module
Manages trading sessions, historical data, and session persistence.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
import pandas as pd

from core.types import Tick, SessionStats
from core.logger import get_logger
from storage.database import DatabaseManager


logger = get_logger(__name__)


class SessionController:
    """
    Manages trading sessions including creation, updating, and persistence.
    """
    
    def __init__(self):
        """Initialize the session controller."""
        self.database = DatabaseManager()
        self._current_session_id: Optional[str] = None
        self._session_ticks: List[Tick] = []
        self._session_start: Optional[datetime] = None
        logger.info("SessionController initialized")
    
    def create_session(self, symbol: str) -> str:
        """
        Create a new trading session.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            str: Session ID
        """
        session_id = self.database.create_session(symbol)
        self._current_session_id = session_id
        self._session_start = datetime.now()
        self._session_ticks = []
        
        logger.info(f"Created session {session_id} for {symbol}")
        return session_id
    
    def add_tick(self, tick: Tick):
        """
        Add a tick to the current session.
        
        Args:
            tick: Tick object
        """
        if not self._current_session_id:
            self.create_session(tick.symbol)
        
        self._session_ticks.append(tick)
        
        # Save to database periodically (every 100 ticks)
        if len(self._session_ticks) % 100 == 0:
            self._save_ticks_batch()
    
    def _save_ticks_batch(self):
        """Save pending ticks to database."""
        if not self._current_session_id or not self._session_ticks:
            return
        
        try:
            # Get last 100 ticks
            batch = self._session_ticks[-100:]
            self.database.save_ticks_batch(batch, self._current_session_id)
            
        except Exception as e:
            logger.error(f"Error saving ticks batch: {e}")
    
    def end_session(self) -> Optional[SessionStats]:
        """
        End the current session and calculate statistics.
        
        Returns:
            Optional[SessionStats]: Session statistics
        """
        if not self._current_session_id:
            logger.warning("No active session to end")
            return None
        
        try:
            # Save remaining ticks
            if self._session_ticks:
                self.database.save_ticks_batch(self._session_ticks, self._current_session_id)
            
            # Calculate session statistics
            stats = self._calculate_session_stats()
            
            # Update session in database
            self.database.update_session(self._current_session_id, stats)
            
            logger.info(f"Ended session {self._current_session_id}")
            
            # Reset session state
            session_id = self._current_session_id
            self._current_session_id = None
            self._session_ticks = []
            self._session_start = None
            
            return stats
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return None
    
    def _calculate_session_stats(self) -> SessionStats:
        """Calculate statistics for the current session."""
        if not self._session_ticks:
            return SessionStats(
                session_id=self._current_session_id,
                start_time=self._session_start or datetime.now(),
                total_ticks=0
            )
        
        ticks = self._session_ticks
        prices = [float(t.price) for t in ticks]
        digits = [t.last_digit for t in ticks]
        
        # Calculate digit counts
        digit_counts = {i: 0 for i in range(10)}
        for digit in digits:
            digit_counts[digit] = digit_counts.get(digit, 0) + 1
        
        # Find most common digit
        most_common = max(digit_counts.items(), key=lambda x: x[1])[0] if digit_counts else None
        
        # Calculate statistics
        import numpy as np
        volatility = np.std(prices) if prices else 0
        
        # Calculate entropy
        total = len(digits)
        entropy = 0
        for count in digit_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * np.log2(p)
        
        return SessionStats(
            session_id=self._current_session_id,
            start_time=self._session_start or datetime.now(),
            end_time=datetime.now(),
            total_ticks=len(ticks),
            symbol=ticks[0].symbol if ticks else "",
            average_price=np.mean(prices) if prices else 0,
            max_price=max(prices) if prices else 0,
            min_price=min(prices) if prices else 0,
            digit_counts=digit_counts,
            most_common_digit=most_common,
            volatility=volatility,
            entropy=entropy,
            market_states=[]
        )
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session details by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[Dict[str, Any]]: Session data
        """
        return self.database.get_session(session_id)
    
    def get_sessions(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of sessions.
        
        Args:
            symbol: Filter by symbol
            limit: Maximum number of sessions
            
        Returns:
            List[Dict[str, Any]]: List of sessions
        """
        return self.database.get_sessions(symbol, limit)
    
    def get_session_ticks(self, session_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get ticks for a specific session.
        
        Args:
            session_id: Session ID
            limit: Maximum number of ticks
            
        Returns:
            List[Dict[str, Any]]: List of ticks
        """
        return self.database.get_ticks(session_id=session_id, limit=limit)
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[Dict[str, Any]]: Session statistics
        """
        return self.database.get_tick_statistics(session_id=session_id)
    
    def export_session(self, session_id: str, format: str = 'csv') -> Optional[str]:
        """
        Export session data.
        
        Args:
            session_id: Session ID
            format: Export format ('csv' or 'json')
            
        Returns:
            Optional[str]: Exported data as string
        """
        try:
            ticks = self.get_session_ticks(session_id, limit=1000000)
            if not ticks:
                return None
            
            if format == 'csv':
                # Convert to DataFrame
                df = pd.DataFrame(ticks)
                return df.to_csv(index=False)
            elif format == 'json':
                import json
                return json.dumps(ticks, default=str)
            else:
                logger.warning(f"Unsupported format: {format}")
                return None
                
        except Exception as e:
            logger.error(f"Error exporting session: {e}")
            return None
    
    def get_current_session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self._current_session_id
    
    def get_session_duration(self) -> Optional[float]:
        """Get duration of current session in seconds."""
        if not self._session_start:
            return None
        return (datetime.now() - self._session_start).total_seconds()
    
    def get_session_tick_count(self) -> int:
        """Get number of ticks in current session."""
        return len(self._session_ticks)
