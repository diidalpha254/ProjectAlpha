"""
Search Module
Searches historical sessions and data for patterns and analysis.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd

from ..core.types import Tick
from ..core.logger import get_logger
from ..storage.database import DatabaseManager

logger = get_logger(__name__)


class SearchEngine:
    """
    Searches historical data for patterns, anomalies, and insights.
    """
    
    def __init__(self):
        """Initialize the search engine."""
        self.database = DatabaseManager()
        logger.info("SearchEngine initialized")
    
    def search_sessions(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_ticks: Optional[int] = None,
        max_ticks: Optional[int] = None,
        min_volatility: Optional[float] = None,
        max_volatility: Optional[float] = None,
        state: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search sessions based on criteria.
        
        Args:
            symbol: Symbol filter
            start_date: Start date filter
            end_date: End date filter
            min_ticks: Minimum ticks
            max_ticks: Maximum ticks
            min_volatility: Minimum volatility
            max_volatility: Maximum volatility
            state: Market state
            limit: Maximum results
            
        Returns:
            List[Dict[str, Any]]: Matching sessions
        """
        try:
            # Get sessions from database
            sessions = self.database.get_sessions(symbol=symbol, limit=1000)
            
            # Filter sessions
            results = []
            for session in sessions:
                # Date filters
                if start_date and session['start_time'] < start_date.timestamp():
                    continue
                if end_date and session['start_time'] > end_date.timestamp():
                    continue
                
                # Tick count filters
                if min_ticks and session['total_ticks'] < min_ticks:
                    continue
                if max_ticks and session['total_ticks'] > max_ticks:
                    continue
                
                # Volatility filters
                if min_volatility and session['volatility'] < min_volatility:
                    continue
                if max_volatility and session['volatility'] > max_volatility:
                    continue
                
                # State filter
                if state and session.get('metadata'):
                    import json
                    try:
                        metadata = json.loads(session['metadata'])
                        if state not in metadata.get('market_states', []):
                            continue
                    except:
                        pass
                
                results.append(session)
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching sessions: {e}")
            return []
    
    def search_patterns(
        self,
        pattern: List[int],
        sessions: List[str],
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for specific patterns in sessions.
        
        Args:
            pattern: Pattern to search for (list of digits)
            sessions: List of session IDs
            limit: Maximum results
            
        Returns:
            List[Dict[str, Any]]: Matches found
        """
        results = []
        
        try:
            for session_id in sessions:
                ticks = self.database.get_ticks(session_id=session_id, limit=10000)
                digits = [t['last_digit'] for t in ticks]
                
                # Search for pattern
                matches = []
                pattern_len = len(pattern)
                for i in range(len(digits) - pattern_len + 1):
                    if digits[i:i+pattern_len] == pattern:
                        matches.append({
                            'position': i,
                            'timestamp': ticks[i]['timestamp'],
                            'price': ticks[i]['price']
                        })
                
                if matches:
                    results.append({
                        'session_id': session_id,
                        'matches': matches,
                        'total_matches': len(matches)
                    })
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching patterns: {e}")
            return []
    
    def search_anomalies(
        self,
        sessions: List[str],
        threshold: float = 2.0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for anomalies in sessions.
        
        Args:
            sessions: List of session IDs
            threshold: Anomaly threshold (z-score)
            limit: Maximum results
            
        Returns:
            List[Dict[str, Any]]: Anomalies found
        """
        anomalies = []
        
        try:
            for session_id in sessions:
                ticks = self.database.get_ticks(session_id=session_id, limit=10000)
                if not ticks:
                    continue
                
                prices = [t['price'] for t in ticks]
                digits = [t['last_digit'] for t in ticks]
                
                # Price anomalies
                import numpy as np
                mean_price = np.mean(prices)
                std_price = np.std(prices)
                
                for i, price in enumerate(prices):
                    z_score = (price - mean_price) / std_price if std_price > 0 else 0
                    if abs(z_score) > threshold:
                        anomalies.append({
                            'session_id': session_id,
                            'type': 'price_anomaly',
                            'position': i,
                            'price': price,
                            'z_score': z_score,
                            'timestamp': ticks[i]['timestamp']
                        })
                
                # Digit anomalies (unusual runs)
                for i in range(len(digits) - 1):
                    if digits[i] == digits[i+1]:
                        # Check for long runs
                        run_length = 1
                        for j in range(i+1, len(digits)):
                            if digits[j] == digits[i]:
                                run_length += 1
                            else:
                                break
                        
                        if run_length > 5:  # Long run anomaly
                            anomalies.append({
                                'session_id': session_id,
                                'type': 'digit_run_anomaly',
                                'position': i,
                                'digit': digits[i],
                                'run_length': run_length,
                                'timestamp': ticks[i]['timestamp']
                            })
                
                if len(anomalies) >= limit:
                    break
            
            return anomalies[:limit]
            
        except Exception as e:
            logger.error(f"Error searching anomalies: {e}")
            return []
    
    def search_digit_sequence(
        self,
        sequence: str,
        sessions: List[str],
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for a specific digit sequence.
        
        Args:
            sequence: Digit sequence as string
            sessions: List of session IDs
            limit: Maximum results
            
        Returns:
            List[Dict[str, Any]]: Matches found
        """
        pattern = [int(c) for c in sequence if c.isdigit()]
        return self.search_patterns(pattern, sessions, limit)