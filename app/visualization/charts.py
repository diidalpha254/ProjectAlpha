"""
Chart Builder Module
Creates interactive Plotly charts for market data visualization.
"""

from typing import List, Dict, Any, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

from ..core.types import Tick
from ..core.constants import DIGIT_COLORS, MARKET_STATE_DESCRIPTIONS
from ..core.logger import get_logger

logger = get_logger(__name__)


class ChartBuilder:
    """
    Builds interactive Plotly charts for market data visualization.
    Supports various chart types including histograms, heat maps, and gauges.
    """
    
    def __init__(self):
        """Initialize the chart builder."""
        self.theme = self._get_default_theme()
        logger.info("ChartBuilder initialized")
    
    def _get_default_theme(self) -> Dict[str, Any]:
        """Get default chart theme."""
        return {
            'template': 'plotly_dark',
            'colorway': ['#2E86C1', '#E67E22', '#27AE60', '#E74C3C', '#F39C12', 
                        '#8E44AD', '#1ABC9C', '#3498DB', '#2ECC71', '#F1C40F'],
            'font_family': 'Inter, Arial, sans-serif',
            'background_color': '#1E1E1E',
            'grid_color': '#2D2D2D',
            'text_color': '#ECF0F1'
        }
    
    def create_frequency_histogram(self, frequencies: Dict[int, float], window_size: int = 100) -> go.Figure:
        """
        Create a frequency histogram of digit distribution.
        
        Args:
            frequencies: Digit frequencies (0-9)
            window_size: Window size used
            
        Returns:
            go.Figure: Plotly figure object
        """
        digits = list(range(10))
        freq_values = [frequencies.get(d, 0) for d in digits]
        
        # Create colors based on frequency
        colors = []
        for freq in freq_values:
            if freq > 0.15:
                colors.append(DIGIT_COLORS.get(freq_values.index(freq), '#FF6B6B'))
            elif freq > 0.1:
                colors.append('#4ECDC4')
            elif freq > 0.05:
                colors.append('#45B7D1')
            else:
                colors.append('#96CEB4')
        
        fig = go.Figure(data=[
            go.Bar(
                x=digits,
                y=freq_values,
                text=[f'{freq:.1%}' for freq in freq_values],
                textposition='auto',
                marker_color=colors,
                hovertemplate='Digit %{x}<br>Frequency: %{y:.1%}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=f'Digit Frequency Distribution (Window: {window_size})',
            xaxis_title='Last Digit',
            yaxis_title='Frequency',
            yaxis_tickformat='.0%',
            template=self.theme['template'],
            font_family=self.theme['font_family'],
            height=400,
            showlegend=False,
            hovermode='x'
        )
        
        # Add expected frequency line
        fig.add_hline(
            y=0.1,
            line_dash="dash",
            line_color="red",
            annotation_text="Expected (10%)",
            annotation_position="bottom right"
        )
        
        return fig
    
    def create_transition_heatmap(self, matrix: np.ndarray) -> go.Figure:
        """
        Create a heatmap of transition probabilities.
        
        Args:
            matrix: 10x10 transition probability matrix
            
        Returns:
            go.Figure: Plotly figure object
        """
        if matrix is None or matrix.shape != (10, 10):
            matrix = np.zeros((10, 10))
        
        fig = go.Figure(data=[
            go.Heatmap(
                z=matrix,
                x=list(range(10)),
                y=list(range(10)),
                colorscale='RdYlGn',
                zmin=0,
                zmax=0.5,
                text=[[f'{val:.1%}' for val in row] for row in matrix],
                texttemplate='%{text}',
                textfont={"size": 10},
                hovertemplate='From: %{y}<br>To: %{x}<br>Probability: %{z:.1%}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Digit Transition Probability Matrix',
            xaxis_title='To Digit',
            yaxis_title='From Digit',
            template=self.theme['template'],
            font_family=self.theme['font_family'],
            height=500,
            width=500
        )
        
        return fig
    
    def create_price_chart(self, ticks: List[Tick]) -> go.Figure:
        """
        Create a price chart with tick data.
        
        Args:
            ticks: List of tick objects
            
        Returns:
            go.Figure: Plotly figure object
        """
        if not ticks:
            return self._empty_figure("No price data available")
        
        timestamps = [t.timestamp for t in ticks]
        prices = [float(t.price) for t in ticks]
        digits = [t.last_digit for t in ticks]
        
        # Create figure with secondary y-axis
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.7, 0.3],
            subplot_titles=('Price Chart', 'Last Digit')
        )
        
        # Price line
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=prices,
                mode='lines',
                name='Price',
                line=dict(color='#2E86C1', width=2),
                hovertemplate='Price: %{y:.4f}<br>Time: %{x}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add price range
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=[np.mean(prices)] * len(prices),
                mode='lines',
                name='Mean',
                line=dict(color='#E67E22', width=1, dash='dash'),
                showlegend=True
            ),
            row=1, col=1
        )
        
        # Last digit markers
        colors = [DIGIT_COLORS.get(d, '#FFFFFF') for d in digits]
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=digits,
                mode='markers',
                name='Last Digit',
                marker=dict(
                    size=8,
                    color=colors,
                    line=dict(width=1, color='white')
                ),
                hovertemplate='Digit: %{y}<br>Time: %{x}<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title='Live Price and Digit Chart',
            template=self.theme['template'],
            font_family=self.theme['font_family'],
            height=600,
            hovermode='x unified'
        )
        
        fig.update_yaxes(title_text='Price', row=1, col=1)
        fig.update_yaxes(title_text='Last Digit', row=2, col=1, dtick=1, range=[-0.5, 9.5])
        
        return fig
    
    def create_confidence_gauge(self, confidence: float) -> go.Figure:
        """
        Create a gauge chart for confidence scores.
        
        Args:
            confidence: Confidence score (0-1)
            
        Returns:
            go.Figure: Plotly figure object
        """
        # Determine color based on confidence
        if confidence >= 0.8:
            color = '#2ECC71'  # Green
            level = "Very High"
        elif confidence >= 0.6:
            color = '#F1C40F'  # Yellow
            level = "High"
        elif confidence >= 0.4:
            color = '#E67E22'  # Orange
            level = "Moderate"
        elif confidence >= 0.2:
            color = '#E74C3C'  # Red
            level = "Low"
        else:
            color = '#C0392B'  # Dark Red
            level = "Very Low"
        
        fig = go.Figure(data=[
            go.Indicator(
                mode="gauge+number+delta",
                value=confidence * 100,
                number={'suffix': '%', 'font': {'size': 40}},
                delta={'reference': 50, 'increasing.color': '#2ECC71', 'decreasing.color': '#E74C3C'},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': color},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 20], 'color': 'rgba(200, 50, 50, 0.3)'},
                        {'range': [20, 40], 'color': 'rgba(200, 100, 50, 0.3)'},
                        {'range': [40, 60], 'color': 'rgba(200, 150, 50, 0.3)'},
                        {'range': [60, 80], 'color': 'rgba(50, 200, 50, 0.3)'},
                        {'range': [80, 100], 'color': 'rgba(50, 200, 50, 0.5)'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 2},
                        'thickness': 0.75,
                        'value': 50
                    }
                }
            )
        ])
        
        fig.update_layout(
            title=f'Confidence: {level} ({confidence:.1%})',
            template=self.theme['template'],
            font_family=self.theme['font_family'],
            height=300,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
    
    def create_volatility_gauge(self, volatility: float) -> go.Figure:
        """
        Create a gauge chart for volatility.
        
        Args:
            volatility: Volatility value
            
        Returns:
            go.Figure: Plotly figure object
        """
        # Normalize volatility (assuming max 0.1 is very high)
        normalized = min(volatility / 0.1, 1.0) * 100
        
        # Determine color based on volatility
        if normalized < 20:
            color = '#2ECC71'
            level = "Very Low"
        elif normalized < 40:
            color = '#F1C40F'
            level = "Low"
        elif normalized < 60:
            color = '#E67E22'
            level = "Moderate"
        elif normalized < 80:
            color = '#E74C3C'
            level = "High"
        else:
            color = '#C0392B'
            level = "Very High"
        
        fig = go.Figure(data=[
            go.Indicator(
                mode="gauge+number",
                value=normalized,
                number={'suffix': '%', 'font': {'size': 40}},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1},
                    'bar': {'color': color},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 20], 'color': 'rgba(50, 200, 50, 0.3)'},
                        {'range': [20, 40], 'color': 'rgba(200, 200, 50, 0.3)'},
                        {'range': [40, 60], 'color': 'rgba(200, 150, 50, 0.3)'},
                        {'range': [60, 80], 'color': 'rgba(200, 100, 50, 0.3)'},
                        {'range': [80, 100], 'color': 'rgba(200, 50, 50, 0.3)'}
                    ]
                }
            )
        ])
        
        fig.update_layout(
            title=f'Volatility: {level} ({volatility:.3f})',
            template=self.theme['template'],
            font_family=self.theme['font_family'],
            height=300,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
    
    def create_market_state_indicator(self, state: str, confidence: float) -> go.Figure:
        """
        Create a market state indicator.
        
        Args:
            state: Market state string
            confidence: Confidence score
            
        Returns:
            go.Figure: Plotly figure object
        """
        # Get state info
        state_info = MARKET_STATE_DESCRIPTIONS.get(state, {})
        emoji = state_info.get('emoji', '📊')
        color = state_info.get('color', '#3498DB')
        
        fig = go.Figure()
        
        # Add annotation for state
        fig.add_annotation(
            text=f"{emoji} {state.upper()}",
            xref="paper", yref="paper",
            x=0.5, y=0.6,
            showarrow=False,
            font=dict(size=40, color=color, family=self.theme['font_family']),
            align="center"
        )
        
        # Add confidence
        fig.add_annotation(
            text=f"Confidence: {confidence:.1%}",
            xref="paper", yref="paper",
            x=0.5, y=0.3,
            showarrow=False,
            font=dict(size=20, color='white', family=self.theme['font_family']),
            align="center"
        )
        
        fig.update_layout(
            template=self.theme['template'],
            height=200,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_digit_timeline(self, ticks: List[Tick], max_points: int = 100) -> go.Figure:
        """
        Create a timeline of last digits.
        
        Args:
            ticks: List of tick objects
            max_points: Maximum number of points to show
            
        Returns:
            go.Figure: Plotly figure object
        """
        if not ticks:
            return self._empty_figure("No data available")
        
        # Limit points
        ticks = ticks[-max_points:]
        
        timestamps = [t.timestamp for t in ticks]
        digits = [t.last_digit for t in ticks]
        colors = [DIGIT_COLORS.get(d, '#FFFFFF') for d in digits]
        
        fig = go.Figure(data=[
            go.Scatter(
                x=timestamps,
                y=digits,
                mode='markers+lines',
                name='Digits',
                marker=dict(
                    size=10,
                    color=colors,
                    line=dict(width=1, color='white')
                ),
                line=dict(color='rgba(255,255,255,0.3)', width=1),
                hovertemplate='Digit: %{y}<br>Time: %{x}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Last Digit Timeline',
            xaxis_title='Time',
            yaxis_title='Last Digit',
            template=self.theme['template'],
            font_family=self.theme['font_family'],
            height=300,
            yaxis=dict(dtick=1, range=[-0.5, 9.5]),
            hovermode='x'
        )
        
        return fig
    
    def create_pattern_heatmap(self, patterns: List[Tuple[List[int], int]]) -> go.Figure:
        """
        Create a heatmap of detected patterns.
        
        Args:
            patterns: List of (pattern, frequency) tuples
            
        Returns:
            go.Figure: Plotly figure object
        """
        if not patterns:
            return self._empty_figure("No patterns detected")
        
        # Prepare data
        pattern_strings = [''.join(map(str, p[0])) for p in patterns[:10]]
        frequencies = [p[1] for p in patterns[:10]]
        
        # Create horizontal bar chart
        fig = go.Figure(data=[
            go.Bar(
                y=pattern_strings,
                x=frequencies,
                orientation='h',
                marker_color='#2E86C1',
                text=frequencies,
                textposition='auto',
                hovertemplate='Pattern: %{y}<br>Frequency: %{x}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Top Detected Patterns',
            xaxis_title='Frequency',
            yaxis_title='Pattern',
            template=self.theme['template'],
            font_family=self.theme['font_family'],
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_digit_distribution_donut(self, frequencies: Dict[int, float]) -> go.Figure:
        """
        Create a donut chart of digit distribution.
        
        Args:
            frequencies: Digit frequencies
            
        Returns:
            go.Figure: Plotly figure object
        """
        if not frequencies:
            return self._empty_figure("No data available")
        
        labels = [f'Digit {i}' for i in range(10)]
        values = [frequencies.get(i, 0) for i in range(10)]
        colors = [DIGIT_COLORS.get(i, '#FFFFFF') for i in range(10)]
        
        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='outside',
                hovertemplate='%{label}<br>Frequency: %{percent}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Digit Distribution',
            template=self.theme['template'],
            font_family=self.theme['font_family'],
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2)
        )
        
        return fig
    
    def create_transition_network(self, matrix: np.ndarray, threshold: float = 0.1) -> go.Figure:
        """
        Create a network diagram of digit transitions.
        
        Args:
            matrix: 10x10 transition matrix
            threshold: Minimum probability to show
            
        Returns:
            go.Figure: Plotly figure object
        """
        if matrix is None or matrix.shape != (10, 10):
            return self._empty_figure("No transition data available")
        
        # Nodes
        node_labels = [f'Digit {i}' for i in range(10)]
        node_colors = [DIGIT_COLORS.get(i, '#FFFFFF') for i in range(10)]
        
        # Edges
        edge_x = []
        edge_y = []
        edge_text = []
        
        # Position nodes in a circle
        angles = np.linspace(0, 2 * np.pi, 10, endpoint=False)
        node_x = np.cos(angles)
        node_y = np.sin(angles)
        
        # Create edges for significant transitions
        for i in range(10):
            for j in range(10):
                if i != j and matrix[i][j] > threshold:
                    # Add edge
                    edge_x.extend([node_x[i], node_x[j], None])
                    edge_y.extend([node_y[i], node_y[j], None])
                    edge_text.append(f'{matrix[i][j]:.1%}')
        
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            mode='lines',
            line=dict(width=1, color='rgba(255,255,255,0.3)'),
            hoverinfo='none',
            showlegend=False
        ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(
                size=30,
                color=node_colors,
                line=dict(width=2, color='white')
            ),
            text=node_labels,
            textposition='middle center',
            textfont=dict(color='white', size=12),
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))
        
        fig.update_layout(
            title='Digit Transition Network',
            template=self.theme['template'],
            font_family=self.theme['font_family'],
            height=500,
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            hovermode='closest'
        )
        
        return fig
    
    def _empty_figure(self, message: str = "No data available") -> go.Figure:
        """Create an empty figure with a message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color='gray')
        )
        fig.update_layout(
            template=self.theme['template'],
            height=400,
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False)
        )
        return fig