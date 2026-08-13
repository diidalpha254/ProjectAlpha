"""
Dashboard Controller Module
Manages the main dashboard state, data flow, and UI interactions.
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np

from ..core.types import Tick, MarketStateAnalysis, AIInsight
from ..core.constants import MarketState, RiskLevel, DIGIT_COLORS
from ..core.logger import get_logger
from ..data.processor import DataProcessor
from ..data.event_bus import event_bus
from ..analytics.engine import AnalyticsEngine
from ..market_state.classifier import MarketClassifier
from ..intelligence.match_differ import MatchDifferIntelligence
from ..ai.insights import AIInsightsEngine
from ..visualization.dashboards import DashboardBuilder
from ..visualization.theme import ThemeManager

logger = get_logger(__name__)


class DashboardController:
    """
    Main controller for the Project Alpha dashboard.
    Manages state, data flow, and UI interactions.
    """
    
    def __init__(self):
        """Initialize the dashboard controller."""
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
        # Listen for processed ticks
        event_bus.subscribe('processed_tick', self._handle_tick, async_handler=False)
        event_bus.subscribe('window_updated', self._handle_window_update, async_handler=False)
        event_bus.subscribe('processing_stats', self._handle_processing_stats, async_handler=False)
        
        logger.info("Event handlers registered")
    
    def _handle_tick(self, event):
        """Handle incoming processed tick."""
        try:
            tick = event.data
            st.session_state.ticks.append(tick)
            
            # Keep only recent ticks (max 50000)
            if len(st.session_state.ticks) > 50000:
                st.session_state.ticks = st.session_state.ticks[-50000:]
            
            # Update analysis if auto-update is enabled
            if st.session_state.auto_update:
                self.update_analysis()
                
        except Exception as e:
            logger.error(f"Error handling tick: {e}")
    
    def _handle_window_update(self, event):
        """Handle window update event."""
        try:
            # Update performance stats
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
            
            # Get selected window
            window_size = st.session_state.selected_window
            window_ticks = ticks[-window_size:] if len(ticks) >= window_size else ticks
            
            # Run analyses
            market_analysis = self.market_classifier.classify(window_ticks)
            st.session_state.market_analysis = market_analysis
            
            # Get Match/Differ analysis
            md_analysis = self.match_differ_intelligence.analyze(window_ticks)
            st.session_state.md_analysis = md_analysis
            
            # Get AI insights
            ai_insight = self.ai_insights_engine.generate_insights(window_ticks)
            st.session_state.ai_insight = ai_insight
            
            # Store last analysis time
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
                # Get current data
                ticks = st.session_state.ticks
                window_size = st.session_state.selected_window
                window_ticks = ticks[-window_size:] if len(ticks) >= window_size else ticks
                
                # Get analysis results
                market_analysis = st.session_state.market_analysis
                md_analysis = st.session_state.md_analysis
                ai_insight = st.session_state.ai_insight
                
                # Prepare data for visualization
                frequencies = self._get_frequencies(window_ticks)
                transition_matrix = self._get_transition_matrix(window_ticks)
                confidence = market_analysis.confidence if market_analysis else 0.5
                volatility = self._get_volatility(window_ticks)
                
                # Create tabs
                tabs = st.tabs([
                    "📊 Market Dashboard",
                    "🎯 Match/Differ",
                    "🤖 AI Insights",
                    "📈 Advanced Analytics",
                    "⚙️ Settings"
                ])
                
                # Tab 1: Market Dashboard
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
                
                # Tab 2: Match/Differ
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
                
                # Tab 3: AI Insights
                with tabs[2]:
                    if ai_insight:
                        self.dashboard_builder.create_ai_insights_dashboard(ai_insight)
                    else:
                        st.info("Waiting for AI insights...")
                
                # Tab 4: Advanced Analytics
                with tabs[3]:
                    self._render_advanced_analytics(window_ticks)
                
                # Tab 5: Settings
                with tabs[4]:
                    self._render_settings()
                
            else:
                self._render_disconnected_state()
                
        except Exception as e:
            logger.error(f"Error rendering dashboard: {e}")
            st.error(f"Dashboard error: {str(e)}")
    
    def _render_sidebar(self):
        """Render the sidebar with controls and status."""
        with st.sidebar:
            st.title("⚙️ Project Alpha")
            
            # Connection status
            st.subheader("🔌 Connection")
            status_color = "🟢" if st.session_state.connection_status else "🔴"
            st.markdown(f"{status_color} **Status:** {'Connected' if st.session_state.connection_status else 'Disconnected'}")
            
            if not st.session_state.connection_status:
                if st.button("🔗 Connect to Deriv", use_container_width=True):
                    self._connect_to_deriv()
            
            st.divider()
            
            # Data controls
            st.subheader("📊 Data Controls")
            
            # Symbol selection
            symbols = ['R_10', 'R_25', 'R_50', 'R_75', 'R_100', 
                      'BOOM_1000', 'BOOM_500', 'BOOM_300', 'BOOM_200', 'BOOM_100']
            selected_symbol = st.selectbox(
                "Symbol",
                symbols,
                index=symbols.index(st.session_state.selected_symbol) if st.session_state.selected_symbol in symbols else 0
            )
            st.session_state.selected_symbol = selected_symbol
            
            # Window size
            window_sizes = [50, 100, 500, 1000, 5000, 10000]
            selected_window = st.selectbox(
                "Window Size",
                window_sizes,
                index=window_sizes.index(st.session_state.selected_window)
            )
            st.session_state.selected_window = selected_window
            
            # Auto-update
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
            
            # Export controls
            if st.button("📥 Export Data to CSV", use_container_width=True):
                self._export_data()
            
            # Theme toggle
            st.divider()
            if st.button(f"🌓 Toggle Theme ({st.session_state.theme})", use_container_width=True):
                st.session_state.theme = self.theme_manager.toggle_theme()
                st.rerun()
            
            st.divider()
            
            # Performance stats
            st.subheader("📈 Performance")
            stats = st.session_state.performance_stats
            st.metric("Tick Rate", f"{stats.get('tick_rate', 0):.1f} ticks/s")
            st.metric("Processing Time", f"{stats.get('processing_time', 0)*1000:.1f} ms")
            st.metric("Total Ticks", f"{len(st.session_state.ticks):,}")
            
            st.divider()
            
            # Notifications
            st.subheader("🔔 Notifications")
            if st.session_state.error_messages:
                for msg in st.session_state.error_messages[-5:]:
                    st.warning(msg)
            else:
                st.info("No notifications")
    
    def _render_disconnected_state(self):
        """Render the disconnected state."""
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
    
    def _render_advanced_analytics(self, ticks: List[Tick]):
        """Render advanced analytics section."""
        st.header("📈 Advanced Analytics")
        
        if len(ticks) < 10:
            st.info("Need more data for advanced analytics")
            return
        
        # Get comprehensive analysis
        analysis = self.analytics_engine.analyze_tick_data(ticks)
        
        # Create metrics grid
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Ticks",
                analysis.summary.get('total_ticks', 0)
            )
        
        with col2:
            st.metric(
                "Entropy",
                f"{analysis.entropy.get('entropy', 0):.2f} bits"
            )
        
        with col3:
            st.metric(
                "Randomness Score",
                f"{analysis.entropy.get('randomness_score', 0):.1%}"
            )
        
        with col4:
            st.metric(
                "Overall Confidence",
                f"{analysis.confidence.get('overall', 0):.1%}"
            )
        
        # Statistical summary
        st.subheader("📊 Statistical Summary")
        
        # Create DataFrame for stats
        stats_data = {
            'Metric': [],
            'Value': []
        }
        
        # Add frequency stats
        if analysis.frequency:
            for digit in range(10):
                stats_data['Metric'].append(f'Digit {digit} Frequency')
                stats_data['Value'].append(f"{analysis.frequency['frequencies'].get(digit, 0):.1%}")
        
        # Add z-scores
        if 'z_scores' in analysis.frequency:
            for digit, z in analysis.frequency['z_scores'].items():
                stats_data['Metric'].append(f'Digit {digit} Z-Score')
                stats_data['Value'].append(f"{z:.2f}")
        
        # Add transition stats
        if hasattr(analysis, 'markov') and 'transition_matrix' in analysis.markov:
            matrix = analysis.markov['transition_matrix']
            if matrix is not None and isinstance(matrix, np.ndarray):
                # Find strongest transitions
                for i in range(10):
                    row = matrix[i]
                    if row.size > 0:
                        max_idx = np.argmax(row)
                        max_val = row[max_idx]
                        if max_val > 0.2:
                            stats_data['Metric'].append(f'{i}→{max_idx} Transition')
                            stats_data['Value'].append(f"{max_val:.1%}")
        
        # Add volatility stats
        if 'volatility' in analysis.__dict__:
            metrics = analysis.volatility.get('metrics', {})
            if metrics:
                stats_data['Metric'].append('Volatility')
                stats_data['Value'].append(f"{metrics.get('standard_deviation', 0):.4f}")
                
                stats_data['Metric'].append('Price Range')
                stats_data['Value'].append(f"{metrics.get('range', 0):.4f}")
        
        # Add momentum stats
        if 'momentum' in analysis.volatility:
            momentum = analysis.volatility['momentum']
            stats_data['Metric'].append('Momentum Direction')
            stats_data['Value'].append(momentum.get('direction', 'neutral'))
            
            stats_data['Metric'].append('Momentum Strength')
            stats_data['Value'].append(f"{momentum.get('strength', 0):.2f}")
        
        # Add pattern stats
        if hasattr(analysis, 'patterns'):
            patterns = analysis.patterns
            stats_data['Metric'].append('Patterns Found')
            stats_data['Value'].append(len(patterns.get('repeated_patterns', [])))
            
            longest = patterns.get('longest_streak', (0, 0))
            stats_data['Metric'].append('Longest Streak')
            stats_data['Value'].append(f"{longest[1]} of {longest[0]}")
        
        # Display as DataFrame
        df = pd.DataFrame(stats_data)
        st.dataframe(df, use_container_width=True)
        
        # Additional charts
        st.subheader("📈 Additional Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pattern heatmap
            patterns = analysis.patterns.get('repeated_patterns', [])
            if patterns:
                pattern_chart = self.dashboard_builder.chart_builder.create_pattern_heatmap(patterns)
                st.plotly_chart(pattern_chart, use_container_width=True)
        
        with col2:
            # Trend analysis
            if 'trend' in analysis.volatility:
                trend = analysis.volatility['trend']
                if trend:
                    st.markdown(f"**Trend Direction:** {trend.get('direction', 'neutral')}")
                    st.markdown(f"**Trend Strength:** {trend.get('trend_strength', 0):.2f}")
                    st.markdown(f"**R-Squared:** {trend.get('r_squared', 0):.3f}")
                    
                    # Simple trend gauge
                    strength = trend.get('trend_strength', 0)
                    st.progress(strength)
                    st.caption(f"Trend Strength: {strength:.1%}")
    
    def _render_settings(self):
        """Render settings page."""
        st.header("⚙️ Settings")
        
        # General settings
        st.subheader("General")
        st.session_state.auto_update = st.toggle(
            "Enable Auto-Update",
            value=st.session_state.auto_update
        )
        
        st.session_state.update_interval = st.slider(
            "Update Interval (seconds)",
            0.5, 5.0, st.session_state.update_interval, 0.5
        )
        
        # Data settings
        st.subheader("Data")
        max_ticks = st.number_input(
            "Max Ticks to Store",
            min_value=1000,
            max_value=100000,
            value=50000,
            step=1000
        )
        
        # Analysis settings
        st.subheader("Analysis")
        window_sizes = [50, 100, 500, 1000, 5000, 10000]
        st.session_state.selected_window = st.selectbox(
            "Default Window Size",
            window_sizes,
            index=window_sizes.index(st.session_state.selected_window)
        )
        
        # Performance settings
        st.subheader("Performance")
        st.session_state.performance_stats = {
            'tick_rate': st.session_state.performance_stats.get('tick_rate', 0),
            'processing_time': st.session_state.performance_stats.get('processing_time', 0),
            'memory_usage': st.session_state.performance_stats.get('memory_usage', 0)
        }
        
        # Reset settings
        if st.button("🔄 Reset to Default Settings", use_container_width=True):
            self._reset_settings()
            st.success("Settings reset to defaults!")
        
        # About
        st.divider()
        st.subheader("ℹ️ About")
        st.markdown("""
        **Project Alpha** - Advanced Market Intelligence Platform
        
        Version: 1.0.0
        Powered by Deriv WebSocket API
        Built with Streamlit, Plotly, and Python
        
        This platform provides statistical market insights for educational purposes only.
        """)
    
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
        
        # Normalize rows
        row_sums = matrix.sum(axis=1, keepdims=True)
        matrix = np.divide(matrix, row_sums, where=row_sums != 0)
        
        return matrix
    
    def _get_volatility(self, ticks: List[Tick]) -> float:
        """Get volatility from ticks."""
        if len(ticks) < 2:
            return 0.0
        
        prices = [float(t.price) for t in ticks]
        return np.std(prices)
    
    def _connect_to_deriv(self):
        """Connect to Deriv WebSocket API."""
        # This will be implemented when we integrate the WebSocket client
        st.session_state.connection_status = True
        st.success("Connected to Deriv WebSocket API!")
    
    def _clear_data(self):
        """Clear all data."""
        st.session_state.ticks = []
        st.session_state.market_analysis = None
        st.session_state.md_analysis = None
        st.session_state.ai_insight = None
        st.session_state.error_messages = []
        self.processor.clear()
        self.market_classifier._state_history = []
        self.ai_insights_engine._insight_history = []
        logger.info("Data cleared")
    
    def _export_data(self):
        """Export data to CSV."""
        ticks = st.session_state.ticks
        if not ticks:
            st.warning("No data to export")
            return
        
        try:
            # Create DataFrame
            data = {
                'tick_id': [t.tick_id for t in ticks],
                'symbol': [t.symbol for t in ticks],
                'price': [float(t.price) for t in ticks],
                'last_digit': [t.last_digit for t in ticks],
                'timestamp': [t.timestamp for t in ticks]
            }
            df = pd.DataFrame(data)
            
            # Export
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
    
    def _reset_settings(self):
        """Reset settings to defaults."""
        st.session_state.auto_update = True
        st.session_state.update_interval = 1.0
        st.session_state.selected_window = 100
        st.session_state.theme = 'dark'
        st.success("Settings reset!")