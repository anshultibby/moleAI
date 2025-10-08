"""
Quick test of benchmark script (10 URLs only)
"""
import asyncio
import sys
import os

# Import the main benchmark script
sys.path.insert(0, os.path.dirname(__file__))
from benchmark_extraction_strategies import *

# Override queries for quick test
USER_QUERIES = [
    "black dresses under $100",
    "summer maxi dresses",
]

if __name__ == "__main__":
    print("🔥 Running QUICK benchmark (10 URLs)...")
    asyncio.run(main())
