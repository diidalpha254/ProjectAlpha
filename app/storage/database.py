"""
SQLite Database Manager
Handles all database operations with connection pooling, query optimization,
and schema management for Project Alpha.
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import threading
from contextlib import contextmanager

from ..core.types import Tick, SessionStats
from ..core.exceptions import StorageError
from ..core.logger import get_logger
from ..core.config import settings

logger = get_logger(__name__)


class DatabaseManager:
    """
    Production-grade SQLite database manager with:
    - Connection pooling with thread safety
    - Automatic schema creation and migration
    - Efficient query optimization
    - Comprehensive error handling
    - Write-ahead logging for better concurrency
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the database manager."""
        if hasattr(self, '_initialized'):
            return
            
        self.db_path = settings.get("storage.database_path", "data/project_alpha.db")
        self._local = threading.local()
        self._initialized = True
        
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
        self._create_indexes()
        
        logger.info(f"DatabaseManager initialized with path: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """
        Get a database connection with context manager support.
        Thread-local connections for better performance.
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            try:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=30.0,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
                )
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=-10000")  # 10MB cache
                conn.execute("PRAGMA foreign_keys=ON")
                conn.row_factory = sqlite3.Row
                self._local.connection = conn
                logger.debug("New database connection created")
            except sqlite3.Error as e:
                raise StorageError(f"Failed to connect to database: {e}")
        
        conn = self._local.connection
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise StorageError(f"Database operation failed: {e}")
        finally:
            # Don't close connection; keep it for reuse
            pass
    
    def _initialize_database(self):
        """Initialize database schema."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create tables
                cursor.executescript("""
                    -- Ticks table
                    CREATE TABLE IF NOT EXISTS ticks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tick_id TEXT UNIQUE NOT NULL,
                        symbol TEXT NOT NULL,
                        price REAL NOT NULL,
                        last_digit INTEGER NOT NULL,
                        bid REAL,
                        ask REAL,
                        volume INTEGER,
                        timestamp INTEGER NOT NULL,
                        epoch INTEGER NOT NULL,
                        created_at INTEGER NOT NULL,
                        session_id TEXT
                    );
                    
                    -- Sessions table
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        start_time INTEGER NOT NULL,
                        end_time INTEGER,
                        total_ticks INTEGER DEFAULT 0,
                        average_price REAL DEFAULT 0,
                        max_price REAL DEFAULT 0,
                        min_price REAL DEFAULT 0,
                        volatility REAL DEFAULT 0,
                        entropy REAL DEFAULT 0,
                        most_common_digit INTEGER,
                        metadata TEXT,
                        created_at INTEGER NOT NULL
                    );
                    
                    -- Analytics cache table
                    CREATE TABLE IF NOT EXISTS analytics_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        window_size INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        analysis_type TEXT NOT NULL,
                        data TEXT NOT NULL,
                        computed_at INTEGER NOT NULL,
                        expires_at INTEGER NOT NULL,
                        UNIQUE(window_size, symbol, analysis_type)
                    );
                    
                    -- Market states table
                    CREATE TABLE IF NOT EXISTS market_states (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        state TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        risk_level TEXT NOT NULL,
                        indicators TEXT NOT NULL,
                        evidence TEXT NOT NULL,
                        explanation TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    );
                    
                    -- Notifications table
                    CREATE TABLE IF NOT EXISTS notifications (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        read INTEGER DEFAULT 0,
                        action TEXT,
                        data TEXT,
                        created_at INTEGER NOT NULL
                    );
                    
                    -- System health table
                    CREATE TABLE IF NOT EXISTS system_health (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        component TEXT NOT NULL,
                        status TEXT NOT NULL,
                        message TEXT,
                        timestamp INTEGER NOT NULL
                    );
                """)
                
                conn.commit()
                logger.info("Database schema initialized successfully")
                
        except sqlite3.Error as e:
            raise StorageError(f"Failed to initialize database schema: {e}")
    
    def _create_indexes(self):
        """Create indexes for performance optimization."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Index for tick queries
                cursor.executescript("""
                    CREATE INDEX IF NOT EXISTS idx_ticks_symbol ON ticks(symbol);
                    CREATE INDEX IF NOT EXISTS idx_ticks_timestamp ON ticks(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_ticks_session ON ticks(session_id);
                    CREATE INDEX IF NOT EXISTS idx_ticks_symbol_timestamp ON ticks(symbol, timestamp);
                    CREATE INDEX IF NOT EXISTS idx_ticks_last_digit ON ticks(last_digit);
                    
                    -- Index for session queries
                    CREATE INDEX IF NOT EXISTS idx_sessions_symbol ON sessions(symbol);
                    CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time);
                    CREATE INDEX IF NOT EXISTS idx_sessions_end_time ON sessions(end_time);
                    
                    -- Index for market states
                    CREATE INDEX IF NOT EXISTS idx_market_states_session ON market_states(session_id);
                    CREATE INDEX IF NOT EXISTS idx_market_states_timestamp ON market_states(timestamp);
                    
                    -- Index for notifications
                    CREATE INDEX IF NOT EXISTS idx_notifications_timestamp ON notifications(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
                """)
                
                conn.commit()
                logger.info("Database indexes created successfully")
                
        except sqlite3.Error as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    def save_tick(self, tick: Tick, session_id: Optional[str] = None) -> bool:
        """
        Save a tick to the database.
        
        Args:
            tick: Tick object to save
            session_id: Optional session ID for grouping
            
        Returns:
            bool: True if successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO ticks (
                        tick_id, symbol, price, last_digit, bid, ask, volume,
                        timestamp, epoch, created_at, session_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tick.tick_id,
                    tick.symbol,
                    float(tick.price),
                    tick.last_digit,
                    float(tick.bid) if tick.bid else None,
                    float(tick.ask) if tick.ask else None,
                    tick.volume,
                    int(tick.timestamp.timestamp()),
                    int(tick.timestamp.timestamp()),
                    int(datetime.now().timestamp()),
                    session_id
                ))
                
                conn.commit()
                logger.debug(f"Saved tick {tick.tick_id} to database")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to save tick: {e}")
            return False
    
    def save_ticks_batch(self, ticks: List[Tick], session_id: Optional[str] = None) -> int:
        """
        Save multiple ticks in batch for better performance.
        
        Args:
            ticks: List of Tick objects
            session_id: Optional session ID
            
        Returns:
            int: Number of ticks saved
        """
        if not ticks:
            return 0
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                data = []
                current_time = int(datetime.now().timestamp())
                
                for tick in ticks:
                    data.append((
                        tick.tick_id,
                        tick.symbol,
                        float(tick.price),
                        tick.last_digit,
                        float(tick.bid) if tick.bid else None,
                        float(tick.ask) if tick.ask else None,
                        tick.volume,
                        int(tick.timestamp.timestamp()),
                        int(tick.timestamp.timestamp()),
                        current_time,
                        session_id
                    ))
                
                cursor.executemany("""
                    INSERT OR IGNORE INTO ticks (
                        tick_id, symbol, price, last_digit, bid, ask, volume,
                        timestamp, epoch, created_at, session_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, data)
                
                conn.commit()
                saved_count = len(data)
                logger.info(f"Saved {saved_count} ticks in batch")
                return saved_count
                
        except sqlite3.Error as e:
            logger.error(f"Failed to save ticks batch: {e}")
            return 0
    
    def create_session(self, symbol: str) -> str:
        """
        Create a new session.
        
        Args:
            symbol: Trading symbol for the session
            
        Returns:
            str: Session ID
        """
        import uuid
        session_id = str(uuid.uuid4())
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO sessions (
                        id, symbol, start_time, created_at
                    ) VALUES (?, ?, ?, ?)
                """, (
                    session_id,
                    symbol,
                    int(datetime.now().timestamp()),
                    int(datetime.now().timestamp())
                ))
                
                conn.commit()
                logger.info(f"Created new session: {session_id}")
                return session_id
                
        except sqlite3.Error as e:
            raise StorageError(f"Failed to create session: {e}")
    
    def update_session(self, session_id: str, stats: SessionStats) -> bool:
        """
        Update session statistics.
        
        Args:
            session_id: Session ID to update
            stats: SessionStats object
            
        Returns:
            bool: True if successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE sessions SET
                        end_time = ?,
                        total_ticks = ?,
                        average_price = ?,
                        max_price = ?,
                        min_price = ?,
                        volatility = ?,
                        entropy = ?,
                        most_common_digit = ?,
                        metadata = ?
                    WHERE id = ?
                """, (
                    int(stats.end_time.timestamp()) if stats.end_time else None,
                    stats.total_ticks,
                    stats.average_price,
                    stats.max_price,
                    stats.min_price,
                    stats.volatility,
                    stats.entropy,
                    stats.most_common_digit,
                    json.dumps({
                        "digit_counts": stats.digit_counts,
                        "market_states": [s.value for s in stats.market_states]
                    }),
                    session_id
                ))
                
                conn.commit()
                logger.info(f"Updated session: {session_id}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to update session: {e}")
            return False
    
    def get_ticks(
        self,
        symbol: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve ticks with filtering options.
        
        Args:
            symbol: Filter by symbol
            limit: Maximum number of ticks
            offset: Offset for pagination
            start_time: Start time filter
            end_time: End time filter
            session_id: Filter by session
            
        Returns:
            List[Dict[str, Any]]: List of tick records
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM ticks WHERE 1=1"
                params = []
                
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(int(start_time.timestamp()))
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(int(end_time.timestamp()))
                
                if session_id:
                    query += " AND session_id = ?"
                    params.append(session_id)
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve ticks: {e}")
            return []
    
    def get_latest_ticks(self, symbol: str, count: int = 100) -> List[Dict[str, Any]]:
        """
        Get the latest ticks for a symbol.
        
        Args:
            symbol: Trading symbol
            count: Number of ticks to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of tick records
        """
        return self.get_ticks(symbol=symbol, limit=count)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session details by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[Dict[str, Any]]: Session data or None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()
                
                return dict(row) if row else None
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    def get_sessions(
        self,
        symbol: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get list of sessions.
        
        Args:
            symbol: Filter by symbol
            limit: Maximum number of sessions
            offset: Offset for pagination
            
        Returns:
            List[Dict[str, Any]]: List of sessions
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM sessions WHERE 1=1"
                params = []
                
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                
                query += " ORDER BY start_time DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get sessions: {e}")
            return []
    
    def save_market_state(
        self,
        session_id: str,
        state: str,
        confidence: float,
        risk_level: str,
        indicators: Dict[str, float],
        evidence: List[str],
        explanation: str
    ) -> bool:
        """
        Save market state analysis.
        
        Args:
            session_id: Session ID
            state: Market state classification
            confidence: Confidence score
            risk_level: Risk level
            indicators: Dictionary of indicators
            evidence: List of evidence strings
            explanation: Text explanation
            
        Returns:
            bool: True if successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO market_states (
                        session_id, state, confidence, risk_level,
                        indicators, evidence, explanation, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    state,
                    confidence,
                    risk_level,
                    json.dumps(indicators),
                    json.dumps(evidence),
                    explanation,
                    int(datetime.now().timestamp())
                ))
                
                conn.commit()
                logger.info(f"Saved market state for session {session_id}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to save market state: {e}")
            return False
    
    def get_market_states(
        self,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get market state history.
        
        Args:
            session_id: Filter by session
            limit: Maximum number of records
            
        Returns:
            List[Dict[str, Any]]: List of market state records
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM market_states WHERE 1=1"
                params = []
                
                if session_id:
                    query += " AND session_id = ?"
                    params.append(session_id)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    record = dict(row)
                    record['indicators'] = json.loads(record['indicators'])
                    record['evidence'] = json.loads(record['evidence'])
                    results.append(record)
                
                return results
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get market states: {e}")
            return []
    
    def save_analytics_cache(
        self,
        window_size: int,
        symbol: str,
        analysis_type: str,
        data: Dict[str, Any],
        ttl_seconds: int = 300
    ) -> bool:
        """
        Save analytics results to cache.
        
        Args:
            window_size: Window size
            symbol: Trading symbol
            analysis_type: Type of analysis
            data: Analytics data
            ttl_seconds: Cache TTL in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            now = int(datetime.now().timestamp())
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO analytics_cache (
                        window_size, symbol, analysis_type, data,
                        computed_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    window_size,
                    symbol,
                    analysis_type,
                    json.dumps(data),
                    now,
                    now + ttl_seconds
                ))
                
                conn.commit()
                logger.debug(f"Saved analytics cache: {analysis_type} for {symbol}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to save analytics cache: {e}")
            return False
    
    def get_analytics_cache(
        self,
        window_size: int,
        symbol: str,
        analysis_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get analytics from cache.
        
        Args:
            window_size: Window size
            symbol: Trading symbol
            analysis_type: Type of analysis
            
        Returns:
            Optional[Dict[str, Any]]: Cached data or None
        """
        try:
            now = int(datetime.now().timestamp())
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT data FROM analytics_cache
                    WHERE window_size = ? AND symbol = ? AND analysis_type = ?
                    AND expires_at > ?
                """, (window_size, symbol, analysis_type, now))
                
                row = cursor.fetchone()
                
                if row:
                    return json.loads(row['data'])
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get analytics cache: {e}")
            return None
    
    def save_notification(self, notification: Dict[str, Any]) -> bool:
        """
        Save a notification.
        
        Args:
            notification: Notification data
            
        Returns:
            bool: True if successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO notifications (
                        id, type, message, timestamp, read, action, data, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    notification['id'],
                    notification['type'],
                    notification['message'],
                    int(notification['timestamp'].timestamp()),
                    1 if notification.get('read', False) else 0,
                    notification.get('action'),
                    json.dumps(notification.get('data', {})),
                    int(datetime.now().timestamp())
                ))
                
                conn.commit()
                logger.debug(f"Saved notification: {notification['id']}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to save notification: {e}")
            return False
    
    def get_notifications(
        self,
        limit: int = 100,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get notifications.
        
        Args:
            limit: Maximum number of notifications
            unread_only: Only get unread notifications
            
        Returns:
            List[Dict[str, Any]]: List of notifications
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM notifications WHERE 1=1"
                params = []
                
                if unread_only:
                    query += " AND read = 0"
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    record = dict(row)
                    record['data'] = json.loads(record['data']) if record['data'] else {}
                    results.append(record)
                
                return results
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            bool: True if successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE notifications SET read = 1
                    WHERE id = ?
                """, (notification_id,))
                
                conn.commit()
                logger.debug(f"Marked notification read: {notification_id}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to mark notification read: {e}")
            return False
    
    def get_tick_statistics(
        self,
        symbol: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregate statistics for ticks.
        
        Args:
            symbol: Trading symbol
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            Dict[str, Any]: Statistics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        COUNT(*) as total_ticks,
                        AVG(price) as avg_price,
                        MAX(price) as max_price,
                        MIN(price) as min_price,
                        AVG(last_digit) as avg_digit,
                        COUNT(DISTINCT tick_id) as unique_ticks
                    FROM ticks
                    WHERE symbol = ?
                """
                params = [symbol]
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(int(start_time.timestamp()))
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(int(end_time.timestamp()))
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                
                stats = dict(row) if row else {}
                
                # Get digit distribution
                digit_query = """
                    SELECT last_digit, COUNT(*) as count
                    FROM ticks
                    WHERE symbol = ?
                """
                digit_params = [symbol]
                
                if start_time:
                    digit_query += " AND timestamp >= ?"
                    digit_params.append(int(start_time.timestamp()))
                
                if end_time:
                    digit_query += " AND timestamp <= ?"
                    digit_params.append(int(end_time.timestamp()))
                
                digit_query += " GROUP BY last_digit ORDER BY last_digit"
                
                cursor.execute(digit_query, digit_params)
                digit_rows = cursor.fetchall()
                
                stats['digit_distribution'] = {
                    row['last_digit']: row['count'] for row in digit_rows
                }
                
                return stats
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get tick statistics: {e}")
            return {}
    
    def export_to_csv(
        self,
        symbol: str,
        output_path: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        Export ticks to CSV file.
        
        Args:
            symbol: Trading symbol
            output_path: Output file path
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            int: Number of rows exported
        """
        try:
            import csv
            
            ticks = self.get_ticks(
                symbol=symbol,
                limit=1000000,  # Max 1M ticks
                start_time=start_time,
                end_time=end_time
            )
            
            if not ticks:
                logger.warning("No ticks to export")
                return 0
            
            with open(output_path, 'w', newline='') as csvfile:
                fieldnames = [
                    'id', 'tick_id', 'symbol', 'price', 'last_digit',
                    'bid', 'ask', 'volume', 'timestamp', 'epoch',
                    'created_at', 'session_id'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(ticks)
            
            logger.info(f"Exported {len(ticks)} ticks to {output_path}")
            return len(ticks)
            
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return 0
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old data older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp())
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete old ticks
                cursor.execute("DELETE FROM ticks WHERE timestamp < ?", (cutoff_time,))
                ticks_deleted = cursor.rowcount
                
                # Delete old market states
                cursor.execute("DELETE FROM market_states WHERE timestamp < ?", (cutoff_time,))
                states_deleted = cursor.rowcount
                
                # Delete old notifications
                cursor.execute("DELETE FROM notifications WHERE timestamp < ?", (cutoff_time,))
                notifications_deleted = cursor.rowcount
                
                # Delete old analytics cache
                cursor.execute("DELETE FROM analytics_cache WHERE expires_at < ?", (cutoff_time,))
                cache_deleted = cursor.rowcount
                
                conn.commit()
                
                total_deleted = ticks_deleted + states_deleted + notifications_deleted + cache_deleted
                logger.info(f"Cleanup complete: {total_deleted} records deleted")
                return total_deleted
                
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0
    
    def vacuum(self) -> bool:
        """
        Vacuum the database to reclaim space and optimize performance.
        
        Returns:
            bool: True if successful
        """
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()
                logger.info("Database vacuum completed")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to vacuum database: {e}")
            return False
    
    def close(self):
        """Close all database connections."""
        if hasattr(self._local, 'connection') and self._local.connection:
            try:
                self._local.connection.close()
                self._local.connection = None
                logger.debug("Database connection closed")
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")
