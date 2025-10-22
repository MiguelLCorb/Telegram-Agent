"""
Enhanced Telegram News Agent with Timestamp Tracking
===================================================

A Telegram bot that monitors groups for news URLs and messages,
extracts article content, and analyzes messages using AI.
Now includes timestamp tracking to process only new messages since last check.

Features:
- Monitors Telegram groups/channels for new messages since last check
- Extracts and analyzes article content from URLs
- Uses LLM (OpenAI/Anthropic) for enhanced content analysis
- Saves articles as JSON and ODT documents
- Processes both URLs and text messages
- Tracks timestamps to avoid processing old messages

Dependencies: telethon, beautifulsoup4, requests, openai, anthropic
"""

import os
import json
import asyncio
import re
from datetime import datetime, timezone
from telethon import TelegramClient, events
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

# Import our modules
from simple_llm_processor import SimpleLLMProcessor
from odt_writer import create_odt_document
from timestamp_tracker import TimestampTracker

# ============================================================================
# CONFIGURATION SECTION
# ============================================================================

# Telegram API Credentials
TELEGRAM_API_ID = "TELEGRAM_API_ID_PLACEHOLDER"
TELEGRAM_API_HASH = "TELEGRAM_API_HASH_PLACEHOLDER"
TELEGRAM_SESSION = "news_agent_session"
TELEGRAM_CHAT_ID = "me"  # Use "me" for Saved Messages, or specific chat ID like "4871136090"

# LLM API Credentials
OPENAI_API_KEY = "OPENAI_API_KEY_PLACEHOLDER"
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY_HERE"  # Invalid key, will be ignored
LLM_PROVIDER = "openai"  # Use OpenAI since it works

# File paths
PUBLICATIONS_DIR = "publications"
DATA_DIR = "data"
JSON_FILE = os.path.join(PUBLICATIONS_DIR, "news_database.json")

# Initialize modules
llm_processor = SimpleLLMProcessor()
timestamp_tracker = TimestampTracker(DATA_DIR)

