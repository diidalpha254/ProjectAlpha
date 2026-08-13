"""
Theme Management Module
Manages dark/light themes and styling for the application.
"""

from typing import Dict, Any, Optional
import streamlit as st
from ..core.logger import get_logger

logger = get_logger(__name__)


class ThemeManager:
    """
    Manages application theming including dark/light modes and custom styles.
    """
    
    def __init__(self):
        """Initialize the theme manager."""
        self._current_theme = 'dark'
        self._themes = self._initialize_themes()
        logger.info("ThemeManager initialized")
    
    def _initialize_themes(self) -> Dict[str, Dict[str, Any]]:
        """Initialize theme configurations."""
        return {
            'dark': {
                'background': '#0E1117',
                'secondary_bg': '#262730',
                'text': '#FAFAFA',
                'text_muted': '#6B6B6B',
                'primary': '#2E86C1',
                'secondary': '#E67E22',
                'success': '#27AE60',
                'danger': '#E74C3C',
                'warning': '#F39C12',
                'info': '#3498DB',
                'border': '#2D2D2D',
                'card_bg': '#1E1E1E',
                'hover': 'rgba(255,255,255,0.05)'
            },
            'light': {
                'background': '#FFFFFF',
                'secondary_bg': '#F0F2F6',
                'text': '#262730',
                'text_muted': '#6B6B6B',
                'primary': '#2E86C1',
                'secondary': '#E67E22',
                'success': '#27AE60',
                'danger': '#E74C3C',
                'warning': '#F39C12',
                'info': '#3498DB',
                'border': '#E0E0E0',
                'card_bg': '#FAFAFA',
                'hover': 'rgba(0,0,0,0.05)'
            }
        }
    
    def apply_theme(self, theme: str = 'dark'):
        """
        Apply the selected theme.
        
        Args:
            theme: Theme name ('dark' or 'light')
        """
        if theme not in self._themes:
            logger.warning(f"Theme {theme} not found, using dark")
            theme = 'dark'
        
        self._current_theme = theme
        theme_config = self._themes[theme]
        
        # Apply custom CSS
        st.markdown(self._generate_css(theme_config), unsafe_allow_html=True)
        
        # Apply to session state
        st.session_state['theme'] = theme
        st.session_state['theme_config'] = theme_config
        
        logger.info(f"Theme {theme} applied")
    
    def _generate_css(self, theme: Dict[str, Any]) -> str:
        """Generate CSS for the theme."""
        return f"""
        <style>
            /* Main theme variables */
            :root {{
                --bg-color: {theme['background']};
                --secondary-bg: {theme['secondary_bg']};
                --text-color: {theme['text']};
                --text-muted: {theme['text_muted']};
                --primary: {theme['primary']};
                --secondary: {theme['secondary']};
                --success: {theme['success']};
                --danger: {theme['danger']};
                --warning: {theme['warning']};
                --info: {theme['info']};
                --border-color: {theme['border']};
                --card-bg: {theme['card_bg']};
                --hover: {theme['hover']};
            }}
            
            /* Global styles */
            .stApp {{
                background-color: var(--bg-color);
                color: var(--text-color);
            }}
            
            /* Cards */
            .card {{
                background-color: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            
            .card-title {{
                color: var(--text-color);
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            
            /* Metric cards */
            .metric-card {{
                background-color: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 10px;
                padding: 15px;
                text-align: center;
                transition: all 0.3s ease;
            }}
            
            .metric-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }}
            
            .metric-value {{
                font-size: 28px;
                font-weight: bold;
                color: var(--primary);
            }}
            
            .metric-label {{
                font-size: 14px;
                color: var(--text-muted);
                margin-top: 5px;
            }}
            
            /* Status indicators */
            .status-indicator {{
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }}
            
            .status-online {{
                background-color: var(--success);
            }}
            
            .status-offline {{
                background-color: var(--danger);
            }}
            
            .status-warning {{
                background-color: var(--warning);
            }}
            
            /* Headers */
            h1, h2, h3, h4, h5, h6 {{
                color: var(--text-color);
            }}
            
            /* Streamlit overrides */
            .stTabs [data-baseweb="tab-list"] {{
                gap: 2px;
            }}
            
            .stTabs [data-baseweb="tab"] {{
                background-color: var(--secondary-bg);
                border-radius: 4px;
                padding: 8px 16px;
                color: var(--text-color);
            }}
            
            .stTabs [aria-selected="true"] {{
                background-color: var(--primary);
                color: white;
            }}
            
            /* Sidebar */
            .css-1d391kg {{
                background-color: var(--secondary-bg);
            }}
            
            /* DataFrame */
            .dataframe {{
                background-color: var(--card-bg);
                color: var(--text-color);
                border: 1px solid var(--border-color);
                border-radius: 5px;
            }}
            
            .dataframe th {{
                background-color: var(--secondary-bg);
                color: var(--text-color);
            }}
            
            .dataframe td {{
                color: var(--text-color);
            }}
            
            /* Scrollbar */
            ::-webkit-scrollbar {{
                width: 8px;
                height: 8px;
            }}
            
            ::-webkit-scrollbar-track {{
                background: var(--secondary-bg);
                border-radius: 4px;
            }}
            
            ::-webkit-scrollbar-thumb {{
                background: var(--primary);
                border-radius: 4px;
            }}
            
            ::-webkit-scrollbar-thumb:hover {{
                background: var(--secondary);
            }}
            
            /* Animations */
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            .fade-in {{
                animation: fadeIn 0.5s ease-out;
            }}
            
            @keyframes pulse {{
                0%, 100% {{ transform: scale(1); }}
                50% {{ transform: scale(1.05); }}
            }}
            
            .pulse {{
                animation: pulse 2s infinite;
            }}
            
            /* Responsive */
            @media (max-width: 768px) {{
                .metric-value {{
                    font-size: 22px;
                }}
                
                .card {{
                    padding: 15px;
                }}
            }}
        </style>
        """
    
    def toggle_theme(self):
        """Toggle between dark and light themes."""
        current = self._current_theme
        new_theme = 'light' if current == 'dark' else 'dark'
        self.apply_theme(new_theme)
        return new_theme
    
    def get_current_theme(self) -> str:
        """Get current theme name."""
        return self._current_theme
    
    def get_theme_config(self) -> Dict[str, Any]:
        """Get current theme configuration."""
        return self._themes.get(self._current_theme, self._themes['dark'])