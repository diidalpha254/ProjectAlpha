"""
Dashboard Controller Module
Manages the main dashboard state, data flow, and UI interactions.
"""

# ============================================================
# 🔧 Add 'app' folder to Python path (so we don't need 'app.' prefix)
# ============================================================
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================
# 🔍 DEBUG: Show which imports are loading
# ============================================================
print("🔍 Loading dashboard_controller.py...")

try:
    print("  → Importing streamlit...")
    import streamlit as st
    print("  → ✅ streamlit imported")
except Exception as e:
    print(f"  → ❌ streamlit failed: {e}")
    raise

try:
    print("  → Importing pandas...")
    import pandas as pd
    print("  → ✅ pandas imported")
except Exception as e:
    print(f"  → ❌ pandas failed: {e}")
    raise

try:
    print("  → Importing numpy...")
    import numpy as np
    print("  → ✅ numpy imported")
except Exception as e:
    print(f"  → ❌ numpy failed: {e}")
    raise

try:
    print("  → Importing core types...")
    from core.types import Tick, MarketStateAnalysis, AIInsight
    print("  → ✅ core types imported")
except Exception as e:
    print(f"  → ❌ core types failed: {e}")
    raise

try:
    print("  → Importing core constants...")
    from core.constants import MarketState, RiskLevel, DIGIT_COLORS
    print("  → ✅ core constants imported")
except Exception as e:
    print(f"  → ❌ core constants failed: {e}")
    raise

try:
    print("  → Importing core logger...")
    from core.logger import get_logger
    print("  → ✅ core logger imported")
except Exception as e:
    print(f"  → ❌ core logger failed: {e}")
    raise

try:
    print("  → Importing data processor...")
    from data.processor import DataProcessor
    print("  → ✅ data processor imported")
except Exception as e:
    print(f"  → ❌ data processor failed: {e}")
    raise

try:
    print("  → Importing event bus...")
    from data.event_bus import event_bus
    print("  → ✅ event bus imported")
except Exception as e:
    print(f"  → ❌ event bus failed: {e}")
    raise

try:
    print("  → Importing analytics engine...")
    from analytics.engine import AnalyticsEngine
    print("  → ✅ analytics engine imported")
except Exception as e:
    print(f"  → ❌ analytics engine failed: {e}")
    raise

try:
    print("  → Importing market classifier...")
    from market_state.classifier import MarketClassifier
    print("  → ✅ market classifier imported")
except Exception as e:
    print(f"  → ❌ market classifier failed: {e}")
    raise

try:
    print("  → Importing match differ intelligence...")
    from intelligence.match_differ import MatchDifferIntelligence
    print("  → ✅ match differ intelligence imported")
except Exception as e:
    print(f"  → ❌ match differ intelligence failed: {e}")
    raise

try:
    print("  → Importing AI insights...")
    from ai.insights import AIInsightsEngine
    print("  → ✅ AI insights imported")
except Exception as e:
    print(f"  → ❌ AI insights failed: {e}")
    raise

try:
    print("  → Importing dashboard builder...")
    from visualization.dashboards import DashboardBuilder
    print("  → ✅ dashboard builder imported")
except Exception as e:
    print(f"  → ❌ dashboard builder failed: {e}")
    raise

try:
    print("  → Importing theme manager...")
    from visualization.theme import ThemeManager
    print("  → ✅ theme manager imported")
except Exception as e:
    print(f"  → ❌ theme manager failed: {e}")
    raise

print("✅ All imports successful!")

# ============================================================
# END OF DEBUG
# ============================================================

from typing import Dict, List, Any, Optional
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np

logger = get_logger(__name__)


