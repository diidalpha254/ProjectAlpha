"""
Deriv WebSocket Client
Manages the connection to Deriv's WebSocket API with automatic reconnection,
heartbeat, and message handling.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from ..core.constants import DerivSymbol
from ..core.exceptions import ConnectionError, WebsocketError
from ..core.logger import get_logger
from ..core.types import Tick
from ..config.settings import Settings

logger = get_logger(__name__)


class DerivWebSocketClient:
    """
    WebSocket client for Deriv's API with production-grade features:
    - Automatic reconnection with exponential backoff
    - Heartbeat management
    - Message queuing
    - Request/response correlation
    - Subscription management
    """
    
    def __init__(self, app_id: int = 1089):
        """
        Initialize the WebSocket client.
        
        Args:
            app_id: Deriv application ID (default: 1089 for test)
        """
        self.settings = Settings()
        self.app_id = app_id
        self.ws_url = self.settings.get("websocket.url")
        self.reconnect_delay = self.settings.get("websocket.reconnect_delay", 5)
        self.max_reconnect_attempts = self.settings.get("websocket.max_reconnect_attempts", 10)
        self.heartbeat_interval = self.settings.get("websocket.heartbeat_interval", 30)
        
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = False
        self._reconnecting = False
        self._reconnect_attempts = 0
        self._message_handlers: Dict[str, Callable] = {}
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._subscriptions: List[str] = []
        self._running = False
        self._receive_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.messages_received = 0
        self.messages_sent = 0
        self.errors = 0
        self.last_message_time: Optional[datetime] = None
        
        # Callbacks
        self.on_tick_callback: Optional[Callable[[Tick], None]] = None
        self.on_connection_callback: Optional[Callable[[bool], None]] = None
        self.on_error_callback: Optional[Callable[[str], None]] = None
        
        logger.info(f"Initialized DerivWebSocketClient with app_id={app_id}")
    
    async def connect(self) -> bool:
        """
        Establish connection to Deriv WebSocket API.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self._websocket and self._connected:
                logger.warning("Already connected")
                return True
            
            logger.info(f"Connecting to {self.ws_url}...")
            
            # Add app_id to URL
            full_url = f"{self.ws_url}?app_id={self.app_id}"
            
            self._websocket = await websockets.connect(
                full_url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
                max_size=10 * 1024 * 1024  # 10MB
            )
            
            self._connected = True
            self._reconnect_attempts = 0
            self._running = True
            self.last_message_time = datetime.now()
            
            # Start receiver and heartbeat tasks
            self._receive_task = asyncio.create_task(self._receive_messages())
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            logger.info("WebSocket connection established successfully")
            
            if self.on_connection_callback:
                self.on_connection_callback(True)
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to connect: {str(e)}"
            logger.error(error_msg)
            self.errors += 1
            
            if self.on_error_callback:
                self.on_error_callback(error_msg)
            
            return False
    
    async def disconnect(self):
        """Gracefully disconnect from the WebSocket."""
        self._running = False
        
        # Cancel tasks
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
        
        # Close websocket
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception as e:
                logger.warning(f"Error closing websocket: {e}")
            self._websocket = None
        
        self._connected = False
        logger.info("WebSocket disconnected")
        
        if self.on_connection_callback:
            self.on_connection_callback(False)
    
    async def _receive_messages(self):
        """Main message receiving loop."""
        while self._running:
            try:
                if not self._websocket or not self._connected:
                    await asyncio.sleep(1)
                    continue
                
                message = await self._websocket.recv()
                self.messages_received += 1
                self.last_message_time = datetime.now()
                
                # Parse and handle message
                await self._handle_message(message)
                
            except ConnectionClosed:
                logger.warning("Connection closed, attempting reconnect...")
                await self._handle_disconnect()
                
            except asyncio.CancelledError:
                logger.info("Receive task cancelled")
                break
                
            except Exception as e:
                logger.error(f"Error in receive loop: {e}", exc_info=True)
                self.errors += 1
                await asyncio.sleep(1)
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages to keep connection alive."""
        while self._running:
            try:
                if self._connected and self._websocket:
                    # Send ping message
                    ping_msg = {
                        "ping": 1,
                        "req_id": str(uuid.uuid4())
                    }
                    await self.send_message(ping_msg)
                    logger.debug("Heartbeat sent")
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)
    
    async def _handle_message(self, message: str):
        """
        Parse and route incoming messages to appropriate handlers.
        
        Args:
            message: Raw JSON message string
        """
        try:
            data = json.loads(message)
            
            # Check for response to pending request
            req_id = data.get("req_id")
            if req_id and req_id in self._pending_requests:
                future = self._pending_requests.pop(req_id)
                if not future.done():
                    future.set_result(data)
                return
            
            # Check for tick data
            if self._is_tick_message(data):
                tick = self._parse_tick(data)
                if tick and self.on_tick_callback:
                    await self._handle_tick(tick)
                return
            
            # Check for subscription events
            if data.get("msg_type") == "tick":
                # Already handled above
                pass
                
            # Check for errors
            if data.get("error"):
                error_msg = data["error"].get("message", "Unknown error")
                logger.error(f"API Error: {error_msg}")
                if self.on_error_callback:
                    self.on_error_callback(error_msg)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
    
    def _is_tick_message(self, data: Dict[str, Any]) -> bool:
        """
        Check if the message contains tick data.
        
        Args:
            data: Parsed message data
            
        Returns:
            bool: True if this is a tick message
        """
        return (
            data.get("msg_type") == "tick" or
            ("tick" in data and isinstance(data["tick"], dict)) or
            ("tick" in data and isinstance(data["tick"], (int, float)))
        )
    
    def _parse_tick(self, data: Dict[str, Any]) -> Optional[Tick]:
        """
        Parse tick data from a WebSocket message.
        
        Args:
            data: Parsed message data
            
        Returns:
            Optional[Tick]: Parsed tick or None if parsing fails
        """
        try:
            # Extract tick data - handles different response formats
            tick_data = data.get("tick", {})
            if isinstance(tick_data, (int, float)):
                # Handle simple tick format
                price = float(tick_data)
                symbol = data.get("symbol", "R_10")
                timestamp = datetime.fromtimestamp(data.get("epoch", datetime.now().timestamp()))
            else:
                # Handle detailed tick format
                price = float(tick_data.get("quote", 0))
                symbol = tick_data.get("symbol", data.get("symbol", "R_10"))
                timestamp = datetime.fromtimestamp(
                    tick_data.get("epoch", data.get("epoch", datetime.now().timestamp()))
                )
            
            # Validate price
            if price <= 0:
                logger.warning(f"Invalid tick price: {price}")
                return None
            
            # Extract last digit
            last_digit = int(str(price)[-1]) if isinstance(price, (int, float)) else 0
            
            # Create tick object
            tick = Tick(
                timestamp=timestamp,
                symbol=symbol,
                price=price,
                last_digit=last_digit,
                tick_id=str(data.get("tick_id", uuid.uuid4())),
                bid=float(tick_data.get("bid", 0)) if tick_data.get("bid") else None,
                ask=float(tick_data.get("ask", 0)) if tick_data.get("ask") else None,
                volume=int(tick_data.get("volume", 0)) if tick_data.get("volume") else None
            )
            
            logger.debug(f"Parsed tick: {tick.symbol} @ {tick.price} (digit: {tick.last_digit})")
            return tick
            
        except Exception as e:
            logger.error(f"Failed to parse tick: {e}")
            return None
    
    async def _handle_tick(self, tick: Tick):
        """
        Handle incoming tick data.
        
        Args:
            tick: Parsed Tick object
        """
        if self.on_tick_callback:
            try:
                # Check if callback is async
                if asyncio.iscoroutinefunction(self.on_tick_callback):
                    await self.on_tick_callback(tick)
                else:
                    # Run sync callbacks in executor to not block
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.on_tick_callback, tick
                    )
            except Exception as e:
                logger.error(f"Error in tick callback: {e}", exc_info=True)
    
    async def _handle_disconnect(self):
        """Handle disconnection and initiate reconnection."""
        self._connected = False
        
        if not self._reconnecting:
            self._reconnecting = True
            await self._reconnect()
    
    async def _reconnect(self):
        """Attempt to reconnect with exponential backoff."""
        while self._reconnect_attempts < self.max_reconnect_attempts and self._running:
            delay = self.reconnect_delay * (2 ** self._reconnect_attempts)
            self._reconnect_attempts += 1
            
            logger.info(f"Reconnection attempt {self._reconnect_attempts}/{self.max_reconnect_attempts} in {delay}s")
            
            await asyncio.sleep(delay)
            
            if await self.connect():
                # Re-subscribe to previous subscriptions
                for subscription in self._subscriptions:
                    await self.subscribe(subscription)
                self._reconnecting = False
                return
        
        logger.error("Max reconnection attempts reached")
        self._reconnecting = False
        self._running = False
        
        if self.on_error_callback:
            self.on_error_callback("Max reconnection attempts reached")
    
    async def send_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a message to the WebSocket.
        
        Args:
            message: Message dict to send
            
        Returns:
            Optional[Dict[str, Any]]: Response if request_id was provided
        """
        try:
            if not self._connected or not self._websocket:
                logger.warning("Cannot send message: Not connected")
                return None
            
            # Convert to JSON
            json_msg = json.dumps(message)
            await self._websocket.send(json_msg)
            self.messages_sent += 1
            
            logger.debug(f"Sent message: {message.get('msg_type', 'unknown')}")
            
            # If this is a request, wait for response
            req_id = message.get("req_id")
            if req_id:
                future = asyncio.Future()
                self._pending_requests[req_id] = future
                try:
                    response = await asyncio.wait_for(future, timeout=10)
                    return response
                except asyncio.TimeoutError:
                    logger.warning(f"Request {req_id} timed out")
                    self._pending_requests.pop(req_id, None)
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.errors += 1
            return None
    
    async def subscribe(self, symbol: str) -> bool:
        """
        Subscribe to tick data for a symbol.
        
        Args:
            symbol: The symbol to subscribe to (e.g., "R_10")
            
        Returns:
            bool: True if subscription successful
        """
        try:
            # Build subscription message
            subscribe_msg = {
                "subscribe": 1,
                "ticks": symbol,
                "req_id": f"sub_{symbol}_{uuid.uuid4().hex[:8]}"
            }
            
            logger.info(f"Subscribing to {symbol}...")
            response = await self.send_message(subscribe_msg)
            
            if response and response.get("error"):
                error_msg = response["error"].get("message", "Unknown error")
                logger.error(f"Subscription failed for {symbol}: {error_msg}")
                return False
            
            if symbol not in self._subscriptions:
                self._subscriptions.append(symbol)
            
            logger.info(f"Successfully subscribed to {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {symbol}: {e}")
            return False
    
    async def unsubscribe(self, symbol: str) -> bool:
        """
        Unsubscribe from tick data for a symbol.
        
        Args:
            symbol: The symbol to unsubscribe from
            
        Returns:
            bool: True if unsubscription successful
        """
        try:
            unsubscribe_msg = {
                "unsubscribe": 1,
                "ticks": symbol,
                "req_id": f"unsub_{symbol}_{uuid.uuid4().hex[:8]}"
            }
            
            logger.info(f"Unsubscribing from {symbol}...")
            response = await self.send_message(unsubscribe_msg)
            
            if response and response.get("error"):
                error_msg = response["error"].get("message", "Unknown error")
                logger.error(f"Unsubscription failed for {symbol}: {error_msg}")
                return False
            
            if symbol in self._subscriptions:
                self._subscriptions.remove(symbol)
            
            logger.info(f"Successfully unsubscribed from {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {symbol}: {e}")
            return False
    
    async def get_ticks(self, symbol: str, count: int = 1000) -> Optional[List[Tick]]:
        """
        Get historical ticks for a symbol.
        
        Args:
            symbol: The symbol to get ticks for
            count: Number of ticks to retrieve
            
        Returns:
            Optional[List[Tick]]: List of ticks or None if request fails
        """
        try:
            request_msg = {
                "ticks": symbol,
                "ticks_history": symbol,
                "end": "latest",
                "count": count,
                "req_id": f"ticks_{symbol}_{uuid.uuid4().hex[:8]}"
            }
            
            logger.info(f"Requesting {count} historical ticks for {symbol}...")
            response = await self.send_message(request_msg)
            
            if not response or response.get("error"):
                error_msg = response.get("error", {}).get("message", "Unknown error") if response else "No response"
                logger.error(f"Failed to get ticks: {error_msg}")
                return None
            
            # Parse tick data
            tick_data = response.get("ticks_history", {}).get("ticks", [])
            if not tick_data:
                logger.warning(f"No tick data received for {symbol}")
                return []
            
            ticks = []
            for tick_value in tick_data:
                try:
                    price = float(tick_value)
                    last_digit = int(str(price)[-1])
                    tick = Tick(
                        timestamp=datetime.now(),  # Will be overridden by epoch if available
                        symbol=symbol,
                        price=price,
                        last_digit=last_digit
                    )
                    ticks.append(tick)
                except Exception as e:
                    logger.warning(f"Failed to parse tick: {e}")
                    continue
            
            logger.info(f"Retrieved {len(ticks)} ticks for {symbol}")
            return ticks
            
        except Exception as e:
            logger.error(f"Failed to get ticks for {symbol}: {e}")
            return None
    
    async def authorize(self, token: str) -> bool:
        """
        Authorize the WebSocket connection with an API token.
        
        Args:
            token: Deriv API token
            
        Returns:
            bool: True if authorization successful
        """
        try:
            auth_msg = {
                "authorize": token,
                "req_id": f"auth_{uuid.uuid4().hex[:8]}"
            }
            
            logger.info("Attempting to authorize connection...")
            response = await self.send_message(auth_msg)
            
            if response and response.get("error"):
                error_msg = response["error"].get("message", "Unknown error")
                logger.error(f"Authorization failed: {error_msg}")
                return False
            
            if response and response.get("authorize"):
                logger.info("Authorization successful")
                return True
            
            logger.error("Authorization failed: Unexpected response")
            return False
            
        except Exception as e:
            logger.error(f"Failed to authorize: {e}")
            return False
    
    def set_tick_callback(self, callback: Callable[[Tick], None]):
        """
        Set a callback for incoming ticks.
        
        Args:
            callback: Function to call on each tick
        """
        self.on_tick_callback = callback
        logger.info("Tick callback registered")
    
    def set_connection_callback(self, callback: Callable[[bool], None]):
        """
        Set a callback for connection status changes.
        
        Args:
            callback: Function to call on connection status change
        """
        self.on_connection_callback = callback
        logger.info("Connection callback registered")
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """
        Set a callback for error events.
        
        Args:
            callback: Function to call on error
        """
        self.on_error_callback = callback
        logger.info("Error callback registered")
    
    @property
    def is_connected(self) -> bool:
        """Return connection status."""
        return self._connected
    
    @property
    def statistics(self) -> Dict[str, Any]:
        """Return client statistics."""
        return {
            "messages_received": self.messages_received,
            "messages_sent": self.messages_sent,
            "errors": self.errors,
            "last_message_time": self.last_message_time,
            "is_connected": self._connected,
            "subscriptions": self._subscriptions
        }
