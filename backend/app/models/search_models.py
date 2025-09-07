"""
Pydantic models for structured search results from Jina AI Search API.

These models provide type-safe access to comprehensive search data including:
- Search metadata and configuration
- Individual search results with content, images, and links
- Token usage tracking
- Raw API response preservation
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class TokenUsage(BaseModel):
    """Token usage information from Jina AI API"""
    tokens: int = Field(..., description="Number of tokens consumed")


class SearchMetadata(BaseModel):
    """Metadata about the search request and configuration"""
    provider: str = Field(..., description="Search provider (google, bing, etc.)")
    type: str = Field(..., description="Search type (web, images, news)")
    num_results: int = Field(..., description="Number of results requested")
    country: str = Field(..., description="Country code for search localization")
    language: str = Field(..., description="Language code for search")
    read_content: bool = Field(..., description="Whether full content reading was enabled")
    with_links_summary: bool = Field(..., description="Whether links summary was enabled")
    with_images_summary: bool = Field(..., description="Whether images summary was enabled")
    with_generated_alt: bool = Field(..., description="Whether AI-generated alt text was enabled")
    respond_with: str = Field(..., description="Response format (content, markdown, etc.)")
    jina_status: int = Field(..., description="Jina API status code")
    jina_code: int = Field(..., description="Jina API response code")
    jina_meta: Dict[str, Any] = Field(..., description="Additional Jina metadata including usage")


class PageMetadata(BaseModel):
    """Metadata extracted from individual web pages"""
    lang: Optional[str] = Field(None, description="Page language")
    viewport: Optional[str] = Field(None, description="Viewport meta tag")
    format_detection: Optional[str] = Field(None, alias="format-detection")
    description: Optional[str] = Field(None, description="Page meta description")
    og_title: Optional[str] = Field(None, alias="og:title", description="Open Graph title")
    og_type: Optional[str] = Field(None, alias="og:type", description="Open Graph type")
    og_image: Optional[str] = Field(None, alias="og:image", description="Open Graph image")
    og_url: Optional[str] = Field(None, alias="og:url", description="Open Graph URL")
    og_site_name: Optional[str] = Field(None, alias="og:site_name", description="Open Graph site name")
    og_locale: Optional[str] = Field(None, alias="og:locale", description="Open Graph locale")
    fb_app_id: Optional[str] = Field(None, alias="fb:app_id", description="Facebook app ID")


class ExternalResources(BaseModel):
    """External resources referenced by the page"""
    preconnect: Optional[List[str]] = Field(None, description="Preconnect URLs")
    preload: Optional[List[str]] = Field(None, description="Preload URLs")
    modulepreload: Optional[List[str]] = Field(None, description="Module preload URLs")
    canonical: Optional[str] = Field(None, description="Canonical URL")
    next: Optional[str] = Field(None, description="Next page URL")


class SearchResult(BaseModel):
    """Individual search result with comprehensive content and metadata"""
    title: str = Field(..., description="Page title")
    url: HttpUrl = Field(..., description="Page URL")
    description: Optional[str] = Field(None, description="Page description/snippet")
    source: str = Field(..., description="Source domain/site name")
    content: str = Field(..., description="Full page content in markdown format")
    images: Dict[str, str] = Field(default_factory=dict, description="Extracted images with descriptions and URLs")
    links: Dict[str, str] = Field(default_factory=dict, description="Extracted links with text and URLs")
    metadata: Optional[PageMetadata] = Field(None, description="Page metadata (meta tags, Open Graph, etc.)")
    external: Optional[ExternalResources] = Field(None, description="External resources referenced")
    usage: TokenUsage = Field(..., description="Token usage for processing this result")

    class Config:
        # Allow field aliases for Open Graph and other meta tags
        allow_population_by_field_name = True


class JinaSearchResponse(BaseModel):
    """Complete structured response from Jina AI Search API"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="List of search results")
    raw_response: Dict[str, Any] = Field(..., description="Complete raw API response for debugging")
    metadata: SearchMetadata = Field(..., description="Search configuration and metadata")
    
    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used across all results"""
        return sum(result.usage.tokens for result in self.results)
    
    @property
    def total_images(self) -> int:
        """Count total images across all results"""
        return sum(len(result.images) for result in self.results)
    
    @property
    def total_links(self) -> int:
        """Count total links across all results"""
        return sum(len(result.links) for result in self.results)
    
    @property
    def average_content_length(self) -> float:
        """Calculate average content length across results"""
        if not self.results:
            return 0.0
        return sum(len(result.content) for result in self.results) / len(self.results)
    
    def get_images_by_description(self, keyword: str) -> List[tuple[str, str]]:
        """Find images containing keyword in description"""
        matching_images = []
        for result in self.results:
            for desc, url in result.images.items():
                if keyword.lower() in desc.lower():
                    matching_images.append((desc, url))
        return matching_images
    
    def get_links_by_text(self, keyword: str) -> List[tuple[str, str]]:
        """Find links containing keyword in text"""
        matching_links = []
        for result in self.results:
            for text, url in result.links.items():
                if keyword.lower() in text.lower():
                    matching_links.append((text, url))
        return matching_links
    
    def get_results_by_source(self, source: str) -> List[SearchResult]:
        """Filter results by source domain"""
        return [result for result in self.results if source.lower() in result.source.lower()]


class SearchSummary(BaseModel):
    """High-level summary of search results for quick overview"""
    query: str
    total_results: int
    total_tokens: int
    total_images: int
    total_links: int
    average_content_length: float
    sources: List[str]
    top_image_categories: List[str] = Field(default_factory=list)
    
    @classmethod
    def from_response(cls, response: JinaSearchResponse) -> "SearchSummary":
        """Create summary from full search response"""
        # Extract top image categories (simplified - just first few words of descriptions)
        image_categories = []
        for result in response.results:
            for desc in result.images.keys():
                # Extract first meaningful word from image description
                words = desc.split()
                if len(words) > 1:
                    category = words[1] if words[0].lower().startswith('image') else words[0]
                    if category not in image_categories and len(image_categories) < 10:
                        image_categories.append(category)
        
        return cls(
            query=response.query,
            total_results=len(response.results),
            total_tokens=response.total_tokens,
            total_images=response.total_images,
            total_links=response.total_links,
            average_content_length=response.average_content_length,
            sources=[result.source for result in response.results],
            top_image_categories=image_categories
        )


def parse_search_response(raw_data: Dict[str, Any]) -> JinaSearchResponse:
    """
    Parse raw JSON response from Jina AI Search API into structured models
    
    Args:
        raw_data: Raw dictionary from JSON response
        
    Returns:
        Structured JinaSearchResponse object
        
    Raises:
        ValidationError: If data doesn't match expected schema
    """
    return JinaSearchResponse.parse_obj(raw_data)


def load_search_response_from_file(file_path: str) -> JinaSearchResponse:
    """
    Load and parse search response from JSON file
    
    Args:
        file_path: Path to JSON file containing search response
        
    Returns:
        Structured JinaSearchResponse object
    """
    import json
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    return parse_search_response(raw_data)
