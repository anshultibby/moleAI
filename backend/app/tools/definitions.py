"""Tool function definitions - Define your functions here to convert them to tools"""

from typing import Optional, List, Dict, Any
from app.tools import tool
from app.modules.serp import search_web, SearchError
from app.modules.direct_scraper import ScrapingBeeScraper, ScrapingBeeError
from app.models.resource import Resource
import uuid
import re
import json
from bs4 import BeautifulSoup


@tool(
    name="search_web_tool",
    description="""Search the web to get SERP results. 
    You can choose which links we should scrape and store as resources.
    """
)
def search_web_tool(
    query: str,
    num_results: int = 3,
    context_vars=None
) -> Dict[str, Any]:
    try:
        if not query or not query.strip():
            return {"error": "Query cannot be empty"}

        results = search_web(
            query=query.strip(),
            num_results=num_results,
            provider="google"
        )
        
        return results
        
    except SearchError as e:
        return {"error": f"Search error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


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
    
    resources = context_vars.get('resources')
    scraper = ScrapingBeeScraper()
    resources_saved = []
    
    for resource_name, url in urls.items():
        try:
            # Validate resource name
            if not resource_name or not isinstance(resource_name, str):
                resources_saved.append(f"Invalid resource name for {url}: {resource_name}")
                continue
                
            # Clean resource name (remove spaces, special chars, make lowercase)
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', resource_name.lower().strip())
            if not clean_name:
                clean_name = f"resource_{len(resources) + 1}"
            
            resource = scraper.scrape_url(
                url.strip(), 
                render_js=render_js, 
                wait=wait,
                smart_js_detection=True  # Enable smart JS detection for better performance
            )
            
            # Override the resource ID with the meaningful name
            resource.id = clean_name
            resources[clean_name] = resource
            resources_saved.append(resource.format_for_llm(exclude_content=True))
        except ScrapingBeeError as e:
            # Log error but continue with other URLs
            resources_saved.append(f"Failed to scrape {url} as '{resource_name}': {str(e)}")

    return f"Extracted and saved the resources: {resources_saved}"


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
        
        # Further truncate if still too long
        if len(context_content) > max_line_length:
            context_content = context_content[:max_line_length] + "..."
        
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
    description="""Search for patterns in a resource's content using regex.
    Returns matching lines with line numbers and absolute character positions where matches occur.
    The start_pos and end_pos can be used directly with get_resource(startidx, endidx) to extract the matched content.
    Prefer using lower limits when you are not sure about the pattern.
    """
)
def grep_resource(
    resource_id: str,
    pattern: str,
    flags: int = 0,
    limit: int = 10,
    context_vars=None
) -> str:
    content, error = get_resource_content(resource_id, context_vars)
    if error:
        return error
    
    matches = grep_content(content, pattern, flags, limit)
    
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
    description="""Display products/items that will stream to the user in real-time as they are processed. Products appear immediately as each one is processed, creating a dynamic streaming experience.

Each item should be a dictionary with these fields:
- product_name (required): The name/title of the product (string)
- price (required): The price as a string, e.g. "29.99", "$45.00", "€35.50" (string)
- store (required): The store/brand name, e.g. "Zara", "H&M", "Amazon" (string)
- image_url (optional): Direct URL to product image (string)
- product_url (optional): Direct link to the product page for purchasing (string)
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
    try:
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
        
    except Exception as e:
        return {"error": f"Error processing items: {str(e)}"}


