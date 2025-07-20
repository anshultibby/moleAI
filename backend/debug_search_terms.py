"""
Debug specific search terms that are returning 0 results
"""

import os
from dotenv import load_dotenv
from app.utils.exa_service import ExaService
from app.utils.hybrid_search_service import HybridSearchService

# Load environment variables
load_dotenv()

def test_search_terms():
    """Test various search terms to understand the issue"""
    
    exa_service = ExaService()
    hybrid_service = HybridSearchService()
    
    # Test cases from your logs that returned 0 results
    failing_terms = [
        "metal office cabinet green",
        "office cabinet",
        "green cabinet"
    ]
    
    # Working terms for comparison
    working_terms = [
        "headphones",
        "laptop",
        "bluetooth speaker",
        "furniture",
        "office furniture"
    ]
    
    print("🔍 Testing Failing Search Terms:")
    print("=" * 50)
    
    for term in failing_terms:
        print(f"\n🔎 Testing: '{term}'")
        
        # Test direct Exa search
        try:
            exa_results = exa_service.search(term, num_results=5)
            print(f"  Exa results: {len(exa_results)}")
            if exa_results:
                for i, result in enumerate(exa_results[:2]):
                    print(f"    {i+1}. {result.title}")
                    print(f"       {result.url}")
        except Exception as e:
            print(f"  ❌ Exa error: {e}")
        
        # Test hybrid search
        try:
            hybrid_results = hybrid_service.search_products(
                term, 
                num_results=5, 
                extract_content=False  # Skip content extraction for speed
            )
            print(f"  Hybrid results: {len(hybrid_results)}")
        except Exception as e:
            print(f"  ❌ Hybrid error: {e}")
    
    print("\n\n✅ Testing Working Search Terms:")
    print("=" * 50)
    
    for term in working_terms:
        print(f"\n🔎 Testing: '{term}'")
        
        try:
            exa_results = exa_service.search(term, num_results=3)
            print(f"  Exa results: {len(exa_results)}")
            if exa_results:
                print(f"    Sample: {exa_results[0].title}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_search_strategies():
    """Test different search strategies for problematic terms"""
    
    exa_service = ExaService()
    problem_query = "metal office cabinet green"
    
    print("\n🧪 Testing Search Strategies:")
    print("=" * 50)
    
    strategies = [
        ("Original", problem_query),
        ("Broader", "office cabinet"),
        ("Generic", "cabinet furniture"),
        ("Shopping focused", "buy office cabinet"),
        ("Brand focused", "office cabinet steelcase herman miller"),
        ("Material focused", "metal cabinet office furniture"),
        ("E-commerce", "office cabinet amazon target"),
        ("Alternative wording", "office storage cabinet"),
        ("Color separate", "green office furniture cabinet")
    ]
    
    for strategy_name, query in strategies:
        print(f"\n🔎 {strategy_name}: '{query}'")
        try:
            results = exa_service.search(query, num_results=3)
            print(f"  Results: {len(results)}")
            if results:
                print(f"  Top result: {results[0].title}")
                print(f"  URL: {results[0].url}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_exa_parameters():
    """Test different Exa search parameters"""
    
    exa_service = ExaService()
    query = "office cabinet"
    
    print("\n⚙️ Testing Exa Parameters:")
    print("=" * 50)
    
    parameter_tests = [
        ("Default", {}),
        ("Neural search", {"type": "neural"}),
        ("Keyword search", {"type": "keyword"}),
        ("With autoprompt", {"use_autoprompt": True}),
        ("Without autoprompt", {"use_autoprompt": False}),
        ("E-commerce domains", {"include_domains": ["amazon.com", "target.com", "walmart.com", "homedepot.com"]}),
        ("More results", {"num_results": 20}),
    ]
    
    for test_name, params in parameter_tests:
        print(f"\n🔧 {test_name}: {params}")
        try:
            results = exa_service.search(query, **params)
            print(f"  Results: {len(results)}")
            if results:
                print(f"  Sample: {results[0].title[:60]}...")
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    print("🐛 Debugging Search Term Issues")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('EXA_API_KEY')
    if not api_key:
        print("❌ No EXA_API_KEY found in environment!")
        exit(1)
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        test_search_terms()
        test_search_strategies()
        test_exa_parameters()
        
        print("\n" + "=" * 60)
        print("🎯 RECOMMENDATIONS:")
        print("1. If specific terms fail, use broader terms")
        print("2. Try different search strategies")
        print("3. Use include_domains for better e-commerce results")
        print("4. Consider using autoprompt=True for better results")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 