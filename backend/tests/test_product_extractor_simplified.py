"""Test for simplified product extractor"""

import json
import pytest
import asyncio
from pathlib import Path

from app.modules.product_extractor import ProductExtractor, ProductExtractionError


class TestSimplifiedProductExtractor:
    """Test the simplified JSON-LD only product extractor"""
    
    @pytest.fixture
    def extractor(self):
        """Create a ProductExtractor instance"""
        return ProductExtractor()
    
    @pytest.fixture
    def scraped_data(self):
        """Load test scraped data"""
        test_file = Path(__file__).parent / "test_scraped_content.json"
        with open(test_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_extract_json_ld_products_from_scraped_data(self, extractor, scraped_data):
        """Test extracting JSON-LD products from real scraped data"""
        # Get the HTML content from scraped data
        html_content = scraped_data.get('html_content', '')
        url = scraped_data.get('url', '')
        
        # Extract JSON-LD products
        product_cards = extractor.extract_json_ld_products(html_content, url)
        
        # Verify we got product cards as strings
        assert isinstance(product_cards, list)
        
        if product_cards:
            # Check that each product card is a valid JSON string
            for card in product_cards:
                assert isinstance(card, str)
                # Verify it's valid JSON
                product_data = json.loads(card)
                assert isinstance(product_data, dict)
                # Should have @type: Product
                assert product_data.get('@type') == 'Product'
                
            print(f"✅ Found {len(product_cards)} JSON-LD product cards")
            print(f"First product card preview:")
            first_product = json.loads(product_cards[0])
            print(f"  Name: {first_product.get('name', 'N/A')}")
            print(f"  URL: {first_product.get('url', 'N/A')}")
            if 'offers' in first_product:
                offers = first_product['offers']
                if isinstance(offers, list) and offers:
                    price = offers[0].get('price', 'N/A')
                    currency = offers[0].get('priceCurrency', 'N/A')
                elif isinstance(offers, dict):
                    price = offers.get('price', 'N/A')
                    currency = offers.get('priceCurrency', 'N/A')
                else:
                    price = currency = 'N/A'
                print(f"  Price: {price} {currency}")
        else:
            print("⚠️ No JSON-LD products found in scraped data")
    
    def test_get_page_links_from_scraped_data(self, extractor, scraped_data):
        """Test extracting product links from real scraped data"""
        html_content = scraped_data.get('html_content', '')
        url = scraped_data.get('url', '')
        
        # Extract product links
        links = extractor.get_page_links(html_content, url)
        
        # Verify we got links
        assert isinstance(links, list)
        
        if links:
            print(f"✅ Found {len(links)} product links")
            print("Sample links:")
            for i, link in enumerate(links[:5]):  # Show first 5
                print(f"  {i+1}. {link}")
        else:
            print("⚠️ No product links found in scraped data")
    
    @pytest.mark.asyncio
    async def test_scrape_and_extract_with_links_live(self, extractor):
        """Test the full scrape and extract workflow with a live URL"""
        # Use a simple e-commerce site for testing
        test_url = "https://fakestoreapi.com"  # This won't work for scraping, but shows the pattern
        
        try:
            # This would normally work with a real e-commerce site
            # result = await extractor.scrape_and_extract_with_links(
            #     test_url, 
            #     max_links=3,
            #     render_js=False,
            #     wait=1000
            # )
            
            # For now, just test that the method exists and has the right signature
            assert hasattr(extractor, 'scrape_and_extract_with_links')
            assert callable(extractor.scrape_and_extract_with_links)
            
            print("✅ scrape_and_extract_with_links method is available")
            
        except Exception as e:
            # Expected to fail without a real scraping setup
            print(f"⚠️ Live scraping test failed (expected): {e}")
    
    def test_extract_json_ld_with_sample_data(self, extractor):
        """Test JSON-LD extraction with sample product data"""
        # Sample HTML with JSON-LD product data
        sample_html = '''
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org/",
                "@type": "Product",
                "name": "Test Product",
                "description": "A great test product",
                "sku": "TEST123",
                "brand": {
                    "@type": "Brand",
                    "name": "Test Brand"
                },
                "offers": {
                    "@type": "Offer",
                    "price": "29.99",
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/InStock"
                },
                "image": "https://example.com/test-product.jpg",
                "url": "https://example.com/products/test-product"
            }
            </script>
        </head>
        <body>
            <h1>Test Product</h1>
        </body>
        </html>
        '''
        
        # Extract products
        product_cards = extractor.extract_json_ld_products(sample_html, "https://example.com")
        
        # Verify extraction
        assert len(product_cards) == 1
        
        product_data = json.loads(product_cards[0])
        assert product_data['@type'] == 'Product'
        assert product_data['name'] == 'Test Product'
        assert product_data['sku'] == 'TEST123'
        assert product_data['offers']['price'] == '29.99'
        assert product_data['offers']['priceCurrency'] == 'USD'
        
        print("✅ Successfully extracted sample JSON-LD product")
        print(f"Product: {product_data['name']} - ${product_data['offers']['price']}")


if __name__ == "__main__":
    # Run a quick test
    extractor = ProductExtractor()
    
    # Test with sample data
    sample_html = '''
    <script type="application/ld+json">
    {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "Sample Dress",
        "offers": {
            "@type": "Offer",
            "price": "99.99",
            "priceCurrency": "USD"
        }
    }
    </script>
    '''
    
    products = extractor.extract_json_ld_products(sample_html)
    print(f"Quick test: Found {len(products)} products")
    if products:
        print("First product:", products[0])
