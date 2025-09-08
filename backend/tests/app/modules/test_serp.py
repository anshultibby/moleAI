#!/usr/bin/env python3
"""
Tests for app.modules.serp module

This module tests the Jina AI Search comprehensive functionality.
"""

import os
import json
import pytest
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.modules.serp import search_comprehensive, search_jina
from app.modules.scraper import extract_jsonld_from_url


class TestJinaSearch:
    """Test cases for Jina AI Search functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        if not os.getenv("JINA_AI_API_KEY"):
            pytest.skip("JINA_AI_API_KEY not found in environment")
    
    def test_comprehensive_search(self):
        """Test comprehensive search with full content reading and save JSON"""
        print("📚 Testing comprehensive search for 'black boots for women'...")
        
        results = search_comprehensive("black boots for women", num_results=3)
        
        # Validate response structure
        assert isinstance(results, dict)
        assert 'query' in results
        assert 'results' in results
        assert 'metadata' in results
        
        # Validate comprehensive search metadata
        metadata = results.get('metadata', {})
        assert metadata.get('read_content') is True
        assert metadata.get('with_links_summary') is True
        assert metadata.get('with_images_summary') is True
        
        # Check for token usage information
        raw_response = results.get('raw_response', {})
        assert 'meta' in raw_response or 'usage' in raw_response
        
        # Save raw JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_results_comprehensive_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"   💾 Saved raw JSON to: {filename}")
        
        print("✅ Comprehensive search test passed!")
        return results
    
    def test_basic_search_no_content(self):
        """Test basic search without content reading and save JSON"""
        print("🔍 Testing basic search for 'black boots for women' (no content reading)...")
        
        results = search_jina("black boots for women", num_results=3)
        
        # Validate response structure
        assert isinstance(results, dict)
        assert 'query' in results
        assert 'results' in results
        assert 'metadata' in results
        assert results['query'] == "black boots for women"
        
        # Validate basic search metadata (should not have content reading)
        metadata = results.get('metadata', {})
        assert metadata.get('read_content') is False
        assert metadata.get('provider') is not None
        assert metadata.get('num_results') == 3
        
        # Save raw JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_results_basic_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"   💾 Saved raw JSON to: {filename}")
        
        print("✅ Basic search test passed!")
        return results
    
    def test_search_and_extract_jsonld(self):
        """Test searching for links and extracting JSON-LD from 3 results"""
        print("🔍🧬 Testing search + JSON-LD extraction workflow...")
        
        # First, perform a search to get some links
        print("   📚 Step 1: Searching for 'e-commerce shoes'...")
        search_results = search_jina("e-commerce shoes", num_results=10)
        
        # Validate search results
        assert isinstance(search_results, dict)
        assert 'results' in search_results
        assert len(search_results['results']) > 0
        
        # Extract URLs from search results
        urls = []
        for result in search_results['results']:
            if 'url' in result and result['url']:
                urls.append(result['url'])
        
        print(f"   🔗 Found {len(urls)} URLs from search")
        assert len(urls) >= 3, f"Need at least 3 URLs, got {len(urls)}"
        
        # Extract JSON-LD from first 3 URLs
        jsonld_results = []
        for i, url in enumerate(urls[:3]):
            print(f"   🧬 Step 2.{i+1}: Extracting JSON-LD from {url[:60]}...")
            
            try:
                jsonld_result = extract_jsonld_from_url(url)
                jsonld_results.append({
                    'url': url,
                    'extraction_result': jsonld_result
                })
                
                # Log results
                if jsonld_result['success']:
                    count = jsonld_result['metadata']['jsonld_count']
                    print(f"      ✅ Success: Found {count} JSON-LD objects")
                    
                    # Print a sample of the JSON-LD data if found
                    if count > 0:
                        sample = jsonld_result['jsonld_data'][0]
                        if isinstance(sample, dict) and '@type' in sample:
                            print(f"      📋 Sample type: {sample.get('@type', 'Unknown')}")
                else:
                    error = jsonld_result['metadata'].get('error', 'Unknown error')
                    print(f"      ❌ Failed: {error}")
                    
            except Exception as e:
                print(f"      ❌ Exception: {str(e)}")
                jsonld_results.append({
                    'url': url,
                    'extraction_result': {
                        'jsonld_data': [],
                        'metadata': {'url': url, 'error': str(e)},
                        'success': False
                    }
                })
        
        # Save combined results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_and_jsonld_results_{timestamp}.json"
        
        combined_results = {
            'search_query': "e-commerce shoes",
            'search_results': search_results,
            'jsonld_extractions': jsonld_results,
            'summary': {
                'total_urls_searched': len(search_results['results']),
                'urls_processed_for_jsonld': len(jsonld_results),
                'successful_extractions': sum(1 for r in jsonld_results if r['extraction_result']['success']),
                'total_jsonld_objects': sum(r['extraction_result']['metadata'].get('jsonld_count', 0) for r in jsonld_results)
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, indent=2, ensure_ascii=False)
        print(f"   💾 Saved combined results to: {filename}")
        
        # Assertions
        assert len(jsonld_results) == 3, f"Expected 3 JSON-LD extractions, got {len(jsonld_results)}"
        
        # At least one extraction should be successful (some sites might not have JSON-LD)
        successful_count = combined_results['summary']['successful_extractions']
        print(f"   📊 Summary: {successful_count}/3 successful JSON-LD extractions")
        
        print("✅ Search + JSON-LD extraction test completed!")
        return combined_results

