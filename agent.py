"""
Telegram News Agent
===================

This agent monitors a Telegram group/channel for shared links, automatically extracts
news article information (title, summary, image), and saves it to local files.

The agent operates without a web interface - all data is saved to local files
in the 'publications' folder as both JSON and ODT documents.
"""

import os
import json
import datetime
import requests
from telethon import TelegramClient, events
from bs4 import BeautifulSoup
from odt_writer import create_odt_document
from llm_processor import LLMProcessor

# ============================================================================
# CONFIGURATION SECTION
# ============================================================================
# Edit these values directly or create an API.txt file with your credentials

# Telegram API Credentials
# Get these from https://my.telegram.org/apps
TELEGRAM_API_ID = "API_ID"  # Replace with your API ID
TELEGRAM_API_HASH = "API_HASH"  # Replace with your API Hash
TELEGRAM_SESSION = "news_agent_session"  # Session name for Telegram client
TELEGRAM_CHAT_ID = "CHAT_ID"  # Chat ID to monitor (use get_chat_id.py to find it)

# LLM API Credentials (Optional - for enhanced content analysis)
# Get OpenAI key from: https://platform.openai.com/api-keys
# Get Anthropic key from: https://console.anthropic.com/
OPENAI_API_KEY = "OPENAI_API_KEY"  # Replace with your OpenAI API key
ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"  # Replace with your Anthropic API key
LLM_PROVIDER = "auto"  # "openai", "anthropic", or "auto" (tries anthropic first, then openai)

# File paths for saving publications
PUBLICATIONS_DIR = "publications"
JSON_FILE = os.path.join(PUBLICATIONS_DIR, "news_database.json")

# Initialize LLM processor for enhanced content analysis
llm_processor = LLMProcessor()

def load_api_credentials():
    """
    Load API credentials from API.txt file if it exists.
    Expected format (one per line):
    TELEGRAM_API_ID=your_api_id
    TELEGRAM_API_HASH=your_api_hash
    TELEGRAM_CHAT_ID=your_chat_id
    OPENAI_API_KEY=your_openai_key
    ANTHROPIC_API_KEY=your_anthropic_key
    LLM_PROVIDER=auto
    """
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
    if not os.path.exists(PUBLICATIONS_DIR):
        os.makedirs(PUBLICATIONS_DIR)
        print(f"📁 Created directory: {PUBLICATIONS_DIR}")

def load_existing_publications():
    """Load existing publications from JSON file"""
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print("⚠️  Could not load existing publications, starting fresh")
    return []

def save_publications(publications):
    """Save publications to JSON file"""
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(publications, f, indent=2, ensure_ascii=False)

def extract_article_data(url):
    """
    Extract article information from a URL using web scraping.
    
    Args:
        url (str): The URL to scrape
        
    Returns:
        dict: Dictionary containing article data (title, summary, image, etc.)
    """
    print(f"🔍 Extracting data from: {url}")
    
    try:
        # Set user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract title (try Open Graph first, then title tag)
        title_element = (
            soup.find("meta", property="og:title") or 
            soup.find("meta", attrs={"name": "title"}) or
            soup.find("title")
        )
        
        if title_element:
            if title_element.name == "title":
                title = title_element.get_text().strip()
            else:
                title = title_element.get("content", "").strip()
        else:
            title = "Article Title Not Found"
        
        # Extract description/summary
        summary_element = (
            soup.find("meta", property="og:description") or 
            soup.find("meta", attrs={"name": "description"}) or
            soup.find("meta", attrs={"name": "twitter:description"})
        )
        
        summary = summary_element.get("content", "").strip() if summary_element else "No summary available"
        
        # Extract image
        image_element = (
            soup.find("meta", property="og:image") or 
            soup.find("meta", attrs={"name": "twitter:image"})
        )
        
        image_url = image_element.get("content", "") if image_element else ""
        if not image_url:
            image_url = "No image available"
        
        # Extract author if available
        author_element = (
            soup.find("meta", attrs={"name": "author"}) or
            soup.find("meta", property="article:author")
        )
        
        author = author_element.get("content", "Unknown Author") if author_element else "Unknown Author"
        
        # Basic extracted data
        basic_data = {
            "title": title[:200],  # Limit title length
            "summary": summary[:500],  # Limit summary length
            "url": url,
            "image": image_url,
            "author": author,
            "date_extracted": datetime.date.today().strftime("%Y-%m-%d"),
            "time_extracted": datetime.datetime.now().strftime("%H:%M:%S")
        }
        
        # Enhance with LLM if available
        if llm_processor.is_available():
            enhanced_data = llm_processor.enhance_article_extraction(url, response.text, basic_data)
            return enhanced_data
        else:
            basic_data['enhanced_by_llm'] = False
            return basic_data
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Network error scraping {url}: {e}")
    except Exception as e:
        print(f"⚠️  Error scraping {url}: {e}")
    
    # Return fallback data if scraping fails
    return {
        "title": "Could not extract title",
        "summary": "Could not extract summary",
        "url": url,
        "image": "No image available",
        "author": "Unknown Author",
        "date_extracted": datetime.date.today().strftime("%Y-%m-%d"),
        "time_extracted": datetime.datetime.now().strftime("%H:%M:%S"),
        "enhanced_by_llm": False
    }

