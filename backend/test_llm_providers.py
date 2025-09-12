#!/usr/bin/env python3
"""
Test script for LLM providers to verify they work correctly.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.config import OPENAI_API_KEY, XLM_API_KEY
from app.llm.router import LLMRouter
from app.models.chat import Message


async def test_openai_provider():
    """Test OpenAI provider with a simple message"""
    print("🔵 Testing OpenAI Provider...")
    
    if not OPENAI_API_KEY:
        print("❌ OpenAI API key not found. Skipping OpenAI test.")
        return False
    
    try:
        router = LLMRouter(openai_api_key=OPENAI_API_KEY)
        
        # Test message
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Say hello in one sentence.")
        ]
        
        # Test GPT-5
        print("  Testing gpt-5...")
        response = router.create_completion(
            messages=messages,
            model="gpt-5"
        )
        
        print(f"  ✅ Response ID: {response.id}")
        print(f"  ✅ Model: {response.model}")
        print(f"  ✅ Output items: {len(response.output)}")
        print(f"  ✅ Usage: {response.usage.total_tokens} tokens")
        
        # Print first output content if available
        if response.output:
            first_output = response.output[0]
            if hasattr(first_output, 'content') and first_output.content:
                if isinstance(first_output.content, list) and first_output.content:
                    print(f"  📝 Response: {first_output.content[0].text[:100]}...")
                else:
                    print(f"  📝 Response: {str(first_output.content)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ OpenAI test failed: {e}")
        return False


async def test_xlm_provider():
    """Test XLM provider with a simple message"""
    print("🟡 Testing XLM Provider...")
    
    if not XLM_API_KEY:
        print("❌ XLM API key not found. Skipping XLM test.")
        return False
    
    try:
        router = LLMRouter(xlm_api_key=XLM_API_KEY)
        
        # Test message
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Say hello in one sentence.")
        ]
        
        # Test GLM-4.5v
        print("  Testing glm-4.5v...")
        response = router.create_completion(
            messages=messages,
            model="glm-4.5v"
        )
        
        print(f"  ✅ Response ID: {response.id}")
        print(f"  ✅ Model: {response.model}")
        print(f"  ✅ Output items: {len(response.output)}")
        print(f"  ✅ Usage: {response.usage.total_tokens} tokens")
        
        # Print first output content if available
        if response.output:
            first_output = response.output[0]
            if hasattr(first_output, 'content') and first_output.content:
                if isinstance(first_output.content, list) and first_output.content:
                    print(f"  📝 Response: {first_output.content[0].text[:100]}...")
                else:
                    print(f"  📝 Response: {str(first_output.content)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ XLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_router():
    """Test the router with both providers"""
    print("🔄 Testing LLM Router...")
    
    try:
        router = LLMRouter(
            openai_api_key=OPENAI_API_KEY,
            xlm_api_key=XLM_API_KEY
        )
        
        # Test model support
        print("  Available models:", router.get_all_supported_models())
        print("  Provider info:", router.get_provider_info())
        
        # Test routing
        if OPENAI_API_KEY:
            provider = router.get_provider_for_model("gpt-5")
            print(f"  ✅ gpt-5 routes to: {type(provider).__name__}")
        
        if XLM_API_KEY:
            provider = router.get_provider_for_model("glm-4.5v")
            print(f"  ✅ glm-4.5v routes to: {type(provider).__name__}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Router test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting LLM Provider Tests\n")
    
    results = []
    
    # Test router
    results.append(await test_router())
    print()
    
    # Test OpenAI
    results.append(await test_openai_provider())
    print()
    
    # Test XLM
    results.append(await test_xlm_provider())
    print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("📊 Test Summary:")
    print(f"  Passed: {passed}/{total}")
    
    if passed == total:
        print("  🎉 All tests passed!")
    else:
        print("  ⚠️  Some tests failed. Check the output above.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
