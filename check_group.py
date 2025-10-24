"""
Quick Telegram Group Checker
=============================

This script connects to Telegram and looks for the MCP_TEST_GROUP
to provide a summary of recent messages.
"""

import asyncio
from telethon import TelegramClient
import json
import os
from datetime import datetime, timedelta

# Use the same API credentials from your MCP configuration
API_ID = "_"
API_HASH = "_"
SESSION_NAME = "mcp_check_session"

async def find_and_summarize_group():
    """Find MCP_TEST_GROUP and provide a summary"""
    
    try:
        async with TelegramClient(SESSION_NAME, int(API_ID), API_HASH) as client:
            print("🔌 Connected to Telegram")
            
            # Find the MCP_TEST_GROUP
            target_group = None
            print("🔍 Looking for MCP_TEST_GROUP...")
            
            async for dialog in client.iter_dialogs():
                username = getattr(dialog.entity, 'username', None) or ""
                if "MCP_TEST_GROUP" in dialog.title or "MCP_TEST_GROUP" in str(username):
                    target_group = dialog
                    break
            
            if not target_group:
                print("❌ MCP_TEST_GROUP not found in your dialogs")
                print("\n📋 Available groups/chats:")
                async for dialog in client.iter_dialogs(limit=10):
                    print(f"  - {dialog.title} (ID: {dialog.entity.id})")
                return
            
            print(f"✅ Found group: {target_group.title}")
            print(f"   Group ID: {target_group.entity.id}")
            print(f"   Type: {type(target_group.entity).__name__}")
            
            # Get recent messages (last 24 hours)
            print("\n📰 Recent messages summary:")
            print("=" * 50)
            
            message_count = 0
            url_count = 0
            recent_urls = []
            participants = set()
            
            # Get messages from last 24 hours  
            since = datetime.now()
            
            async for message in client.iter_messages(target_group.entity, limit=50):
                # Calculate hours difference instead of direct comparison
                hours_diff = (since - message.date.replace(tzinfo=None)).total_seconds() / 3600
                if hours_diff > 24:
                    break
                    
                message_count += 1
                
                # Track participants
                if message.sender:
                    if hasattr(message.sender, 'first_name'):
                        name = f"{message.sender.first_name or ''} {message.sender.last_name or ''}".strip()
                    elif hasattr(message.sender, 'title'):
                        name = message.sender.title
                    else:
                        name = str(message.sender_id)
                    participants.add(name)
                
                # Check for URLs
                if message.message:
                    words = message.message.split()
                    urls_in_message = [word for word in words if word.startswith(('http://', 'https://'))]
                    if urls_in_message:
                        url_count += len(urls_in_message)
                        for url in urls_in_message:
                            recent_urls.append({
                                'url': url,
                                'sender': name if 'name' in locals() else 'Unknown',
                                'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                                'message_preview': message.message[:100] + '...' if len(message.message) > 100 else message.message
                            })
            
            # Display summary
            print(f"📊 Messages in last 24 hours: {message_count}")
            print(f"🔗 URLs shared: {url_count}")
            print(f"👥 Active participants: {len(participants)}")
            
            if participants:
                print(f"\n👤 Participants:")
                for participant in sorted(participants):
                    print(f"  - {participant}")
            
            if recent_urls:
                print(f"\n🔗 Recent URLs shared:")
                for i, url_info in enumerate(recent_urls[-5:], 1):  # Show last 5 URLs
                    print(f"\n  {i}. {url_info['url']}")
                    print(f"     Shared by: {url_info['sender']}")
                    print(f"     Date: {url_info['date']}")
                    print(f"     Message: {url_info['message_preview']}")
            
            # Get some recent messages for context
            print(f"\n💬 Recent messages:")
            print("-" * 30)
            
            async for message in client.iter_messages(target_group.entity, limit=5):
                if message.message:
                    sender_name = "Unknown"
                    if message.sender:
                        if hasattr(message.sender, 'first_name'):
                            sender_name = f"{message.sender.first_name or ''} {message.sender.last_name or ''}".strip()
                        elif hasattr(message.sender, 'title'):
                            sender_name = message.sender.title
                    
                    date_str = message.date.strftime('%Y-%m-%d %H:%M')
                    message_preview = message.message[:100] + '...' if len(message.message) > 100 else message.message
                    print(f"[{date_str}] {sender_name}: {message_preview}")
            
    except Exception as e:
        print(f"❌ Error accessing Telegram: {e}")

def main():
    print("🤖 TELEGRAM GROUP CHECKER")
    print("=" * 40)
    print("Connecting to check MCP_TEST_GROUP...")
    
    asyncio.run(find_and_summarize_group())

if __name__ == "__main__":

    main()