def save_article_as_odt(article_data):
    """
    Save an individual article as an ODT document.
    
    Args:
        article_data (dict): Article information
    """
    try:
        # Create safe filename from title
        safe_title = "".join(c for c in article_data["title"] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:50]  # Limit filename length
        
        filename = f"{article_data['date_extracted']}_{safe_title}.odt"
        filepath = os.path.join(PUBLICATIONS_DIR, filename)
        
        # Create ODT document
        create_odt_document(article_data, filepath)
        print(f"📄 Saved ODT: {filename}")
        
    except Exception as e:
        print(f"⚠️  Error creating ODT file: {e}")

def display_article_preview(article_data):
    """Display article information for user review"""
    print("\n" + "="*60)
    print("📰 ARTICLE PREVIEW")
    print("="*60)
    print(f"📌 Title: {article_data['title']}")
    print(f"📝 Summary: {article_data['summary']}")
    print(f"👤 Author: {article_data['author']}")
    print(f"🖼️  Image: {article_data['image']}")
    print(f"🔗 URL: {article_data['url']}")
    print(f"📅 Date: {article_data['date_extracted']} at {article_data['time_extracted']}")
    
    # Show LLM-enhanced information if available
    if article_data.get('enhanced_by_llm', False):
        print(f"\n🤖 AI ENHANCEMENT (by {article_data.get('llm_provider', 'LLM').upper()}):")
        if article_data.get('category'):
            print(f"🏷️  Category: {article_data['category']}")
        if article_data.get('article_type'):
            print(f"📄 Type: {article_data['article_type']}")
        if article_data.get('confidence'):
            print(f"🎯 Confidence: {article_data['confidence']}")
        if article_data.get('key_points'):
            print(f"🔑 Key Points: {', '.join(article_data['key_points'])}")
    else:
        print(f"\n⚠️  Basic extraction only (no LLM enhancement)")
    
    print("="*60)

def get_user_decision():
    """Get user decision on whether to save the article"""
    while True:
        decision = input("\n🤔 Action: (A)ccept, (R)eject, or (M)odify? ").strip().upper()
        if decision in ['A', 'R', 'M']:
            return decision
        print("❌ Please enter A, R, or M")

def modify_article_data(article_data):
    """Allow user to modify article data before saving"""
    print("\n✏️  MODIFY ARTICLE DATA")
    print("(Press Enter to keep current value)")
    
    new_title = input(f"Title [{article_data['title']}]: ").strip()
    if new_title:
        article_data['title'] = new_title
    
    new_summary = input(f"Summary [{article_data['summary'][:50]}...]: ").strip()
    if new_summary:
        article_data['summary'] = new_summary
    
    new_author = input(f"Author [{article_data['author']}]: ").strip()
    if new_author:
        article_data['author'] = new_author
    
    new_image = input(f"Image URL [{article_data['image'][:50]}...]: ").strip()
    if new_image:
        article_data['image'] = new_image
    
    return article_data

# ============================================================================
# TELEGRAM CLIENT SETUP
# ============================================================================

