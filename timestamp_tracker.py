"""
Timestamp Tracker Module
========================

Handles tracking of last check times to process only new messages.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional

class TimestampTracker:
    """Manages timestamp tracking for message processing"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.timestamp_file = os.path.join(data_dir, "last_check.json")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize timestamp file if it doesn't exist
        if not os.path.exists(self.timestamp_file):
            self._save_timestamp_data({})
    
    def _save_timestamp_data(self, data: Dict) -> None:
        """Save timestamp data to file"""
        try:
            with open(self.timestamp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Error saving timestamp data: {e}")
    
    def _load_timestamp_data(self) -> Dict:
        """Load timestamp data from file"""
        try:
            if os.path.exists(self.timestamp_file):
                with open(self.timestamp_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading timestamp data: {e}")
        return {}
    
    def get_last_check_timestamp(self, chat_id: Optional[int] = None) -> Optional[datetime]:
        """
        Get the last check timestamp for a specific chat or global
        
        Args:
            chat_id (int, optional): Specific chat ID. If None, gets global timestamp.
        
        Returns:
            datetime: Last check timestamp or None if never checked
        """
        data = self._load_timestamp_data()
        
        key = str(chat_id) if chat_id else "global"
        timestamp_str = data.get(key)
        
        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str)
            except ValueError:
                print(f"⚠️  Invalid timestamp format for {key}: {timestamp_str}")
        
        return None
    
    def update_last_check_timestamp(self, chat_id: Optional[int] = None, timestamp: Optional[datetime] = None) -> None:
        """
        Update the last check timestamp for a specific chat or global
        
        Args:
            chat_id (int, optional): Specific chat ID. If None, updates global timestamp.
            timestamp (datetime, optional): Timestamp to set. If None, uses current time.
        """
        data = self._load_timestamp_data()
        
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Ensure timezone-aware datetime
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        key = str(chat_id) if chat_id else "global"
        data[key] = timestamp.isoformat()
        
        self._save_timestamp_data(data)
        print(f"📅 Updated last check time for {key}: {timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    def get_formatted_last_check(self, chat_id: Optional[int] = None) -> str:
        """
        Get a human-readable string of the last check time
        
        Args:
            chat_id (int, optional): Specific chat ID. If None, gets global timestamp.
        
        Returns:
            str: Formatted last check time or "Never" if not found
        """
        last_check = self.get_last_check_timestamp(chat_id)
        
        if last_check:
            return last_check.strftime('%Y-%m-%d %H:%M:%S %Z')
        else:
            return "Never"
    
    def should_process_message(self, message_date: datetime, chat_id: Optional[int] = None) -> bool:
        """
        Check if a message should be processed based on its date and last check time
        
        Args:
            message_date (datetime): Date/time when the message was sent
            chat_id (int, optional): Specific chat ID. If None, uses global timestamp.
        
        Returns:
            bool: True if message should be processed (is newer than last check)
        """
        last_check = self.get_last_check_timestamp(chat_id)
        
        # If we've never checked before, process all messages
        if last_check is None:
            return True
        
        # Ensure both datetimes are timezone-aware for comparison
        if message_date.tzinfo is None:
            message_date = message_date.replace(tzinfo=timezone.utc)
        
        if last_check.tzinfo is None:
            last_check = last_check.replace(tzinfo=timezone.utc)
        
        return message_date > last_check
    
    def get_summary(self) -> Dict:
        """
        Get a summary of all tracked timestamps
        
        Returns:
            dict: Summary of all tracked timestamps
        """
        data = self._load_timestamp_data()
        summary = {}
        
        for key, timestamp_str in data.items():
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                summary[key] = {
                    'last_check': timestamp.strftime('%Y-%m-%d %H:%M:%S %Z'),
                    'iso_format': timestamp_str,
                    'chat_type': 'global' if key == 'global' else f'chat_{key}'
                }
            except ValueError:
                summary[key] = {
                    'last_check': 'Invalid format',
                    'iso_format': timestamp_str,
                    'chat_type': 'error'
                }
        
        return summary
    
    def reset_timestamps(self, chat_id: Optional[int] = None) -> None:
        """
        Reset timestamps (useful for testing or manual reset)
        
        Args:
            chat_id (int, optional): Specific chat ID to reset. If None, resets all timestamps.
        """
        if chat_id is None:
            # Reset all timestamps
            self._save_timestamp_data({})
            print("🔄 All timestamps reset")
        else:
            # Reset specific chat timestamp
            data = self._load_timestamp_data()
            key = str(chat_id)
            if key in data:
                del data[key]
                self._save_timestamp_data(data)
                print(f"🔄 Timestamp reset for chat {chat_id}")
            else:
                print(f"ℹ️  No timestamp found for chat {chat_id}")