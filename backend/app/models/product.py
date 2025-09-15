"""Product data models for e-commerce product representation"""

from typing import Optional, Tuple, Any, Dict, List
from pydantic import BaseModel, Field, field_validator, model_validator
import re




class Product(BaseModel):
    """
    Strict product data model - all fields required with smart defaults
    """
    
    product_name: str = Field(description="Product name/title")
    store: str = Field(description="Brand or store name")  
    price: str = Field(description="Product price as string (e.g., '$89.99')")
    price_value: float = Field(description="Product price as float for filtering/sorting")
    product_url: str = Field(description="URL to the product page")
    image_url: str = Field(description="Primary product image URL")
    currency: str = Field(default="USD", description="Price currency")
    sku: Optional[str] = Field(default=None, description="Stock Keeping Unit")
    product_id: Optional[str] = Field(default=None, description="Unique product identifier")
    variant_id: Optional[str] = Field(default=None, description="Unique variant identifier")
    
    # Enhanced product attributes
    product_type: Optional[str] = Field(default=None, description="Product type/category (e.g., 'Dress', 'Shirt')")
    color: Optional[str] = Field(default=None, description="Primary color of this variant")
    size: Optional[str] = Field(default=None, description="Size of this variant")
    material: Optional[str] = Field(default=None, description="Material/fabric information")
    tags: Optional[List[str]] = Field(default=None, description="Product tags/categories")
    color_variants: Optional[List[str]] = Field(default=None, description="Available color options")
    size_variants: Optional[List[str]] = Field(default=None, description="Available size options")
    variant_options: Optional[Dict[str, List[str]]] = Field(default=None, description="All variant options (color, size, etc.)")
    
    @field_validator('product_name', mode='before')
    @classmethod
    def clean_product_name(cls, v: Any) -> str:
        """Clean and validate product name"""
        if not v:
            raise ValueError("Product name is required")
        
        # Clean up the name
        name = str(v).strip()
        # Remove extra whitespace
        name = ' '.join(name.split())
        # Remove common prefixes/suffixes that aren't useful
        name = name.replace('New!', '').replace('Sale!', '').strip()
        
        if not name:
            raise ValueError("Product name cannot be empty after cleaning")
        
        return name
    
    @field_validator('store', mode='before')
    @classmethod
    def clean_store_name(cls, v: Any, info) -> str:
        """Clean store name or extract from product_url if missing"""
        if v:
            # Clean existing store name
            store = str(v).strip()
            store = ' '.join(store.split())  # Remove extra whitespace
            return store
        
        # Try to extract from product_url if available
        if hasattr(info, 'data') and info.data and 'product_url' in info.data:
            product_url = info.data.get('product_url')
            if product_url:
                from urllib.parse import urlparse
                try:
                    domain = urlparse(product_url).netloc
                    if domain:
                        # Clean up domain to make it a nice store name
                        # Remove www. prefix
                        clean_domain = domain.replace('www.', '')
                        # Remove common TLDs and get the main domain name
                        for tld in ['.com', '.net', '.org', '.co.uk', '.ca', '.au']:
                            clean_domain = clean_domain.replace(tld, '')
                        # Capitalize first letter of each word (for multi-word domains)
                        store = clean_domain.replace('-', ' ').replace('_', ' ').title()
                        return store
                except Exception:
                    pass
        
        # If we still don't have a store name, use a default
        return "Unknown Store"
    
    @field_validator('price', mode='before')
    @classmethod
    def parse_price_field(cls, v: Any) -> str:
        """
        Clean and validate price field, keeping it as a string.
        
        Args:
            v: Price value (can be string like '$89.99' or numeric)
            
        Returns:
            Cleaned price string
            
        Raises:
            ValueError: If price cannot be parsed or is None/empty
        """
        if v is None or v == '':
            raise ValueError("Price is required and cannot be empty")
        
        # If it's a number, format it nicely
        if isinstance(v, (int, float)):
            return f"${v:.2f}"
        
        # If string, clean it up
        if isinstance(v, str):
            price_str = str(v).strip()
            if not price_str:
                raise ValueError("Price cannot be empty")
            
            # If it doesn't have a currency symbol, try to parse and add $
            if not any(symbol in price_str for symbol in ['$', '€', '£', '¥', '₹']):
                try:
                    price_num = float(price_str.replace(',', ''))
                    return f"${price_num:.2f}"
                except ValueError:
                    pass
            
            return price_str
        
        # Fallback: convert to string
        return str(v)
    
    @field_validator('price_value', mode='before')
    @classmethod
    def calculate_price_value(cls, v: Any, info) -> float:
        """
        Calculate numeric price value from price string for filtering/sorting.
        If price_value is provided directly, use it. Otherwise extract from price string.
        """
        # If price_value is explicitly provided, use it
        if v is not None and v != '':
            try:
                return float(v)
            except (ValueError, TypeError):
                pass
        
        # Extract from price string if available
        if hasattr(info, 'data') and info.data and 'price' in info.data:
            price_str = info.data.get('price')
            if price_str:
                try:
                    price_num, _ = cls.parse_price_and_currency(str(price_str))
                    if price_num is not None:
                        return price_num
                except:
                    pass
        
        # If we can't extract a price value, this will fail validation
        raise ValueError("Could not determine numeric price value")
    
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
        if self.product_name:
            parts.append(f"'{self.product_name}'")
        if self.store:
            parts.append(f"by {self.store}")
        if self.color:
            parts.append(f"in {self.color}")
        if self.size:
            parts.append(f"size {self.size}")
        if self.price and self.currency:
            parts.append(f"- {self.price} {self.currency}")
        elif self.price:
            parts.append(f"- {self.price}")
        if self.product_type:
            parts.append(f"({self.product_type})")
        if self.sku:
            parts.append(f"(SKU: {self.sku})")
        
        return " ".join(parts) if parts else "Product"
