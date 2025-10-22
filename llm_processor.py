"""
LLM Integration Module
======================

This module provides AI-powered content analysis using OpenAI GPT or Anthropic Claude.
It enhances web scraping with intelligent content extraction and provides 
message summarization capabilities.
"""

import os
import requests
from typing import Dict, Optional, List, Tuple
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI library not available - install with: pip install openai")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  Anthropic library not available - install with: pip install anthropic")

class LLMProcessor:
    """Handles LLM-based content processing and analysis"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.provider = None
        self.openai_model = "gpt-4o-mini"
        self.anthropic_model = "claude-3-haiku-20240307"
        
    def load_api_keys(self, api_file="API.txt"):
        """Load LLM API keys from configuration file"""
        openai_key = None
        anthropic_key = None
        provider_preference = "auto"
        
        if os.path.exists(api_file):
            with open(api_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        if key == "OPENAI_API_KEY" and value != "YOUR_OPENAI_API_KEY_HERE":
                            openai_key = value
                        elif key == "ANTHROPIC_API_KEY" and value != "YOUR_ANTHROPIC_API_KEY_HERE":
                            anthropic_key = value
                        elif key == "LLM_PROVIDER":
                            provider_preference = value
                        elif key == "OPENAI_MODEL":
                            self.openai_model = value
                        elif key == "ANTHROPIC_MODEL":
                            self.anthropic_model = value
        
        # Initialize clients based on available keys
        if anthropic_key and ANTHROPIC_AVAILABLE:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                print("✅ Anthropic Claude client initialized")
            except Exception as e:
                print(f"⚠️  Error initializing Anthropic client: {e}")
        
        if openai_key and OPENAI_AVAILABLE:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                print("✅ OpenAI GPT client initialized")
            except Exception as e:
                print(f"⚠️  Error initializing OpenAI client: {e}")
        
        # Determine which provider to use
        if provider_preference == "anthropic" and self.anthropic_client:
            self.provider = "anthropic"
        elif provider_preference == "openai" and self.openai_client:
            self.provider = "openai"
        elif provider_preference == "auto":
            if self.anthropic_client:
                self.provider = "anthropic"
            elif self.openai_client:
                self.provider = "openai"
        
        if self.provider:
            print(f"🤖 Using {self.provider.upper()} as LLM provider")
        else:
            print("❌ No LLM provider available - add API keys to API.txt")
        
        return self.provider is not None
    
    def load_api_keys_direct(self, openai_key=None, anthropic_key=None, provider_preference="auto"):
        """
        Load LLM API keys directly from parameters (for hardcoded credentials)
        
        Args:
            openai_key (str): OpenAI API key
            anthropic_key (str): Anthropic API key  
            provider_preference (str): Which provider to prefer
            
        Returns:
            bool: True if at least one LLM provider is available
        """
        
        # Filter out placeholder values
        if openai_key and openai_key in ["YOUR_OPENAI_API_KEY_HERE", "", "None"]:
            openai_key = None
        if anthropic_key and anthropic_key in ["YOUR_ANTHROPIC_API_KEY_HERE", "", "None"]:
            anthropic_key = None
            
        # Initialize clients based on available keys with error handling
        if anthropic_key and ANTHROPIC_AVAILABLE:
            try:
                # Create a minimal Anthropic client
                self.anthropic_client = anthropic.Anthropic(
                    api_key=anthropic_key,
                )
                # Test the client with a simple call to verify it works
                print("✅ Anthropic Claude client initialized")
            except TypeError as e:
                if "proxies" in str(e):
                    print("⚠️  Anthropic client version incompatibility - trying alternative initialization")
                    try:
                        # Try with older initialization method
                        self.anthropic_client = anthropic.Client(api_key=anthropic_key)
                        print("✅ Anthropic Claude client initialized (legacy mode)")
                    except:
                        print(f"❌ Could not initialize Anthropic client: {e}")
                else:
                    print(f"⚠️  Error initializing Anthropic client: {e}")
            except Exception as e:
                print(f"⚠️  Error initializing Anthropic client: {e}")
        
        if openai_key and OPENAI_AVAILABLE:
            try:
                # Create a minimal OpenAI client
                self.openai_client = openai.OpenAI(
                    api_key=openai_key,
                )
                print("✅ OpenAI GPT client initialized")
            except TypeError as e:
                if "proxies" in str(e):
                    print("⚠️  OpenAI client version incompatibility - trying alternative initialization")
                    try:
                        # Try with older initialization method
                        openai.api_key = openai_key
                        self.openai_client = openai  # Use module directly
                        print("✅ OpenAI GPT client initialized (legacy mode)")
                    except:
                        print(f"❌ Could not initialize OpenAI client: {e}")
                else:
                    print(f"⚠️  Error initializing OpenAI client: {e}")
            except Exception as e:
                print(f"⚠️  Error initializing OpenAI client: {e}")
        
        # Determine which provider to use
        if provider_preference == "anthropic" and self.anthropic_client:
            self.provider = "anthropic"
        elif provider_preference == "openai" and self.openai_client:
            self.provider = "openai"
        elif provider_preference == "auto":
            if self.anthropic_client:
                self.provider = "anthropic"
            elif self.openai_client:
                self.provider = "openai"
        
        if self.provider:
            print(f"🤖 Using {self.provider.upper()} as LLM provider")
        else:
            print("❌ No LLM provider available - check API keys")
        
        return self.provider is not None
    
    def is_available(self) -> bool:
        """Check if LLM processing is available"""
        return self.provider is not None
    
    def _call_anthropic(self, prompt: str, system_prompt: str = "") -> str:
        """Make a call to Anthropic Claude"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": self.anthropic_model,
                "messages": messages,
                "max_tokens": 1000
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.anthropic_client.messages.create(**kwargs)
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"⚠️  Anthropic API error: {e}")
            return ""
    
    def _call_openai(self, prompt: str, system_prompt: str = "") -> str:
        """Make a call to OpenAI GPT"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=messages,
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️  OpenAI API error: {e}")
            return ""
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Make a call to the configured LLM provider"""
        if not self.is_available():
            return ""
        
        if self.provider == "anthropic":
            return self._call_anthropic(prompt, system_prompt)
        elif self.provider == "openai":
            return self._call_openai(prompt, system_prompt)
        
        return ""
    
    def enhance_article_extraction(self, url: str, raw_html: str, basic_data: Dict) -> Dict:
        """
        Use LLM to enhance article extraction with better title, summary, and metadata
        
        Args:
            url (str): The article URL
            raw_html (str): Raw HTML content
            basic_data (dict): Basic extracted data from web scraping
            
        Returns:
            dict: Enhanced article data
        """
        if not self.is_available():
            return basic_data
        
        print("🤖 Enhancing article extraction with LLM...")
        
        # Prepare the HTML content (truncate if too long)
        html_content = raw_html[:8000] if len(raw_html) > 8000 else raw_html
        
        system_prompt = """You are a professional article analyzer. Extract key information from web articles with high accuracy.

Your task is to analyze HTML content and provide structured information about the article.
Focus on accuracy and relevance. If information is not clear, indicate uncertainty."""

        user_prompt = f"""Analyze this article from {url}

HTML Content:
{html_content}

Current extracted data:
- Title: {basic_data.get('title', 'Unknown')}
- Summary: {basic_data.get('summary', 'Unknown')}
- Author: {basic_data.get('author', 'Unknown')}
- Image: {basic_data.get('image', 'Unknown')}

Please provide improved extraction in this exact JSON format:
{{
    "title": "Clear, descriptive article title (max 150 chars)",
    "summary": "Concise 2-3 sentence summary of main points (max 300 chars)", 
    "author": "Author name or 'Unknown' if not found",
    "category": "Article category (news, tech, politics, etc.)",
    "key_points": ["Key point 1", "Key point 2", "Key point 3"],
    "confidence": "high/medium/low based on content clarity",
    "article_type": "news/opinion/analysis/blog/other"
}}

Only return the JSON, no other text."""

        try:
            response = self._call_llm(user_prompt, system_prompt)
            
            if response:
                # Try to parse JSON response
                import json
                try:
                    enhanced_data = json.loads(response)
                    
                    # Merge enhanced data with basic data
                    result = basic_data.copy()
                    result.update({
                        'title': enhanced_data.get('title', basic_data.get('title')),
                        'summary': enhanced_data.get('summary', basic_data.get('summary')),
                        'author': enhanced_data.get('author', basic_data.get('author')),
                        'category': enhanced_data.get('category', 'Unknown'),
                        'key_points': enhanced_data.get('key_points', []),
                        'confidence': enhanced_data.get('confidence', 'medium'),
                        'article_type': enhanced_data.get('article_type', 'unknown'),
                        'enhanced_by_llm': True,
                        'llm_provider': self.provider
                    })
                    
                    print(f"✅ Article enhanced by {self.provider.upper()}")
                    return result
                    
                except json.JSONDecodeError:
                    print("⚠️  LLM response was not valid JSON, using basic extraction")
                    
        except Exception as e:
            print(f"⚠️  Error in LLM enhancement: {e}")
        
        # Return basic data if LLM enhancement fails
        basic_data['enhanced_by_llm'] = False
        return basic_data
    
    def summarize_message(self, message_text: str, sender_name: str = "Unknown") -> Dict:
        """
        Analyze and summarize a Telegram message using LLM
        
        Args:
            message_text (str): The message content
            sender_name (str): Name of the message sender
            
        Returns:
            dict: Message analysis including summary, sentiment, topics
        """
        if not self.is_available() or not message_text.strip():
            return {
                'summary': message_text[:100] + '...' if len(message_text) > 100 else message_text,
                'sentiment': 'neutral',
                'topics': [],
                'importance': 'medium',
                'enhanced_by_llm': False
            }
        
        print(f"🤖 Analyzing message from {sender_name}...")
        
        system_prompt = """You are a message analyzer that provides concise analysis of text messages.
Provide objective analysis focusing on content, sentiment, and key topics."""

        user_prompt = f"""Analyze this message from {sender_name}:

Message: "{message_text}"

Provide analysis in this exact JSON format:
{{
    "summary": "One sentence summary of the message (max 100 chars)",
    "sentiment": "positive/negative/neutral/mixed",
    "topics": ["topic1", "topic2", "topic3"],
    "importance": "high/medium/low",
    "message_type": "question/announcement/discussion/link_share/other",
    "key_words": ["word1", "word2", "word3"]
}}

Only return the JSON, no other text."""

        try:
            response = self._call_llm(user_prompt, system_prompt)
            
            if response:
                import json
                try:
                    analysis = json.loads(response)
                    analysis['enhanced_by_llm'] = True
                    analysis['llm_provider'] = self.provider
                    analysis['original_message'] = message_text
                    analysis['sender'] = sender_name
                    
                    print(f"✅ Message analyzed by {self.provider.upper()}")
                    return analysis
                    
                except json.JSONDecodeError:
                    print("⚠️  LLM response was not valid JSON")
                    
        except Exception as e:
            print(f"⚠️  Error in message analysis: {e}")
        
        # Fallback analysis
        return {
            'summary': message_text[:100] + '...' if len(message_text) > 100 else message_text,
            'sentiment': 'neutral',
            'topics': [],
            'importance': 'medium',
            'message_type': 'other',
            'key_words': [],
            'enhanced_by_llm': False,
            'original_message': message_text,
            'sender': sender_name
        }
    
    def analyze_conversation_context(self, messages: List[Dict]) -> Dict:
        """
        Analyze a series of messages to understand conversation context
        
        Args:
            messages (List[Dict]): List of message dictionaries
            
        Returns:
            dict: Conversation analysis
        """
        if not self.is_available() or not messages:
            return {
                'main_topics': [],
                'conversation_type': 'unknown',
                'summary': 'No analysis available',
                'participant_count': len(set(msg.get('sender', '') for msg in messages)),
                'enhanced_by_llm': False
            }
        
        print("🤖 Analyzing conversation context...")
        
        # Prepare conversation text
        conversation_text = "\n".join([
            f"{msg.get('sender', 'Unknown')}: {msg.get('message', '')[:200]}"
            for msg in messages[-10:]  # Last 10 messages
        ])
        
        system_prompt = """You are a conversation analyzer. Analyze group chat conversations to identify main topics, themes, and conversation patterns."""

        user_prompt = f"""Analyze this conversation:

{conversation_text}

Provide analysis in this exact JSON format:
{{
    "main_topics": ["topic1", "topic2", "topic3"],
    "conversation_type": "news_discussion/casual_chat/question_answer/link_sharing/debate/other",
    "summary": "Brief summary of what the conversation is about (max 200 chars)",
    "sentiment_overall": "positive/negative/neutral/mixed",
    "activity_level": "high/medium/low"
}}

Only return the JSON, no other text."""

        try:
            response = self._call_llm(user_prompt, system_prompt)
            
            if response:
                import json
                try:
                    analysis = json.loads(response)
                    analysis['enhanced_by_llm'] = True
                    analysis['llm_provider'] = self.provider
                    analysis['participant_count'] = len(set(msg.get('sender', '') for msg in messages))
                    analysis['message_count'] = len(messages)
                    
                    print(f"✅ Conversation analyzed by {self.provider.upper()}")
                    return analysis
                    
                except json.JSONDecodeError:
                    print("⚠️  LLM response was not valid JSON")
                    
        except Exception as e:
            print(f"⚠️  Error in conversation analysis: {e}")
        
        # Fallback analysis
        return {
            'main_topics': ['general discussion'],
            'conversation_type': 'unknown',
            'summary': f'Conversation with {len(messages)} messages',
            'sentiment_overall': 'neutral',
            'activity_level': 'medium',
            'enhanced_by_llm': False,
            'participant_count': len(set(msg.get('sender', '') for msg in messages)),
            'message_count': len(messages)
        }