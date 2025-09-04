"""
MongoDB Manager for the GenAI SMS Chatbot.

This module handles conversation persistence, user registration,
and conversation history management using MongoDB.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

from config.project_config import BaseConfigurable

class MongoDBManager(BaseConfigurable):
    """
    Manages MongoDB operations for conversation persistence and user data.
    """
    
    def __init__(self):
        """Initialize MongoDB connection."""
        super().__init__()
        try:
            load_dotenv()
            
            # Get MongoDB connection string from environment
            mongo_uri = os.getenv('MONGODB_URI', 'mongodb://admin:password123@localhost:27017/sms_chatbot?authSource=admin')
            database_name = os.getenv('MONGODB_DATABASE', 'sms_chatbot')
            
            from pymongo import MongoClient
            self.client = MongoClient(mongo_uri)
            self.db = self.client[database_name]
            
            # Collections
            self.users_collection = self.db['users']
            self.conversations_collection = self.db['conversations']
            
            # Create indexes for better performance
            self.users_collection.create_index("phone_number", unique=True)
            self.conversations_collection.create_index("phone_number")
            self.conversations_collection.create_index("timestamp")
            
            self.logger.info(f"MongoDB connected successfully to database: {database_name}")
            self.is_connected = True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.db = None
            self.is_connected = False
    
    def user_exists(self, phone_number: str) -> bool:
        """
        Check if a user exists in the database.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            True if user exists, False otherwise
        """
        if not self.is_connected:
            return False

        if not phone_number:
            self.logger.warning("Phone number is required to check if user exists.")
            return False

        try:
            user = self.users_collection.find_one({"phone_number": phone_number})
            self.logger.debug(f"User exists check for {phone_number}: {user is not None}")
            return user is not None
        except Exception as e:
            self.logger.error(f"Error checking if user exists: {e}")
            return False
    
    def get_user_conversation_summary(self, phone_number: str) -> Optional[str]:
        """
        Get the conversation summary for a user.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Conversation summary or None if not found
        """
        if not self.is_connected:
            return None

        if not phone_number:
            self.logger.warning("Phone number is required to get user conversation summary.")
            return None

        try:
            user = self.users_collection.find_one({"phone_number": phone_number})
            if user:
                summary = user.get('conversation_summary', '')
                self.logger.debug(f"Retrieved conversation summary for {phone_number}:\n{summary}\n")
                return summary
            return None
        except Exception as e:
            self.logger.error(f"Error getting user conversation summary: {e}")
            return None
    
    def create_new_user(self, phone_number: str, job_interest: str = "") -> bool:
        """
        Create a new user in the database.
        
        Args:
            phone_number: User's phone number
            job_interest: User's job interest (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False

        if not phone_number:
            self.logger.warning("Phone number is required to create a new user.")
            return False

        try:
            user_data = {
                "phone_number": phone_number,
                "job_interest": job_interest,
                "conversation_summary": "",
                "created_at": datetime.now(timezone.utc),
                "last_updated": datetime.now(timezone.utc)
            }
            
            result = self.users_collection.insert_one(user_data)
            self.logger.info(f"Created new user with phone number: {phone_number}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating new user: {e}")
            return False
    
    def save_conversation_transcript(self, phone_number: str, transcript: List[Dict[str, Any]]) -> bool:
        """
        Save a conversation transcript to the database.
        
        Args:
            phone_number: User's phone number
            transcript: List of conversation messages
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False

        if not phone_number:
            self.logger.warning("Phone number is required to save conversation.")
            return False

        if not transcript:
            self.logger.warning("Transcript is required to save conversation.")
            return False

        try:
            conversation_data = {
                "phone_number": phone_number,
                "transcript": transcript,
                "timestamp": datetime.utcnow(),
                "message_count": len(transcript)
            }
            
            result = self.conversations_collection.insert_one(conversation_data)
            self.logger.info(f"Saved conversation transcript for {phone_number}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving conversation transcript: {e}")
            return False
    
    def update_conversation_summary(self, phone_number: str, new_summary: str) -> bool:
        """
        Update the conversation summary for a user.
        
        Args:
            phone_number: User's phone number
            new_summary: New conversation summary
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False
        
        if not phone_number:
            self.logger.warning("Phone number is required to update conversation summary.")
            return False

        if not new_summary:
            self.logger.warning("New summary is required to update conversation summary.")
            return False

        try:
            result = self.users_collection.update_one(
                {"phone_number": phone_number},
                {
                    "$set": {
                        "conversation_summary": new_summary,
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Updated conversation summary for {phone_number}")
                return True
            else:
                self.logger.warning(f"No user found to update summary for {phone_number}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating conversation summary: {e}")
            return False
    
    def get_user_info(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from the database.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            User information dictionary or None if not found
        """
        if not self.is_connected:
            return None

        if not phone_number:
            self.logger.warning("Phone number is required to get user info.")
            return None

        try:
            user = self.users_collection.find_one({"phone_number": phone_number})
            if user:
                # Remove MongoDB ObjectId for JSON serialization
                user.pop('_id', None)
                return user
            return None
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            return None
    
    def get_conversation_history(self, phone_number: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user.
        
        Args:
            phone_number: User's phone number
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation records
        """
        if not self.is_connected:
            return []

        if not phone_number:
            self.logger.warning("Phone number is required to get conversation history.")
            return []

        try:
            conversations = list(self.conversations_collection.find(
                {"phone_number": phone_number}
            ).sort("timestamp", -1).limit(limit))
            
            # Remove MongoDB ObjectIds for JSON serialization
            for conv in conversations:
                conv.pop('_id', None)
            
            return conversations
            
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []
    
    def update_job_interest(self, phone_number: str, job_interest: str) -> bool:
        """
        Update user's job interest.
        
        Args:
            phone_number: User's phone number
            job_interest: New job interest
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False

        if not phone_number:
            self.logger.warning("Phone number is required to update job interest.")
            return False

        if not job_interest:
            self.logger.warning("Job interest is required to update job interest.")
            return False

        try:
            result = self.users_collection.update_one(
                {"phone_number": phone_number},
                {
                    "$set": {
                        "job_interest": job_interest,
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Updated job interest for {phone_number}")
                return True
            else:
                self.logger.warning(f"No user found to update job interest for {phone_number}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating job interest: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        if not self.is_connected:
            return {}
        
        try:
            stats = {
                "total_users": self.users_collection.count_documents({}),
                "total_conversations": self.conversations_collection.count_documents({}),
                "database_name": self.db.name,
                "is_connected": self.is_connected
            }
            return stats
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {"is_connected": False}


# Global instance
global_mongodb_manager = MongoDBManager() 