"""
Dashboard Builder Module
Creates comprehensive dashboards combining multiple visualizations.
"""

from typing import List, Dict, Any, Optional
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np

from core.types import Tick, MarketStateAnalysis
from core.constants import MarketState, DIGIT_COLORS
from core.logger import get_logger
from.charts import ChartBuilder

logger = get_logger(__name__)


class DashboardBuilder:
    """
    Builds comprehensive dashboards with multiple visualizations.
    Creates both full-page and component-based dashboards.
    """
    
    def __init__(self):
        """Initialize the dashboard builder."""
        self.chart_builder = ChartBuilder()
        logger.info("DashboardBuilder initialized")
    
    def create_main_dashboard(
        self,
        ticks: List[Tick],
        market_analysis: Optional[MarketStateAnalysis],
        frequencies: Dict[int, float],
        transition_matrix: np.ndarray,
        confidence: float,
        volatility: float,
        window_size: int = 100
    ) -> None:
        """
        Create the main dashboard layout.
        
        Args:
            ticks: List of tick objects
            market_analysis: Market state analysis
            frequencies: Digit frequencies
            transition_matrix: Transition matrix
            confidence: Confidence score
            volatility: Volatility value
            window_size: Window size
        """
        # Header
        self._render_header(market_analysis, window_size)
        
        # Row 1: Market State, Confidence, Volatility
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if market_analysis:
                state_indicator = self.chart_builder.create_market_state_indicator(
                    market_analysis.state.value,
                    market_analysis.confidence
                )
                st.plotly_chart(state_indicator, use_container_width=True)
        
        with col2:
            confidence_gauge = self.chart_builder.create_confidence_gauge(confidence)
            st.plotly_chart(confidence_gauge, use_container_width=True)
        
        with col3:
            volatility_gauge = self.chart_builder.create_volatility_gauge(volatility)
            st.plotly_chart(volatility_gauge, use_container_width=True)
        
        # Row 2: Price Chart and Digit Timeline
        col1, col2 = st.columns([2, 1])
        
        with col1:
            price_chart = self.chart_builder.create_price_chart(ticks)
            st.plotly_chart(price_chart, use_container_width=True)
        
        with col2:
            timeline = self.chart_builder.create_digit_timeline(ticks)
            st.plotly_chart(timeline, use_container_width=True)
        
        # Row 3: Frequency Histogram and Distribution
        col1, col2 = st.columns(2)
        
        with col1:
            histogram = self.chart_builder.create_frequency_histogram(frequencies, window_size)
            st.plotly_chart(histogram, use_container_width=True)
        
        with col2:
            donut = self.chart_builder.create_digit_distribution_donut(frequencies)
            st.plotly_chart(donut, use_container_width=True)
        
        # Row 4: Transition Heatmap and Network
        col1, col2 = st.columns(2)
        
        with col1:
            heatmap = self.chart_builder.create_transition_heatmap(transition_matrix)
            st.plotly_chart(heatmap, use_container_width=True)
        
        with col2:
            network = self.chart_builder.create_transition_network(transition_matrix)
            st.plotly_chart(network, use_container_width=True)
    
    def _render_header(self, market_analysis: Optional[MarketStateAnalysis], window_size: int):
        """Render the dashboard header."""
        st.title("📊 Project Alpha - Market Intelligence Dashboard")
        
        if market_analysis:
            state = market_analysis.state.value.upper()
            emoji = MARKET_STATE_DESCRIPTIONS.get(state, {}).get('emoji', '📊')
            color = MARKET_STATE_DESCRIPTIONS.get(state, {}).get('color', '#3498DB')
            
            st.markdown(
                f"""
                <div style='background-color: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px; border-left: 5px solid {color};'>
                    <h2>{emoji} Market State: <span style='color: {color};'>{state}</span></h2>
                    <p><strong>Confidence:</strong> {market_analysis.confidence:.1%} | 
                       <strong>Risk Level:</strong> {market_analysis.risk_level.value.upper()} | 
                       <strong>Window:</strong> {window_size} ticks</p>
                    <p><strong>Analysis Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style='background-color: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px;'>
                    <h2>⏳ Waiting for Market Data</h2>
                    <p>Connect to Deriv and start receiving ticks to see analysis.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    def create_match_differ_dashboard(
        self,
        ticks: List[Tick],
        md_insight: Any,
        frequencies: Dict[int, float],
        transition_probs: Dict[str, float]
    ) -> None:
        """
        Create the Match/Differ intelligence dashboard.
        
        Args:
            ticks: List of tick objects
            md_insight: Match/Differ insight
            frequencies: Digit frequencies
            transition_probs: Transition probabilities
        """
        st.header("🎯 Match/Differ Intelligence Dashboard")
        
        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._render_metric_card(
                "Market Condition",
                md_insight.market_condition.upper(),
                "📊"
            )
        
        with col2:
            match_prob = transition_probs.get('match_probability', 0)
            self._render_metric_card(
                "Match Probability",
                f"{match_prob:.1%}",
                "🎯"
            )
        
        with col3:
            differ_prob = transition_probs.get('differ_probability', 0)
            self._render_metric_card(
                "Differ Probability",
                f"{differ_prob:.1%}",
                "🎯"
            )
        
        with col4:
            confidence = md_insight.confidence_indicators.get('overall_confidence', 0)
            self._render_metric_card(
                "Confidence",
                f"{confidence:.1%}",
                "📈"
            )
        
        # Observations
        st.subheader("📝 Key Observations")
        for obs in md_insight.observations[:5]:
            st.markdown(f"• {obs}")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            dist_chart = self.chart_builder.create_digit_distribution_donut(frequencies)
            st.plotly_chart(dist_chart, use_container_width=True)
        
        with col2:
            if hasattr(md_insight, 'transition_probabilities'):
                # Create a simple bar chart of transition probs
                probs = md_insight.transition_probabilities
                if probs:
                    fig = go.Figure(data=[
                        go.Bar(
                            x=list(probs.keys()),
                            y=list(probs.values()),
                            marker_color='#2E86C1',
                            text=[f'{v:.1%}' for v in probs.values()],
                            textposition='auto'
                        )
                    ])
                    fig.update_layout(
                        title='Key Transition Probabilities',
                        yaxis_title='Probability',
                        yaxis_tickformat='.0%',
                        template='plotly_dark',
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Pattern Summary
        st.subheader("🔍 Pattern Summary")
        st.markdown(md_insight.pattern_summary)
        
        # Historical Context
        st.subheader("📜 Historical Context")
        st.markdown(md_insight.historical_context)
        
        # Explanation
        st.subheader("💡 AI Explanation")
        st.markdown(md_insight.explanation)
    
    def _render_metric_card(self, label: str, value: str, icon: str):
        """Render a metric card."""
        st.markdown(
            f"""
            <div style='background-color: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; text-align: center;'>
                <div style='font-size: 24px;'>{icon}</div>
                <div style='font-size: 14px; color: #888;'>{label}</div>
                <div style='font-size: 20px; font-weight: bold;'>{value}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def create_ai_insights_dashboard(self, insight: Any) -> None:
        """
        Create the AI Insights dashboard.
        
        Args:
            insight: AI Insight object
        """
        st.header("🤖 AI Market Analyst")
        
        # What's happening
        st.subheader("📌 What Is Happening")
        st.markdown(f"*{insight.what_is_happening}*")
        
        # Why classified
        st.subheader("🔍 Why The Market Was Classified This Way")
        st.markdown(insight.why_classified)
        
        # Statistical factors
        st.subheader("📊 Statistical Factors")
        for factor in insight.statistical_factors:
            st.markdown(f"• {factor}")
        
        # Market differences
        st.subheader("🔄 How Current Market Differs From Previous Periods")
        st.markdown(insight.market_differences)
        
        # Risks
        st.subheader("⚠️ Risks & Warnings")
        for risk in insight.risks:
            st.warning(risk)
        
        # Confidence
        st.subheader("📈 Confidence Level")
        confidence_color = self._get_confidence_color(insight.confidence_level)
        st.progress(insight.confidence_level)
        st.markdown(f"Confidence: **{insight.confidence_level:.1%}** - {self._get_confidence_text(insight.confidence_level)}")
    
    def _get_confidence_color(self, confidence: float) -> str:
        """Get color for confidence level."""
        if confidence >= 0.8:
            return "#2ECC71"
        elif confidence >= 0.6:
            return "#F1C40F"
        elif confidence >= 0.4:
            return "#E67E22"
        else:
            return "#E74C3C"
    
    def _get_confidence_text(self, confidence: float) -> str:
        """Get text for confidence level."""
        if confidence >= 0.8:
            return "Very High"
        elif confidence >= 0.6:
            return "High"
        elif confidence >= 0.4:
            return "Moderate"
        elif confidence >= 0.2:
            return "Low"
        else:
            return "Very Low"
