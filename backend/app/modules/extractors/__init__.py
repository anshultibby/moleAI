"""Product extractors package"""

from .base import BaseProductExtractor, ProductExtractionError
from .general import GeneralProductExtractor
from .simple_extractor import extract_products_simple, extract_products_from_url_simple
# Legacy extractors (deprecated)
from .shopify_analytics import ShopifyAnalyticsExtractor
from .atom_feed import AtomFeedExtractor
from .html_heuristic import HtmlHeuristicExtractor

# Import simple extractor to register tools
from . import simple_extractor

__all__ = [
    'BaseProductExtractor',
    'ProductExtractionError',
    'GeneralProductExtractor',
    'extract_products_simple',
    'extract_products_from_url_simple',
    # Legacy (deprecated)
    'ShopifyAnalyticsExtractor',
    'AtomFeedExtractor',
    'HtmlHeuristicExtractor'
]
