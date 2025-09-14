"""Chat history storage utilities"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.models.chat import InputMessage


class PrettyJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that ensures safe JSON serialization"""
    
    def encode(self, obj):
        # Don't replace newlines - keep them escaped for safe JSON
        return json.JSONEncoder.encode(self, obj)
    
    def iterencode(self, obj, _one_shot=False):
        """Encode the given object and yield each string representation as available."""
        for chunk in json.JSONEncoder.iterencode(self, obj, _one_shot):
            # Don't replace newlines - keep them escaped for safe JSON
            yield chunk


class ChatHistoryStorage:
    """Handles saving and loading chat history to/from JSON files"""
    
    def __init__(self, base_path: str = "resources/chat_history"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        # Track active conversations for incremental updates
        self._active_conversations: Dict[str, str] = {}  # conversation_id -> filepath
    
    def _clean_string(self, text: str) -> str:
        """Remove control characters that can cause JSON parsing issues"""
        if not isinstance(text, str):
            return text
        
        # Remove control characters except for common whitespace
        # Keep \n, \r, \t but remove other control characters
        # Also remove any characters that could break JSON parsing
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Additional cleaning for characters that might break JSON
        # Replace problematic quotes and backslashes
        cleaned = cleaned.replace('\x00', '').replace('\x01', '').replace('\x02', '')
        cleaned = cleaned.replace('\x03', '').replace('\x04', '').replace('\x05', '')
        cleaned = cleaned.replace('\x06', '').replace('\x07', '').replace('\x08', '')
        
        return cleaned
    
    def _clean_control_characters(self, obj: Any) -> Any:
        """Recursively clean control characters from nested objects"""
        if isinstance(obj, str):
            return self._clean_string(obj)
        elif isinstance(obj, dict):
            return {key: self._clean_control_characters(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_control_characters(item) for item in obj]
        else:
            return obj
    
    def save_chat_history(self, conversation_id: str, messages: List[InputMessage], metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save chat history to a JSON file
        
        Args:
            conversation_id: Unique identifier for the conversation
            messages: List of messages in the conversation
            metadata: Optional metadata about the conversation
            
        Returns:
            Path to the saved file
        """
        try:
            # Create filename with timestamp for uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{conversation_id}_{timestamp}.json"
            filepath = self.base_path / filename
            
            # Convert messages to serializable format
            serializable_messages = []
            for msg in messages:
                if msg is not None:
                    try:
                        # Use the model's dict() method for proper serialization
                        msg_dict = msg.dict()
                        serializable_messages.append(msg_dict)
                    except Exception as e:
                        # Fallback for messages that can't be serialized
                        print(f"Warning: Could not serialize message: {e}")
                        serializable_messages.append({
                            "role": getattr(msg, 'role', 'unknown'),
                            "content": str(getattr(msg, 'content', '')),
                            "type": type(msg).__name__,
                            "serialization_error": str(e)
                        })
            
            # Prepare the data structure
            chat_data = {
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "message_count": len(serializable_messages),
                "metadata": metadata or {},
                "messages": serializable_messages
            }
            
            # Save to file with pretty formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False, cls=PrettyJSONEncoder)
            
            print(f"Chat history saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"Error saving chat history: {e}")
            raise
    
    def start_conversation(self, conversation_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new conversation and create initial file in a conversation-specific folder
        
        Args:
            conversation_id: Unique identifier for the conversation
            metadata: Optional metadata about the conversation
            
        Returns:
            Path to the created file
        """
        try:
            # Create conversation-specific directory
            conversation_dir = self.base_path / conversation_id
            conversation_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename - just use chat_history.json since it's in its own folder
            filename = "chat_history.json"
            filepath = conversation_dir / filename
            
            # Prepare initial data structure
            chat_data = {
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "message_count": 0,
                "metadata": metadata or {},
                "messages": []
            }
            
            # Save initial file with pretty formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False, cls=PrettyJSONEncoder)
            
            # Track this conversation
            self._active_conversations[conversation_id] = str(filepath)
            
            print(f"Started conversation: {conversation_id} -> {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"Error starting conversation: {e}")
            raise
    
    def append_message(self, conversation_id: str, message: InputMessage) -> bool:
        """
        Append a single message to an existing conversation
        
        Args:
            conversation_id: Unique identifier for the conversation
            message: Message to append
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the filepath for this conversation
            filepath = self._active_conversations.get(conversation_id)
            if not filepath or not Path(filepath).exists():
                # Try to find the conversation folder and chat_history.json
                conversation_dir = self.base_path / conversation_id
                chat_file = conversation_dir / "chat_history.json"
                if chat_file.exists():
                    filepath = str(chat_file)
                    self._active_conversations[conversation_id] = filepath
                else:
                    # Start a new conversation if none exists
                    filepath = self.start_conversation(conversation_id)
            
            # Load existing data
            with open(filepath, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
            
            # Convert message to serializable format
            if message is not None:
                try:
                    msg_dict = message.dict()
                    # Clean any control characters that might cause JSON issues
                    msg_dict = self._clean_control_characters(msg_dict)
                    chat_data["messages"].append(msg_dict)
                    chat_data["message_count"] = len(chat_data["messages"])
                    chat_data["last_updated"] = datetime.now().isoformat()
                except Exception as e:
                    # Fallback for messages that can't be serialized
                    print(f"Warning: Could not serialize message: {e}")
                    fallback_msg = {
                        "role": getattr(message, 'role', 'unknown'),
                        "content": self._clean_string(str(getattr(message, 'content', ''))),
                        "type": type(message).__name__,
                        "serialization_error": str(e)
                    }
                    chat_data["messages"].append(fallback_msg)
                    chat_data["message_count"] = len(chat_data["messages"])
                    chat_data["last_updated"] = datetime.now().isoformat()
            
            # Save updated data with pretty formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False, cls=PrettyJSONEncoder)
            
            return True
            
        except Exception as e:
            print(f"Error appending message to conversation {conversation_id}: {e}")
            return False
    
    def end_conversation(self, conversation_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark a conversation as ended and update metadata
        
        Args:
            conversation_id: Unique identifier for the conversation
            metadata: Optional final metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = self._active_conversations.get(conversation_id)
            if not filepath or not Path(filepath).exists():
                return False
            
            # Load existing data
            with open(filepath, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
            
            # Update metadata
            if metadata:
                chat_data["metadata"].update(metadata)
            chat_data["ended_at"] = datetime.now().isoformat()
            
            # Save updated data with pretty formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False, cls=PrettyJSONEncoder)
            
            # Remove from active conversations
            del self._active_conversations[conversation_id]
            
            print(f"Ended conversation: {conversation_id}")
            return True
            
        except Exception as e:
            print(f"Error ending conversation {conversation_id}: {e}")
            return False
    
    def load_chat_history(self, conversation_id: str, timestamp: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load chat history from a JSON file
        
        Args:
            conversation_id: Unique identifier for the conversation
            timestamp: Optional specific timestamp to load (deprecated - now uses folder structure)
            
        Returns:
            Dictionary containing the chat history data, or None if not found
        """
        try:
            # Try new folder structure first
            conversation_dir = self.base_path / conversation_id
            chat_file = conversation_dir / "chat_history.json"
            if chat_file.exists():
                with open(chat_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Fallback to old structure for backward compatibility
            if timestamp:
                # Load specific file
                filename = f"{conversation_id}_{timestamp}.json"
                filepath = self.base_path / filename
                if filepath.exists():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        return json.load(f)
            else:
                # Find the most recent file for this conversation in old structure
                pattern = f"{conversation_id}_*.json"
                matching_files = list(self.base_path.glob(pattern))
                if matching_files:
                    # Sort by filename (which includes timestamp) to get the most recent
                    latest_file = sorted(matching_files)[-1]
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            return None
            
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return None
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all available conversations (supports both old and new folder structures)
        
        Returns:
            List of dictionaries with conversation metadata
        """
        try:
            conversations = {}
            
            # Scan new folder structure first
            for conversation_dir in self.base_path.iterdir():
                if conversation_dir.is_dir():
                    chat_file = conversation_dir / "chat_history.json"
                    if chat_file.exists():
                        try:
                            with open(chat_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            conv_id = data.get('conversation_id', conversation_dir.name)
                            timestamp = data.get('timestamp', '')
                            
                            conversations[conv_id] = {
                                'conversation_id': conv_id,
                                'timestamp': timestamp,
                                'message_count': data.get('message_count', 0),
                                'filepath': str(chat_file),
                                'metadata': data.get('metadata', {}),
                                'structure': 'new'  # Mark as new folder structure
                            }
                            
                        except Exception as e:
                            print(f"Error reading folder {conversation_dir}: {e}")
                            continue
            
            # Scan old file structure for backward compatibility
            for filepath in self.base_path.glob("*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    conv_id = data.get('conversation_id', 'unknown')
                    timestamp = data.get('timestamp', '')
                    
                    # Only add if not already found in new structure
                    if conv_id not in conversations:
                        conversations[conv_id] = {
                            'conversation_id': conv_id,
                            'timestamp': timestamp,
                            'message_count': data.get('message_count', 0),
                            'filepath': str(filepath),
                            'metadata': data.get('metadata', {}),
                            'structure': 'old'  # Mark as old file structure
                        }
                    elif timestamp > conversations[conv_id]['timestamp']:
                        # Update if this old file is newer than what we found
                        conversations[conv_id].update({
                            'timestamp': timestamp,
                            'message_count': data.get('message_count', 0),
                            'filepath': str(filepath),
                            'metadata': data.get('metadata', {}),
                            'structure': 'old'
                        })
                        
                except Exception as e:
                    print(f"Error reading file {filepath}: {e}")
                    continue
            
            # Return sorted by timestamp (most recent first)
            return sorted(conversations.values(), key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            print(f"Error listing conversations: {e}")
            return []
    
    def cleanup_old_files(self, days_to_keep: int = 30) -> int:
        """
        Clean up old chat history files
        
        Args:
            days_to_keep: Number of days to keep files (default: 30)
            
        Returns:
            Number of files deleted
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            for filepath in self.base_path.glob("*.json"):
                try:
                    # Get file modification time
                    file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                    
                    if file_mtime < cutoff_date:
                        filepath.unlink()
                        deleted_count += 1
                        print(f"Deleted old chat history file: {filepath}")
                        
                except Exception as e:
                    print(f"Error processing file {filepath}: {e}")
                    continue
            
            return deleted_count
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            return 0


# Global instance for easy access
chat_storage = ChatHistoryStorage()
