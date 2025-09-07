"""
Pytest configuration for moleAI backend tests

This file contains shared fixtures and configuration for all tests.
"""

import os
import sys
import pytest
from pathlib import Path

# Add the backend directory to Python path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables for tests
from dotenv import load_dotenv
load_dotenv()


@pytest.fixture(scope="session")
def api_keys():
    """Fixture to provide API keys for tests"""
    return {
        "jina_ai": os.getenv("JINA_AI_API_KEY"),
        "serper_dev": os.getenv("SERPER_DEV_API_KEY")  # Legacy, if still present
    }


@pytest.fixture(scope="session") 
def test_data_dir():
    """Fixture to provide test data directory path"""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_search_query():
    """Fixture providing a standard test search query"""
    return "black boots for women"


@pytest.fixture
def sample_search_results():
    """Fixture providing sample search results for testing"""
    return {
        "query": "test query",
        "results": [
            {
                "title": "Test Product 1",
                "url": "https://example.com/1",
                "content": "Test content 1",
                "usage": {"tokens": 100}
            },
            {
                "title": "Test Product 2", 
                "url": "https://example.com/2",
                "content": "Test content 2",
                "usage": {"tokens": 150}
            }
        ],
        "metadata": {
            "provider": "google",
            "type": "web",
            "num_results": 2,
            "country": "us",
            "language": "en",
            "read_content": False,
            "with_links_summary": True,
            "with_images_summary": True,
            "with_generated_alt": True,
            "respond_with": "content",
            "jina_status": "success",
            "jina_code": 200,
            "jina_meta": {"usage": {"tokens": 250}}
        },
        "raw_response": {
            "status": "success",
            "code": 200,
            "data": "test data",
            "meta": {"usage": {"tokens": 250}}
        }
    }


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring API keys"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Mark integration tests
        if "integration" in item.name or "api" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests
        if "comprehensive" in item.name or "large" in item.name:
            item.add_marker(pytest.mark.slow)
