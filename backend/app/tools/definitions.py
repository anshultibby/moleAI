"""Tool function definitions - Define your functions here to convert them to tools"""

from typing import Optional, List, Dict, Any
from app.tools import tool
from app.modules.serp import search_web, SearchError
from app.modules.direct_scraper import DirectScraper, DirectScraperError
from app.models.resource import Resource, ResourceMetadata
import uuid
import re
import json
import asyncio
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class StreamHelper:
    """Centralized helper for tool streaming functionality"""
    
    def __init__(self, stream_callback, tool_name: str):
        self.stream_callback = stream_callback
        self.tool_name = tool_name
    
    def progress(self, message: str, **progress_data):
        """Emit a progress update"""
        if self.stream_callback:
            self.stream_callback(self.tool_name, "progress", message=message, progress=progress_data)
    
    def completed(self, message: str, result_data: Dict = None, **progress_data):
        """Emit a completion update"""
        if self.stream_callback:
            result_json = json.dumps(result_data) if result_data else None
            self.stream_callback(self.tool_name, "completed", 
                               message=message, 
                               progress=progress_data,
                               result=result_json)
    
    def error(self, message: str, **progress_data):
        """Emit an error update"""
        if self.stream_callback:
            self.stream_callback(self.tool_name, "error", message=message, progress=progress_data)
    
    @classmethod
    def for_search(cls, stream_callback, query: str, num_results: int, results: List[Dict] = None, error_msg: str = None):
        """Factory method for search tool streaming"""
        helper = cls(stream_callback, "search_web_tool")
        
        if results is not None:
            # Success case with results
            stores = []
            for result in results:
                stores.append({
                    "title": result.get('title', 'Store'),
                    "url": result.get('url', '')
                })
            
            result_data = {
                "query": query,
                "results": stores
            }
            
            message = f"Found {len(stores)} stores" if stores else "No results found"
            helper.completed(message, result_data, query=query, num_results=num_results)
        else:
            # Error case or empty results
            result_data = {
                "query": query,
                "results": []
            }
            
            message = error_msg or "No results found"
            helper.completed(message, result_data, query=query, num_results=num_results)
    
    @classmethod
    def for_scraping(cls, stream_callback, tool_name: str = "scrape_website"):
        """Factory method for scraping tool streaming"""
        return cls(stream_callback, tool_name)



@tool(
    name="search_web_tool",
    description="""Search the web to get SERP results using broad, general queries.
    
    IMPORTANT: Use natural, general search queries without site restrictions (no "site:" operators).
    Let Google's algorithm naturally surface the best results from various retailers.
    
    Examples:
    - Good: "trendy winter coats for women 2025"
    - Good: "midi dresses under $100"
    - Bad: "winter coats site:zara.com OR site:hm.com"
    - Bad: "dresses site:nordstrom.com"
    
    After getting search results, you can choose which diverse retailer links to scrape.
    Focus on the product attributes the user wants, not specific brands unless explicitly requested.
    """
)
def search_web_tool(
    query: str,
    num_results: int = 10,
    context_vars=None
) -> Dict[str, Any]:
    if not query or not query.strip():
        return {"error": "Query cannot be empty"}

    # Create stream helper
    stream_callback = context_vars.get('stream_callback') if context_vars else None
    streamer = StreamHelper(stream_callback, "search_web_tool")
    
    try:
        # Emit progress update
        streamer.progress(f"🔍 Searching the web for: {query}", query=query, num_results=num_results)

        results = search_web(
            query=query.strip(),
            num_results=num_results,
            provider="google"
        )
        
        # Emit completion update
        search_results = results.get('results', []) if isinstance(results, dict) else []
        StreamHelper.for_search(stream_callback, query, num_results, search_results)
        
        return results
        
    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        StreamHelper.for_search(stream_callback, query, num_results, error_msg=error_msg)
        return {"error": error_msg}


