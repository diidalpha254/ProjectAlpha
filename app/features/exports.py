"""
Data Export Module
Exports data to various formats including CSV, JSON, and Excel.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import pandas as pd
import json
import csv
from io import StringIO, BytesIO

from app.core.types import Tick
from app.core.logger import get_logger
from app.storage.database import DatabaseManager

logger = get_logger(__name__)


class DataExporter:
    """
    Exports market data to various formats.
    Supports CSV, JSON, Excel, and HTML formats.
    """
    
    def __init__(self):
        """Initialize the data exporter."""
        self.database = DatabaseManager()
        logger.info("DataExporter initialized")
    
    def export_ticks_to_csv(self, ticks: List[Tick]) -> str:
        """
        Export ticks to CSV format.
        
        Args:
            ticks: List of tick objects
            
        Returns:
            str: CSV data as string
        """
        if not ticks:
            return ""
        
        try:
            # Convert to DataFrame
            data = {
                'tick_id': [t.tick_id for t in ticks],
                'symbol': [t.symbol for t in ticks],
                'price': [float(t.price) for t in ticks],
                'last_digit': [t.last_digit for t in ticks],
                'timestamp': [t.timestamp.isoformat() for t in ticks],
                'bid': [float(t.bid) if t.bid else None for t in ticks],
                'ask': [float(t.ask) if t.ask else None for t in ticks],
                'volume': [t.volume for t in ticks]
            }
            df = pd.DataFrame(data)
            
            # Export to CSV
            output = StringIO()
            df.to_csv(output, index=False)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting ticks to CSV: {e}")
            return ""
    
    def export_ticks_to_json(self, ticks: List[Tick]) -> str:
        """
        Export ticks to JSON format.
        
        Args:
            ticks: List of tick objects
            
        Returns:
            str: JSON data as string
        """
        if not ticks:
            return "[]"
        
        try:
            data = []
            for tick in ticks:
                data.append({
                    'tick_id': tick.tick_id,
                    'symbol': tick.symbol,
                    'price': float(tick.price),
                    'last_digit': tick.last_digit,
                    'timestamp': tick.timestamp.isoformat(),
                    'bid': float(tick.bid) if tick.bid else None,
                    'ask': float(tick.ask) if tick.ask else None,
                    'volume': tick.volume
                })
            
            return json.dumps(data, indent=2)
            
        except Exception as e:
            logger.error(f"Error exporting ticks to JSON: {e}")
            return "[]"
    
    def export_ticks_to_excel(self, ticks: List[Tick]) -> BytesIO:
        """
        Export ticks to Excel format.
        
        Args:
            ticks: List of tick objects
            
        Returns:
            BytesIO: Excel file as bytes
        """
        if not ticks:
            return BytesIO()
        
        try:
            # Convert to DataFrame
            data = {
                'tick_id': [t.tick_id for t in ticks],
                'symbol': [t.symbol for t in ticks],
                'price': [float(t.price) for t in ticks],
                'last_digit': [t.last_digit for t in ticks],
                'timestamp': [t.timestamp.isoformat() for t in ticks],
                'bid': [float(t.bid) if t.bid else None for t in ticks],
                'ask': [float(t.ask) if t.ask else None for t in ticks],
                'volume': [t.volume for t in ticks]
            }
            df = pd.DataFrame(data)
            
            # Export to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Ticks', index=False)
                
                # Add summary sheet
                summary = pd.DataFrame({
                    'Metric': ['Total Ticks', 'Symbol', 'Start Time', 'End Time', 'Average Price'],
                    'Value': [
                        len(ticks),
                        ticks[0].symbol if ticks else '',
                        ticks[0].timestamp.isoformat() if ticks else '',
                        ticks[-1].timestamp.isoformat() if ticks else '',
                        sum(float(t.price) for t in ticks) / len(ticks) if ticks else 0
                    ]
                })
                summary.to_excel(writer, sheet_name='Summary', index=False)
            
            output.seek(0)
            return output
            
        except Exception as e:
            logger.error(f"Error exporting ticks to Excel: {e}")
            return BytesIO()
    
    def export_analysis_to_html(self, analysis: Dict[str, Any]) -> str:
        """
        Export analysis results to HTML format.
        
        Args:
            analysis: Analysis results dictionary
            
        Returns:
            str: HTML data as string
        """
        try:
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Project Alpha - Analysis Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                    h1 { color: #2E86C1; }
                    .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                    .metric { display: inline-block; margin: 10px 20px; }
                    .value { font-size: 24px; font-weight: bold; color: #2E86C1; }
                    .label { font-size: 14px; color: #666; }
                    table { width: 100%; border-collapse: collapse; }
                    th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📊 Project Alpha - Analysis Report</h1>
                    <p>Generated: {timestamp}</p>
            """
            
            # Add summary
            if 'summary' in analysis:
                html += '<div class="section"><h2>Summary</h2>'
                for key, value in analysis['summary'].items():
                    html += f'<div class="metric"><div class="value">{value}</div><div class="label">{key}</div></div>'
                html += '</div>'
            
            # Add frequency analysis
            if 'frequency' in analysis:
                html += '<div class="section"><h2>Digit Frequency Analysis</h2>'
                html += '<table><tr><th>Digit</th><th>Count</th><th>Frequency</th><th>Z-Score</th></tr>'
                freq = analysis['frequency']
                for digit in range(10):
                    count = freq.get('digit_counts', {}).get(digit, 0)
                    frequency = freq.get('frequencies', {}).get(digit, 0)
                    z_score = freq.get('z_scores', {}).get(digit, 0)
                    html += f'<tr><td>{digit}</td><td>{count}</td><td>{frequency:.1%}</td><td>{z_score:.2f}</td></tr>'
                html += '</table></div>'
            
            # Add transition matrix
            if 'markov' in analysis:
                html += '<div class="section"><h2>Transition Matrix</h2>'
                html += '<table><tr><th>From\\To</th>'
                for i in range(10):
                    html += f'<th>{i}</th>'
                html += '</tr>'
                matrix = analysis['markov'].get('transition_matrix', [])
                if matrix is not None:
                    for i in range(min(10, len(matrix))):
                        html += f'<tr><td><b>{i}</b></td>'
                        row = matrix[i]
                        for j in range(min(10, len(row))):
                            html += f'<td>{row[j]:.1%}</td>'
                        html += '</tr>'
                html += '</table></div>'
            
            # Close HTML
            html += """
                    <p style="margin-top: 30px; color: #999; font-size: 12px;">
                        This report was generated by Project Alpha - Market Intelligence Platform.<br>
                        For informational purposes only. Not financial advice.
                    </p>
                </div>
            </body>
            </html>
            """
            
            return html.format(timestamp=datetime.now().isoformat())
            
        except Exception as e:
            logger.error(f"Error exporting analysis to HTML: {e}")
            return "<html><body><p>Error generating report</p></body></html>"
    
    def export_ticks(self, ticks: List[Tick], format: str = 'csv') -> Union[str, BytesIO]:
        """
        Export ticks in specified format.
        
        Args:
            ticks: List of tick objects
            format: Export format ('csv', 'json', 'excel')
            
        Returns:
            Union[str, BytesIO]: Exported data
        """
        if format == 'csv':
            return self.export_ticks_to_csv(ticks)
        elif format == 'json':
            return self.export_ticks_to_json(ticks)
        elif format == 'excel':
            return self.export_ticks_to_excel(ticks)
        else:
            logger.warning(f"Unsupported format: {format}")
            return ""
