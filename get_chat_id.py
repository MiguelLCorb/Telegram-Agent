"""
Get Telegram Chat ID Helper
============================

This utility script helps you find the Chat ID of a Telegram group or channel
that you want to monitor with the news agent.

To use this script:
1. Make sure you've configured your API credentials in API.txt or agent.py
2. Run this script: python get_chat_id.py
3. The script will list all your recent chats with their IDs
4. Copy the desired Chat ID and use it in your agent configuration
"""

import asyncio
from telethon import TelegramClient
import os

# Load API credentials from the same sources as the main agent
def load_api_credentials():
    """Load API credentials from API.txt or use hardcoded values"""
    
    # Default values (edit these or use API.txt)
    api_id = "TG_API_ID"
    api_hash = "TG_API_HASH"
    
    # Try to load from API.txt file
    api_file = "API.txt"
    if os.path.exists(api_file):
        print("📁 Loading API credentials from API.txt...")
        with open(api_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    key, value = line.split('=', 1)
                    if key == "TELEGRAM_API_ID":
                        api_id = value
                    elif key == "TELEGRAM_API_HASH":
                        api_hash = value
    
    return api_id, api_hash

async def get_chat_ids():
    """Get and display chat IDs from your Telegram account"""
    
    api_id, api_hash = load_api_credentials()
    
    # Validate credentials
    if api_id == "YOUR_API_ID_HERE" or api_hash == "YOUR_API_HASH_HERE":
        print("❌ Please configure your API credentials first!")
        print("Either edit the values in this script or create an API.txt file")
        return
    
    # Initialize Telegram client
    session_name = "get_chat_id_session"
    
    try:
        async with TelegramClient(session_name, int(api_id), api_hash) as client:
            print("🔌 Connected to Telegram")
            print("\n📋 Your recent chats and their IDs:")
            print("=" * 60)
            
            # Get all dialogs (conversations)
            async for dialog in client.iter_dialogs():
                chat_id = dialog.entity.id
                chat_title = dialog.title
                chat_type = type(dialog.entity).__name__
                
                # Format the output
                print(f"ID: {chat_id}")
                print(f"Name: {chat_title}")
                print(f"Type: {chat_type}")
                print("-" * 40)
            
            print("\n💡 Tips:")
            print("• Group IDs are usually negative numbers")
            print("• Channel IDs start with -100")
            print("• Private chat IDs are positive numbers")
            print("• Copy the ID of the group/channel you want to monitor")
            
    except ValueError as e:
        print(f"❌ Error with API credentials: {e}")
    except Exception as e:
        print(f"❌ Error connecting to Telegram: {e}")

def main():
    """Main function"""
    print("🔍 TELEGRAM CHAT ID FINDER")
    print("=" * 40)
    print("This script will show you all your Telegram chats and their IDs")
    print("Use the Chat ID in your news agent configuration")
    print("=" * 40)
    
    # Run the async function
    asyncio.run(get_chat_ids())

if __name__ == "__main__":
    main()