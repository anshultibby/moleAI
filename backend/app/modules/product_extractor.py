"""Product extraction module for e-commerce platforms"""

from typing import List
from loguru import logger

from app.models.product import Product
from .extractors import (
    ProductExtractionError,
    ShopifyAnalyticsExtractor,
    AtomFeedExtractor,
    HtmlHeuristicExtractor
)


class ProductExtractor:
    """
    Main product extractor that orchestrates multiple extraction methods.
    
    Uses a cascade of extraction methods:
    1. Shopify Analytics (fast path) - extracts from analytics blob
    2. Atom Feed - extracts from RSS/Atom feeds 
    3. HTML Heuristics - extracts using CSS selectors and patterns
    """
    
    def __init__(self):
        """Initialize the product extractor with all extraction methods"""
        self.shopify_extractor = ShopifyAnalyticsExtractor()
        self.atom_extractor = AtomFeedExtractor()
        self.html_extractor = HtmlHeuristicExtractor()
    
    def extract_products(self, html_content: str, url: str = "") -> List[Product]:
        """
        Extract products using all available methods in priority order.
        
        Args:
            html_content: The HTML content to extract from
            url: Optional URL for context and logging
            
        Returns:
            List of Product instances
            
        Raises:
            ProductExtractionError: If all extraction methods fail
        """
        try:
            logger.info(f"Starting product extraction {'for ' + url if url else ''}")
            
            # Method 1: Try Shopify Analytics (fastest, most reliable)
            try:
                products = self.shopify_extractor.extract_products(html_content, url)
                if products:
                    logger.info(f"Successfully extracted {len(products)} products using Shopify analytics")
                    return products
            except Exception as e:
                logger.debug(f"Shopify analytics extraction failed: {e}")
            
            # Method 2: Try Atom Feed extraction
            try:
                products = self.atom_extractor.extract_products(html_content, url)
                if products:
                    logger.info(f"Successfully extracted {len(products)} products using Atom feeds")
                    return products
            except Exception as e:
                logger.debug(f"Atom feed extraction failed: {e}")
            
            # Method 3: Try HTML heuristics (fallback)
            try:
                products = self.html_extractor.extract_products(html_content, url)
                if products:
                    logger.info(f"Successfully extracted {len(products)} products using HTML heuristics")
                    return products
            except Exception as e:
                logger.debug(f"HTML heuristic extraction failed: {e}")
            
            # If all methods failed
            logger.warning("All extraction methods failed to find products")
            return []
            
        except Exception as e:
            error_msg = f"Product extraction failed: {str(e)}"
            logger.error(error_msg)
            raise ProductExtractionError(error_msg)
    
    def extract_shopify_products(self, html_content: str, url: str = "") -> List[Product]:
        """
        Extract products specifically using Shopify analytics method.
        
        This method is kept for backward compatibility.
        
        Args:
            html_content: The HTML content of the Shopify page
            url: Optional URL for logging purposes
            
        Returns:
            List of Product instances
        """
        return self.shopify_extractor.extract_products(html_content, url)
    
    def extract_from_atom_feeds(self, html_content: str, url: str = "") -> List[Product]:
        """
        Extract products specifically using Atom feed method.
        
        Args:
            html_content: The HTML content to search for Atom feed links
            url: Optional URL for context
            
        Returns:
            List of Product instances
        """
        return self.atom_extractor.extract_products(html_content, url)
    
    def extract_from_html_heuristics(self, html_content: str, url: str = "") -> List[Product]:
        """
        Extract products specifically using HTML heuristic method.
        
        Args:
            html_content: The HTML content to extract from
            url: Optional URL for context
            
        Returns:
            List of Product instances
        """
        return self.html_extractor.extract_products(html_content, url)
