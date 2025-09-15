"""Product collection model for holding extracted products from a source"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, computed_field, model_validator
from urllib.parse import urlparse
from loguru import logger

from .product import Product


class ProductCollection(BaseModel):
    source_name: str = Field(..., description="Meaningful name for the source (e.g., 'zara_dresses')")
    source_url: str = Field(..., description="Original URL that was scraped")
    pages_scraped: List[int] = Field(default_factory=list, description="List of page numbers scraped")
    products: List[Product] = Field(default_factory=list, description="List of extracted products")
    
    # Extraction metadata
    extraction_method: Optional[str] = Field(default=None, description="Method used for extraction (e.g., 'shopify_analytics')")
    
    # Source metadata
    site_name: Optional[str] = Field(default=None, description="Human-readable site name (e.g., 'Zara')")
    category: Optional[str] = Field(default=None, description="Product category if known")
    
    @computed_field
    @property
    def total_products(self) -> int:
        """Computed field for total product count"""
        return len(self.products)
    
    @model_validator(mode='before')
    @classmethod
    def set_defaults(cls, values):
        """Set default values during model creation"""
        if isinstance(values, dict):
            # Extract site name from URL if not provided
            if values.get('site_name') is None and values.get('source_url'):
                try:
                    parsed = urlparse(values['source_url'])
                    domain = parsed.netloc.replace('www.', '').split('.')[0]
                    values['site_name'] = domain.title()
                except:
                    values['site_name'] = values.get('source_name', '').title()
        
        return values
    
    def add_product(self, product: Product) -> None:
        """Add a product to the collection"""
        self.products.append(product)
    
    def add_products(self, products: List[Product]) -> None:
        """Add multiple products to the collection"""
        self.products.extend(products)
    
    
    def get_products(self, limit: int = 10, summary: bool = False, max_price: Optional[float] = None) -> Dict[str, Any]:
        """Get products with collection metadata in JSON format
        
        Args:
            limit: Maximum number of products to return (default: 10)
            summary: If True, return just product names; if False, return full Product objects (default: False)
            max_price: Maximum price filter - only include products under this price (optional)
            
        Returns:
            Dictionary with collection metadata and products list
        """
        # First filter by price if specified
        filtered_products = self.products
        if max_price is not None:
            filtered_products = [
                product for product in self.products 
                if product.price is not None and product.price <= max_price
            ]
        
        # Then apply limit (if limit is -1, return all products)
        if limit == -1:
            limited_products = filtered_products
        else:
            limited_products = filtered_products[:limit]
        
        # Prepare products data based on summary flag
        if summary:
            # Return just the product names/titles
            products_data = [product.product_name or "Untitled Product" for product in limited_products]
        else:
            # Return full Product objects as dictionaries
            products_data = [product.model_dump() for product in limited_products]
        
        # Return JSON object with metadata and products
        return {
            "source_name": self.source_name,
            "site_name": self.site_name,
            "source_url": self.source_url,
            "extraction_method": self.extraction_method,
            "total_products": self.total_products,
            "filtered_products": len(filtered_products),
            "showing_products": len(limited_products),
            "max_price_filter": max_price,
            "products": products_data
        }
    
    def __str__(self) -> str:
        """String representation"""
        if self.total_products == 0:
            return f"ProductCollection('{self.source_name}' from {self.site_name}: No products found)"
        
        lines = [
            f"ProductCollection: {self.source_name} from {self.site_name}",
            f"Total Products: {self.total_products}"
        ]
        
        # Add sample product names
        result = self.get_products(limit=3, summary=True)
        sample_names = result["products"]
        if sample_names:
            lines.append(f"Sample Products: {', '.join(sample_names)}")
            if self.total_products > 3:
                lines.append(f"... and {self.total_products - 3} more")
        
        return "\n".join(lines)
    
    def __len__(self) -> int:
        """Return number of products"""
        return len(self.products)
    
    def __iter__(self):
        """Make collection iterable over products"""
        return iter(self.products)
    
    def save_to_file(self, conversation_id: Optional[str] = None, base_dir: str = "/Users/anshul/code/moleAI/backend/resources/chat_history") -> str:
        """
        Save the ProductCollection to a JSON file in a conversation-specific folder
        
        Args:
            conversation_id: Optional conversation ID to organize files by conversation
            base_dir: Base directory for storing files (default: chat_history directory)
            
        Returns:
            The path to the saved JSON file
        """
        try:
            # Determine the directory structure
            if conversation_id:
                # Create conversation-specific folder
                conversation_dir = os.path.join(base_dir, conversation_id)
                os.makedirs(conversation_dir, exist_ok=True)
                target_dir = conversation_dir
            else:
                # Fallback to base directory
                os.makedirs(base_dir, exist_ok=True)
                target_dir = base_dir
            
            # Create filename using source name and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"products_{self.source_name}_{timestamp}.json"
            filepath = os.path.join(target_dir, filename)
            
            # Prepare data to save (use model_dump for proper serialization)
            collection_data = self.model_dump()
            collection_data.update({
                "saved_at": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "file_type": "product_collection"
            })
            
            # Save to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(collection_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved ProductCollection to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save ProductCollection for {self.source_name}: {e}")
            return ""
