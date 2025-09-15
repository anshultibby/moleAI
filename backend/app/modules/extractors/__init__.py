"""Product extractors package"""

from .base import BaseProductExtractor, ProductExtractionError
from .general import GeneralProductExtractor
# Legacy extractors (deprecated)
from .shopify_analytics import ShopifyAnalyticsExtractor
from .atom_feed import AtomFeedExtractor
from .html_heuristic import HtmlHeuristicExtractor

__all__ = [
    'BaseProductExtractor',
    'ProductExtractionError',
    'GeneralProductExtractor',
    # Legacy (deprecated)
    'ShopifyAnalyticsExtractor',
    'AtomFeedExtractor',
    'HtmlHeuristicExtractor'
]
