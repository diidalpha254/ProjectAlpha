"""
Project Alpha - Main Application Entry Point
Advanced Deriv Match/Differ Market Intelligence Platform
"""

# ============================================================
# 🔍 DEBUG WRAPPER (catch any error and display on screen)
# ============================================================
try:
    import streamlit as st
    import asyncio
    import threading
    from datetime import datetime
    from typing import Optional

    from core.logger import get_logger
    from core.config import settings
    from data.websocket_client import DerivWebSocketClient
    from data.processor import DataProcessor
    from data.event_bus import event_bus
    from controllers.dashboard_controller import DashboardController
    from controllers.session_controller import SessionController
    from features.replay import HistoricalReplay
    from features.recording import TickRecorder
    from features.notifications import NotificationManager
    from features.plugins import PluginManager

    logger = get_logger(__name__)

    # Page configuration
    st.set_page_config(
        page_title="Project Alpha - Market Intelligence",
        page_icon="📊",  # ✅ Fixed: using emoji instead of Image()
        layout="wide",
        initial_sidebar_state="expanded"
    )

    class ProjectAlphaApp:
        """
        Main application class that orchestrates all components.
        """

        def __init__(self):
            """Initialize the application."""
            self.websocket_client: Optional[DerivWebSocketClient] = None
            self.data_processor: Optional[DataProcessor] = None
            self.dashboard_controller: Optional[DashboardController] = None
            self.session_controller: Optional[SessionController] = None
            self.replay_engine: Optional[HistoricalReplay] = None
            self.recorder: Optional[TickRecorder] = None
            self.notification_manager: Optional[NotificationManager] = None
            self.plugin_manager: Optional[PluginManager] = None

            self._initialized = False
            self._connection_thread: Optional[threading.Thread] = None
            self._loop: Optional[asyncio.AbstractEventLoop] = None

            # Initialize session state
            self._init_session_state()

            logger.info("ProjectAlphaApp initialized")

        def _init_session_state(self):
            """Initialize Streamlit session state variables."""
            defaults = {
                'app_initialized': False,
                'connection_status': False,
                'current_symbol': 'R_10',
                'selected_window': 100,
                'auto_update': True,
                'theme': 'dark',
                'ticks': [],
                'market_analysis': None,
                'md_analysis': None,
                'ai_insight': None,
                'replay_mode': False,
                'recording_mode': False,
                'notifications': [],
                'error_messages': []
            }

            for key, value in defaults.items():
                if key not in st.session_state:
                    st.session_state[key] = value

        def initialize(self):
            """Initialize all application components with error handling."""
            if self._initialized:
                return

            try:
                st.info("🔄 Initializing application components...")

                # Initialize components one by one with error handling
                try:
                    self.data_processor = DataProcessor()
                    st.success("✅ Data Processor initialized")
                except Exception as e:
                    st.error(f"❌ Data Processor failed: {e}")
                    raise

                try:
                    self.dashboard_controller = DashboardController()
                    st.success("✅ Dashboard Controller initialized")
                except Exception as e:
                    st.error(f"❌ Dashboard Controller failed: {e}")
                    raise

                try:
                    self.session_controller = SessionController()
                    st.success("✅ Session Controller initialized")
                except Exception as e:
                    st.error(f"❌ Session Controller failed: {e}")
                    raise

                try:
                    self.replay_engine = HistoricalReplay()
                    st.success("✅ Replay Engine initialized")
                except Exception as e:
                    st.error(f"❌ Replay Engine failed: {e}")
                    raise

                try:
                    self.recorder = TickRecorder()
                    st.success("✅ Tick Recorder initialized")
                except Exception as e:
                    st.error(f"❌ Tick Recorder failed: {e}")
                    raise

                try:
                    self.notification_manager = NotificationManager()
                    st.success("✅ Notification Manager initialized")
                except Exception as e:
                    st.error(f"❌ Notification Manager failed: {e}")
                    raise

                try:
                    self.plugin_manager = PluginManager()
                    self.plugin_manager.load_all_plugins()
                    st.success("✅ Plugin Manager initialized")
                except Exception as e:
                    st.error(f"❌ Plugin Manager failed: {e}")
                    raise

                # Set up event handlers
                self._setup_event_handlers()

                self._initialized = True
                st.session_state.app_initialized = True

                st.success("🎉 Application initialized successfully!")

            except Exception as e:
                logger.error(f"Error initializing application: {e}", exc_info=True)
                st.error(f"❌ Failed to initialize application: {str(e)}")
                st.info("Please check the logs for more details.")
                self._initialized = False

        def _setup_event_handlers(self):
            """Set up event bus handlers."""
            # Handle processed ticks
            event_bus.subscribe('processed_tick', self._on_tick_received, async_handler=False)

            # Handle connection status
            event_bus.subscribe('connection_status', self._on_connection_status, async_handler=False)

            # Handle errors
            event_bus.subscribe('error', self._on_error, async_handler=False)

            # Handle notifications
            event_bus.subscribe('notification_created', self._on_notification, async_handler=False)

            logger.info("Event handlers setup complete")

        def _on_tick_received(self, event):
            """Handle incoming tick."""
            tick = event.data

            # Add to session
            if self.session_controller and not st.session_state.replay_mode:
                self.session_controller.add_tick(tick)

            # Update session state
            if 'ticks' in st.session_state:
                st.session_state.ticks.append(tick)
                if len(st.session_state.ticks) > 50000:
                    st.session_state.ticks = st.session_state.ticks[-50000:]

        def _on_connection_status(self, event):
            """Handle connection status changes."""
            status = event.data
            st.session_state.connection_status = status

            if status:
                self.notification_manager.add_notification(
                    "info",
                    "Connected to Deriv WebSocket API",
                    action="connect"
                )
            else:
                self.notification_manager.add_notification(
                    "warning",
                    "Disconnected from Deriv WebSocket API",
                    action="disconnect"
                )

        def _on_error(self, event):
            """Handle errors."""
            error_msg = event.data
            st.session_state.error_messages.append(error_msg)

            self.notification_manager.add_notification(
                "error",
                f"Error: {error_msg}",
                action="error"
            )

            logger.error(f"Error event: {error_msg}")

        def _on_notification(self, event):
            """Handle notifications."""
            notification = event.data
            if 'notifications' in st.session_state:
                st.session_state.notifications.append(notification)

        def connect_to_deriv(self, symbol: str = "R_10", app_id: int = 1089):
            """
            Connect to Deriv WebSocket API.

            Args:
                symbol: Trading symbol
                app_id: Deriv application ID
            """
            if self.websocket_client and self.websocket_client.is_connected:
                st.warning("Already connected to Deriv")
                return

            try:
                # Create WebSocket client
                self.websocket_client = DerivWebSocketClient(app_id=app_id)

                # Set up callbacks
                self.websocket_client.set_tick_callback(self._handle_tick)
                self.websocket_client.set_connection_callback(self._handle_connection)
                self.websocket_client.set_error_callback(self._handle_error)

                # Create event loop for WebSocket
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

                # Start connection in background thread
                def run_websocket():
                    asyncio.set_event_loop(self._loop)
                    self._loop.run_until_complete(self._connect_and_subscribe(symbol))

                self._connection_thread = threading.Thread(
                    target=run_websocket,
                    name="WebSocketThread",
                    daemon=True
                )
                self._connection_thread.start()

                st.session_state.current_symbol = symbol
                st.success(f"Connecting to {symbol}...")

            except Exception as e:
                logger.error(f"Error connecting to Deriv: {e}")
                st.error(f"Connection failed: {str(e)}")

        async def _connect_and_subscribe(self, symbol: str):
            """Connect and subscribe to symbol."""
            try:
                # Connect
                connected = await self.websocket_client.connect()
                if not connected:
                    logger.error("Failed to connect to WebSocket")
                    return

                # Subscribe to symbol
                subscribed = await self.websocket_client.subscribe(symbol)
                if subscribed:
                    event_bus.publish("connection_status", True, "WebSocket")
                    logger.info(f"Subscribed to {symbol}")
                else:
                    logger.error(f"Failed to subscribe to {symbol}")

            except Exception as e:
                logger.error(f"Error in WebSocket connection: {e}")
                event_bus.publish("error", str(e), "WebSocket")

        def _handle_tick(self, tick):
            """Handle tick from WebSocket."""
            # Emit raw tick event
            event_bus.publish("raw_tick", tick, "WebSocket")

        def _handle_connection(self, connected: bool):
            """Handle connection status change."""
            event_bus.publish("connection_status", connected, "WebSocket")

            if connected:
                st.success("Connected to Deriv WebSocket API")
            else:
                st.warning("Disconnected from Deriv WebSocket API")

        def _handle_error(self, error: str):
            """Handle WebSocket error."""
            event_bus.publish("error", error, "WebSocket")
            st.error(f"WebSocket error: {error}")

        def disconnect_from_deriv(self):
            """Disconnect from Deriv WebSocket API."""
            if self.websocket_client:
                # Stop the WebSocket client
                if self._loop and not self._loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        self.websocket_client.disconnect(),
                        self._loop
                    )

                self.websocket_client = None
                st.session_state.connection_status = False
                logger.info("Disconnected from Deriv")
                st.success("Disconnected from Deriv")

        def render(self):
            """Render the main application."""
            # Initialize if not done
            if not st.session_state.app_initialized:
                self.initialize()

            # Render header
            self._render_header()

            # Render main content with proper error handling
            if self.dashboard_controller is not None:
                try:
                    self.dashboard_controller.render_dashboard()
                except Exception as e:
                    st.error(f"❌ Dashboard error: {str(e)}")
                    st.info("Please check the logs for more details.")
            else:
                # Show a helpful message instead of the misleading warning
                st.warning("⚠️ Dashboard controller not available. Please rebuild the app.")
                st.info("Go to Streamlit Cloud → More → Rebuild")
                st.markdown("""
                ### 🔧 How to fix:
                1. Go to **Streamlit Cloud** dashboard
                2. Click on your app → **More** → **Rebuild**
                3. Wait for the rebuild to complete
                4. Refresh this page
                """)
                if st.button("🔄 Rebuild Now"):
                    st.cache_data.clear()
                    st.rerun()

            # Render footer
            self._render_footer()

        def _render_header(self):
            """Render application header."""
            col1, col2, col3 = st.columns([1, 2, 1])

            with col1:
                st.markdown("### 📊 Project Alpha")

            with col2:
                # Status indicators
                status_color = "🟢" if st.session_state.connection_status else "🔴"
                status_text = "Connected" if st.session_state.connection_status else "Disconnected"
                st.markdown(f"<div style='text-align: center;'>{status_color} {status_text}</div>", unsafe_allow_html=True)

            with col3:
                # Current time
                current_time = datetime.now().strftime("%H:%M:%S")
                st.markdown(f"<div style='text-align: right;'>🕐 {current_time}</div>", unsafe_allow_html=True)

            st.divider()

        def _render_footer(self):
            """Render application footer."""
            st.divider()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(
                    """
                    <div style='text-align: center; font-size: 12px; color: #666;'>
                        📊 Project Alpha v1.0.0
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown(
                    """
                    <div style='text-align: center; font-size: 12px; color: #666;'>
                        ⚠️ For informational purposes only. Not financial advice.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col3:
                tick_count = len(st.session_state.ticks) if 'ticks' in st.session_state else 0
                st.markdown(
                    f"""
                    <div style='text-align: center; font-size: 12px; color: #666;'>
                        📈 Ticks: {tick_count:,}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        def cleanup(self):
            """Clean up resources on shutdown."""
            try:
                # Disconnect from Deriv
                if self.websocket_client:
                    if self._loop and not self._loop.is_closed():
                        asyncio.run_coroutine_threadsafe(
                            self.websocket_client.disconnect(),
                            self._loop
                        )

                # Close WebDriver for screenshots
                if hasattr(self, 'screenshot_capture'):
                    self.screenshot_capture.close()

                logger.info("Application cleanup complete")

            except Exception as e:
                logger.error(f"Error during cleanup: {e}")


    # Create application instance
    app = ProjectAlphaApp()

    # Main entry point
    def main():
        """Main application entry point."""
        try:
            # Render the application
            app.render()

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            app.cleanup()

        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            st.error(f"Application error: {str(e)}")
            app.cleanup()

    if __name__ == "__main__":
        main()

# ============================================================
# 🔍 If ANY error occurs, it will be displayed here
# ============================================================
except Exception as e:
    import streamlit as st
    import traceback
    st.error(f"🚨 ERROR IN APP: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()