@tool(
    name="scrape_website",
    description="""Scrape content from a website URL with JavaScript support using direct HTTP requests.
    It scrapes the website and stores the content as a resource with a meaningful name.
    When you need to use these results you can use the get_resource tool to fetch the resource 
    or grep tool/css_select tool (if its html) to search inside of it.
    
    Parameters:
    - urls: Dictionary where keys are meaningful resource names and values are URLs to scrape
           Example: {"zara_dresses": "https://zara.com/dresses", "hm_shirts": "https://hm.com/shirts"}
    - render_js: Whether to render JavaScript (default: True for dynamic content)
    - wait: Time to wait in milliseconds after page load (default: 2000ms)
    
    Use meaningful, succinct resource names that describe the content being scraped.
    Good examples: "zara_dresses", "amazon_laptops", "nike_shoes"
    Avoid generic names like "resource1", "page1", etc.
    """
)
def scrape_websites(
    urls: Dict[str, str],
    render_js: bool = True,
    wait: int = 2000,
    context_vars=None
) -> str:
    if not urls:
        return "URLs cannot be empty"
    
    # Handle different input types for urls parameter
    if isinstance(urls, str):
        # If it's a single URL string, create a dictionary with a default name
        # Extract domain name for a meaningful resource name
        try:
            parsed = urlparse(urls)
            domain = parsed.netloc.replace('www.', '').split('.')[0]
            resource_name = f"{domain}_content"
        except:
            resource_name = "scraped_content"
        
        urls = {resource_name: urls}
    elif isinstance(urls, list):
        # If it's a list of URLs, auto-generate resource names from domains
        url_dict = {}
        domain_counts = {}  # Track domain usage to avoid duplicates
        
        for url in urls:
            if not isinstance(url, str):
                return f"Error: All URLs in list must be strings, got {type(url)}"
            
            try:
                parsed = urlparse(url.strip())
                domain = parsed.netloc.replace('www.', '').split('.')[0]
                
                # Handle duplicate domains by adding a counter
                if domain in domain_counts:
                    domain_counts[domain] += 1
                    resource_name = f"{domain}_content_{domain_counts[domain]}"
                else:
                    domain_counts[domain] = 1
                    resource_name = f"{domain}_content"
                    
            except Exception as e:
                # Fallback to generic name if URL parsing fails
                resource_name = f"scraped_content_{len(url_dict) + 1}"
            
            url_dict[resource_name] = url.strip()
        
        urls = url_dict
    elif not isinstance(urls, dict):
        return f"Error: urls parameter must be a dictionary, got {type(urls)}. If you have a list of URLs, please convert to dict format: {{\"site1\": \"url1\", \"site2\": \"url2\"}}"
    
    async def _async_scrape():
        resources = context_vars.get('resources')
        stream_callback = context_vars.get('stream_callback')
        streamer = StreamHelper.for_scraping(stream_callback)
        scraper = DirectScraper()
        resources_saved = []
        
        total_urls = len(urls)
        
        for idx, (resource_name, url) in enumerate(urls.items(), 1):
            try:
                # Emit progress update
                streamer.progress(
                    f"🛒 Browsing {resource_name} for products ({idx}/{total_urls})",
                    current=idx, total=total_urls, url=url
                )
                
                # Validate resource name
                if not resource_name or not isinstance(resource_name, str):
                    resources_saved.append(f"Invalid resource name for {url}: {resource_name}")
                    continue
                    
                # Clean resource name (remove spaces, special chars, make lowercase)
                clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', resource_name.lower().strip())
                if not clean_name:
                    clean_name = f"resource_{len(resources) + 1}"
                
                resource = await scraper.scrape_url(
                    url.strip(), 
                    render_js=render_js, 
                    wait=wait,
                    smart_js_detection=True,  # Enable smart JS detection for better performance
                    resource_name=clean_name,  # Pass resource name for JSON file naming
                    conversation_id=context_vars.get('conversation_id')  # Pass conversation ID for folder organization
                )
                
                # Override the resource ID with the meaningful name
                resource.id = clean_name
                resources[clean_name] = resource
                resources_saved.append(resource.format_for_llm(exclude_content=True))
                
                # Emit success update
                streamer.progress(
                    f"✅ Found products at {resource_name}! Analyzing {len(resource.content)} items...",
                    current=idx, total=total_urls, status="success"
                )
                
            except Exception as e:
                # Log error but continue with other URLs
                error_msg = f"Failed to scrape {url} as '{resource_name}': {str(e)}"
                resources_saved.append(error_msg)
                
                # Emit error update
                streamer.progress(
                    f"❌ Couldn't access {resource_name} - trying next store...",
                    current=idx, total=total_urls, status="error"
                )
            finally:
                # Clean up browser resources
                await scraper.cleanup()

        # Send completion update with detailed format including actual URLs
        scraped_sites = []
        
        # Track both successful and failed scrapes with actual URLs
        for idx, (resource_name, original_url) in enumerate(urls.items(), 1):
            # Check if this resource was successfully saved
            resource_saved = False
            for resource_info in resources_saved:
                if isinstance(resource_info, str) and resource_name in resource_info:
                    resource_saved = True
                    break
            
            # Extract clean site name from resource name or URL
            if resource_name.endswith('_content'):
                site_name = resource_name.replace('_content', '').replace('_', ' ').title()
            else:
                # Fallback to extracting from URL
                try:
                    parsed = urlparse(original_url)
                    site_name = parsed.netloc.replace('www.', '').split('.')[0].title()
                except:
                    site_name = resource_name.title()
            
            scraped_sites.append({
                "name": site_name,
                "url": original_url,
                "success": resource_saved
            })
        
        # Filter successful sites for the message
        successful_sites = [site for site in scraped_sites if site["success"]]
        
        if successful_sites:
            result_data = {
                "scraped_sites": scraped_sites,
                "successful_sites": len(successful_sites),
                "total_sites": len(scraped_sites)
            }
            
            if len(successful_sites) == 1:
                message = f"Checked {successful_sites[0]['name']}"
            else:
                message = f"Checked {len(successful_sites)} websites"
            
            streamer.completed(message, result_data)
        else:
            # No successful scrapes
            result_data = {
                "scraped_sites": scraped_sites,
                "successful_sites": 0,
                "total_sites": len(scraped_sites)
            }
            streamer.completed("No websites could be accessed", result_data)
        
        return f"Extracted and saved the resources: {resources_saved}"
    
    # Check if we're in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, we need to run this in a thread pool
        # to avoid blocking the event loop
        import concurrent.futures
        import threading
        
        def run_in_thread():
            # Create a new event loop for this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(_async_scrape())
            finally:
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
    except RuntimeError:
        # No event loop running, we can use asyncio.run directly
        return asyncio.run(_async_scrape())


