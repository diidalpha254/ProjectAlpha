"""
Notification Module
Provides real-time notifications for market events and alerts.
"""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import uuid
import threading
from collections import deque

from core.types import Notification
from core.constants import NotificationType
from core.logger import get_logger
from data.event_bus import event_bus


logger = get_logger(__name__)


class NotificationManager:
    """
    Manages real-time notifications for market events and alerts.
    Supports multiple notification channels and filtering.
    """
    
    def __init__(self, max_notifications: int = 100):
        """
        Initialize the notification manager.
        
        Args:
            max_notifications: Maximum notifications to store
        """
        self.max_notifications = max_notifications
        self._notifications: deque = deque(maxlen=max_notifications)
        self._listeners: List[Callable] = []
        self._filter_types = set()
        self._lock = threading.Lock()
        
        # Subscribe to events
        event_bus.subscribe('processed_tick', self._check_alerts, async_handler=False)
        
        logger.info("NotificationManager initialized")
    
    def add_notification(
        self,
        notification_type: NotificationType,
        message: str,
        action: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Add a new notification.
        
        Args:
            notification_type: Type of notification
            message: Notification message
            action: Optional action to take
            data: Optional additional data
            
        Returns:
            Notification: Created notification
        """
        with self._lock:
            # Check filters
            if self._filter_types and notification_type not in self._filter_types:
                return None
            
            notification = Notification(
                id=str(uuid.uuid4()),
                type=notification_type.value,
                message=message,
                timestamp=datetime.now(),
                read=False,
                action=action,
                data=data
            )
            
            self._notifications.append(notification)
            
            # Notify listeners
            self._notify_listeners(notification)
            
            # Emit event
            event_bus.publish("notification_created", notification, "NotificationManager")
            
            logger.info(f"Notification: [{notification_type.value}] {message[:50]}...")
            return notification
    
    def _notify_listeners(self, notification: Notification):
        """Notify all listeners of a new notification."""
        for listener in self._listeners:
            try:
                listener(notification)
            except Exception as e:
                logger.error(f"Error in notification listener: {e}")
    
    def add_listener(self, callback: Callable):
        """
        Add a listener for notifications.
        
        Args:
            callback: Callback function
        """
        self._listeners.append(callback)
        logger.debug("Notification listener added")
    
    def remove_listener(self, callback: Callable):
        """
        Remove a listener.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._listeners:
            self._listeners.remove(callback)
            logger.debug("Notification listener removed")
    
    def get_notifications(
        self,
        limit: int = 50,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None
    ) -> List[Notification]:
        """
        Get notifications.
        
        Args:
            limit: Maximum number of notifications
            unread_only: Only unread notifications
            notification_type: Filter by type
            
        Returns:
            List[Notification]: List of notifications
        """
        with self._lock:
            notifications = list(self._notifications)
            
            # Filter
            if unread_only:
                notifications = [n for n in notifications if not n.read]
            
            if notification_type:
                notifications = [n for n in notifications if n.type == notification_type.value]
            
            return notifications[-limit:]
    
    def mark_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            bool: True if successful
        """
        with self._lock:
            for notification in self._notifications:
                if notification.id == notification_id:
                    notification.read = True
                    return True
            return False
    
    def mark_all_read(self) -> int:
        """
        Mark all notifications as read.
        
        Returns:
            int: Number of notifications marked
        """
        with self._lock:
            count = 0
            for notification in self._notifications:
                if not notification.read:
                    notification.read = True
                    count += 1
            return count
    
    def clear_notifications(self):
        """Clear all notifications."""
        with self._lock:
            self._notifications.clear()
            logger.info("Notifications cleared")
    
    def set_filter(self, notification_types: List[NotificationType]):
        """
        Set notification type filters.
        
        Args:
            notification_types: List of types to allow
        """
        self._filter_types = set(notification_types)
        logger.info(f"Notification filters set: {[t.value for t in notification_types]}")
    
    def clear_filter(self):
        """Clear all notification filters."""
        self._filter_types.clear()
        logger.info("Notification filters cleared")
    
    def _check_alerts(self, event):
        """Check for market alerts based on tick data."""
        tick = event.data
        
        try:
            # Price alert (extreme movement)
            if hasattr(self, '_last_price'):
                price_change = abs(float(tick.price) - self._last_price)
                if price_change > 1.0:  # Large price move
                    self.add_notification(
                        NotificationType.ALERT,
                        f"Large price movement detected: {price_change:.2f}",
                        data={'price': float(tick.price)}
                    )
            
            # Digit streak alert
            if hasattr(self, '_last_digit') and tick.last_digit == self._last_digit:
                if not hasattr(self, '_streak_count'):
                    self._streak_count = 0
                self._streak_count += 1
                
                if self._streak_count >= 5:
                    self.add_notification(
                        NotificationType.WARNING,
                        f"Long streak: {self._streak_count} consecutive {tick.last_digit}s"
                    )
            else:
                self._streak_count = 0
            
            self._last_price = float(tick.price)
            self._last_digit = tick.last_digit
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def get_unread_count(self) -> int:
        """
        Get count of unread notifications.
        
        Returns:
            int: Number of unread notifications
        """
        return sum(1 for n in self._notifications if not n.read)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get notification statistics.
        
        Returns:
            Dict[str, Any]: Statistics
        """
        total = len(self._notifications)
        unread = self.get_unread_count()
        
        type_counts = {}
        for notification in self._notifications:
            type_counts[notification.type] = type_counts.get(notification.type, 0) + 1
        
        return {
            'total': total,
            'unread': unread,
            'read': total - unread,
            'type_counts': type_counts,
            'filtered': len(self._filter_types) > 0
        }
