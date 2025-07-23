#!/usr/bin/env python3
"""
Run the agent example from the backend directory
This ensures all imports work correctly
"""

from app.modules.example_usage import demo_conversation

if __name__ == "__main__":
    print("🤖 Running Agent Example from backend directory")
    print("="*50)
    demo_conversation() 