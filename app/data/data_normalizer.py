"""
Data Normalizer Module
Validates, cleans, and normalizes incoming tick data before processing.
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid

from core.types import Tick
from core.exceptions import DataValidationError
from core.logger import get_logger
from core.constants import DerivSymbol


logger = get_logger(__name__)


class DataNormalizer:
    """
    Validates and normalizes tick data from various sources.
    Ensures data quality before entering the processing pipeline.
    """
    
    # Supported symbols pattern
    SYMBOL_PATTERN = re.compile(r'^[A-Z0-9_]+$')
    
    # Price validation ranges
    MIN_PRICE = 0.01
    MAX_PRICE = 1000000.0
    
    def __init__(self):
        """Initialize the data normalizer."""
        self.validation_stats = {
            "total_validated": 0,
            "total_invalid": 0,
            "errors_by_type": {}
        }
        logger.info("DataNormalizer initialized")
    
    def normalize_tick(self, raw_data: Dict[str, Any]) -> Optional[Tick]:
        """
        Normalize raw tick data into a validated Tick object.
        
        Args:
            raw_data: Raw tick data from WebSocket
            
        Returns:
            Optional[Tick]: Normalized Tick object or None if invalid
        """
        try:
            self.validation_stats["total_validated"] += 1
            
            # Validate required fields
            if not self._validate_required_fields(raw_data):
                self._increment_error("missing_required_fields")
                return None
            
            # Extract and validate symbol
            symbol = self._normalize_symbol(raw_data.get("symbol", ""))
            if not symbol:
                self._increment_error("invalid_symbol")
                return None
            
            # Extract and validate price
            price = self._normalize_price(raw_data)
            if price is None:
                self._increment_error("invalid_price")
                return None
            
            # Extract timestamp
            timestamp = self._normalize_timestamp(raw_data)
            if timestamp is None:
                self._increment_error("invalid_timestamp")
                return None
            
            # Extract tick_id or generate one
            tick_id = raw_data.get("tick_id") or raw_data.get("id") or str(uuid.uuid4())
            
            # Extract optional fields
            bid = self._normalize_price_value(raw_data.get("bid"))
            ask = self._normalize_price_value(raw_data.get("ask"))
            volume = self._normalize_volume(raw_data.get("volume"))
            
            # Calculate last digit from price
            last_digit = self._extract_last_digit(price)
            
            # Create Tick object
            tick = Tick(
                tick_id=tick_id,
                symbol=symbol,
                price=price,
                last_digit=last_digit,
                timestamp=timestamp,
                bid=bid,
                ask=ask,
                volume=volume
            )
            
            # Final validation
            if not self._validate_tick(tick):
                self._increment_error("validation_failed")
                return None
            
            logger.debug(f"Normalized tick: {tick.symbol} @ {tick.price} (digit: {tick.last_digit})")
            return tick
            
        except Exception as e:
            logger.error(f"Error normalizing tick: {e}", exc_info=True)
            self._increment_error("normalization_error")
            return None
    
    def _validate_required_fields(self, data: Dict[str, Any]) -> bool:
        """Validate that all required fields are present."""
        # Check if tick is present (could be nested or flat)
        has_price = (
            "tick" in data or 
            "price" in data or 
            "quote" in data
        )
        
        if not has_price:
            logger.warning(f"Missing price data in: {data.keys()}")
            return False
        
        # Check for symbol
        if not data.get("symbol"):
            logger.warning("Missing symbol in data")
            return False
        
        # Check for timestamp
        if not data.get("epoch") and not data.get("timestamp"):
            logger.warning("Missing timestamp in data")
            return False
        
        return True
    
    def _normalize_symbol(self, symbol: str) -> Optional[str]:
        """Normalize and validate symbol string."""
        if not symbol:
            return None
        
        # Clean symbol
        symbol = symbol.strip().upper()
        
        # Validate against allowed symbols
        if not self.SYMBOL_PATTERN.match(symbol):
            logger.warning(f"Invalid symbol format: {symbol}")
            return None
        
        return symbol
    
    def _normalize_price(self, data: Dict[str, Any]) -> Optional[Decimal]:
        """Extract and normalize price from various formats."""
        # Try different price field names
        price_value = None
        
        # Check nested tick object
        if "tick" in data and isinstance(data["tick"], dict):
            price_value = data["tick"].get("quote")
        elif "tick" in data and isinstance(data["tick"], (int, float, str)):
            price_value = data["tick"]
        elif "quote" in data:
            price_value = data["quote"]
        elif "price" in data:
            price_value = data["price"]
        
        if price_value is None:
            return None
        
        return self._normalize_price_value(price_value)
    
    def _normalize_price_value(self, value: Any) -> Optional[Decimal]:
        """Normalize a single price value."""
        if value is None:
            return None
        
        try:
            # Convert to Decimal for precision
            if isinstance(value, (int, float, str)):
                price = Decimal(str(value))
                
                # Validate price range
                if price < self.MIN_PRICE or price > self.MAX_PRICE:
                    logger.warning(f"Price out of range: {price}")
                    return None
                
                # Round to appropriate precision
                if price > 1000:
                    price = price.quantize(Decimal('0.001'))
                elif price > 100:
                    price = price.quantize(Decimal('0.0001'))
                else:
                    price = price.quantize(Decimal('0.00001'))
                
                return price
            else:
                logger.warning(f"Invalid price type: {type(value)}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to normalize price: {e}")
            return None
    
    def _normalize_timestamp(self, data: Dict[str, Any]) -> Optional[datetime]:
        """Extract and normalize timestamp."""
        try:
            # Try epoch timestamp first
            if "epoch" in data:
                epoch = data["epoch"]
                if isinstance(epoch, (int, float)):
                    return datetime.fromtimestamp(epoch)
            
            # Try timestamp field
            if "timestamp" in data:
                ts = data["timestamp"]
                if isinstance(ts, (int, float)):
                    return datetime.fromtimestamp(ts)
                elif isinstance(ts, str):
                    try:
                        return datetime.fromisoformat(ts)
                    except ValueError:
                        pass
            
            # Use current time as fallback
            logger.warning("Using current time as fallback timestamp")
            return datetime.now()
            
        except Exception as e:
            logger.warning(f"Failed to normalize timestamp: {e}")
            return None
    
    def _normalize_volume(self, volume: Any) -> Optional[int]:
        """Normalize volume value."""
        if volume is None:
            return None
        
        try:
            if isinstance(volume, (int, float, str)):
                vol = int(float(str(volume)))
                if vol >= 0:
                    return vol
            return None
        except:
            return None
    
    def _extract_last_digit(self, price: Decimal) -> int:
        """Extract the last digit from a price value."""
        try:
            # Convert to string and get last digit
            price_str = str(price)
            # Remove decimal point and get last character
            clean_str = price_str.replace('.', '').replace('-', '')
            if clean_str:
                last_digit = int(clean_str[-1])
                return last_digit
            return 0
        except Exception as e:
            logger.warning(f"Failed to extract last digit: {e}")
            return 0
    
    def _validate_tick(self, tick: Tick) -> bool:
        """Perform final validation on a Tick object."""
        try:
            # Validate last digit
            if not 0 <= tick.last_digit <= 9:
                logger.warning(f"Invalid last digit: {tick.last_digit}")
                return False
            
            # Validate price is positive
            if tick.price <= 0:
                logger.warning(f"Non-positive price: {tick.price}")
                return False
            
            # Validate symbol
            if not tick.symbol:
                logger.warning("Empty symbol")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Tick validation failed: {e}")
            return False
    
    def _increment_error(self, error_type: str):
        """Increment error counter."""
        self.validation_stats["total_invalid"] += 1
        self.validation_stats["errors_by_type"][error_type] = (
            self.validation_stats["errors_by_type"].get(error_type, 0) + 1
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            **self.validation_stats,
            "error_rate": (
                self.validation_stats["total_invalid"] / 
                max(1, self.validation_stats["total_validated"]) * 100
            )
        }
    
    def reset_stats(self):
        """Reset validation statistics."""
        self.validation_stats = {
            "total_validated": 0,
            "total_invalid": 0,
            "errors_by_type": {}
        }
