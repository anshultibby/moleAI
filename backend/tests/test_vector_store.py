"""Test vector store functionality"""

import pytest
import json
import os
from app.modules.vector_store import SimpleVectorStore, get_vector_store


class TestVectorStore:
    """Test cases for SimpleVectorStore"""
    
    def setup_method(self):
        """Set up test environment"""
        # Create a test vector store instance
        self.vector_store = SimpleVectorStore()
        
        # Clear any existing data for clean tests
        self.vector_store.clear_all()
        
        # Load test scraped content
        test_file = os.path.join(os.path.dirname(__file__), "test_scraped_content.json")
        with open(test_file, 'r') as f:
            self.test_data = json.load(f)
    
    def test_dress_queries(self):
        """Test searching for specific dress queries"""
        # Store the test content
        doc_id = self.vector_store.store(
            url=self.test_data["url"],
            content=self.test_data["raw_content"],
            resource_name=self.test_data["resource_name"]
        )
        
        print(f"✅ Stored content with ID: {doc_id}")
        
        # Test the two specific queries
        queries = [
            "black dress under 100 dollars",
            "cocktail dress under 50 dollars"
        ]
        
        for query in queries:
            print(f"\n🔍 Search Results for '{query}':")
            results = self.vector_store.search(query, n_results=5)
            
            if results:
                for i, result in enumerate(results):
                    print(f"  {i+1}. Resource: {result['resource_name']}")
                    print(f"     URL: {result['url']}")
                    print(f"     Content preview: {result['content']}")
                    print()
                print(f"✅ Found {len(results)} results for '{query}'")
            else:
                print(f"❌ No results found for '{query}'")
            
            # Verify we got results
            assert len(results) > 0, f"No results found for query: {query}"


if __name__ == "__main__":
    # Run tests directly
    test = TestVectorStore()
    test.setup_method()
    
    print("🧪 Running Vector Store Test with Dress Queries...\n")
    
    try:
        test.test_dress_queries()
        
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
