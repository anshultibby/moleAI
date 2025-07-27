"""Product manipulation tools"""

from typing import Optional
from .decorator import tool
from ..utils.debug_logger import log_execution, debug_log
from ..utils.product_event_emitter import get_product_emitter


@tool(
    name="add_product", 
    description="Display a specific product to the user in the products panel. Use this after finding products with fetch_products to show selected items to the user."
)
@log_execution
def add_product(
    product_name: str,
    price: str,
    store: str,
    image_url: Optional[str] = None,
    product_url: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None
) -> str:
    """Add a product to be displayed in the frontend products panel"""
    debug_log(f"Adding product: {product_name} from {store}")
    
    try:
        # Generate a unique ID for the product
        product_id = f"{store}-{product_name}".lower().replace(" ", "-").replace("/", "-").replace("&", "and")
        
        # Create the product data
        product_data = {
            "product_name": product_name,
            "price": price,
            "store": store,
            "image_url": image_url or "",
            "product_url": product_url or "",
            "description": description or "",
            "category": category or "",
            "id": product_id
        }
        
        # Emit the product event for real-time display
        get_product_emitter().emit_product(product_data)
        
        debug_log(f"Successfully added product: {product_id}")
        return f"Added {product_name} from {store} to your product list."
        
    except Exception as e:
        debug_log(f"Error adding product: {str(e)}")
        return f"Error adding product: {str(e)}" 