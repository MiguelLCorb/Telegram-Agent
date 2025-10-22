"""
Test script for the Simple LLM Processor
========================================

Tests the new direct API approach to ensure it works without proxy errors.
"""

import sys
import os

# Add current directory to path so we can import our modules
sys.path.insert(0, os.getcwd())

from simple_llm_processor import SimpleLLMProcessor

def test_llm_processor():
    """Test the LLM processor with direct API calls"""
    
    print("🧪 Testing Simple LLM Processor...")
    print("=" * 50)
    
    # Initialize processor
    processor = SimpleLLMProcessor()
    
    # Load API keys (using the same keys from agent)
    openai_key = "YOUR_OPENAI_API_KEY"
    anthropic_key = "YOUR_ANTHROPIC_API_KEY"
    
    success = processor.load_api_keys_direct(
        openai_key=openai_key,
        anthropic_key=anthropic_key,
        provider_preference="auto"
    )
    
    if not success:
        print("❌ Failed to initialize LLM processor")
        return False
    
    print(f"✅ LLM processor initialized with {processor.provider}")
    print(f"🔧 Available: {processor.is_available()}")
    
    # Test message summarization
    print("\n📝 Testing message summarization...")
    test_message = "Hey everyone! Just found this amazing article about the new AI developments in 2024. The research shows that AI models are becoming much more efficient and can now run on smaller devices. This could revolutionize mobile computing!"
    
    try:
        result = processor.summarize_message(test_message, "TestUser")
        print("✅ Message summarization test completed")
        print(f"📊 Summary: {result.get('summary', 'N/A')}")
        print(f"😊 Sentiment: {result.get('sentiment', 'N/A')}")
        print(f"🏷️  Topics: {result.get('topics', [])}")
        print(f"⚡ Enhanced by LLM: {result.get('enhanced_by_llm', False)}")
        
        if result.get('enhanced_by_llm'):
            print("🎉 LLM enhancement working correctly!")
            return True
        else:
            print("⚠️  LLM enhancement not working, using fallback")
            return False
            
    except Exception as e:
        print(f"❌ Error in message summarization: {e}")
        return False

def test_timestamp_tracker():
    """Test the timestamp tracking functionality"""
    
    print("\n⏰ Testing Timestamp Tracker...")
    print("=" * 50)
    
    from timestamp_tracker import TimestampTracker
    from datetime import datetime, timezone, timedelta
    
    # Initialize tracker
    tracker = TimestampTracker("test_data")
    
    # Test basic operations
    print("📅 Testing basic timestamp operations...")
    
    # Check initial state
    last_check = tracker.get_last_check_timestamp(12345)
    print(f"Initial last check: {last_check}")
    
    # Update timestamp
    test_time = datetime.now(timezone.utc)
    tracker.update_last_check_timestamp(12345, test_time)
    
    # Check if it was saved
    retrieved_time = tracker.get_last_check_timestamp(12345)
    print(f"Retrieved timestamp: {retrieved_time}")
    
    # Test message processing logic
    old_message_time = test_time - timedelta(minutes=10)
    new_message_time = test_time + timedelta(minutes=10)
    
    should_process_old = tracker.should_process_message(old_message_time, 12345)
    should_process_new = tracker.should_process_message(new_message_time, 12345)
    
    print(f"Should process old message: {should_process_old}")
    print(f"Should process new message: {should_process_new}")
    
    # Get summary
    summary = tracker.get_summary()
    print(f"Timestamp summary: {summary}")
    
    # Clean up test data
    import shutil
    if os.path.exists("test_data"):
        shutil.rmtree("test_data")
    
    if not should_process_old and should_process_new:
        print("✅ Timestamp tracking working correctly!")
        return True
    else:
        print("❌ Timestamp tracking not working as expected")
        return False

if __name__ == "__main__":
    print("🔍 Running Enhanced Agent Tests...")
    print("=" * 60)
    
    llm_success = test_llm_processor()
    timestamp_success = test_timestamp_tracker()
    
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print(f"🤖 LLM Processor: {'✅ PASS' if llm_success else '❌ FAIL'}")
    print(f"⏰ Timestamp Tracker: {'✅ PASS' if timestamp_success else '❌ FAIL'}")
    
    if llm_success and timestamp_success:
        print("\n🎉 All tests passed! Enhanced agent ready to run.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
    
    print("=" * 60)