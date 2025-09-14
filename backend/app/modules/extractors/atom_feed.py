"""Atom feed product extractor"""

import re
import xml.etree.ElementTree as ET
from typing import List, Optional
from loguru import logger
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from app.models.product import Product
from .base import BaseProductExtractor, ProductExtractionError

# Atom feed constants
ATOM_FEED_REL = 'alternate'
ATOM_FEED_TYPE = 'application/atom+xml'

# Atom namespaces
ATOM_NS = {'atom': 'http://www.w3.org/2005/Atom'}


class AtomFeedExtractor(BaseProductExtractor):
    """Extract products from Atom feed links"""
    
    def extract_products(self, html_content: str, url: str = "") -> List[Product]:
        """
        Extract product data by finding and parsing Atom feed links.
        
        Args:
            html_content: The HTML content to search for Atom feed links
            url: Base URL for resolving relative links
            
        Returns:
            List of Product instances with basic info (title, URL)
        """
        try:
            logger.info(f"Extracting products from Atom feed links {'for ' + url if url else ''}")
            
            # Find Atom feed links in HTML
            atom_feed_urls = self._find_atom_feed_links(html_content, url)
            if not atom_feed_urls:
                logger.warning("No Atom feed links found")
                return []
            
            products = []
            for feed_url in atom_feed_urls:
                try:
                    feed_products = self._extract_from_atom_feed(feed_url, url)
                    products.extend(feed_products)
                except Exception as e:
                    logger.warning(f"Failed to extract from Atom feed {feed_url}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(products)} products from Atom feeds")
            return products
            
        except Exception as e:
            error_msg = f"Failed to extract products from Atom feeds: {str(e)}"
            logger.error(error_msg)
            raise ProductExtractionError(error_msg)
    
    def _find_atom_feed_links(self, html_content: str, base_url: str = "") -> List[str]:
        """
        Find Atom feed links in HTML head section.
        
        Args:
            html_content: HTML content to search
            base_url: Base URL for resolving relative links
            
        Returns:
            List of Atom feed URLs
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        atom_links = []
        
        # Look for link tags with rel="alternate" and type="application/atom+xml"
        link_tags = soup.find_all('link', {
            'rel': ATOM_FEED_REL,
            'type': ATOM_FEED_TYPE
        })
        
        for link in link_tags:
            href = link.get('href')
            if href:
                # Make URL absolute if needed
                if href.startswith('/') and base_url:
                    href = urljoin(base_url, href)
                atom_links.append(href)
                logger.debug(f"Found Atom feed link: {href}")
        
        return atom_links
    
    def _extract_from_atom_feed(self, feed_url: str, base_url: str = "") -> List[Product]:
        """
        Extract products from an Atom feed URL.
        
        Note: This method would need to fetch the feed content.
        For now, it returns an empty list as a placeholder.
        
        Args:
            feed_url: URL of the Atom feed
            base_url: Base URL for context
            
        Returns:
            List of Product instances
        """
        # TODO: Implement actual Atom feed fetching and parsing
        # This would require making HTTP requests to fetch the feed content
        # For now, return empty list as this is a fallback method
        
        logger.info(f"Atom feed extraction from {feed_url} - not implemented yet")
        logger.info("This would require fetching the feed content via HTTP request")
        
        return []
    
    def _parse_atom_feed_content(self, atom_content: str, base_url: str = "") -> List[Product]:
        """
        Parse Atom feed XML content to extract products.
        
        Args:
            atom_content: Raw Atom feed XML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of Product instances
        """
        products = []
        
        try:
            # Parse XML content
            root = ET.fromstring(atom_content)
            
            # Find all entry elements
            entries = root.findall('.//atom:entry', ATOM_NS)
            
            for entry in entries:
                try:
                    # Extract basic product info from entry
                    title_elem = entry.find('atom:title', ATOM_NS)
                    title = title_elem.text if title_elem is not None else None
                    
                    # Find product link
                    link_elem = entry.find('atom:link[@rel="alternate"]', ATOM_NS)
                    if link_elem is None:
                        link_elem = entry.find('atom:link', ATOM_NS)
                    
                    product_url = link_elem.get('href') if link_elem is not None else None
                    
                    # Extract product ID from URL
                    product_id = self.extract_product_id_from_url(product_url) if product_url else None
                    
                    # Create basic product (Atom feeds typically don't have price/vendor info)
                    product = self.create_product_from_data(
                        title=title,
                        product_id=product_id,
                        product_url=product_url,
                        base_url=base_url
                    )
                    
                    if product:
                        products.append(product)
                        
                except Exception as e:
                    logger.warning(f"Failed to parse Atom entry: {e}")
                    continue
            
            logger.debug(f"Parsed {len(products)} products from Atom feed")
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse Atom feed XML: {e}")
        except Exception as e:
            logger.error(f"Error parsing Atom feed content: {e}")
        
        return products
