"""Product data models for e-commerce product representation"""

from typing import Optional, Tuple
from pydantic import BaseModel, Field
import re


class Product(BaseModel):
    """
    Simple product data model with core fields:
    - price: Product price amount
    - currency: Price currency (USD, EUR, etc.)
    - title: Product name/title
    - vendor: Brand or vendor name
    - sku: Stock Keeping Unit
    - image_url: Primary product image URL
    - product_id: Unique product identifier
    - variant_id: Unique variant identifier (if applicable)
    - product_url: URL to the product page
    """
    
    title: Optional[str] = Field(default=None, description="Product name/title")
    price: Optional[float] = Field(default=None, description="Product price amount")
    currency: Optional[str] = Field(default=None, description="Price currency (USD, EUR, etc.)")
    vendor: Optional[str] = Field(default=None, description="Brand or vendor name")
    sku: Optional[str] = Field(default=None, description="Stock Keeping Unit")
    image_url: Optional[str] = Field(default=None, description="Primary product image URL")
    product_id: Optional[str] = Field(default=None, description="Unique product identifier")
    variant_id: Optional[str] = Field(default=None, description="Unique variant identifier")
    product_url: Optional[str] = Field(default=None, description="URL to the product page")
    
    @classmethod
    def parse_price_and_currency(cls, price_str: str, default_currency: str = "USD") -> Tuple[Optional[float], Optional[str]]:
        """
        Parse price string and extract amount and currency
        
        Args:
            price_str: Price string like "$19.99" or "19.99 EUR"
            default_currency: Default currency if none detected
            
        Returns:
            Tuple of (price_amount, currency)
        """
        if not price_str:
            return None, None
        
        price_clean = str(price_str).strip()
        
        # Currency symbols mapping
        currency_symbols = {
            '$': 'USD',
            '€': 'EUR', 
            '£': 'GBP',
            '¥': 'JPY',
            '₹': 'INR'
        }
        
        # Check for currency symbols
        currency = default_currency
        for symbol, code in currency_symbols.items():
            if symbol in price_clean:
                currency = code
                break
        
        # Check for currency codes
        currency_codes = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'CAD', 'AUD']
        for code in currency_codes:
            if code in price_clean.upper():
                currency = code
                break
        
        # Extract numeric value
        numeric_match = re.search(r'[\d,]+\.?\d*', price_clean)
        if numeric_match:
            numeric_str = numeric_match.group().replace(',', '')
            try:
                price = float(numeric_str)
                return price, currency
            except ValueError:
                pass
        
        return None, currency
    
    def __str__(self) -> str:
        """String representation of the product"""
        parts = []
        if self.title:
            parts.append(f"'{self.title}'")
        if self.vendor:
            parts.append(f"by {self.vendor}")
        if self.price and self.currency:
            parts.append(f"- {self.price} {self.currency}")
        elif self.price:
            parts.append(f"- {self.price}")
        if self.sku:
            parts.append(f"(SKU: {self.sku})")
        
        return " ".join(parts) if parts else "Product"