def load_api_credentials():
    """Load API credentials from API.txt file if it exists"""
    api_file = "API.txt"
    if os.path.exists(api_file):
        print("📁 Loading API credentials from API.txt...")
        with open(api_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    if key == "TELEGRAM_API_ID":
                        global TELEGRAM_API_ID
                        TELEGRAM_API_ID = value
                    elif key == "TELEGRAM_API_HASH":
                        global TELEGRAM_API_HASH
                        TELEGRAM_API_HASH = value
                    elif key == "TELEGRAM_CHAT_ID":
                        global TELEGRAM_CHAT_ID
                        TELEGRAM_CHAT_ID = value
                    elif key == "OPENAI_API_KEY" and value != "YOUR_OPENAI_API_KEY_HERE":
                        global OPENAI_API_KEY
                        OPENAI_API_KEY = value
                    elif key == "ANTHROPIC_API_KEY" and value != "YOUR_ANTHROPIC_API_KEY_HERE":
                        global ANTHROPIC_API_KEY
                        ANTHROPIC_API_KEY = value
                    elif key == "LLM_PROVIDER":
                        global LLM_PROVIDER
                        LLM_PROVIDER = value
        print("✅ API credentials loaded successfully")
    else:
        print("⚠️  API.txt not found, using hardcoded values")

def ensure_directories():
    """Create necessary directories if they don't exist"""
    for directory in [PUBLICATIONS_DIR, DATA_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created directory: {directory}")

def load_existing_publications():
    """Load existing publications from JSON file"""
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print("⚠️  Error loading existing publications, starting fresh")
            return []
    return []

def save_publications(publications_list):
    """Save publications list to JSON file"""
    try:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(publications_list, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error saving publications: {e}")
        return False

def extract_urls_from_text(text):
    """Extract URLs from text message"""
    if not text:
        return []
    
    # More comprehensive URL pattern
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
    urls = re.findall(url_pattern, text)
    
    # Debug output
    if urls:
        print(f"🔗 Found URLs: {urls}")
    else:
        print(f"🔍 No URLs detected in text: {text[:100]}...")
    
    return urls

def extract_article_content(url):
    """Extract article content from URL using web scraping"""
    try:
        print(f"🌐 Fetching: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic article data
        title = None
        summary = None
        author = None
        image = None
        
        # Try multiple selectors for title
        title_selectors = ['h1', 'title', '.title', '.headline', 'h1.title']
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                title = element.get_text(strip=True)
                break
        
        # Try to find meta description for summary
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            summary = meta_desc.get('content', '')
        
        # Try to find author
        author_selectors = [
            'meta[name="author"]',
            '.author',
            '.byline',
            '[rel="author"]'
        ]
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    author = element.get('content', '')
                else:
                    author = element.get_text(strip=True)
                if author:
                    break
        
        # Try to find main image
        image_selectors = [
            'meta[property="og:image"]',
            'meta[name="twitter:image"]',
            '.featured-image img',
            'article img',
            '.content img'
        ]
        for selector in image_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    image = element.get('content', '')
                else:
                    image = element.get('src', '')
                if image:
                    # Make relative URLs absolute
                    if image.startswith('//'):
                        image = 'https:' + image
                    elif image.startswith('/'):
                        parsed_url = urlparse(url)
                        image = f"{parsed_url.scheme}://{parsed_url.netloc}{image}"
                    break
        
        # Basic extracted data
        article_data = {
            'url': url,
            'title': title or 'Unknown Title',
            'summary': summary or 'No summary available',
            'author': author or 'Unknown Author',
            'image': image,
            'extracted_at': datetime.now(timezone.utc).isoformat(),
            'extraction_method': 'web_scraping'
        }
        
        # Enhance with LLM if available
        if llm_processor.is_available():
            article_data = llm_processor.enhance_article_extraction(
                url, response.text, article_data
            )
        else:
            article_data['enhanced_by_llm'] = False
        
        return article_data
        
    except Exception as e:
        print(f"❌ Error extracting content from {url}: {e}")
        return {
            'url': url,
            'title': f'Failed to extract: {url}',
            'summary': f'Error occurred: {str(e)}',
            'author': 'Unknown',
            'image': None,
            'extracted_at': datetime.now(timezone.utc).isoformat(),
            'extraction_method': 'error',
            'enhanced_by_llm': False
        }

def process_urls_in_message(message_text, sender_name="Unknown"):
    """Process all URLs found in a message"""
    urls = extract_urls_from_text(message_text)
    
    if not urls:
        return []
    
    print(f"🔗 Found {len(urls)} URL(s) in message from {sender_name}")
    
    articles = []
    for url in urls:
        try:
            article_data = extract_article_content(url)
            if article_data:
                article_data['sender'] = sender_name
                articles.append(article_data)
                print(f"✅ Processed: {article_data['title']}")
        except Exception as e:
            print(f"❌ Error processing URL {url}: {e}")
    
    return articles

def process_message_content(message_text, sender_name="Unknown"):
    """Process message content for analysis"""
    if not message_text.strip():
        return None
    
    print(f"💬 Analyzing message content from {sender_name}")
    
    # Always analyze message content, regardless of URLs
    if llm_processor.is_available():
        return llm_processor.summarize_message(message_text, sender_name)
    else:
        # Basic analysis without LLM
        return {
            'summary': message_text[:100] + '...' if len(message_text) > 100 else message_text,
            'sentiment': 'neutral',
            'topics': [],
            'importance': 'medium',
            'message_type': 'text',
            'enhanced_by_llm': False,
            'original_message': message_text,
            'sender': sender_name,
            'analyzed_at': datetime.now(timezone.utc).isoformat()
        }

async def handle_new_message(event):
    """Handle new messages from Telegram"""
    try:
        message = event.message
        sender = await message.get_sender()
        sender_name = getattr(sender, 'first_name', 'Unknown')
        message_text = message.text or ""
        message_date = message.date
        
        # Ensure message date is timezone-aware
        if message_date.tzinfo is None:
            message_date = message_date.replace(tzinfo=timezone.utc)
        
        print(f"\n📨 New message from {sender_name} at {message_date}")
        print(f"💬 Content: {message_text[:100]}...")
        
        # Get the proper tracking ID
        tracking_chat_id = "me" if str(TELEGRAM_CHAT_ID).lower() == "me" else str(TELEGRAM_CHAT_ID)
        
        # Check if we should process this message based on timestamp
        if not timestamp_tracker.should_process_message(message_date, tracking_chat_id):
            print(f"⏭️  Skipping old message (before last check)")
            return
        
        # Load existing publications
        publications = load_existing_publications()
        new_items_added = False
        
        # Process URLs in the message
        print(f"🔍 Checking for URLs in message...")
        articles = process_urls_in_message(message_text, sender_name)
        
        if articles:
            print(f"📰 Found {len(articles)} articles to process")
            for article in articles:
                publications.append(article)
                new_items_added = True
                
                # Create ODT document for the article
                odt_filename = f"article_{len(publications)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.odt"
                odt_path = os.path.join(PUBLICATIONS_DIR, odt_filename)
                
                try:
                    if create_odt_document(article, odt_path):
                        article['odt_file'] = odt_filename
                        print(f"📄 ODT document created: {odt_filename}")
                except Exception as e:
                    print(f"⚠️  Error creating ODT: {e}")
        else:
            print(f"🔍 No URLs found in message")
        
        # Process message content (if it's not just URLs)
        message_analysis = process_message_content(message_text, sender_name)
        if message_analysis:
            message_analysis['message_date'] = message_date.isoformat()
            message_analysis['chat_id'] = tracking_chat_id
            publications.append(message_analysis)
            new_items_added = True
            print(f"💡 Message analysis completed")
        
        # Save updated publications if new items were added
        if new_items_added:
            if save_publications(publications):
                print(f"💾 Publications saved (total: {len(publications)})")
        
        # Update timestamp for this message
        timestamp_tracker.update_last_check_timestamp(tracking_chat_id, message_date)
        
    except Exception as e:
        print(f"❌ Error handling message: {e}")

async def find_chat_entity(client, chat_id):
    """Find the correct chat entity for the given chat ID"""
    
    # Handle "me" case for Saved Messages
    if str(chat_id).lower() == "me":
        try:
            entity = await client.get_me()
            print(f"✅ Using Saved Messages (me): {entity.first_name}")
            return entity
        except Exception as e:
            print(f"❌ Error getting 'me' entity: {e}")
            return None
    
    try:
        # First try to get entity directly
        entity = await client.get_entity(int(chat_id))
        print(f"✅ Found chat entity: {entity}")
        return entity
    except Exception as e:
        print(f"⚠️  Direct entity lookup failed: {e}")
        
        # Try to find in dialogs
        print("🔍 Searching through dialogs...")
        async for dialog in client.iter_dialogs():
            if dialog.id == int(chat_id) or dialog.entity.id == int(chat_id):
                print(f"✅ Found chat in dialogs: {dialog.name} (ID: {dialog.id})")
                return dialog.entity
        
        # If not found, list available chats for debugging
        print("📋 Available chats (first 10):")
        count = 0
        async for dialog in client.iter_dialogs(limit=10):
            chat_type = type(dialog.entity).__name__
            chat_name = getattr(dialog.entity, 'title', getattr(dialog.entity, 'first_name', 'Unknown'))
            print(f"   - {chat_name}: {dialog.id} (Type: {chat_type})")
            count += 1
        
        if count == 0:
            print("   No dialogs found")
        else:
            print(f"💡 Found {count} chats. Use get_chat_id.py to see all available chats.")
        
        return None

async def process_recent_messages(client, chat_id, limit=100):
    """Process ALL recent messages since last check"""
    print(f"📋 Checking for messages since last check...")
    
    # Get the proper tracking ID first
    tracking_chat_id = "me" if str(chat_id).lower() == "me" else str(chat_id)
    last_check = timestamp_tracker.get_last_check_timestamp(tracking_chat_id)
    print(f"📅 Last check: {timestamp_tracker.get_formatted_last_check(tracking_chat_id)}")
    
    processed_count = 0
    messages_to_process = []
    
    try:
        # Find the correct chat entity
        entity = await find_chat_entity(client, chat_id)
        if not entity:
            print(f"❌ Could not find chat entity for ID: {chat_id}")
            return
        
        # Collect ALL messages since last check (in reverse chronological order)
        print(f"🔍 Scanning messages (limit: {limit})...")
        async for message in client.iter_messages(entity, limit=limit):
            message_date = message.date
            if message_date.tzinfo is None:
                message_date = message_date.replace(tzinfo=timezone.utc)
            
            # Check if this message should be processed
            if timestamp_tracker.should_process_message(message_date, tracking_chat_id):
                messages_to_process.append(message)
                print(f"📝 Found new message from {message_date}: {(message.text or '')[:50]}...")
            else:
                # We've reached messages older than last check, but don't break
                # Continue checking in case there are newer messages mixed in
                pass
        
        # Process messages in chronological order (oldest first)
        messages_to_process.reverse()
        
        print(f"📊 Processing {len(messages_to_process)} new messages...")
        
        for message in messages_to_process:
            try:
                # Create a mock event for processing
                class MockEvent:
                    def __init__(self, msg):
                        self.message = msg
                
                await handle_new_message(MockEvent(message))
                processed_count += 1
                print(f"✅ Processed message {processed_count}/{len(messages_to_process)}")
                
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                continue
    
    except Exception as e:
        print(f"❌ Error processing recent messages: {e}")
        print(f"💡 Try running get_chat_id.py to verify your chat ID is correct")
    
    print(f"🎉 Finished! Processed {processed_count} new messages")
    
    # Update global timestamp to now (only if we successfully processed messages)
    if processed_count >= 0:  # Update even if 0 messages to mark that we checked
        timestamp_tracker.update_last_check_timestamp(tracking_chat_id)

async def main():
    """Main function to run the Telegram news agent"""
    print("🚀 Starting Enhanced Telegram News Agent with Timestamp Tracking...")
    print("=" * 60)
    
    # Load configuration
    load_api_credentials()
    ensure_directories()
    
    # Initialize LLM processor
    llm_available = llm_processor.load_api_keys_direct(
        openai_key=OPENAI_API_KEY,
        anthropic_key=ANTHROPIC_API_KEY,
        provider_preference=LLM_PROVIDER
    )
    
    if llm_available:
        print("🤖 LLM processor initialized successfully")
    else:
        print("⚠️  LLM processor not available - using basic extraction only")
    
    # Show timestamp summary
    print("\n📅 Timestamp Tracking Summary:")
    summary = timestamp_tracker.get_summary()
    if summary:
        for key, info in summary.items():
            chat_display = "Saved Messages" if key == "me" else f"Chat {key}"
            print(f"   {chat_display}: {info['last_check']}")
    else:
        print("   No previous checks recorded")
    
    # Initialize Telegram client
    print(f"\n📱 Connecting to Telegram...")
    print(f"📊 Monitoring chat: {TELEGRAM_CHAT_ID}")
    
    client = TelegramClient(TELEGRAM_SESSION, TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    try:
        await client.start()
        print("✅ Connected to Telegram successfully!")
        
        # Find the chat entity first
        chat_entity = await find_chat_entity(client, TELEGRAM_CHAT_ID)
        if not chat_entity:
            print(f"❌ Cannot monitor chat ID {TELEGRAM_CHAT_ID} - not found!")
            print("💡 Please run get_chat_id.py to find the correct chat ID")
            return
        
        # Process recent messages since last check (increased limit to catch more messages)
        await process_recent_messages(client, TELEGRAM_CHAT_ID, limit=200)
        
        # Set up event handler for new messages
        @client.on(events.NewMessage(chats=[chat_entity]))
        async def message_handler(event):
            await handle_new_message(event)
        
        print(f"\n👂 Listening for new messages...")
        print("Press Ctrl+C to stop the agent")
        print("=" * 60)
        
        # Keep the client running
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()
        print("👋 Telegram News Agent stopped")

if __name__ == "__main__":
    asyncio.run(main())