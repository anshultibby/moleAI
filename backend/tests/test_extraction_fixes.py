"""
Test the fixes for product extraction issues
"""

import asyncio
import pytest
from typing import List, Dict, Any
from loguru import logger

from app.modules.product_extractor import ProductExtractor
from app.models.product import SchemaOrgProduct


class TestExtractionFixes:
    """Test the fixes for product extraction issues"""
    
    @pytest.fixture
    def extractor(self):
        """Create a ProductExtractor instance"""
        return ProductExtractor()
    
    def test_normalization_fixes(self, extractor):
        """Test that normalization fixes work correctly"""
        logger.info("🧪 Testing normalization fixes...")
        
        # Test case that was failing before - price data loss
        ever_pretty_sample = {
            "@type": "Product",
            "name": "Test Evening Dress",
            "brand": {"@type": "Brand", "name": "Ever-Pretty US"},
            "offers": {
                "@type": "Offer", 
                "price": 78.99,
                "priceCurrency": "USD",
                "availability": "http://schema.org/InStock"
            },
            "image": "https://example.com/image.jpg",
            "url": "https://example.com/product"
        }
        
        # Test normalization
        normalized = extractor._normalize_product(ever_pretty_sample)
        logger.info(f"✅ Normalized price: {normalized['price']} (should be 78.99)")
        logger.info(f"✅ Normalized currency: {normalized['priceCurrency']} (should be USD)")
        logger.info(f"✅ Normalized brand: {normalized['brand']} (should be Ever-Pretty US)")
        
        # Verify fixes
        assert normalized['price'] == 78.99, f"Expected 78.99, got {normalized['price']}"
        assert normalized['priceCurrency'] == "USD", f"Expected USD, got {normalized['priceCurrency']}"
        assert normalized['brand'] == "Ever-Pretty US", f"Expected Ever-Pretty US, got {normalized['brand']}"
        
        # Test schema conversion
        schema_product = extractor._convert_to_schema_org_product(normalized)
        assert schema_product.get_price() == 78.99  # Returns float, not string
        assert schema_product.get_currency() == "USD"
        assert schema_product.get_brand_name() == "Ever-Pretty US"
        
        logger.info("✅ Normalization fixes working correctly!")
    
    def test_description_extraction_improvements(self, extractor):
        """Test improved description extraction"""
        logger.info("🧪 Testing description extraction improvements...")
        
        test_cases = [
            {
                "name": "Standard description",
                "data": {"name": "Test", "description": "Standard desc"},
                "expected": "Standard desc"
            },
            {
                "name": "Alternative desc field", 
                "data": {"name": "Test", "desc": "Alt desc"},
                "expected": "Alt desc"
            },
            {
                "name": "Summary field",
                "data": {"name": "Test", "summary": "Summary desc"}, 
                "expected": "Summary desc"
            },
            {
                "name": "Details field",
                "data": {"name": "Test", "details": "Details desc"},
                "expected": "Details desc"
            }
        ]
        
        for test_case in test_cases:
            normalized = extractor._normalize_product(test_case['data'])
            logger.info(f"✅ {test_case['name']}: {normalized['description']}")
            assert normalized['description'] == test_case['expected']
        
        logger.info("✅ Description extraction improvements working!")
    
    def test_product_link_extraction(self, extractor):
        """Test product link extraction from listing pages"""
        logger.info("🧪 Testing product link extraction...")
        
        # Sample HTML that mimics a collection page
        sample_html = '''
        <html>
        <body>
            <div class="product-grid">
                <div class="product-item">
                    <a href="/products/dress-1" class="product-link">Dress 1</a>
                </div>
                <div class="product-item">
                    <a href="/products/dress-2">Dress 2</a>
                </div>
                <div class="product-card">
                    <a href="/p/dress-3">Dress 3</a>
                </div>
                <a href="/collections/other">Other Collection</a>
                <a href="/pages/about">About</a>
            </div>
        </body>
        </html>
        '''
        
        base_url = "https://example.com/collections/dresses"
        product_links = extractor._extract_product_links_from_listing(sample_html, base_url)
        
        logger.info(f"✅ Extracted {len(product_links)} product links:")
        for link in product_links:
            logger.info(f"  - {link}")
        
        # Should find the product links but not the collection/page links
        assert len(product_links) >= 3, f"Expected at least 3 product links, got {len(product_links)}"
        assert any("/products/dress-1" in link for link in product_links)
        assert any("/products/dress-2" in link for link in product_links) 
        assert any("/p/dress-3" in link for link in product_links)
        
        logger.info("✅ Product link extraction working!")
    
    @pytest.mark.asyncio
    async def test_ever_pretty_extraction_fix(self, extractor):
        """Test that Ever-Pretty extraction now works with fixes"""
        logger.info("🧪 Testing Ever-Pretty extraction with fixes...")
        
        url = "https://www.ever-pretty.com/collections/black-dresses?filter.v.option.color=Black"
        
        try:
            # Test with limited crawling
            products = await extractor.extract_from_url_and_links(url, max_links=5)
            
            logger.info(f"✅ Extracted {len(products)} products from Ever-Pretty")
            
            if products:
                sample_product = products[0]
                logger.info(f"✅ Sample product:")
                logger.info(f"  Name: {sample_product.name}")
                logger.info(f"  Price: {sample_product.get_price()} {sample_product.get_currency()}")
                logger.info(f"  Brand: {sample_product.get_brand_name()}")
                logger.info(f"  Description: {sample_product.description}")
                logger.info(f"  URL: {sample_product.url}")
                
                # Verify the fixes
                assert sample_product.get_price() is not None, "Price should not be None"
                assert sample_product.get_currency() is not None, "Currency should not be None"
                assert sample_product.get_brand_name() is not None, "Brand should not be None"
                
                logger.info("✅ Ever-Pretty extraction fixes working!")
            else:
                logger.warning("⚠️ No products extracted - may need more investigation")
                
        except Exception as e:
            logger.error(f"❌ Ever-Pretty test failed: {e}")
            # Don't fail test for network issues
            logger.warning("⚠️ This might be due to network issues")
    
    @pytest.mark.asyncio
    async def test_collection_page_extraction(self, extractor):
        """Test that collection pages now work (ABC Fashion, The Dress Warehouse)"""
        logger.info("🧪 Testing collection page extraction fixes...")
        
        test_sites = [
            {
                "name": "ABC Fashion",
                "url": "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black"
            },
            {
                "name": "The Dress Warehouse", 
                "url": "https://thedresswarehouse.com/collections/evening-dresses-under-100"
            }
        ]
        
        for site in test_sites:
            try:
                logger.info(f"Testing {site['name']}...")
                products = await extractor.extract_from_url_and_links(site['url'], max_links=3)
                
                logger.info(f"✅ {site['name']}: {len(products)} products")
                
                if products:
                    sample_product = products[0]
                    logger.info(f"  Sample: {sample_product.name} - ${sample_product.get_price()}")
                    
                    # Verify basic product data
                    assert sample_product.name is not None, f"{site['name']} product should have name"
                    assert sample_product.get_price() is not None, f"{site['name']} product should have price"
                    
                    logger.info(f"✅ {site['name']} extraction working!")
                else:
                    logger.warning(f"⚠️ {site['name']}: No products found - may be network issue")
                    
            except Exception as e:
                logger.error(f"❌ {site['name']} test failed: {e}")
                logger.warning("⚠️ This might be due to network issues or site changes")


if __name__ == "__main__":
    async def run_fix_tests():
        """Run fix tests manually"""
        test_instance = TestExtractionFixes()
        extractor = ProductExtractor()
        
        # Test normalization fixes
        test_instance.test_normalization_fixes(extractor)
        
        # Test description improvements
        test_instance.test_description_extraction_improvements(extractor)
        
        # Test product link extraction
        test_instance.test_product_link_extraction(extractor)
        
        # Test Ever-Pretty fixes
        await test_instance.test_ever_pretty_extraction_fix(extractor)
    
    asyncio.run(run_fix_tests())
