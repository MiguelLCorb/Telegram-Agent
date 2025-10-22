"""
Test LLM Client Initialization
==============================
Simple test to debug the LLM client initialization issue
"""

import os

print("Testing LLM client initialization...")

# Test OpenAI
try:
    import openai
    print("✅ OpenAI library imported successfully")
    
    # Try to initialize with a dummy key
    client = openai.OpenAI(api_key="test-key")
    print("✅ OpenAI client initialized successfully")
except Exception as e:
    print(f"❌ OpenAI error: {e}")

print()

# Test Anthropic
try:
    import anthropic
    print("✅ Anthropic library imported successfully")
    
    # Try to initialize with a dummy key
    client = anthropic.Anthropic(api_key="test-key")
    print("✅ Anthropic client initialized successfully")
except Exception as e:
    print(f"❌ Anthropic error: {e}")

print()
print("Environment variables that might affect clients:")
for key in os.environ:
    if 'PROXY' in key.upper() or 'HTTP' in key.upper():
        print(f"  {key}: {os.environ[key]}")