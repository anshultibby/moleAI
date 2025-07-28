"""Product manipulation tools"""

from typing import Optional, List
from .decorator import tool
from ..utils.debug_logger import log_execution, debug_log
from ..utils.product_event_emitter import get_product_emitter


@tool(
    name="display_product", 
    description="Display a specific product to the user in the products panel. Use this after finding products with fetch_products to show selected items to the user."
)
@log_execution
def display_product(
    product_name: str,
    price: str,
    store: str,
    image_url: Optional[str] = None,
    product_url: Optional[str] = None,
    category: Optional[str] = None
) -> str:
    """Add a product to be displayed in the frontend products panel"""
    debug_log(f"Displaying product: {product_name} from {store}")
    
    try:
        # Generate a unique ID for the product
        product_id = f"{store}-{product_name}".lower().replace(" ", "-").replace("/", "-").replace("&", "and")
        
        # Create the product data
        product_data = {
            "product_name": product_name,
            "price": price,
            "currency": "USD",  # Default to USD, could be made a parameter in the future
            "store": store,
            "image_url": image_url or "",
            "product_url": product_url or "",
            "description": "",
            "category": category or "",
            "id": product_id
        }
        
        # Emit the product event for real-time display
        get_product_emitter().emit_product(product_data)
        
        debug_log(f"Successfully displayed product: {product_id}")
        return f"Displayed {product_name} from {store} to your product list."
        
    except Exception as e:
        debug_log(f"Error displaying product: {str(e)}")
        return f"Error displaying product: {str(e)}"


@tool(
    name="get_displayed_products",
    description="Get all products currently displayed to the user in the products panel. Returns a list of all products with their details."
)
@log_execution
def get_displayed_products() -> str:
    """Get all products currently displayed in the frontend products panel"""
    debug_log("Getting all displayed products")
    
    try:
        products = get_product_emitter().get_all_products()
        
        if not products:
            return "No products are currently displayed."
        
        # Format the products for the LLM
        product_list = []
        for i, product in enumerate(products, 1):
            product_info = f"{i}. {product.get('product_name', 'Unknown')} from {product.get('store', 'Unknown')} - {product.get('price', 'Price not available')}"
            if product.get('description'):
                product_info += f"\n   Description: {product.get('description')[:100]}..."
            product_list.append(product_info)
        
        result = f"Currently displaying {len(products)} products:\n\n" + "\n\n".join(product_list)
        debug_log(f"Retrieved {len(products)} displayed products")
        return result
        
    except Exception as e:
        debug_log(f"Error getting displayed products: {str(e)}")
        return f"Error getting displayed products: {str(e)}"


@tool(
    name="remove_displayed_products",
    description="Remove specific products from display by name, or remove all products if no names provided. Provide product names exactly as they appear in the display."
)
@log_execution
def remove_displayed_products(product_names: Optional[List[str]] = None) -> str:
    """Remove specific products by name, or all products if no names provided"""
    debug_log(f"Removing displayed products: {product_names}")
    
    try:
        if product_names is None:
            product_names = []
        
        removed_names = get_product_emitter().remove_products_by_name(product_names)
        
        if not removed_names:
            if product_names:
                return f"No products found with the specified names: {product_names}"
            else:
                return "No products were displayed to remove."
        
        if not product_names:
            # All products were removed
            debug_log(f"Successfully removed all {len(removed_names)} products")
            return f"Removed all {len(removed_names)} products from display."
        else:
            # Specific products were removed
            debug_log(f"Successfully removed {len(removed_names)} specific products")
            return f"Removed {len(removed_names)} products from display: {', '.join(removed_names)}"
        
    except Exception as e:
        debug_log(f"Error removing displayed products: {str(e)}")
        return f"Error removing displayed products: {str(e)}" 