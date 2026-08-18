"""
Event Bus Module
Provides an event-driven architecture for asynchronous data processing.
"""

from typing import Dict, List, Callable, Any, Optional
import asyncio
import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import uuid

from ..core.types import Tick
from ..core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Event:
    """Represents an event in the system."""
    id: str
    event_type: str
    data: Any
    timestamp: datetime
    source: Optional[str] = None


class EventBus:
    """
    Central event bus for publish/subscribe messaging.
    Supports both synchronous and asynchronous event handlers.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(EventBus, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the event bus."""
        if hasattr(self, '_initialized'):
            return
        
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._async_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._initialized = True
        
        logger.info("EventBus initialized")
    
    def subscribe(self, event_type: str, callback: Callable, async_handler: bool = False):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Callback function to execute
            async_handler: Whether the callback is async
        """
        if async_handler:
            self._async_subscribers[event_type].append(callback)
        else:
            self._subscribers[event_type].append(callback)
        
        logger.debug(f"Subscribed handler to event: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to remove
        """
        if callback in self._subscribers.get(event_type, []):
            self._subscribers[event_type].remove(callback)
        if callback in self._async_subscribers.get(event_type, []):
            self._async_subscribers[event_type].remove(callback)
        
        logger.debug(f"Unsubscribed handler from event: {event_type}")
    
    def publish(self, event_type: str, data: Any, source: Optional[str] = None):
        """
        Publish an event synchronously.
        
        Args:
            event_type: Type of event
            data: Event data
            source: Source of the event
        """
        event = Event(
            id=str(uuid.uuid4()),
            event_type=event_type,
            data=data,
            timestamp=datetime.now(),
            source=source
        )
        
        # Store history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        logger.debug(f"Publishing event: {event_type}")
        
        # Call synchronous handlers
        for callback in self._subscribers.get(event_type, []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}", exc_info=True)
        
        # Call asynchronous handlers
        for callback in self._async_subscribers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    # Schedule async handler
                    asyncio.create_task(callback(event))
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in async event handler: {e}", exc_info=True)
    
    async def publish_async(self, event_type: str, data: Any, source: Optional[str] = None):
        """
        Publish an event asynchronously.
        
        Args:
            event_type: Type of event
            data: Event data
            source: Source of the event
        """
        event = Event(
            id=str(uuid.uuid4()),
            event_type=event_type,
            data=data,
            timestamp=datetime.now(),
            source=source
        )
        
        # Store history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        logger.debug(f"Publishing async event: {event_type}")
        
        # Call sync handlers
        for callback in self._subscribers.get(event_type, []):
            try:
                # Run sync callbacks in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, callback, event)
            except Exception as e:
                logger.error(f"Error in async event handler: {e}", exc_info=True)
        
        # Call async handlers
        for callback in self._async_subscribers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in async event handler: {e}", exc_info=True)
    
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: List of events
        """
        if event_type:
            filtered = [e for e in self._event_history if e.event_type == event_type]
            return filtered[-limit:]
        return self._event_history[-limit:]
    
    def clear_history(self):
        """Clear event history."""
        self._event_history.clear()
        logger.info("Event history cleared")


# Global event bus instance
event_bus = EventBus()
