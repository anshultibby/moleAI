"""Product extraction module for e-commerce platforms"""

from typing import List, Dict, Any, Optional
import re
import asyncio
from loguru import logger

from app.models.product import Product
from app.models.product_collection import ProductCollection
from .direct_scraper import DirectScraper
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
        self.scraper = DirectScraper()
    
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
    
    async def scrape_and_extract_products(self, 
                                        source_name: str, 
                                        url: str, 
                                        render_js: bool = True, 
                                        wait: int = 2000) -> ProductCollection:
        """
        Scrape a URL and extract products, returning a ProductCollection.
        
        Args:
            source_name: Meaningful name for the source (e.g., "zara_dresses")
            url: URL to scrape and extract products from
            render_js: Whether to render JavaScript (default: True)
            wait: Time to wait in milliseconds after page load (default: 2000ms)
            
        Returns:
            ProductCollection with extracted products
            
        Raises:
            ProductExtractionError: If scraping or extraction fails
        """
        try:
            logger.info(f"Scraping and extracting products from {source_name}: {url}")
            
            # Step 1: Scrape the page content
            html_content = await self.scraper.scrape_url(
                url, 
                render_js=render_js, 
                wait=wait,
                smart_js_detection=True
            )
            
            # Step 2: Extract products from the scraped content
            products = self.extract_products(html_content, url)
            
            # Step 3: Create ProductCollection
            product_collection = ProductCollection(
                source_name=source_name,
                source_url=url,
                products=products,
                extraction_method="multi_method"
            )
            
            logger.info(f"Successfully extracted {len(products)} products from {source_name}")
            return product_collection
            
        except Exception as e:
            error_msg = f"Failed to scrape and extract products from {url}: {str(e)}"
            logger.error(error_msg)
            raise ProductExtractionError(error_msg)
        finally:
            # Clean up scraper resources
            await self.scraper.cleanup()
    
    async def scrape_and_extract_multiple(self, 
                                         urls: Dict[str, str], 
                                         render_js: bool = True, 
                                         wait: int = 2000,
                                         progress_callback=None,
                                         max_concurrent: int = 3,
                                         conversation_id: Optional[str] = None) -> List[ProductCollection]:
        """
        Scrape multiple URLs and extract products in parallel, returning ProductCollections.
        
        Args:
            urls: Dictionary where keys are meaningful resource names and values are URLs
            render_js: Whether to render JavaScript (default: True)
            wait: Time to wait in milliseconds after page load (default: 2000ms)
            progress_callback: Optional callback function for progress updates
            max_concurrent: Maximum number of concurrent extractions (default: 3)
            conversation_id: Optional conversation ID for saving files to conversation directory
            
        Returns:
            List of ProductCollection instances
            
        Raises:
            ProductExtractionError: If extraction fails
        """
        total_urls = len(urls)
        logger.info(f"Starting parallel extraction from {total_urls} URLs with max_concurrent={max_concurrent}")
        
        # Create semaphore to limit concurrent extractions
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_single(resource_name: str, url: str, idx: int) -> ProductCollection:
            """Extract products from a single URL with semaphore control"""
            async with semaphore:
                try:
                    # Emit progress update if callback provided
                    if progress_callback:
                        progress_callback(
                            f"🛒 Extracting products from {resource_name} ({idx}/{total_urls})",
                            current=idx, total=total_urls, url=url
                        )
                    
                    # Use default name if resource name is invalid
                    if not resource_name or not isinstance(resource_name, str):
                        resource_name = f"site_{idx}"
                    
                    # Create a new scraper instance for this extraction to avoid conflicts
                    scraper = DirectScraper()
                    try:
                        # Step 1: Scrape the page content
                        html_content = await scraper.scrape_url(
                            url, 
                            render_js=render_js, 
                            wait=wait,
                            smart_js_detection=True,
                            resource_name=resource_name,
                            conversation_id=conversation_id
                        )
                        
                        # Step 2: Extract products from the scraped content
                        products = self.extract_products(html_content, url)
                        
                        # Step 3: Create ProductCollection
                        product_collection = ProductCollection(
                            source_name=resource_name,
                            source_url=url,
                            products=products,
                            extraction_method="multi_method"
                        )
                        
                        # Step 4: Save ProductCollection if conversation_id is provided
                        if conversation_id and len(products) > 0:
                            try:
                                saved_path = product_collection.save_to_file(conversation_id=conversation_id)
                                logger.debug(f"Saved ProductCollection to: {saved_path}")
                            except Exception as e:
                                logger.warning(f"Failed to save ProductCollection: {e}")
                        
                        # Emit success/warning update
                        if progress_callback:
                            if len(product_collection) > 0:
                                progress_callback(
                                    f"✅ Extracted {len(product_collection)} products from {resource_name}!",
                                    current=idx, total=total_urls, status="success"
                                )
                            else:
                                progress_callback(
                                    f"⚠️ No products found at {resource_name}",
                                    current=idx, total=total_urls, status="warning"
                                )
                        
                        logger.info(f"Successfully extracted {len(products)} products from {resource_name}")
                        return product_collection
                        
                    finally:
                        # Clean up this scraper instance
                        await scraper.cleanup()
                        
                except Exception as e:
                    # Log error and create empty collection
                    error_msg = f"Failed to extract products from {url} as '{resource_name}': {str(e)}"
                    logger.error(error_msg)
                    
                    # Create empty collection for failed extraction
                    empty_collection = ProductCollection(
                        source_name=resource_name,
                        source_url=url,
                        products=[],
                        extraction_method="failed"
                    )
                    
                    if progress_callback:
                        progress_callback(
                            f"❌ Couldn't extract products from {resource_name}",
                            current=idx, total=total_urls, status="error"
                        )
                    
                    return empty_collection
        
        # Create tasks for all URLs
        tasks = [
            extract_single(resource_name, url, idx)
            for idx, (resource_name, url) in enumerate(urls.items(), 1)
        ]
        
        # Execute all tasks in parallel (with semaphore limiting concurrency)
        product_collections = await asyncio.gather(*tasks, return_exceptions=False)
        
        # Filter out any None results and log summary
        valid_collections = [c for c in product_collections if c is not None]
        successful_extractions = len([c for c in valid_collections if len(c) > 0])
        
        logger.info(f"Completed parallel extraction from {total_urls} URLs, found products in {successful_extractions} sources")
        return valid_collections
    
    async def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'scraper'):
            await self.scraper.cleanup()