def get_resource_content(resource_id: str, context_vars) -> tuple[str, Optional[str]]:
    """Helper to get resource content with validation. Returns (content, error_message)"""
    resources = context_vars.get('resources')
    resource = resources.get(resource_id)
    
    if not resource:
        return None, f"Resource with ID '{resource_id}' not found"
    
    if not resource.content:
        return None, f"Resource '{resource_id}' has no content to search"
    
    return resource.content, None


def grep_content(content: str, pattern: str, flags: int = 0, limit: Optional[int] = None, max_line_length: int = 200, context_chars: int = 100) -> List[Dict[str, Any]]:
    """Extract matches from content using regex patterns with line numbers and absolute positions
    
    Args:
        content: The text content to search
        pattern: Regex pattern to search for
        flags: Regex flags
        limit: Maximum number of matches to return
        max_line_length: Maximum length of line content to return (truncate if longer)
        context_chars: Number of characters to show around the match for context
    """
    matches = []
    
    # Use re.finditer on the entire content to get absolute positions
    for match in re.finditer(pattern, content, flags):
        # Calculate line number by counting newlines before the match
        line_start = content.rfind('\n', 0, match.start()) + 1
        line_end = content.find('\n', match.start())
        if line_end == -1:
            line_end = len(content)
        
        full_line_content = content[line_start:line_end]
        line_number = content[:match.start()].count('\n') + 1
        
        # Create context around the match within the line
        match_start_in_line = match.start() - line_start
        match_end_in_line = match.end() - line_start
        
        # Calculate context boundaries
        context_start = max(0, match_start_in_line - context_chars)
        context_end = min(len(full_line_content), match_end_in_line + context_chars)
        
        # Extract context with the match
        context_content = full_line_content[context_start:context_end]
        
        # Add ellipsis if we truncated
        if context_start > 0:
            context_content = "..." + context_content
        if context_end < len(full_line_content):
            context_content = context_content + "..."
        
        # Always enforce hard limit of 200 characters
        if len(context_content) > context_chars:
            context_content = context_content[:context_chars] + "..."
        
        match_info = {
            'line_number': line_number,
            'line_content': context_content.strip(),
            'match_text': match.group(),
            'start_pos': match.start(),  # Absolute position in entire content
            'end_pos': match.end()       # Absolute position in entire content
        }
        matches.append(match_info)
        
        # Apply limit if specified
        if limit is not None and len(matches) >= limit:
            break
    
    return matches


