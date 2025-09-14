"""Tests for ProductExtractor module"""

import pytest
import json
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from app.modules.product_extractor import ProductExtractor, ProductExtractionError
from app.models.product import Product


class TestProductExtractor:
    """Test cases for ProductExtractor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = ProductExtractor()
    
    def test_init(self):
        """Test ProductExtractor initialization"""
        assert isinstance(self.extractor, ProductExtractor)
    
    def test_find_analytics_script_with_collection_viewed(self):
        """Test finding analytics script with collection_viewed indicator"""
        html_content = """
        <html>
            <script>
                analytics.track('collection_viewed', {
                    collection: {id: "123", productVariants: []}
                });
            </script>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        result = self.extractor._find_analytics_script(soup)
        
        assert result is not None
        assert 'collection_viewed' in result
    
    def test_find_analytics_script_with_json_ld_fallback(self):
        """Test finding JSON-LD script as fallback"""
        html_content = """
        <html>
            <script type="application/ld+json">
                {"@type": "Product", "name": "Test Product"}
            </script>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        result = self.extractor._find_analytics_script(soup)
        
        assert result is not None
        assert 'Product' in result
    
    def test_find_analytics_script_not_found(self):
        """Test when no analytics script is found"""
        html_content = """
        <html>
            <script>console.log('no analytics here');</script>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        result = self.extractor._find_analytics_script(soup)
        
        assert result is None
    
    def test_clean_json_string(self):
        """Test JSON string cleaning"""
        dirty_json = '{\\"title\\":\\"Test Product\\",\\"price\\":99.0}'
        clean_json = self.extractor._clean_json_string(dirty_json)
        
        assert clean_json == '{"title":"Test Product","price":99.0}'
    
    def test_extract_from_collection_events(self):
        """Test extracting products from collection_viewed events"""
        script_content = '''
        analytics.track('collection_viewed', {"collection":{"id":"123","productVariants":[
            {"price":{"amount":99.0,"currencyCode":"USD"},"product":{"title":"Test Product","vendor":"Test Brand","id":"456"}}
        ]}});
        '''
        
        variants = self.extractor._extract_from_collection_events(script_content)
        
        assert len(variants) == 1
        assert variants[0]['price']['amount'] == 99.0
        assert variants[0]['product']['title'] == 'Test Product'
    
    def test_extract_from_product_variants_arrays(self):
        """Test extracting products from productVariants arrays"""
        script_content = '''
        productVariants: [
            {"price":{"amount":79.0,"currencyCode":"USD"},"product":{"title":"Another Product","vendor":"Another Brand","id":"789"}}
        ]
        '''
        
        variants = self.extractor._extract_from_product_variants_arrays(script_content)
        
        assert len(variants) == 1
        assert variants[0]['price']['amount'] == 79.0
        assert variants[0]['product']['title'] == 'Another Product'
    
    def test_create_shopify_product(self):
        """Test creating Product instance from Shopify variant data"""
        variant_data = {
            'price': {'amount': 99.0, 'currencyCode': 'USD'},
            'product': {
                'title': 'Test Dress',
                'vendor': 'Test Brand',
                'id': '123456'
            },
            'id': '789012',
            'sku': 'TEST123',
            'image': {'src': '//example.com/image.jpg'}
        }
        
        product = self.extractor._create_shopify_product(variant_data, 'https://test.com')
        
        assert isinstance(product, Product)
        assert product.title == 'Test Dress'
        assert product.price == 99.0
        assert product.currency == 'USD'
        assert product.vendor == 'Test Brand'
        assert product.sku == 'TEST123'
        assert product.product_id == '123456'
        assert product.variant_id == '789012'
        assert product.image_url == 'https://example.com/image.jpg'
    
    def test_create_shopify_product_missing_data(self):
        """Test creating Product with missing essential data"""
        variant_data = {
            'price': {'amount': 50.0, 'currencyCode': 'EUR'},
            'sku': 'INCOMPLETE'
        }
        
        product = self.extractor._create_shopify_product(variant_data)
        
        # Should return None if missing essential data (title or product_id)
        assert product is None
    
    def test_extract_shopify_products_success(self):
        """Test successful product extraction from HTML"""
        html_content = '''
        <html>
            <script>
                analytics.track('collection_viewed', {
                    "collection": {
                        "id": "123",
                        "productVariants": [
                            {
                                "price": {"amount": 99.0, "currencyCode": "USD"},
                                "product": {"title": "Test Product", "vendor": "Test Brand", "id": "456"},
                                "id": "789",
                                "sku": "TEST123"
                            }
                        ]
                    }
                });
            </script>
        </html>
        '''
        
        products = self.extractor.extract_shopify_products(html_content, 'https://test.com')
        
        assert len(products) == 1
        assert isinstance(products[0], Product)
        assert products[0].title == 'Test Product'
        assert products[0].price == 99.0
        assert products[0].currency == 'USD'
    
    def test_extract_shopify_products_no_analytics_script(self):
        """Test extraction when no analytics script is found"""
        html_content = '<html><body>No analytics here</body></html>'
        
        products = self.extractor.extract_shopify_products(html_content)
        
        assert len(products) == 0
    
    def test_extract_shopify_products_invalid_html(self):
        """Test extraction with invalid HTML raises exception"""
        with pytest.raises(ProductExtractionError):
            self.extractor.extract_shopify_products("")


class TestProductExtractorIntegration:
    """Integration tests using real scraped data"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = ProductExtractor()
    
    @pytest.mark.integration
    def test_extract_from_abc_fashion_data(self):
        """Test extraction using real ABC Fashion scraped data"""
        # This test requires the actual scraped data file
        try:
            with open('resources/chat_history/scraped_abc_fashion_20250914_144517.json', 'r') as f:
                data = json.load(f)
            
            html_content = data['raw_content']
            url = data['url']
            
            products = self.extractor.extract_shopify_products(html_content, url)
            
            # Verify we extracted the expected number of products
            assert len(products) == 32
            
            # Verify product structure
            for product in products:
                assert isinstance(product, Product)
                assert product.title is not None
                assert product.price is not None
                assert product.currency is not None
                assert product.vendor is not None
            
            # Check specific product details
            first_product = products[0]
            assert 'Gown' in first_product.title or 'Dress' in first_product.title
            assert first_product.currency == 'USD'
            assert first_product.price > 0
            
        except FileNotFoundError:
            pytest.skip("ABC Fashion scraped data file not found")


if __name__ == '__main__':
    pytest.main([__file__])
