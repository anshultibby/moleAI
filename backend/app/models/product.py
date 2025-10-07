"""Product data models for e-commerce product representation"""

from datetime import date
from typing import Optional, Tuple, Any, Dict, List, Union
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_validator
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
    
    @field_validator('sku', mode='before')
    @classmethod
    def validate_sku(cls, v):
        """Convert SKU to string if it's an integer or other type"""
        if v is None:
            return None
        return str(v)
    
    @classmethod
    def from_json_ld(cls, data: Dict[str, Any], url: str = "") -> "Product":
        """
        Create Product from JSON-LD structured data.
        
        Args:
            data: JSON-LD product data dictionary
            url: Product URL (fallback if not in data)
        """
        # Extract brand
        brand = ""
        brand_data = data.get('brand', {})
        if isinstance(brand_data, dict):
            brand = brand_data.get('name', '')
        elif isinstance(brand_data, str):
            brand = brand_data
        
        # Extract price and currency from offers
        price_value = 0.0
        currency = "USD"
        offers = data.get('offers', {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if isinstance(offers, dict):
            try:
                price_value = float(offers.get('price', 0))
            except (ValueError, TypeError):
                pass
            currency = offers.get('priceCurrency', 'USD')
        
        # Extract image
        image_url = ""
        image = data.get('image')
        if isinstance(image, list):
            image_url = image[0] if image else ""
        elif isinstance(image, dict):
            image_url = image.get('url', '')
        elif isinstance(image, str):
            image_url = image
        
        return cls(
            product_name=data.get('name', ''),
            store=brand,
            price=f"${price_value:.2f}" if price_value > 0 else "N/A",
            price_value=price_value,
            product_url=data.get('url', url),
            image_url=image_url or "https://via.placeholder.com/300x300?text=No+Image",
            currency=currency,
            sku=data.get('sku'),
            description=data.get('description')
        )
    
    @classmethod
    def from_nextjs_data(cls, data: Dict[str, Any], url: str = "") -> "Product":
        """
        Create Product from Next.js __NEXT_DATA__ object.
        
        Common for React/Next.js e-commerce sites like Hello Molly.
        
        Args:
            data: Next.js product data dictionary
            url: Product URL
        """
        # Extract title
        title = data.get('title') or data.get('name', '')
        
        # Extract brand/vendor
        brand = data.get('vendor', '') or data.get('brand', '')
        
        # Extract price from variants (Shopify format)
        price_value = 0.0
        currency = "USD"
        variants = data.get('variants', [])
        if variants and len(variants) > 0:
            first_variant = variants[0]
            price = first_variant.get('price')
            
            # Handle different price formats
            if isinstance(price, dict):
                # Format: {"amount": "109.00", "currencyCode": "USD"}
                price_value = float(price.get('amount', 0))
                currency = price.get('currencyCode', 'USD')
            elif price:
                try:
                    # Shopify sometimes stores price as string or in cents
                    price_float = float(price)
                    # If price seems to be in cents (> 100), convert to dollars
                    price_value = price_float / 100 if price_float > 1000 else price_float
                except (ValueError, TypeError):
                    pass
            
            # Fallback to currency field if available
            if 'currency' in first_variant:
                currency = first_variant.get('currency', 'USD')
        
        # Extract image
        image_url = ""
        images = data.get('images', [])
        if images and len(images) > 0:
            first_image = images[0]
            if isinstance(first_image, dict):
                image_url = first_image.get('src', '') or first_image.get('url', '')
            elif isinstance(first_image, str):
                image_url = first_image
        elif 'featuredImage' in data:
            featured = data['featuredImage']
            if isinstance(featured, dict):
                image_url = featured.get('url', '') or featured.get('src', '')
            elif isinstance(featured, str):
                image_url = featured
        
        return cls(
            product_name=title,
            store=brand,
            price=f"${price_value:.2f}" if price_value > 0 else "N/A",
            price_value=price_value,
            product_url=url,
            image_url=image_url or "https://via.placeholder.com/300x300?text=No+Image",
            currency=currency,
            sku=data.get('sku', '') or data.get('id', ''),
            description=data.get('description')
        )
    
    @classmethod
    def from_meta_tags(cls, title: str, description: str = "", image_url: str = "", 
                      price: Optional[float] = None, currency: str = "USD", url: str = "") -> "Product":
        """
        Create Product from Open Graph / meta tags.
        
        Fallback method with limited data.
        
        Args:
            title: Product title
            description: Product description
            image_url: Product image URL
            price: Product price (if available)
            currency: Price currency
            url: Product URL
        """
        price_value = price or 0.0
        
        return cls(
            product_name=title,
            store="",  # Usually not available in meta tags
            price=f"${price_value:.2f}" if price_value > 0 else "N/A",
            price_value=price_value,
            product_url=url,
            image_url=image_url or "https://via.placeholder.com/300x300?text=No+Image",
            currency=currency,
            description=description
        )
    
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