def css_select(html_content: str, selector: str, text_only: bool = False, limit: Optional[int] = None, 
               max_element_length: int = 500, summary_only: bool = False):
    """Select elements from HTML content using CSS selectors
    
    Args:
        html_content: The HTML content to search
        selector: CSS selector to use
        text_only: Return only text content of elements
        limit: Maximum number of elements to return
        max_element_length: Maximum length of element content (truncate if longer)
        summary_only: Return only summary info (tag names, counts) instead of full content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    elements = soup.select(selector)
    
    # Apply limit if specified
    if limit is not None:
        elements = elements[:limit]
    
    if summary_only:
        # Return summary information instead of full content
        tag_counts = {}
        for elem in elements:
            tag_name = elem.name
            tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1
        
        return {
            'total_elements': len(elements),
            'tag_counts': tag_counts,
            'sample_elements': [{'tag': elem.name, 'classes': elem.get('class', []), 'id': elem.get('id')} 
                              for elem in elements[:3]]  # Show first 3 as samples
        }
    
    if text_only:
        results = []
        for elem in elements:
            text = elem.get_text(strip=True)
            if len(text) > max_element_length:
                text = text[:max_element_length] + "..."
            results.append(text)
        return results
    
    # Return elements with position tracking and truncation
    results = []
    for elem in elements:
        elem_str = str(elem)
        
        # Find position of this element in the original HTML
        elem_start = html_content.find(elem_str)
        elem_end = elem_start + len(elem_str) if elem_start != -1 else -1
        
        # Truncate if too long
        if len(elem_str) > max_element_length:
            elem_str = elem_str[:max_element_length] + "..."
        
        element_info = {
            'content': elem_str,
            'tag': elem.name,
            'classes': elem.get('class', []),
            'id': elem.get('id'),
            'start_pos': elem_start,
            'end_pos': elem_end
        }
        results.append(element_info)
    
    return results


@tool(
    name="grep_resource",
    description="""Search for patterns in a resource's content using regex (case-insensitive by default).
    Returns matching lines with line numbers and absolute character positions where matches occur.
    The start_pos and end_pos can be used directly with get_resource(startidx, endidx) to extract the matched content.
    Prefer using lower limits when you are not sure about the pattern.

    You can control how much context is shown around the match by setting the max_line_length and context_chars parameters.
    """
)
def grep_resource(
    resource_id: str,
    pattern: str,
    max_line_length: int = 200,
    context_chars: int = 100,
    limit: int = 10,
    context_vars=None
) -> str:
    content, error = get_resource_content(resource_id, context_vars)
    if error:
        return error
    
    # Default to case-insensitive matching
    matches = grep_content(content, pattern, re.IGNORECASE, limit, max_line_length, context_chars)
    
    if not matches:
        return f"No matches found for pattern '{pattern}' in resource '{resource_id}'"
    
    result_lines = []
    for match in matches:
        result_lines.append(
            f"Line {match['line_number']}: {match['line_content']}\n"
            f"  Match: '{match['match_text']}' at absolute positions {match['start_pos']}-{match['end_pos']}\n"
            f"  (Use get_resource('{resource_id}', {match['start_pos']}, {match['end_pos']}) to extract this match)"
        )
    
    return f"Found {len(matches)} matches in resource '{resource_id}':\n\n" + "\n\n".join(result_lines)


@tool(
    name="css_select_resource",
    description="""Select elements from a resource's HTML content using CSS selectors.
    Useful for extracting specific elements like prices, titles, descriptions, etc.
    
    Parameters:
    - resource_id: The resource to search in
    - selector: CSS selector to use
    - text_only: Return only text content (default: False)
    - limit: Maximum number of elements to return (default: 10)
    - max_element_length: Maximum length of each element's content (default: 500)
    - summary_only: Return only summary info instead of full content (default: False)
    
    Use summary_only=True to get an overview when you're not sure about the selector.
    Use lower limits and max_element_length when dealing with large elements.
    The start_pos and end_pos can be used with get_resource(startidx, endidx) to extract full elements.
    """
)
def css_select_resource(
    resource_id: str,
    selector: str,
    text_only: bool = False,
    limit: int = 10,
    max_element_length: int = 500,
    summary_only: bool = False,
    context_vars=None
) -> str:
    content, error = get_resource_content(resource_id, context_vars)
    if error:
        return error
    
    elements = css_select(content, selector, text_only, limit, max_element_length, summary_only)
    
    if not elements:
        return f"No elements found for CSS selector '{selector}' in resource '{resource_id}'"
    
    if summary_only:
        summary = elements  # css_select returns dict when summary_only=True
        result_lines = [
            f"Found {summary['total_elements']} elements matching '{selector}' in resource '{resource_id}'",
            f"Tag distribution: {summary['tag_counts']}",
            f"Sample elements: {summary['sample_elements']}"
        ]
        return "\n".join(result_lines)
    
    if text_only:
        return f"Found {len(elements)} text elements in resource '{resource_id}':\n" + "\n".join(elements)
    else:
        # Format structured element info
        result_lines = []
        for i, elem_info in enumerate(elements, 1):
            lines = [
                f"Element {i}: <{elem_info['tag']}> {elem_info['content']}"
            ]
            if elem_info['classes']:
                lines.append(f"  Classes: {elem_info['classes']}")
            if elem_info['id']:
                lines.append(f"  ID: {elem_info['id']}")
            if elem_info['start_pos'] != -1:
                lines.append(f"  Position: {elem_info['start_pos']}-{elem_info['end_pos']}")
                lines.append(f"  (Use get_resource('{resource_id}', {elem_info['start_pos']}, {elem_info['end_pos']}) to extract full element)")
            result_lines.append("\n".join(lines))
        
        return f"Found {len(elements)} HTML elements in resource '{resource_id}':\n\n" + "\n\n".join(result_lines)


@tool(
    name="get_resource",
    description="""Get a resource by its name. 
    Returns the resource content if found.

    Parameters:
    - resource_id: The ID of the resource to get
    - startidx: Starting character index (inclusive). If None, starts from beginning.
    - endidx: Ending character index (exclusive). If None, goes to end.
    - context_vars: The context variables to use

    Please dont read large resources as it will slow down the agent. 
    Prefer to use the grep_resource or css_select_resource tools to search inside of the resource.
    You can read a portion of the resource to better inform the search strategy.
    """
)
def get_resource(
    resource_id: str,
    startidx: Optional[int] = None,
    endidx: Optional[int] = None,
    context_vars=None
) -> str:
    resources = context_vars.get('resources')
    resource = resources.get(resource_id)
    if not resource:
        return f"Resource with ID '{resource_id}' not found"
    
    return resource.format_for_llm(exclude_content=False, startidx=startidx, endidx=endidx)


@tool(
    name="create_resource",
    description="""Create a new resource from text content.
    
    Parameters:
    - text: The text content to store as a resource (required)
    - resource_name: A meaningful name for the resource (required)
                    Should be descriptive and unique, e.g. "user_notes", "product_specs", "meeting_summary"
    
    The resource will be stored and can be accessed later using get_resource, grep_resource, or css_select_resource tools.
    Use meaningful, succinct resource names that describe the content being stored.
    """
)
def create_resource(
    text: str,
    resource_name: str,
    context_vars=None
) -> str:
    if not text or not text.strip():
        return "Error: text content cannot be empty"
    
    if not resource_name or not isinstance(resource_name, str):
        return "Error: resource_name must be a non-empty string"
    
    # Clean resource name (remove spaces, special chars, make lowercase)
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', resource_name.lower().strip())
    if not clean_name:
        return "Error: resource_name must contain at least one alphanumeric character"
    
    resources = context_vars.get('resources')
    if not resources:
        return "Error: resources context not available"
    
    # Check if resource already exists
    if clean_name in resources:
        return f"Error: resource with name '{clean_name}' already exists. Use a different name or get the existing resource."
    
    # Determine content type based on content
    content_type = "html" if "<html" in text.lower() or "<body" in text.lower() or "<div" in text.lower() else "text"
    
    # Create resource metadata
    metadata = ResourceMetadata(
        content_type=content_type,
        length=len(text),
        num_lines=len(text.split('\n'))
    )
    
    # Create and store the resource
    resource = Resource(
        id=clean_name,
        content=text.strip(),
        metadata=metadata
    )
    
    resources[clean_name] = resource
    
    return f"Successfully created resource '{clean_name}' with {len(text)} characters ({content_type} content)"


@tool(
    name="list_resources",
    description="""List all resources that have been created so far.
    Returns a dictionary of all resources with their IDs as keys and content as metadata.
    """
)
def list_resources(context_vars=None) -> List[str]:
    resources = context_vars.get('resources')
    if not resources:
        return "No resources found"
    return [resource.format_for_llm(exclude_content=True) for resource in resources.values()]


@tool(
    name="display_items",
    description="""Display products/items that will stream to the user in real-time as they are processed. 
    Products appear immediately as each one is processed, creating a dynamic streaming experience.
    This is a very important tool to call as it makes for a very delightful experience for the user, our main goal is to keep the user engaged.

