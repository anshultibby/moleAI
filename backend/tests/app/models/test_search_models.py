#!/usr/bin/env python3
"""
Tests for app.models.search_models module

This module tests the Pydantic models for structured search results including:
- JinaSearchResponse model validation
- SearchSummary functionality
- Data parsing and validation
- Model serialization/deserialization
"""

import os
import json
import pytest
from datetime import datetime
from typing import Dict, Any

from app.models.search_models import (
    JinaSearchResponse, 
    SearchSummary, 
    load_search_response_from_file,
    parse_search_response,
    TokenUsage,
    SearchMetadata,
    SearchResult
)


class TestSearchModels:
    """Test cases for search data models"""
    
    def test_token_usage_model(self):
        """Test TokenUsage model validation"""
        # Valid token usage
        usage = TokenUsage(tokens=1000)
        assert usage.tokens == 1000
        
        # Test serialization
        usage_dict = usage.model_dump()
        assert usage_dict == {"tokens": 1000}
        
        # Test deserialization
        usage_from_dict = TokenUsage(**usage_dict)
        assert usage_from_dict.tokens == 1000
    
    def test_search_metadata_model(self):
        """Test SearchMetadata model validation"""
        metadata = SearchMetadata(
            provider="google",
            type="web",
            num_results=3,
            country="us",
            language="en",
            read_content=True,
            with_links_summary=True,
            with_images_summary=True,
            with_generated_alt=True,
            respond_with="markdown",
            jina_status="success",
            jina_code=200
        )
        
        assert metadata.provider == "google"
        assert metadata.num_results == 3
        assert metadata.read_content is True
        
        # Test serialization
        metadata_dict = metadata.model_dump()
        assert "provider" in metadata_dict
        assert "jina_code" in metadata_dict
    
    def test_search_result_model(self):
        """Test SearchResult model validation"""
        result = SearchResult(
            title="Test Product",
            url="https://example.com/product",
            content="Product description content",
            usage=TokenUsage(tokens=500)
        )
        
        assert result.title == "Test Product"
        assert result.url == "https://example.com/product"
        assert result.usage.tokens == 500
        
        # Test optional fields
        result_minimal = SearchResult(
            title="Minimal Product",
            url="https://example.com/minimal"
        )
        assert result_minimal.content is None
        assert result_minimal.usage is None
    
    def test_jina_search_response_model(self):
        """Test complete JinaSearchResponse model"""
        # Create a complete response
        metadata = SearchMetadata(
            provider="google",
            type="web", 
            num_results=2,
            country="us",
            language="en",
            read_content=False,
            with_links_summary=True,
            with_images_summary=True,
            with_generated_alt=True,
            respond_with="content",
            jina_status="success",
            jina_code=200
        )
        
        results = [
            SearchResult(
                title="Product 1",
                url="https://example.com/1",
                content="Content 1",
                usage=TokenUsage(tokens=100)
            ),
            SearchResult(
                title="Product 2", 
                url="https://example.com/2",
                content="Content 2",
                usage=TokenUsage(tokens=200)
            )
        ]
        
        response = JinaSearchResponse(
            query="test query",
            results=results,
            metadata=metadata,
            raw_response={"status": "success", "data": "test"}
        )
        
        assert response.query == "test query"
        assert len(response.results) == 2
        assert response.metadata.provider == "google"
        assert "status" in response.raw_response
        
        # Test computed properties
        total_tokens = sum(r.usage.tokens for r in response.results if r.usage)
        assert total_tokens == 300
    
    def test_search_summary_functionality(self):
        """Test SearchSummary utility functions"""
        # Create test data
        metadata = SearchMetadata(
            provider="google",
            type="web",
            num_results=2,
            country="us", 
            language="en",
            read_content=True,
            with_links_summary=True,
            with_images_summary=True,
            with_generated_alt=True,
            respond_with="markdown",
            jina_status="success",
            jina_code=200
        )
        
        results = [
            SearchResult(
                title="Product 1",
                url="https://example.com/1",
                content="A" * 1000,  # 1000 chars
                usage=TokenUsage(tokens=100)
            ),
            SearchResult(
                title="Product 2",
                url="https://example.com/2", 
                content="B" * 2000,  # 2000 chars
                usage=TokenUsage(tokens=200)
            )
        ]
        
        response = JinaSearchResponse(
            query="test query",
            results=results,
            metadata=metadata,
            raw_response={"meta": {"usage": {"tokens": 300}}}
        )
        
        summary = SearchSummary.from_response(response)
        
        assert summary.query == "test query"
        assert summary.total_results == 2
        assert summary.total_tokens == 300  # From raw_response meta
        assert summary.total_content_length == 3000  # 1000 + 2000
        assert summary.provider == "google"
        assert summary.has_content is True
    
    @pytest.mark.skipif(
        not os.path.exists("search_results_comprehensive_20250907_013425.json"),
        reason="Test data file not found"
    )
    def test_load_real_search_data(self):
        """Test loading and parsing real search results"""
        try:
            response = load_search_response_from_file("search_results_comprehensive_20250907_013425.json")
            
            # Validate the loaded response
            assert isinstance(response, JinaSearchResponse)
            assert response.query is not None
            assert len(response.results) > 0
            assert response.metadata is not None
            
            # Test summary generation
            summary = SearchSummary.from_response(response)
            assert summary.total_results > 0
            assert summary.total_tokens > 0
            
            print(f"✅ Successfully loaded real data:")
            print(f"   Query: {summary.query}")
            print(f"   Results: {summary.total_results}")
            print(f"   Tokens: {summary.total_tokens}")
            print(f"   Content length: {summary.total_content_length:,} chars")
            
        except Exception as e:
            pytest.fail(f"Failed to load real search data: {e}")


def test_model_validation_errors():
    """Test that models properly validate input data"""
    # Test invalid token usage
    with pytest.raises(ValueError):
        TokenUsage(tokens=-1)  # Negative tokens should be invalid
    
    # Test invalid metadata
    with pytest.raises(ValueError):
        SearchMetadata(
            provider="google",
            type="web",
            num_results=-1,  # Negative results should be invalid
            country="us",
            language="en"
        )


def test_model_serialization():
    """Test model serialization and deserialization"""
    # Create a complete response
    metadata = SearchMetadata(
        provider="google",
        type="web",
        num_results=1,
        country="us",
        language="en",
        read_content=False,
        with_links_summary=True,
        with_images_summary=True, 
        with_generated_alt=True,
        respond_with="content",
        jina_status="success",
        jina_code=200
    )
    
    result = SearchResult(
        title="Test Product",
        url="https://example.com/test",
        content="Test content",
        usage=TokenUsage(tokens=50)
    )
    
    response = JinaSearchResponse(
        query="test",
        results=[result],
        metadata=metadata,
        raw_response={"test": "data"}
    )
    
    # Serialize to dict
    response_dict = response.model_dump()
    
    # Deserialize back to model
    response_restored = JinaSearchResponse(**response_dict)
    
    # Verify data integrity
    assert response_restored.query == response.query
    assert len(response_restored.results) == len(response.results)
    assert response_restored.results[0].title == response.results[0].title
    assert response_restored.metadata.provider == response.metadata.provider


if __name__ == "__main__":
    # Run basic tests
    test_model_validation_errors()
    test_model_serialization()
    
    print("✅ All search model tests passed!")
