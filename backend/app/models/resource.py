from pydantic import BaseModel, model_validator
from typing import Literal, Optional, Dict, Any
from .product_collection import ProductCollection


class ResourceMetadata(BaseModel):
    content_type: Literal["product_collection"]
    product_count: int
    source_url: str
    extraction_method: Optional[str] = None
    site_name: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return f"ResourceMetadata(content_type={self.content_type}, product_count={self.product_count}, site_name={self.site_name})"
    
    def format_for_llm(self) -> str:
        """Format metadata for LLM without including the extra field"""
        return f"ResourceMetadata(content_type={self.content_type}, product_count={self.product_count}, site_name={self.site_name}, source_url={self.source_url})"

class Resource(BaseModel):
    id: str
    product_collection: ProductCollection
    metadata: ResourceMetadata
    
    @model_validator(mode='before')
    @classmethod
    def set_metadata_from_collection(cls, values):
        """Automatically set metadata from ProductCollection"""
        if isinstance(values, dict) and 'product_collection' in values:
            collection = values['product_collection']
            if isinstance(collection, ProductCollection) and 'metadata' in values:
                metadata = values['metadata']
                if isinstance(metadata, dict):
                    # Set product_count if not already provided
                    if 'product_count' not in metadata:
                        metadata['product_count'] = len(collection.products)
                    # Set source_url if not already provided
                    if 'source_url' not in metadata:
                        metadata['source_url'] = collection.source_url
                    # Set site_name if not already provided
                    if 'site_name' not in metadata:
                        metadata['site_name'] = collection.site_name
                    # Set extraction_method if not already provided
                    if 'extraction_method' not in metadata:
                        metadata['extraction_method'] = collection.extraction_method
        return values

    def format_for_llm(self, exclude_content: bool = False, max_products: Optional[int] = 5) -> str:
        if exclude_content:
            return f"Resource ID: {self.id}\nMetadata: {self.metadata.format_for_llm()}"
        else:
            # Format product collection summary
            collection = self.product_collection
            summary_lines = [
                f"Resource ID: {self.id}",
                f"Product Collection: {collection.source_name}",
                f"Site: {collection.site_name}",
                f"Total Products: {len(collection.products)}",
                f"Source URL: {collection.source_url}"
            ]
            
            if collection.products and max_products and max_products > 0:
                summary_lines.append("\nSample Products:")
                for i, product in enumerate(collection.products[:max_products]):
                    title = product.title or 'Untitled Product'
                    price_info = f"{product.price} {product.currency}" if product.price and product.currency else "Price not available"
                    vendor_info = f" by {product.vendor}" if product.vendor else ""
                    summary_lines.append(f"  {i+1}. {title}{vendor_info} - {price_info}")
                
                if len(collection.products) > max_products:
                    summary_lines.append(f"  ... and {len(collection.products) - max_products} more products")
            
            summary_lines.append(f"\nMetadata: {self.metadata.format_for_llm()}")
            return "\n".join(summary_lines)

