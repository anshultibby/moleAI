"""Product extractors package"""

from .simple_extractor import extract_products_simple, extract_products_from_url_simple
from .zyte_extractor import extract_products_zyte, extract_products_from_url_zyte

# Import extractors to register tools
from . import simple_extractor
from . import zyte_extractor

__all__ = [
    'extract_products_simple',
    'extract_products_from_url_simple',
    'extract_products_zyte',
    'extract_products_from_url_zyte',
    'simple_extractor',
    'zyte_extractor'
]
