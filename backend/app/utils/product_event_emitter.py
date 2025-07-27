"""Simple product event emitter for real-time product broadcasting"""

from typing import List, Dict, Optional
from threading import Lock
from ..utils.debug_logger import debug_log


class ProductEventEmitter:
    """Simple event emitter for products during conversations"""
    
    def __init__(self):
        self._conversation_products: List[Dict] = []
        self._sent_products: List[Dict] = []
        self._removed_product_ids: List[str] = []  # Track removed product IDs
        self._lock = Lock()
    
    def emit_product(self, product_data: Dict) -> None:
        """Emit a product for the current conversation"""
        with self._lock:
            debug_log(f"Emitting product: {product_data.get('product_name', 'Unknown')} from {product_data.get('store', 'Unknown')}")
            self._conversation_products.append(product_data)
    
    def get_new_products(self) -> List[Dict]:
        """Get products emitted since last call (don't clear all products)"""
        with self._lock:
            # Find products that haven't been sent yet
            new_products = []
            for product in self._conversation_products:
                if product not in self._sent_products:
                    new_products.append(product)
                    self._sent_products.append(product)
            
            debug_log(f"Retrieved {len(new_products)} new products out of {len(self._conversation_products)} total")
            if new_products:
                for product in new_products:
                    debug_log(f"  → {product.get('product_name', 'Unknown')} from {product.get('store', 'Unknown')}")
            return new_products
    
    def get_all_products(self) -> List[Dict]:
        """Get all products currently in the conversation"""
        with self._lock:
            debug_log(f"Retrieved all {len(self._conversation_products)} conversation products")
            return self._conversation_products.copy()
    
    def remove_products_by_name(self, product_names: List[str]) -> List[str]:
        """Remove products by name and return list of actually removed product names"""
        with self._lock:
            if not product_names:
                # Remove all products
                removed_count = len(self._conversation_products)
                removed_names = [p.get('product_name', 'Unknown') for p in self._conversation_products]
                # Track all removed product IDs
                for product in self._conversation_products:
                    if product.get('id'):
                        self._removed_product_ids.append(product['id'])
                self._conversation_products.clear()
                self._sent_products.clear()
                debug_log(f"Cleared all {removed_count} products")
                return removed_names
            
            # Remove specific products by name and track their IDs
            removed_names = []
            products_to_keep = []
            for product in self._conversation_products:
                if product.get('product_name', '') in product_names:
                    removed_names.append(product.get('product_name', ''))
                    # Track removed product ID
                    if product.get('id'):
                        self._removed_product_ids.append(product['id'])
                else:
                    products_to_keep.append(product)
            
            self._conversation_products = products_to_keep
            
            # Also remove from sent products
            self._sent_products = [
                product for product in self._sent_products
                if product.get('product_name', '') not in product_names
            ]
            
            debug_log(f"Removed {len(removed_names)} products: {removed_names}")
            return removed_names
    
    def reset_conversation(self) -> None:
        """Reset for new conversation"""
        with self._lock:
            debug_log("Resetting conversation products")
            self._conversation_products.clear()
            self._sent_products.clear()
    
    def add_removed_product_id(self, product_id: str) -> None:
        """Add a product ID to the list of removed products."""
        with self._lock:
            self._removed_product_ids.append(product_id)
            debug_log(f"Added removed product ID: {product_id}")
    
    def get_removed_product_ids(self) -> List[str]:
        """Get product IDs that were removed since last call"""
        with self._lock:
            removed_ids = self._removed_product_ids.copy()
            self._removed_product_ids.clear()  # Clear after returning
            if removed_ids:
                debug_log(f"Retrieved {len(removed_ids)} removed product IDs: {removed_ids}")
            return removed_ids


# Singleton instance
_product_emitter = ProductEventEmitter()


def get_product_emitter() -> ProductEventEmitter:
    """Get the global product emitter instance"""
    return _product_emitter 