"""Simple product event emitter for real-time product broadcasting"""

from typing import List, Dict, Optional
from threading import Lock
from ..utils.debug_logger import debug_log


class ProductEventEmitter:
    """Simple event emitter for products during conversations"""
    
    def __init__(self):
        self._conversation_products: List[Dict] = []
        self._sent_products: List[Dict] = []
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
    
    def reset_conversation(self) -> None:
        """Reset for new conversation"""
        with self._lock:
            debug_log("Resetting conversation products")
            self._conversation_products.clear()
            self._sent_products.clear()


# Singleton instance
_product_emitter = ProductEventEmitter()


def get_product_emitter() -> ProductEventEmitter:
    """Get the global product emitter instance"""
    return _product_emitter 