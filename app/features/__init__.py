"""
Features module initialization
Exports all advanced feature components.
"""

from .replay import HistoricalReplay
from .recording import TickRecorder
from .export import DataExporter
from .screenshot import ScreenshotCapture
from .search import SearchEngine
from .plugins import Plugin, PluginManager
from .notifications import NotificationManager

__all__ = [
    'HistoricalReplay',
    'TickRecorder',
    'DataExporter',
    'ScreenshotCapture',
    'SearchEngine',
    'Plugin',
    'PluginManager',
    'NotificationManager'
]