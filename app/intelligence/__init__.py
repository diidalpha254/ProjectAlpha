"""
Intelligence module initialization
Exports Match/Differ intelligence components.
"""

from .match_differ import MatchDifferIntelligence, MatchDifferAnalysis
from .context import HistoricalContext

__all__ = [
    'MatchDifferIntelligence',
    'MatchDifferAnalysis',
    'HistoricalContext'
]