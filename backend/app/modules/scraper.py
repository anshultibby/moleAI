"""Web scraper module using Jina AI Reader for fast content extraction"""

import os
import requests
import json
import re
import hashlib
from typing import Dict, Any, Optional, List, Union
from loguru import logger
import extruct
from bs4 import BeautifulSoup

from app.models.resource import Resource, ResourceMetadata


class ScraperError(Exception):
    """Custom exception for scraper-related errors"""
    pass


class JinaAIScraper:
    """Client for scraping web content using Jina AI Reader"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Jina AI scraper client
        
        Args:
            api_key: Jina AI API key. If None, will try to get from JINA_AI_API_KEY env var
        """
        self.api_key = api_key or os.getenv("JINA_AI_API_KEY")
        if not self.api_key:
            raise ScraperError("JINA_AI_API_KEY not provided and not found in environment variables")
        
        self.base_url = "https://r.jina.ai"
        self.timeout = 30
    
    def scrape_url(self, url: str, format: str = "markdown", wait_for_js: bool = True) -> Resource:
        """
        Scrape content from a single URL using Jina AI Reader
        
        Args:
            url: The URL to scrape
            format: Output format ("markdown", "text", "html")
        
        Returns:
            Resource object containing scraped content and metadata
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        
        # Clean and validate URL
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Prepare request to Jina AI Reader
        jina_url = f"{self.base_url}/{url}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Return-Format": format
        }
        
        # Add JavaScript loading options
        if wait_for_js:
            headers["X-Respond-Timing"] = "mutation-idle"  # Wait for DOM mutations to settle
            headers["X-Timeout"] = "30"  # 30 second timeout
        
        try:
            logger.info(f"Scraping URL with Jina AI: {url}")
            
            response = requests.get(jina_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Jina AI Reader returns the content directly as text
            content = response.text
            
            # Create Resource object
            resource_id = hashlib.md5(url.encode()).hexdigest()
            
            # Determine content type based on format
            content_type = "html" if format == "html" else "text"
            
            resource_metadata = ResourceMetadata(
                content_type=content_type,
                length=len(content)
            )
            
            resource = Resource(
                id=resource_id,
                content=content,
                metadata=resource_metadata
            )
            
            logger.info(f"Successfully scraped content from {url} ({len(content)} characters)")
            return resource
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to scrape {url}: {str(e)}"
            logger.error(error_msg)
            raise ScraperError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error scraping {url}: {str(e)}"
            logger.error(error_msg)
            raise ScraperError(error_msg)
    
    def scrape_multiple_urls(self, urls: List[str], format: str = "markdown") -> List[Resource]:
        """
        Scrape content from multiple URLs
        
        Args:
            urls: List of URLs to scrape
            format: Output format ("markdown", "text", "html")
        
        Returns:
            List of Resource objects containing scraped content and metadata
        """
        if not urls:
            raise ValueError("URLs list cannot be empty")
        
        results = []
        
        for url in urls:
            try:
                result = self.scrape_url(url, format)
                results.append(result)
            except ScraperError as e:
                # Continue with other URLs even if one fails
                logger.warning(f"Failed to scrape {url}: {e}")
                # Create empty resource for failed scrapes
                resource_id = hashlib.md5(url.encode()).hexdigest()
                content_type = "html" if format == "html" else "text"
                
                failed_resource = Resource(
                    id=resource_id,
                    content={format: ""},
                    metadata=ResourceMetadata(
                        content_type=content_type,
                        length=0
                    )
                )
                results.append(failed_resource)
        
        successful_count = sum(1 for r in results if len(list(r.content.values())[0]) > 0)
        logger.info(f"Completed scraping {len(urls)} URLs, {successful_count} successful")
        return results


# Convenience functions for backward compatibility and simple usage
def scrape_url(url: str, format: str = "markdown") -> Resource:
    """
    Convenience function to scrape a single URL using default client
    
    Args:
        url: The URL to scrape
        format: Output format ("markdown", "text", "html")
    
    Returns:
        Resource object containing scraped content and metadata
    """
    scraper = JinaAIScraper()
    return scraper.scrape_url(url, format)


def scrape_multiple_urls(urls: List[str], format: str = "markdown") -> List[Resource]:
    """
    Convenience function to scrape multiple URLs using default client
    
    Args:
        urls: List of URLs to scrape
        format: Output format ("markdown", "text", "html")
    
    Returns:
        List of Resource objects containing scraped content and metadata
    """
    scraper = JinaAIScraper()
    return scraper.scrape_multiple_urls(urls, format)