def initialize_telegram_client():
    """Initialize and return the Telegram client"""
    try:
        client = TelegramClient(TELEGRAM_SESSION, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
        return client
    except ValueError as e:
        print(f"❌ Error initializing Telegram client: {e}")
        print("Please check your API credentials in API.txt or in the code")
        return None

# ============================================================================
# MAIN EVENT HANDLER
# ============================================================================

async def handle_new_message(event):
    """
    Handle new messages in the monitored Telegram chat.
    Processes both URLs for article extraction and regular messages for analysis.
    """
    message_text = event.message.message
    
    # Get sender information
    sender_name = "Unknown"
    if event.message.sender:
        if hasattr(event.message.sender, 'first_name'):
            sender_name = f"{event.message.sender.first_name or ''} {event.message.sender.last_name or ''}".strip()
        elif hasattr(event.message.sender, 'title'):
            sender_name = event.message.sender.title
    
    # Find all URLs in the message
    words = message_text.split()
    urls = [word for word in words if word.startswith(('http://', 'https://'))]
    
    # Process URLs for article extraction
    if urls:
        await process_urls_in_message(urls, message_text, sender_name)
    
    # Process message content if LLM is available and message is substantial
    if llm_processor.is_available() and len(message_text.strip()) > 20:
        await process_message_content(message_text, sender_name)

async def process_urls_in_message(urls, message_text, sender_name):
    """Process URLs found in a message"""
    
    print(f"\n🔗 Found {len(urls)} URL(s) in message from {sender_name}")
    
    # Load existing publications
    publications = load_existing_publications()
    
    for url in urls:
        print(f"\n🌐 Processing URL: {url}")
        
        # Check if URL already exists in our database
        existing = any(pub['url'] == url for pub in publications)
        if existing:
            print(f"⚠️  URL already processed: {url}")
            continue
        
        # Extract article data
        article_data = extract_article_data(url)
        
        # Display preview to user
        display_article_preview(article_data)
        
        # Get user decision
        decision = get_user_decision()
        
        if decision == 'R':
            print("❌ Article rejected")
            continue
        elif decision == 'M':
            article_data = modify_article_data(article_data)
            display_article_preview(article_data)
            confirm = input("\n💾 Save modified article? (Y/N): ").strip().upper()
            if confirm != 'Y':
                print("❌ Article not saved")
                continue
        
        # Save the article
        publications.append(article_data)
        save_publications(publications)
        save_article_as_odt(article_data)
        
        print(f"✅ Article saved successfully!")
        print(f"📊 Total articles in database: {len(publications)}")

async def process_message_content(message_text, sender_name):
    """
    Process and analyze message content using LLM
    
    Args:
        message_text (str): The message content
        sender_name (str): Name of the message sender
    """
    print(f"\n💬 Analyzing message from {sender_name}...")
    
    # Analyze the message with LLM
    message_analysis = llm_processor.summarize_message(message_text, sender_name)
    
    # Display analysis results
    print("\n" + "="*60)
    print("📝 MESSAGE ANALYSIS")
    print("="*60)
    print(f"👤 Sender: {sender_name}")
    print(f"📄 Original: {message_text}")
    print(f"📋 Summary: {message_analysis.get('summary', 'No summary')}")
    print(f"😊 Sentiment: {message_analysis.get('sentiment', 'neutral')}")
    print(f"🏷️  Topics: {', '.join(message_analysis.get('topics', []))}")
    print(f"⭐ Importance: {message_analysis.get('importance', 'medium')}")
    print(f"📝 Type: {message_analysis.get('message_type', 'unknown')}")
    if message_analysis.get('enhanced_by_llm', False):
        print(f"🤖 Enhanced by: {message_analysis.get('llm_provider', 'LLM').upper()}")
    print("="*60)
    
    # Ask user if they want to save this analysis
    if message_analysis.get('importance') == 'high' or len(message_analysis.get('topics', [])) > 0:
        save_analysis = input("\n💾 Save this message analysis? (Y/N): ").strip().upper()
        
        if save_analysis == 'Y':
            # Load existing publications to add message analysis
            publications = load_existing_publications()
            
            # Add message analysis to the database
            message_entry = {
                "type": "message_analysis",
                "sender": sender_name,
                "original_message": message_text,
                "analysis": message_analysis,
                "date_extracted": datetime.date.today().strftime("%Y-%m-%d"),
                "time_extracted": datetime.datetime.now().strftime("%H:%M:%S")
            }
            
            publications.append(message_entry)
            save_publications(publications)
            
            print("✅ Message analysis saved!")
            print(f"📊 Total entries in database: {len(publications)}")

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function to run the Telegram news agent"""
    print("🤖 TELEGRAM NEWS AGENT")
    print("=" * 50)
    print("This agent monitors Telegram for shared links and saves news articles locally.")
    print("Articles are saved as JSON data and individual ODT documents.")
    print("=" * 50)
    
    # Load API credentials
    load_api_credentials()
    
    # Initialize LLM processor with credentials
    llm_available = llm_processor.load_api_keys_direct(
        openai_key=OPENAI_API_KEY,
        anthropic_key=ANTHROPIC_API_KEY,
        provider_preference=LLM_PROVIDER
    )
    if llm_available:
        print("🧠 LLM processor initialized - enhanced analysis available")
    else:
        print("⚠️  LLM not available - using basic extraction only")
        print("   Add OpenAI or Anthropic API keys to agent.py or API.txt for enhanced features")
    
    # Validate credentials
    if (TELEGRAM_API_ID == "YOUR_API_ID_HERE" or 
        TELEGRAM_API_HASH == "YOUR_API_HASH_HERE" or
        TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE"):
        print("❌ Please configure your API credentials!")
        print("Either edit the values in agent.py or create an API.txt file")
        return
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize Telegram client
    client = initialize_telegram_client()
    if not client:
        return
    
    # Register event handler for new messages
    @client.on(events.NewMessage(chats=int(TELEGRAM_CHAT_ID)))
    async def message_handler(event):
        await handle_new_message(event)
    
    print(f"🔌 Connecting to Telegram...")
    print(f"👀 Monitoring chat ID: {TELEGRAM_CHAT_ID}")
    print("🚀 Agent is running... Press Ctrl+C to stop")
    
    # Start the client and run until disconnected
    try:
        with client:
            client.run_until_disconnected()
    except KeyboardInterrupt:
        print("\n⏹️  Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Error running agent: {e}")

if __name__ == "__main__":
    main()