Each item should be a dictionary with these fields:
- product_name (required): The name/title of the product (string)
- price (required): The price as a string, e.g. "29.99", "$45.00", "€35.50" (string)
- store (required): The store/brand name, e.g. "Zara", "H&M", "Amazon" (string)
- image_url (required): Direct URL to product image (string)
- product_url (required): Direct link to the product page for purchasing (string)
- description (optional): Brief product description or details (string)
- currency (optional): Currency code like "USD", "EUR", "GBP" - defaults to "USD" (string)
- category (optional): Product category like "dress", "shoes", "jacket" (string)

Example usage:
display_items([
    {
        "product_name": "Classic White Button Shirt",
        "price": "49.99",
        "store": "Zara",
        "currency": "USD",
        "image_url": "https://example.com/shirt.jpg",
        "product_url": "https://zara.com/shirt-123",
        "description": "Cotton blend button-up shirt",
        "category": "shirt"
    }
])

Products will appear one by one in real-time as they are processed, not all at once at the end."""
)
def display_items(
    items: List[Any],
    title: Optional[str] = None,
    context_vars=None
) -> Dict[str, Any]:
    if not items:
        return {"error": "Items list cannot be empty"}
    
    processed_items = []
    
    for i, raw_item in enumerate(items):
        # Handle case where item might be a JSON string
        if isinstance(raw_item, str):
            try:
                item = json.loads(raw_item)
            except json.JSONDecodeError:
                return {"error": f"Item {i+1} is not valid JSON: {raw_item[:100]}..."}
        elif isinstance(raw_item, dict):
            item = raw_item
        else:
            return {"error": f"Item {i+1} must be a dictionary or JSON string, got {type(raw_item)}"}
        
        # Extract required fields with fallbacks
        product_name = item.get('product_name') or item.get('name') or ''
        price = item.get('price') or ''
        store = item.get('store') or item.get('store_name') or ''
        
        # Simple validation - just check if we have the basics
        if not product_name.strip():
            return {"error": f"Item {i+1} missing product name"}
        if not price.strip():
            return {"error": f"Item {i+1} missing price"}
        if not store.strip():
            return {"error": f"Item {i+1} missing store name"}
        
        # Generate unique ID
        clean_store = str(store).lower().replace(' ', '-').replace('&', 'and')[:20]
        clean_name = str(product_name).lower().replace(' ', '-')[:30]
        item_id = f"{clean_store}-{clean_name}-{str(uuid.uuid4())[:8]}"
        
        # Create normalized item
        processed_item = {
            "id": item_id,
            "product_name": str(product_name).strip(),
            "name": str(product_name).strip(),
            "price": str(price).strip(),
            "currency": str(item.get('currency', 'USD')),
            "store": str(store).strip(),
            "store_name": str(store).strip(),
            "image_url": str(item.get('image_url', '')),
            "product_url": str(item.get('product_url', '')),
            "description": str(item.get('description', '')),
            "category": str(item.get('category', '')),
            "type": "streaming_product"
        }
        
        processed_items.append(processed_item)
    
    return {
        "success": True,
        "stream_products": True,
        "title": title or "Products Found",
        "items": processed_items,
        "count": len(processed_items),
        "message": f"Found {len(processed_items)} products"
    }


@tool(
    name="checklist",
    description="""Manage checklists with create, update, and get operations.
    
    Operations:
    - create: Create a new checklist with title and items
    - update: Mark checklist items as completed or uncompleted
    - get: Retrieve existing checklist
    
    The checklist is stored in the agent's context and automatically included in conversations.
    When a checklist exists, always include it and ask the user to mark completed items.
    
    Parameters:
    - operation: "create", "update", or "get"
    - title: Title for the checklist (required for create)
    - items: List of checklist items as strings (required for create)
    - item_updates: Dictionary mapping item indices to completion status for update
                   Example: {0: True, 2: False} marks first item complete, third incomplete
    """
)
def checklist(
    operation: str,
    title: str = None,
    items: List[str] = None,
    item_updates: Dict[int, bool] = None,
    context_vars=None
) -> str:
    if not operation or operation not in ["create", "update", "get"]:
        return "Error: operation must be 'create', 'update', or 'get'"
    
    agent = context_vars.get('agent')
    if not agent:
        return "Error: Agent context not available"
    
    if operation == "get":
        if agent.checklist:
            return f"Current checklist: {json.dumps(agent.checklist, indent=2)}"
        else:
            return "No checklist found"
    
    elif operation == "create":
        if not title or not items:
            return "Error: title and items are required for create operation"
        
        # Create new checklist
        agent.checklist = {
            "title": title,
            "items": [{"text": item, "completed": False} for item in items],
            "created_at": datetime.now().isoformat()
        }
        
        return f"Created checklist '{title}' with {len(items)} items"
    
    elif operation == "update":
        if not agent.checklist:
            return "Error: No existing checklist found to update"
        
        if not item_updates:
            return "Error: item_updates required for update operation"
        
        # Update checklist items
        for item_index, completed in item_updates.items():
            if 0 <= item_index < len(agent.checklist["items"]):
                agent.checklist["items"][item_index]["completed"] = completed
        
        agent.checklist["updated_at"] = datetime.now().isoformat()
        
        # Count completed items
        completed_count = sum(1 for item in agent.checklist["items"] if item["completed"])
        total_count = len(agent.checklist["items"])
        
        return f"Updated checklist: {completed_count}/{total_count} items completed"


