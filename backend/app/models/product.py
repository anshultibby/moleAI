"""Product data models for e-commerce product representation"""

from datetime import date
from typing import Optional, Tuple, Any, Dict, List, Union
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
import re


# Import SchemaOrgProduct from schema_org_product module to avoid duplication
from .schema_org_product import SchemaOrgProduct


class Product(BaseModel):
    """
    Core product model for the tools system.
    
    This is a simplified product model with just the essential fields
    that our tools need to work with.
    """
    
    # Essential fields
    product_name: str = Field(description="Product name/title")
    store: str = Field(description="Brand or store name")
    price: str = Field(description="Product price as string (e.g., '$89.99')")
    price_value: float = Field(description="Product price as float for filtering/sorting")
    product_url: str = Field(description="URL to the product page")
    image_url: str = Field(description="Primary product image URL")
    
    # Optional fields
    currency: str = Field(default="USD", description="Price currency")
    sku: Optional[str] = Field(default=None, description="Stock Keeping Unit")
    product_id: Optional[str] = Field(default=None, description="Unique product identifier")
    color: Optional[str] = Field(default=None, description="Product color")
    size: Optional[str] = Field(default=None, description="Product size")
    description: Optional[str] = Field(default=None, description="Product description")
    
    @classmethod
    def from_schema_org_product(cls, schema_product: SchemaOrgProduct) -> "Product":
        """
        Convert a SchemaOrgProduct to a Product.
        
        Args:
            schema_product: SchemaOrgProduct instance
            
        Returns:
            Product instance with essential fields
        """
        # Extract price and ensure we have valid values
        price_value = schema_product.get_price() or 0.0
        price_str = f"${price_value:.2f}" if price_value > 0 else "N/A"
        
        # Get image URL, fallback to placeholder if none
        image_url = schema_product.get_image_url() or "https://via.placeholder.com/300x300?text=No+Image"
        
        # Get product URL, fallback to empty string if none
        product_url = str(schema_product.url) if schema_product.url else ""
        
        return cls(
            product_name=schema_product.name or "Unknown Product",
            store=schema_product.get_brand_name() or "Unknown Store",
            price=price_str,
            price_value=price_value,
            product_url=product_url,
            image_url=image_url,
            currency=schema_product.get_currency(),
            sku=schema_product.sku,
            product_id=schema_product.product_id,
            color=schema_product.color,
            size=schema_product.size,
            description=schema_product.description
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for compatibility with existing tools"""
        return {
            "product_name": self.product_name,
            "store": self.store,
            "price": self.price,
            "price_value": self.price_value,
            "product_url": self.product_url,
            "image_url": self.image_url,
            "currency": self.currency,
            "sku": self.sku,
            "product_id": self.product_id,
            "color": self.color,
            "size": self.size,
            "description": self.description
        }
    
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