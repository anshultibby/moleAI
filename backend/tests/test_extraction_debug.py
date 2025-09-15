"""
Debug tests for product extraction failures
Comprehensive logging and analysis of why extractions fail
"""

import asyncio
import json
import pytest
from typing import List, Dict, Any
from loguru import logger
import aiohttp
from bs4 import BeautifulSoup
from extruct import extract as extruct_extract
from w3lib.html import get_base_url

from app.modules.product_extractor import ProductExtractor
from app.models.product import SchemaOrgProduct


class TestExtractionDebug:
    """Debug product extraction failures with detailed logging"""
    
    @pytest.fixture
    def extractor(self):
        """Create a ProductExtractor instance"""
        return ProductExtractor()
    
    def setup_method(self):
        """Setup detailed logging for each test"""
        logger.add("extraction_debug.log", rotation="1 MB", level="DEBUG")
        logger.info("=" * 80)
        logger.info("STARTING NEW EXTRACTION DEBUG TEST")
        logger.info("=" * 80)
    
    @pytest.mark.asyncio
    async def test_failed_sites_individual_analysis(self, extractor):
        """Test each failed site individually with detailed analysis"""
        
        failed_sites = [
            {
                "name": "ABC Fashion",
                "url": "https://www.abcfashion.net/collections/long-prom-dresses-under-100/black?srsltid=AfmBOoqXE01QiiKHbKcA-UioCzrCW_hg8li5Qlz0OUgPfv6PgEkGX9Kz",
                "expected_products": "> 0"
            },
            {
                "name": "Amazon",
                "url": "https://www.amazon.com/Black-evening-dresses-50-100/s?rh=n%3A21308586011%2Cp_36%3A2661614011",
                "expected_products": "> 0"
            },
            {
                "name": "The Dress Warehouse", 
                "url": "https://thedresswarehouse.com/collections/evening-dresses-under-100?srsltid=AfmBOordvROQ04hMxZDRVORmsu1vSknD9lJwi-_XvOjpEaOe3GhDGUf9",
                "expected_products": "> 0"
            }
        ]
        
        for site in failed_sites:
            logger.info(f"\n🔍 ANALYZING FAILED SITE: {site['name']}")
            logger.info(f"URL: {site['url']}")
            logger.info("-" * 60)
            
            try:
                # Step 1: Test basic connectivity
                await self._test_site_connectivity(site['url'])
                
                # Step 2: Fetch and analyze HTML structure
                html_content = await self._fetch_and_analyze_html(site['url'])
                
                if html_content:
                    # Step 3: Test structured data extraction
                    await self._test_structured_data_extraction(html_content, site['url'], site['name'])
                    
                    # Step 4: Test product extraction pipeline
                    await self._test_product_extraction_pipeline(extractor, site['url'], site['name'])
                
            except Exception as e:
                logger.error(f"❌ Failed to analyze {site['name']}: {e}")
                logger.exception("Full error details:")
    
    async def _test_site_connectivity(self, url: str):
        """Test basic site connectivity and response"""
        logger.info("🌐 Testing site connectivity...")
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers={
                    "User-Agent": "ProductExtractorBot/1.0 (+mailto:test@example.com)"
                }) as response:
                    logger.info(f"✅ Response Status: {response.status}")
                    logger.info(f"✅ Content-Type: {response.headers.get('content-type', 'N/A')}")
                    logger.info(f"✅ Content-Length: {response.headers.get('content-length', 'N/A')}")
                    
                    if response.status != 200:
                        logger.warning(f"⚠️ Non-200 status code: {response.status}")
                        return False
                    
                    content_type = response.headers.get('content-type', '')
                    if 'text/html' not in content_type:
                        logger.warning(f"⚠️ Non-HTML content type: {content_type}")
                        return False
                    
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Connectivity test failed: {e}")
            return False
    
    async def _fetch_and_analyze_html(self, url: str) -> str:
        """Fetch HTML and analyze its structure"""
        logger.info("📄 Fetching and analyzing HTML structure...")
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers={
                    "User-Agent": "ProductExtractorBot/1.0 (+mailto:test@example.com)"
                }) as response:
                    html = await response.text(errors="ignore")
                    
                    # Basic HTML analysis
                    soup = BeautifulSoup(html, 'html.parser')
                    logger.info(f"✅ HTML length: {len(html)} characters")
                    logger.info(f"✅ Title: {soup.title.string if soup.title else 'N/A'}")
                    
                    # Check for structured data scripts
                    json_ld_scripts = soup.find_all('script', type='application/ld+json')
                    logger.info(f"✅ JSON-LD scripts found: {len(json_ld_scripts)}")
                    
                    # Check for microdata
                    microdata_elements = soup.find_all(attrs={"itemtype": True})
                    logger.info(f"✅ Microdata elements found: {len(microdata_elements)}")
                    
                    # Check for product-like content
                    product_indicators = [
                        soup.find_all(class_=lambda x: x and 'product' in x.lower()),
                        soup.find_all(attrs={"data-product": True}),
                        soup.find_all('div', attrs={"itemtype": lambda x: x and 'product' in x.lower() if x else False})
                    ]
                    total_product_indicators = sum(len(indicators) for indicators in product_indicators)
                    logger.info(f"✅ Product-like elements found: {total_product_indicators}")
                    
                    # Log first few JSON-LD scripts for analysis
                    for i, script in enumerate(json_ld_scripts[:3]):
                        try:
                            data = json.loads(script.string)
                            logger.info(f"📋 JSON-LD Script {i+1}: {json.dumps(data, indent=2)[:500]}...")
                        except:
                            logger.warning(f"⚠️ Invalid JSON in script {i+1}")
                    
                    return html
                    
        except Exception as e:
            logger.error(f"❌ HTML fetch/analysis failed: {e}")
            return ""
    
    async def _test_structured_data_extraction(self, html: str, url: str, site_name: str):
        """Test structured data extraction using extruct"""
        logger.info("🔍 Testing structured data extraction...")
        
        try:
            base_url = get_base_url(html, url)
            logger.info(f"✅ Base URL: {base_url}")
            
            # Extract all structured data
            data = extruct_extract(html, base_url=base_url, syntaxes=['json-ld', 'microdata', 'rdfa'])
            
            logger.info(f"✅ JSON-LD blocks: {len(data.get('json-ld', []))}")
            logger.info(f"✅ Microdata items: {len(data.get('microdata', []))}")
            logger.info(f"✅ RDFa items: {len(data.get('rdfa', []))}")
            
            # Analyze JSON-LD data
            json_ld_products = []
            for block in data.get('json-ld', []):
                items = block if isinstance(block, list) else [block]
                for item in items:
                    if isinstance(item, dict):
                        # Check for @graph
                        nodes = item.get('@graph', []) if '@graph' in item else [item]
                        for node in nodes:
                            if isinstance(node, dict):
                                node_type = node.get('@type', '')
                                if isinstance(node_type, str) and 'product' in node_type.lower():
                                    json_ld_products.append(node)
                                    logger.info(f"📦 Found JSON-LD Product: {node.get('name', 'N/A')}")
                                elif isinstance(node_type, list) and any('product' in t.lower() for t in node_type):
                                    json_ld_products.append(node)
                                    logger.info(f"📦 Found JSON-LD Product (list type): {node.get('name', 'N/A')}")
            
            # Analyze microdata
            microdata_products = []
            for item in data.get('microdata', []):
                if isinstance(item, dict):
                    item_type = item.get('type', '')
                    if isinstance(item_type, str) and 'product' in item_type.lower():
                        microdata_products.append(item)
                        logger.info(f"📦 Found Microdata Product: {item.get('properties', {}).get('name', ['N/A'])[0] if item.get('properties', {}).get('name') else 'N/A'}")
            
            logger.info(f"🎯 Total products found - JSON-LD: {len(json_ld_products)}, Microdata: {len(microdata_products)}")
            
            # Log sample product data
            if json_ld_products:
                logger.info(f"📋 Sample JSON-LD Product: {json.dumps(json_ld_products[0], indent=2)[:1000]}...")
            if microdata_products:
                logger.info(f"📋 Sample Microdata Product: {json.dumps(microdata_products[0], indent=2)[:1000]}...")
                
            return {
                'json_ld': json_ld_products,
                'microdata': microdata_products,
                'total': len(json_ld_products) + len(microdata_products)
            }
            
        except Exception as e:
            logger.error(f"❌ Structured data extraction failed: {e}")
            logger.exception("Full error details:")
            return {'json_ld': [], 'microdata': [], 'total': 0}
    
    async def _test_product_extraction_pipeline(self, extractor: ProductExtractor, url: str, site_name: str):
        """Test the full product extraction pipeline"""
        logger.info("🔄 Testing full product extraction pipeline...")
        
        try:
            # Test with limited crawling first
            products = await extractor.extract_from_url_and_links(url, max_links=3)
            
            logger.info(f"🎯 Pipeline result: {len(products)} products extracted")
            
            if products:
                for i, product in enumerate(products[:3]):  # Log first 3 products
                    logger.info(f"📦 Product {i+1}:")
                    logger.info(f"  Name: {product.name}")
                    logger.info(f"  Price: {product.get_price()} {product.get_currency()}")
                    logger.info(f"  Brand: {product.get_brand_name()}")
                    logger.info(f"  Description: {product.description}")
                    logger.info(f"  URL: {product.url}")
                    logger.info(f"  SKU: {product.sku}")
                    logger.info(f"  Image: {product.image}")
                    
                    # Check for missing description specifically
                    if not product.description:
                        logger.warning(f"⚠️ Product {i+1} missing description")
                        # Log the raw data to see what's available
                        simple_dict = product.to_simple_dict()
                        logger.info(f"📋 Raw product data: {json.dumps(simple_dict, indent=2)}")
            else:
                logger.warning(f"⚠️ No products extracted from {site_name}")
                
        except Exception as e:
            logger.error(f"❌ Pipeline test failed: {e}")
            logger.exception("Full error details:")
    
    @pytest.mark.asyncio
    async def test_ever_pretty_description_issue(self, extractor):
        """Specifically test why Ever-Pretty products have no descriptions"""
        logger.info("\n🔍 ANALYZING EVER-PRETTY DESCRIPTION ISSUE")
        logger.info("=" * 60)
        
        url = "https://www.ever-pretty.com/collections/black-dresses?filter.v.option.color=Black"
        
        try:
            # Fetch a single product page to analyze description extraction
            html = await self._fetch_and_analyze_html(url)
            
            if html:
                # Test internal extraction method
                products = extractor._extract_products_from_html(html, url)
                
                logger.info(f"🎯 Raw extraction found {len(products)} products")
                
                for i, product_data in enumerate(products[:3]):
                    logger.info(f"\n📦 Raw Product {i+1}:")
                    logger.info(f"📋 Full raw data: {json.dumps(product_data, indent=2)}")
                    
                    # Check what description fields are available
                    description_fields = ['description', 'desc', 'summary', 'details', 'about']
                    for field in description_fields:
                        if field in product_data:
                            logger.info(f"✅ Found {field}: {product_data[field]}")
                    
                    # Test normalization
                    normalized = extractor._normalize_product(product_data)
                    logger.info(f"📋 Normalized data: {json.dumps(normalized, indent=2)}")
                    
                    # Test schema conversion
                    schema_product = extractor._convert_to_schema_org_product(normalized)
                    logger.info(f"📋 Schema product description: {schema_product.description}")
                    
        except Exception as e:
            logger.error(f"❌ Ever-Pretty analysis failed: {e}")
            logger.exception("Full error details:")
    
    def test_normalization_logic(self, extractor):
        """Test the product normalization logic with various inputs"""
        logger.info("\n🔍 TESTING NORMALIZATION LOGIC")
        logger.info("=" * 60)
        
        test_cases = [
            {
                "name": "Standard Product",
                "data": {
                    "name": "Test Dress",
                    "description": "A beautiful test dress",
                    "sku": "TEST123",
                    "offers": {"price": "99.99", "priceCurrency": "USD"}
                }
            },
            {
                "name": "Product with nested description",
                "data": {
                    "name": "Test Dress 2",
                    "desc": "Alternative description field",
                    "sku": "TEST456",
                    "offers": [{"price": "149.99", "priceCurrency": "USD"}]
                }
            },
            {
                "name": "Product with brand object",
                "data": {
                    "name": "Test Dress 3",
                    "description": "Third test dress",
                    "brand": {"@type": "Brand", "name": "Test Brand"},
                    "offers": {"price": "199.99", "priceCurrency": "USD"}
                }
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"\n🧪 Testing: {test_case['name']}")
            
            # Test normalization
            normalized = extractor._normalize_product(test_case['data'])
            logger.info(f"📋 Normalized: {json.dumps(normalized, indent=2)}")
            
            # Test schema conversion
            schema_product = extractor._convert_to_schema_org_product(normalized)
            logger.info(f"📦 Schema Product:")
            logger.info(f"  Name: {schema_product.name}")
            logger.info(f"  Description: {schema_product.description}")
            logger.info(f"  Price: {schema_product.get_price()}")
            logger.info(f"  Brand: {schema_product.get_brand_name()}")


if __name__ == "__main__":
    async def run_debug_tests():
        """Run debug tests manually"""
        test_instance = TestExtractionDebug()
        test_instance.setup_method()
        
        extractor = ProductExtractor()
        
        # Test failed sites
        await test_instance.test_failed_sites_individual_analysis(extractor)
        
        # Test Ever-Pretty description issue
        await test_instance.test_ever_pretty_description_issue(extractor)
        
        # Test normalization
        test_instance.test_normalization_logic(extractor)
    
    asyncio.run(run_debug_tests())
