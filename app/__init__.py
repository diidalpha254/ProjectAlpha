"""
Project Alpha - Advanced Market Intelligence Platform
"""

__version__ = "1.0.0"
__author__ = "Project Alpha Team"

from .main import main
from .core.logger import get_logger
from .core.constants import MarketState, RiskLevel
from .core.types import Tick, MarketStateAnalysis

__all__ = [
    'main',
    'get_logger',
    'MarketState',
    'RiskLevel',
    'Tick',
    'MarketStateAnalysis'
]