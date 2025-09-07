#!/usr/bin/env python3
"""
Tests for app.modules.serp module

This module tests the Jina AI Search functionality including:
- Basic search functionality
- Comprehensive search with content reading
- Token usage tracking
- Response structure validation
"""

import os
import json
import pytest
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.modules.serp import search_jina, search_comprehensive


class TestJinaSearch:
    """Test cases for Jina AI Search functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        if not os.getenv("JINA_AI_API_KEY"):
            pytest.skip("JINA_AI_API_KEY not found in environment")
    
    def test_basic_search(self):
        """Test basic search with 3 results"""
        print("🔍 Testing basic search for 'black boots for women' with 3 results...")
        
        results = search_jina("black boots for women", num_results=3)
        
        # Validate response structure
        assert isinstance(results, dict)
        assert 'query' in results
        assert 'results' in results
        assert 'metadata' in results
        assert results['query'] == "black boots for women"
        
        # Validate metadata
        metadata = results.get('metadata', {})
        assert metadata.get('provider') is not None
        assert metadata.get('num_results') == 3
        
        print("✅ Basic search test passed!")
        return results
    
    def test_comprehensive_search(self):
        """Test comprehensive search with full content reading"""
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
        
        print("✅ Comprehensive search test passed!")
        return results
    
    def test_token_usage_tracking(self):
        """Test that token usage information is captured"""
        results = search_comprehensive("test query", num_results=1)
        
        # Look for token usage in various places
        token_found = False
        
        # Check raw response
        raw_response = results.get('raw_response', {})
        if 'meta' in raw_response and 'usage' in raw_response['meta']:
            token_found = True
        
        # Check results for per-item usage
        search_results = results.get('results', [])
        if isinstance(search_results, list) and search_results:
            for result in search_results:
                if isinstance(result, dict) and 'usage' in result:
                    token_found = True
                    break
        
        assert token_found, "Token usage information should be available"
        print("✅ Token usage tracking test passed!")
    
    def test_response_structure_validation(self):
        """Test that response structure is consistent"""
        results = search_jina("test", num_results=1)
        
        # Required top-level keys
        required_keys = ['query', 'results', 'metadata', 'raw_response']
        for key in required_keys:
            assert key in results, f"Missing required key: {key}"
        
        # Metadata structure
        metadata = results['metadata']
        metadata_keys = ['provider', 'type', 'num_results', 'jina_status', 'jina_code']
        for key in metadata_keys:
            assert key in metadata, f"Missing metadata key: {key}"
        
        print("✅ Response structure validation passed!")


def test_basic_search_standalone():
    """Standalone test function for basic search"""
    if not os.getenv("JINA_AI_API_KEY"):
        print("⚠️ JINA_AI_API_KEY not found - skipping test")
        return None
    
    print("🔍 Testing search for 'black boots for women' with 3 results...")
    
    try:
        results = search_jina("black boots for women", num_results=3)
        
        print("✅ Success!")
        print(f"   Query: {results.get('query')}")
        print(f"   Provider: {results.get('metadata', {}).get('provider')}")
        print(f"   Links summary: {results.get('metadata', {}).get('with_links_summary')}")
        print(f"   Images summary: {results.get('metadata', {}).get('with_images_summary')}")
        print(f"   Generated alt text: {results.get('metadata', {}).get('with_generated_alt')}")
        
        # Print structure analysis
        print(f"   Raw response keys: {list(results.keys())}")
        print(f"   Metadata keys: {list(results.get('metadata', {}).keys())}")
        
        search_results = results.get('results')
        print(f"   Results type: {type(search_results)}")
        if isinstance(search_results, str):
            print(f"   Content length: {len(search_results)} characters")
            print(f"   Preview: {search_results[:200]}...")
        elif isinstance(search_results, dict):
            print(f"   Results dict keys: {list(search_results.keys())}")
        elif isinstance(search_results, list):
            print(f"   Results list length: {len(search_results)}")
            if search_results:
                print(f"   First item type: {type(search_results[0])}")
                if isinstance(search_results[0], dict):
                    print(f"   First item keys: {list(search_results[0].keys())}")
        
        # Save raw JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_results_basic_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"   💾 Saved raw JSON to: {filename}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_comprehensive_search_standalone():
    """Standalone test function for comprehensive search"""
    if not os.getenv("JINA_AI_API_KEY"):
        print("⚠️ JINA_AI_API_KEY not found - skipping test")
        return None
    
    print("\n📚 Testing comprehensive search for 'black boots for women' (with content reading)...")
    
    try:
        print("   📖 Running comprehensive search with content reading...")
        results = search_comprehensive("black boots for women", num_results=3)
        
        print("✅ Success!")
        metadata = results.get('metadata', {})
        print(f"   Query: {results.get('query')}")
        print(f"   Provider: {metadata.get('provider')}")
        print(f"   Read content: {metadata.get('read_content')}")
        print(f"   Response format: {metadata.get('respond_with')}")
        
        # Print structure analysis
        print(f"   Raw response keys: {list(results.keys())}")
        print(f"   Metadata keys: {list(results.get('metadata', {}).keys())}")
        
        search_results = results.get('results')
        print(f"   Results type: {type(search_results)}")
        if isinstance(search_results, str):
            print(f"   Content length: {len(search_results)} characters")
            print(f"   Preview: {search_results[:200]}...")
        elif isinstance(search_results, dict):
            print(f"   Results dict keys: {list(search_results.keys())}")
        elif isinstance(search_results, list):
            print(f"   Results list length: {len(search_results)}")
            if search_results:
                print(f"   First item type: {type(search_results[0])}")
                if isinstance(search_results[0], dict):
                    print(f"   First item keys: {list(search_results[0].keys())}")
        
        # Save raw JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_results_comprehensive_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"   💾 Saved raw JSON to: {filename}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main test function for standalone execution"""
    print("🚀 Jina AI Search Test - Comprehensive Search Only")
    print("="*60)
    
    # Check API key
    if not os.getenv("JINA_AI_API_KEY"):
        print("❌ Error: JINA_AI_API_KEY not found!")
        print("Please set your Jina AI API key in your .env file")
        return
    
    # Run only comprehensive search
    comp_results = test_comprehensive_search_standalone()
    
    print(f"\n{'='*60}")
    print("🎉 Test completed!")
    
    # Check for token usage info
    if comp_results:
        print("\n🔍 Checking for token usage info...")
        raw_response = comp_results.get('raw_response', {})
        jina_meta = comp_results.get('metadata', {}).get('jina_meta', {})
        
        print(f"Raw response keys: {list(raw_response.keys())}")
        if jina_meta:
            print(f"Jina meta keys: {list(jina_meta.keys())}")
            print(f"Jina meta content: {jina_meta}")
        else:
            print("No jina_meta found")
        
        # Look for any token-related fields
        def find_token_fields(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if 'token' in key.lower() or 'usage' in key.lower() or 'cost' in key.lower():
                        print(f"Found potential usage field: {current_path} = {value}")
                    if isinstance(value, (dict, list)):
                        find_token_fields(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_token_fields(item, f"{path}[{i}]")
        
        find_token_fields(raw_response)
        
        print("\n💡 Full raw response saved to JSON file for detailed analysis")


if __name__ == "__main__":
    main()