class DashboardController:
    """
    Main controller for the Project Alpha dashboard.
    Manages state, data flow, and UI interactions.
    """

    def __init__(self):
        """Initialize the dashboard controller."""
        print("🔍 DashboardController.__init__() called")
        self.processor = DataProcessor()
        self.analytics_engine = AnalyticsEngine()
        self.market_classifier = MarketClassifier()
        self.match_differ_intelligence = MatchDifferIntelligence()
        self.ai_insights_engine = AIInsightsEngine()
        self.dashboard_builder = DashboardBuilder()
        self.theme_manager = ThemeManager()

        self._initialize_session_state()
        self._register_event_handlers()

        logger.info("DashboardController initialized")
        print("✅ DashboardController initialization complete")

    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        defaults = {
            'ticks': [],
            'last_analysis': None,
            'market_analysis': None,
            'md_analysis': None,
            'ai_insight': None,
            'selected_window': 100,
            'selected_symbol': 'R_10',
            'auto_update': True,
            'update_interval': 1.0,
            'theme': 'dark',
            'connection_status': False,
            'session_id': None,
            'error_messages': [],
            'notification_count': 0,
            'replay_mode': False,
            'replay_speed': 1,
            'recording_enabled': False,
            'performance_stats': {
                'tick_rate': 0.0,
                'processing_time': 0.0,
                'memory_usage': 0.0
            }
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def _register_event_handlers(self):
        """Register event bus handlers."""
        event_bus.subscribe('processed_tick', self._handle_tick, async_handler=False)
        event_bus.subscribe('window_updated', self._handle_window_update, async_handler=False)
        event_bus.subscribe('processing_stats', self._handle_processing_stats, async_handler=False)
        logger.info("Event handlers registered")

    def _handle_tick(self, event):
        """Handle incoming processed tick."""
        try:
            tick = event.data
            st.session_state.ticks.append(tick)
            if len(st.session_state.ticks) > 50000:
                st.session_state.ticks = st.session_state.ticks[-50000:]
            if st.session_state.auto_update:
                self.update_analysis()
        except Exception as e:
            logger.error(f"Error handling tick: {e}")

    def _handle_window_update(self, event):
        """Handle window update event."""
        try:
            stats = event.data
            if stats and hasattr(stats, 'get'):
                window_stats = stats.get(st.session_state.selected_window)
                if window_stats:
                    st.session_state.performance_stats['tick_rate'] = window_stats.get('tick_rate', 0)
        except Exception as e:
            logger.error(f"Error handling window update: {e}")

    def _handle_processing_stats(self, event):
        """Handle processing statistics event."""
        try:
            stats = event.data
            if stats:
                st.session_state.performance_stats['processing_time'] = stats.get('avg_processing_time', 0)
        except Exception as e:
            logger.error(f"Error handling processing stats: {e}")

    def update_analysis(self):
        """Update all analyses with current data."""
        try:
            ticks = st.session_state.ticks
            if len(ticks) < 10:
                return

            window_size = st.session_state.selected_window
            window_ticks = ticks[-window_size:] if len(ticks) >= window_size else ticks

            market_analysis = self.market_classifier.classify(window_ticks)
            st.session_state.market_analysis = market_analysis

            md_analysis = self.match_differ_intelligence.analyze(window_ticks)
            st.session_state.md_analysis = md_analysis

            ai_insight = self.ai_insights_engine.generate_insights(window_ticks)
            st.session_state.ai_insight = ai_insight

            st.session_state.last_analysis = datetime.now()

        except Exception as e:
            logger.error(f"Error updating analysis: {e}")
            st.session_state.error_messages.append(f"Analysis error: {str(e)}")

    def render_dashboard(self):
        """Render the main dashboard."""
        try:
            # Apply theme
            self.theme_manager.apply_theme(st.session_state.theme)

            # Sidebar
            self._render_sidebar()

            # Main content
            if st.session_state.connection_status:
                ticks = st.session_state.ticks
                window_size = st.session_state.selected_window
                window_ticks = ticks[-window_size:] if len(ticks) >= window_size else ticks

                market_analysis = st.session_state.market_analysis
                md_analysis = st.session_state.md_analysis
                ai_insight = st.session_state.ai_insight

                frequencies = self._get_frequencies(window_ticks)
                transition_matrix = self._get_transition_matrix(window_ticks)
                confidence = market_analysis.confidence if market_analysis else 0.5
                volatility = self._get_volatility(window_ticks)

                tabs = st.tabs([
                    "📊 Market Dashboard",
                    "🎯 Match/Differ",
                    "🤖 AI Insights",
                    "📈 Advanced Analytics",
                    "⚙️ Settings"
                ])

                with tabs[0]:
                    self.dashboard_builder.create_main_dashboard(
                        window_ticks,
                        market_analysis,
                        frequencies,
                        transition_matrix,
                        confidence,
                        volatility,
                        window_size
                    )

                with tabs[1]:
                    if md_analysis:
                        self.dashboard_builder.create_match_differ_dashboard(
                            window_ticks,
                            md_analysis,
                            frequencies,
                            md_analysis.transition_probabilities
                        )
                    else:
                        st.info("Waiting for Match/Differ analysis...")

                with tabs[2]:
                    if ai_insight:
                        self.dashboard_builder.create_ai_insights_dashboard(ai_insight)
                    else:
                        st.info("Waiting for AI insights...")

                with tabs[3]:
                    self._render_advanced_analytics(window_ticks)

                with tabs[4]:
                    self._render_settings()

            else:
                self._render_disconnected_state()

        except Exception as e:
            logger.error(f"Error rendering dashboard: {e}")
            st.error(f"Dashboard error: {str(e)}")

    def _render_sidebar(self):
        """Render the sidebar."""
        with st.sidebar:
            st.title("⚙️ Project Alpha")

            # Connection status
            st.subheader("🔌 Connection")
            status_color = "🟢" if st.session_state.connection_status else "🔴"
            st.markdown(f"{status_color} **Status:** {'Connected' if st.session_state.connection_status else 'Disconnected'}")

            if not st.session_state.connection_status:
                if st.button("🔗 Connect to Deriv", use_container_width=True):
                    # This will be handled by main app
                    pass

            st.divider()

            # Data controls
            st.subheader("📊 Data Controls")

            symbols = ['R_10', 'R_25', 'R_50', 'R_75', 'R_100',
                      'BOOM_1000', 'BOOM_500', 'BOOM_300', 'BOOM_200', 'BOOM_100']
            selected_symbol = st.selectbox(
                "Symbol",
                symbols,
                index=symbols.index(st.session_state.selected_symbol) if st.session_state.selected_symbol in symbols else 0
            )
            st.session_state.selected_symbol = selected_symbol

            window_sizes = [50, 100, 500, 1000, 5000, 10000]
            selected_window = st.selectbox(
                "Window Size",
                window_sizes,
                index=window_sizes.index(st.session_state.selected_window)
            )
            st.session_state.selected_window = selected_window

            st.session_state.auto_update = st.toggle(
                "Auto Update",
                value=st.session_state.auto_update
            )

            if st.session_state.auto_update:
                update_interval = st.slider(
                    "Update Interval (seconds)",
                    0.5, 5.0, st.session_state.update_interval, 0.5
                )
                st.session_state.update_interval = update_interval

            st.divider()

            # Manual controls
            st.subheader("🔄 Controls")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh Analysis", use_container_width=True):
                    self.update_analysis()
                    st.success("Analysis updated!")

            with col2:
                if st.button("🧹 Clear Data", use_container_width=True):
                    self._clear_data()
                    st.success("Data cleared!")

            if st.button("📥 Export Data to CSV", use_container_width=True):
                self._export_data()

            st.divider()

            # Performance stats
            st.subheader("📈 Performance")
            stats = st.session_state.performance_stats
            st.metric("Tick Rate", f"{stats.get('tick_rate', 0):.1f} ticks/s")
            st.metric("Processing Time", f"{stats.get('processing_time', 0)*1000:.1f} ms")
            st.metric("Total Ticks", f"{len(st.session_state.ticks):,}")

    def _render_disconnected_state(self):
        """Render disconnected state."""
        st.markdown(
            """
            <div style='text-align: center; padding: 50px;'>
                <h1>🔌 Waiting for Connection</h1>
                <p style='font-size: 18px; color: #888;'>
                    Connect to Deriv WebSocket API to start receiving market data.
                </p>
                <p style='font-size: 14px; color: #666;'>
                    Click the "Connect to Deriv" button in the sidebar to begin.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    def _render_advanced_analytics(self, ticks):
        """Render advanced analytics."""
        st.header("📈 Advanced Analytics")
        if len(ticks) < 10:
            st.info("Need more data for advanced analytics")
            return
        st.info("Advanced analytics coming soon...")

    def _render_settings(self):
        """Render settings page."""
        st.header("⚙️ Settings")
        st.info("Settings coming soon...")

    def _get_frequencies(self, ticks: List[Tick]) -> Dict[int, float]:
        """Get digit frequencies from ticks."""
        if not ticks:
            return {i: 0.0 for i in range(10)}
        digits = [t.last_digit for t in ticks]
        total = len(digits)
        frequencies = {}
        for digit in range(10):
            count = sum(1 for d in digits if d == digit)
            frequencies[digit] = count / total if total > 0 else 0.0
        return frequencies

    def _get_transition_matrix(self, ticks: List[Tick]) -> np.ndarray:
        """Get transition matrix from ticks."""
        if len(ticks) < 2:
            return np.zeros((10, 10))
        digits = [t.last_digit for t in ticks]
        matrix = np.zeros((10, 10))
        for i in range(len(digits) - 1):
            from_digit = digits[i]
            to_digit = digits[i + 1]
            matrix[from_digit][to_digit] += 1
        row_sums = matrix.sum(axis=1, keepdims=True)
        matrix = np.divide(matrix, row_sums, where=row_sums != 0)
        return matrix

    def _get_volatility(self, ticks: List[Tick]) -> float:
        """Get volatility from ticks."""
        if len(ticks) < 2:
            return 0.0
        prices = [float(t.price) for t in ticks]
        return np.std(prices)

    def _clear_data(self):
        """Clear all data."""
        st.session_state.ticks = []
        st.session_state.market_analysis = None
        st.session_state.md_analysis = None
        st.session_state.ai_insight = None
        st.session_state.error_messages = []
        st.success("Data cleared!")

    def _export_data(self):
        """Export data to CSV."""
        ticks = st.session_state.ticks
        if not ticks:
            st.warning("No data to export")
            return
        try:
            data = {
                'tick_id': [t.tick_id for t in ticks],
                'symbol': [t.symbol for t in ticks],
                'price': [float(t.price) for t in ticks],
                'last_digit': [t.last_digit for t in ticks],
                'timestamp': [t.timestamp for t in ticks]
            }
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"project_alpha_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            st.success("Data exported successfully!")
        except Exception as e:
            st.error(f"Export failed: {str(e)}")
