"""
Simple LLM Integration Module
=============================

This module provides AI-powered content analysis using direct API calls
to avoid client initialization issues with proxies.
"""

import requests
import json
from typing import Dict, Optional

class SimpleLLMProcessor:
    """Handles LLM-based content processing using direct API calls"""
    
    def __init__(self):
        self.openai_key = None
        self.anthropic_key = None
        self.provider = None
        
    def load_api_keys_direct(self, openai_key=None, anthropic_key=None, provider_preference="auto"):
        """
        Load LLM API keys directly from parameters
        
        Args:
            openai_key (str): OpenAI API key
            anthropic_key (str): Anthropic API key  
            provider_preference (str): Which provider to prefer
            
        Returns:
            bool: True if at least one LLM provider is available
        """
        
        # Filter out placeholder values
        if openai_key and openai_key not in ["YOUR_OPENAI_API_KEY_HERE", "", "None"]:
            self.openai_key = openai_key
        if anthropic_key and anthropic_key not in ["YOUR_ANTHROPIC_API_KEY_HERE", "", "None"]:
            self.anthropic_key = anthropic_key
        
        # Determine which provider to use
        if provider_preference == "anthropic" and self.anthropic_key:
            self.provider = "anthropic"
        elif provider_preference == "openai" and self.openai_key:
            self.provider = "openai"
        elif provider_preference == "auto":
            if self.anthropic_key:
                self.provider = "anthropic"
            elif self.openai_key:
                self.provider = "openai"
        
        if self.provider:
            print(f"🤖 Using {self.provider.upper()} as LLM provider")
            return True
        else:
            print("❌ No LLM provider available - check API keys")
            return False
    
    def is_available(self) -> bool:
        """Check if LLM processing is available"""
        return self.provider is not None and (self.openai_key or self.anthropic_key)
    
    def _call_openai_api(self, messages: list, max_tokens: int = 1000) -> str:
        """Make direct API call to OpenAI"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                print(f"⚠️  OpenAI API error: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            print(f"⚠️  OpenAI API error: {e}")
            return ""
    
    def _call_anthropic_api(self, system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> str:
        """Make direct API call to Anthropic"""
        try:
            headers = {
                "x-api-key": self.anthropic_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "user", "content": user_prompt}
                ]
            }
            
            if system_prompt:
                data["system"] = system_prompt
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"].strip()
            else:
                print(f"⚠️  Anthropic API error: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            print(f"⚠️  Anthropic API error: {e}")
            return ""
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Make a call to the configured LLM provider"""
        if not self.is_available():
            return ""
        
        if self.provider == "anthropic":
            return self._call_anthropic_api(system_prompt, prompt)
        elif self.provider == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            return self._call_openai_api(messages)
        
        return ""
    
    def enhance_article_extraction(self, url: str, raw_html: str, basic_data: Dict) -> Dict:
        """
        Use LLM to enhance article extraction with better title, summary, and metadata
        """
        if not self.is_available():
            basic_data['enhanced_by_llm'] = False
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
        """
        if not self.is_available() or not message_text.strip():
            return {
                'summary': message_text[:100] + '...' if len(message_text) > 100 else message_text,
                'sentiment': 'neutral',
                'topics': [],
                'importance': 'medium',
                'enhanced_by_llm': False,
                'original_message': message_text,
                'sender': sender_name
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