"""
Risk Communication Module
Communicates risk assessments and warnings in a clear, transparent manner.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.constants import RiskLevel, MarketState
from ..core.logger import get_logger

logger = get_logger(__name__)


class RiskCommunicator:
    """
    Communicates risk assessments in clear, actionable language.
    Avoids overstatement and maintains transparency.
    """
    
    def __init__(self):
        """Initialize the risk communicator."""
        self._risk_warnings = self._initialize_warnings()
        logger.info("RiskCommunicator initialized")
    
    def _initialize_warnings(self) -> Dict[str, List[str]]:
        """Initialize risk warning templates."""
        return {
            'market': {
                'volatile': [
                    "⚠️ High volatility increases risk. Adjust position sizing accordingly.",
                    "⚠️ Volatility is elevated. Consider reducing trade size.",
                    "⚠️ Price swings are large. Risk management is critical."
                ],
                'chaotic': [
                    "🚨 Extreme chaotic conditions. Maximum caution advised.",
                    "🚨 Market is highly unpredictable. Consider staying on the sidelines.",
                    "🚨 Chaotic environment. Risk of significant losses is elevated."
                ],
                'trending': [
                    "📊 Trending market. Watch for potential reversals.",
                    "📊 Trend strength is building. Monitor for exhaustion.",
                    "📊 Directional movement is clear. Set appropriate stop-losses."
                ],
                'random': [
                    "🎲 Random conditions. Avoid over-committing to any direction.",
                    "🎲 Market is unpredictable. Use smaller position sizes.",
                    "🎲 No clear pattern. Diversify risk."
                ]
            },
            'general': [
                "⚠️ All trading involves risk. Never risk more than you can afford to lose.",
                "⚠️ Past performance does not guarantee future results.",
                "⚠️ This analysis is for informational purposes only.",
                "⚠️ Always use stop-loss orders to manage risk.",
                "⚠️ Consider consulting with a financial advisor for personalized advice.",
                "⚠️ Market conditions can change rapidly. Stay vigilant.",
                "⚠️ Diversification can help manage risk."
            ]
        }
    
    def communicate_risk(self, risk_level: RiskLevel, market_state: MarketState, confidence: float) -> List[str]:
        """
        Generate risk communications.
        
        Args:
            risk_level: Current risk level
            market_state: Current market state
            confidence: Confidence in analysis
            
        Returns:
            List[str]: Risk communication messages
        """
        messages = []
        
        try:
            # Add risk level warning
            if risk_level == RiskLevel.VERY_HIGH:
                messages.append("🚨 VERY HIGH RISK: Extreme caution required. Consider avoiding new positions.")
            elif risk_level == RiskLevel.HIGH:
                messages.append("⚠️ HIGH RISK: Careful risk management essential. Reduce position sizes.")
            elif risk_level == RiskLevel.MODERATE:
                messages.append("⚖️ MODERATE RISK: Normal risk management practices recommended.")
            elif risk_level == RiskLevel.LOW:
                messages.append("✅ LOW RISK: Favorable conditions, but maintain standard risk practices.")
            else:
                messages.append("✅ VERY LOW RISK: Stable conditions, maintain normal position sizing.")
            
            # Add market state warnings
            market_warnings = self._risk_warnings['market'].get(market_state.value.lower(), [])
            if market_warnings:
                messages.append(market_warnings[0])
            
            # Add confidence warning
            if confidence < 0.3:
                messages.append("⚠️ Low confidence in analysis. Exercise extra caution.")
            elif confidence < 0.5:
                messages.append("⚠️ Moderate confidence. Consider this one of many indicators.")
            
            # Add specific risk indicators
            if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
                messages.append("💡 Consider reducing exposure or using tighter stops.")
            elif risk_level in [RiskLevel.LOW, RiskLevel.VERY_LOW]:
                messages.append("💡 Stable environment. Maintain normal risk parameters.")
            
            # Add general warnings
            general_warnings = self._risk_warnings['general']
            if confidence < 0.6:
                # Add more warnings when confidence is low
                messages.extend(general_warnings[:3])
            else:
                messages.append(general_warnings[0])
            
        except Exception as e:
            logger.warning(f"Error communicating risk: {e}")
            messages.append("⚠️ Risk assessment in progress. Trade responsibly.")
        
        return messages
    
    def get_detailed_risk_explanation(self, risk_factors: Dict[str, Any]) -> str:
        """
        Generate detailed risk explanation based on risk factors.
        
        Args:
            risk_factors: Dictionary of risk factors
            
        Returns:
            str: Detailed risk explanation
        """
        explanation_parts = []
        
        try:
            # Market risk
            if 'market_risk' in risk_factors:
                mr = risk_factors['market_risk']
                if mr > 0.7:
                    explanation_parts.append("Market risk is elevated due to unstable conditions")
                elif mr > 0.4:
                    explanation_parts.append("Market risk is moderate")
                else:
                    explanation_parts.append("Market risk is low")
            
            # Pattern risk
            if 'pattern_risk' in risk_factors:
                pr = risk_factors['pattern_risk']
                if pr > 0.7:
                    explanation_parts.append("Pattern risk is high due to unpredictable behavior")
                elif pr > 0.4:
                    explanation_parts.append("Pattern risk is moderate")
                else:
                    explanation_parts.append("Pattern risk is low")
            
            # Volatility risk
            if 'volatility_risk' in risk_factors:
                vr = risk_factors['volatility_risk']
                if vr > 0.7:
                    explanation_parts.append("Volatility risk is high with large price swings")
                elif vr > 0.4:
                    explanation_parts.append("Volatility risk is moderate")
                else:
                    explanation_parts.append("Volatility risk is low")
            
            # Confidence risk
            if 'confidence_risk' in risk_factors:
                cr = risk_factors['confidence_risk']
                if cr > 0.7:
                    explanation_parts.append("Confidence in analysis is low, increasing uncertainty")
                elif cr > 0.4:
                    explanation_parts.append("Confidence in analysis is moderate")
                else:
                    explanation_parts.append("Confidence in analysis is high")
            
            # Overall risk
            if 'overall_risk' in risk_factors:
                overall = risk_factors['overall_risk']
                if overall > 0.7:
                    explanation_parts.append("Overall risk is HIGH - exercise maximum caution")
                elif overall > 0.4:
                    explanation_parts.append("Overall risk is MODERATE - maintain standard practices")
                else:
                    explanation_parts.append("Overall risk is LOW - favorable conditions")
            
        except Exception as e:
            logger.warning(f"Error generating risk explanation: {e}")
            explanation_parts.append("Risk analysis in progress")
        
        return ". ".join(explanation_parts) if explanation_parts else "No risk analysis available"
    
    def get_risk_mitigation_suggestions(self, risk_level: RiskLevel) -> List[str]:
        """
        Get risk mitigation suggestions based on risk level.
        
        Args:
            risk_level: Current risk level
            
        Returns:
            List[str]: Risk mitigation suggestions
        """
        suggestions = []
        
        if risk_level == RiskLevel.VERY_HIGH:
            suggestions.extend([
                "🚨 Consider avoiding all new positions",
                "📉 Reduce existing position sizes significantly",
                "🔍 Monitor market closely for reversals",
                "⏰ Consider waiting for conditions to stabilize",
                "📊 Use wider stop-losses to avoid premature exits"
            ])
        elif risk_level == RiskLevel.HIGH:
            suggestions.extend([
                "📉 Reduce position sizes by 50%",
                "🛑 Set tight stop-losses",
                "📊 Monitor positions actively",
                "🔍 Look for signs of volatility decrease",
                "💡 Consider hedging strategies"
            ])
        elif risk_level == RiskLevel.MODERATE:
            suggestions.extend([
                "⚖️ Maintain standard position sizing",
                "🛑 Use normal stop-loss levels",
                "📊 Regular position monitoring",
                "💡 Consider taking partial profits"
            ])
        elif risk_level == RiskLevel.LOW:
            suggestions.extend([
                "📈 Consider slightly larger positions",
                "🛑 Use normal stop-losses",
                "📊 Monitor for changing conditions",
                "💡 Look for opportunities"
            ])
        else:  # VERY_LOW
            suggestions.extend([
                "📈 Normal position sizing",
                "🛑 Standard stop-loss levels",
                "📊 Regular monitoring sufficient",
                "💡 Consider scaling in"
            ])
        
        # Add universal suggestions
        suggestions.extend([
            "⚠️ Always use stop-loss orders",
            "📊 Diversify your positions",
            "🔍 Stay informed about market conditions"
        ])
        
        return suggestions
    
    def get_transparent_disclaimer(self) -> str:
        """
        Get the transparent disclaimer for all communications.
        
        Returns:
            str: Disclaimer text
        """
        return """
        ⚠️ TRANSPARENT ANALYSIS DISCLAIMER:
        
        • This analysis is based on statistical observations and historical data patterns.
        • No prediction of future outcomes is implied or guaranteed.
        • Market conditions can change rapidly and unpredictably.
        • Use this analysis as one of many tools in your decision-making process.
        • All trading involves risk. Never risk more than you can afford to lose.
        • Past performance does not guarantee future results.
        • Consider consulting with a qualified financial advisor.
        """