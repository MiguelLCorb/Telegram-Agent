"""
Setup Script for Telegram News Agent
=====================================

This script helps you set up the Telegram News Agent by checking prerequisites,
installing dependencies, and guiding you through the configuration process.
"""

import os
import sys
import subprocess
import json

def check_python_version():
    """Check if Python version is 3.7 or higher"""
    print("🔍 Checking Python version...")
    
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    except FileNotFoundError:
        print("❌ requirements.txt file not found")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ["publications"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"ℹ️  Directory already exists: {directory}")

def setup_api_credentials():
    """Guide user through API setup"""
    print("\n🔐 Setting up API credentials...")
    print("You need Telegram API credentials to use this agent.")
    print("Get them from: https://my.telegram.org/apps")
    print()
    
    # Check if API.txt already exists and has valid data
    if os.path.exists("API.txt"):
        with open("API.txt", 'r') as f:
            content = f.read()
            if "YOUR_API_ID_HERE" not in content:
                print("✅ API.txt file already configured")
                return True
    
    # Get user input for API credentials
    print("Please enter your Telegram API credentials:")
    
    api_id = input("API ID: ").strip()
    api_hash = input("API Hash: ").strip()
    
    if not api_id or not api_hash:
        print("❌ API ID and Hash are required")
        return False
    
    # Validate API ID is numeric
    try:
        int(api_id)
    except ValueError:
        print("❌ API ID must be a number")
        return False
    
    # Ask about chat ID
    print("\nFor the Chat ID, you can:")
    print("1. Enter it now if you know it")
    print("2. Leave it blank and use get_chat_id.py later")
    
    chat_id = input("Chat ID (optional): ").strip()
    if not chat_id:
        chat_id = "YOUR_CHAT_ID_HERE"
    
    # Write API.txt file
    try:
        api_content = f"""# API Configuration File
# ======================
# Your Telegram API credentials

TELEGRAM_API_ID={api_id}
TELEGRAM_API_HASH={api_hash}
TELEGRAM_CHAT_ID={chat_id}
"""
        
        with open("API.txt", 'w') as f:
            f.write(api_content)
        
        print("✅ API credentials saved to API.txt")
        
        if chat_id == "YOUR_CHAT_ID_HERE":
            print("⚠️  Remember to run 'python get_chat_id.py' to find your Chat ID")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving API credentials: {e}")
        return False

def test_imports():
    """Test if all required modules can be imported"""
    print("\n🧪 Testing imports...")
    
    required_modules = [
        ("requests", "requests"),
        ("beautifulsoup4", "bs4"),
        ("telethon", "telethon")
    ]
    
    all_good = True
    
    for package_name, import_name in required_modules:
        try:
            __import__(import_name)
            print(f"✅ {package_name} imported successfully")
        except ImportError:
            print(f"❌ {package_name} not found")
            all_good = False
    
    return all_good

def display_next_steps():
    """Display information about next steps"""
    print("\n🎉 SETUP COMPLETE!")
    print("=" * 40)
    print("Next steps:")
    print()
    print("1. If you haven't set your Chat ID yet:")
    print("   python get_chat_id.py")
    print()
    print("2. Run the news agent:")
    print("   python agent.py")
    print()
    print("3. View saved publications:")
    print("   python publications_viewer.py")
    print()
    print("4. Read the README.md file for detailed instructions")
    print()
    print("🔗 Need help? Check the troubleshooting section in README.md")

def main():
    """Main setup function"""
    print("🤖 TELEGRAM NEWS AGENT SETUP")
    print("=" * 40)
    print("This script will help you set up the Telegram News Agent")
    print()
    
    # Check prerequisites
    if not check_python_version():
        return
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed: Could not install dependencies")
        return
    
    # Test imports
    if not test_imports():
        print("\n❌ Setup failed: Some modules could not be imported")
        print("Try running: pip install -r requirements.txt")
        return
    
    # Create directories
    create_directories()
    
    # Setup API credentials
    if not setup_api_credentials():
        print("\n⚠️  API credentials not configured")
        print("You can configure them later by editing API.txt")
    
    # Show next steps
    display_next_steps()

if __name__ == "__main__":
    main()