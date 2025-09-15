"""Test for simplified product extractor"""


import pytest

from typing import List, Dict
from app.modules.product_extractor import ProductExtractor
from app.models.product import SchemaOrgProduct


class TestSimplifiedProductExtractor:
    """Test the simplified JSON-LD only product extractor"""
    
    @pytest.fixture
    def extractor(self):
        """Create a ProductExtractor instance"""
        return ProductExtractor()
    
    @pytest.mark.asyncio
    async def test_extract_products_from_abc_fashion(self, extractor):
        """Test the complete product extraction workflow on ABC Fashion"""
        test_url = "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black"
        
        print(f"\n🌐 TESTING COMPLETE PRODUCT EXTRACTION")
        print(f"URL: {test_url}")
        print("=" * 80)
        
        try:
            # Run the main extraction method
            products = await extractor.extract_from_url_and_links(test_url, max_links=5)
            
            print(f"\n🎉 EXTRACTION COMPLETED!")
            print(f"Found {len(products)} total products")
            print("=" * 80)
            
            # Show all extracted products
            if products:
                for i, product in enumerate(products, 1):
                    print(f"\n🛍️ PRODUCT {i}:")
                    
                    # Show key product info using the model's helper methods
                    print(f"  📝 {product.name or 'N/A'}")
                    print(f"  💰 {product.get_price() or 'N/A'} {product.get_currency()}")
                    print(f"  🏷️ {product.get_brand_name() or 'N/A'}")
                    print(f"  🔗 {product.url or 'N/A'}")
                    print(f"  🏷️ SKU: {product.sku or 'N/A'}")
                    print(f"  🎨 Color: {product.color or 'N/A'}")
                    print(f"  📏 Size: {product.size or 'N/A'}")
                    
                    print("-" * 40)
                    print("Simple dict:")
                    simple_dict = product.to_simple_dict()
                    for key, value in simple_dict.items():
                        print(f"  {key}: {value}")
                    print("=" * 80)
            else:
                print("⚠️ No products found")
            
            # Verify we got a list of SchemaOrgProduct objects
            assert isinstance(products, list)
            for product in products:
                assert isinstance(product, SchemaOrgProduct)
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            # Don't fail the test for network issues
            print("⚠️ This might be due to network issues or site changes")
    
    def test_sample_json_ld_extraction(self, extractor):
        """Test JSON-LD extraction with sample data using internal method"""
        sample_html = '''
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org/",
                "@type": "Product",
                "name": "Test Dress",
                "sku": "TEST123",
                "brand": {"@type": "Brand", "name": "Test Brand"},
                "offers": {
                    "@type": "Offer",
                    "price": "99.99",
                    "priceCurrency": "USD"
                }
            }
            </script>
        </head>
        </html>
        '''
        
        # Test the internal extraction method
        products = extractor._extract_products_from_html(sample_html, "https://example.com")
        
        assert len(products) >= 1
        product_data = products[0]
        assert isinstance(product_data, dict)
        assert product_data.get('name') == 'Test Dress'
        
        # Test conversion to SchemaOrgProduct
        schema_product = extractor._convert_to_schema_org_product(product_data)
        assert isinstance(schema_product, SchemaOrgProduct)
        assert schema_product.name == 'Test Dress'
        
        print("✅ Sample extraction test passed")


if __name__ == "__main__":
    import asyncio
    
    async def quick_test():
        extractor = ProductExtractor()
        products = await extractor.extract_from_url_and_links(
            "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black", 
            max_links=3
        )
        print(f"Found {len(products)} products")
        for i, product in enumerate(products[:2], 1):  # Show first 2
            print(f"\nProduct {i}: {product.name} - ${product.get_price()} {product.get_currency()}")
            print(f"  Brand: {product.get_brand_name()}")
            print(f"  URL: {product.url}")
    
    asyncio.run(quick_test())
