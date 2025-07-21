"""
Real-time Product Streaming Service
Handles streaming products to frontend as they are discovered
"""

import queue
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime


class ProductStreamingService:
    """Manages real-time streaming of products to frontend"""
    
    def __init__(self):
        self.product_queue = queue.Queue(maxsize=1000)  # Prevent memory issues
        self.streaming_callback: Optional[Callable] = None
        self._stats = {
            'products_queued': 0,
            'products_yielded': 0,
            'queue_overflows': 0,
            'session_start': datetime.now()
        }
    
    def set_streaming_callback(self, callback: Callable):
        """Set the callback function for streaming updates"""
        self.streaming_callback = callback
        print(f"🔧 STREAMING: Callback set (ID: {id(callback) if callback else 'None'})")
    
    def get_streaming_callback(self) -> Optional[Callable]:
        """Get the current streaming callback"""
        return self.streaming_callback
    
    def queue_product(self, update_type: str, data: Dict[str, Any]) -> bool:
        """Queue a product for streaming to frontend"""
        if update_type == "product" and isinstance(data, dict):
            product_update = {"type": "product", "data": data}
            product_name = data.get('product_name', 'Unknown')
            
            try:
                self.product_queue.put_nowait(product_update)
                self._stats['products_queued'] += 1
                print(f"   🚀 QUEUED: {product_name} (queue size: {self.product_queue.qsize()})")
                return True
                
            except queue.Full:
                self._stats['queue_overflows'] += 1
                print(f"   ⚠️  Queue full, dropping product: {product_name}")
                return False
                
            except Exception as e:
                print(f"   ❌ Queue error for {product_name}: {e}")
                return False
        
        return False
    
    def get_queued_products(self) -> list:
        """Get all queued products without blocking"""
        products = []
        try:
            while True:
                product_update = self.product_queue.get_nowait()
                products.append(product_update)
                self._stats['products_yielded'] += 1
        except queue.Empty:
            pass
        
        if products:
            print(f"   ✅ Retrieved {len(products)} products from queue")
        
        return products
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.product_queue.qsize()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics"""
        return {
            **self._stats,
            'current_queue_size': self.product_queue.qsize(),
            'session_duration': (datetime.now() - self._stats['session_start']).total_seconds()
        }
    
    def clear_queue(self):
        """Clear the product queue"""
        cleared_count = self.product_queue.qsize()
        
        try:
            while True:
                self.product_queue.get_nowait()
        except queue.Empty:
            pass
        
        if cleared_count > 0:
            print(f"   🧹 Cleared {cleared_count} products from queue")
    
    def create_streaming_callback(self):
        """Create a callback function that queues products for streaming"""
        def streaming_callback(update_type: str, data: Any):
            """Stream products to queue for real-time delivery"""
            return self.queue_product(update_type, data)
        
        return streaming_callback


# Global instance for shared use across modules
_streaming_service = ProductStreamingService()


def get_streaming_service() -> ProductStreamingService:
    """Get the global streaming service instance"""
    return _streaming_service


def set_streaming_callback(callback: Callable):
    """Set the streaming callback (compatibility function)"""
    _streaming_service.set_streaming_callback(callback)


def get_streaming_callback() -> Optional[Callable]:
    """Get the streaming callback (compatibility function)"""
    return _streaming_service.get_streaming_callback() 