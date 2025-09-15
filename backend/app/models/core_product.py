"""
Core Product model for the tools system

This is a simplified product model with just the essential fields
that our tools need to work with.
"""

from typing import Optional
from pydantic import BaseModel, Field

from app.models.schema_org_product import SchemaOrgProduct


class CoreProduct(BaseModel):
    """
    Core product model with essential fields for the tools system.
    
    This is a simplified version of the full schema.org Product model,
    containing only the fields we actually use in our tools.
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
    def from_schema_org_product(cls, schema_product: SchemaOrgProduct) -> "CoreProduct":
        """
        Convert a SchemaOrgProduct to a CoreProduct.
        
        Args:
            schema_product: SchemaOrgProduct instance
            
        Returns:
            CoreProduct instance with essential fields
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
