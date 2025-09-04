"""
Exit Advisor Fallback Manager for the GenAI SMS Chatbot.

This class centralizes all fallback logic for the ExitAdvisor when OpenAI is not available.
"""

import logging
from typing import Dict, Any, List
from config.project_config import BaseConfigurable

# Error and fallback responses
EXIT_FALLBACK_RESPONSE = "Thank you for your time! If you have any questions later, feel free to reach out. Good luck!"

class ExitAdvisorFallbackManager(BaseConfigurable):
    """
    Fallback manager for the ExitAdvisor that handles cases when OpenAI is not available.
    """

    def __init__(self):
        """Initialize the fallback manager."""
        super().__init__()
        self.logger.info("ExitAdvisor fallback manager initialized")
    
    def get_fallback_exit_confirmation(self, user_message: str) -> bool:
        """
        Fallback exit confirmation when OpenAI client is not available.
        
        Args:
            user_message: The user's message
            
        Returns:
            True if the user wants to end the conversation, False otherwise
        """
        user_message_lower = user_message.lower()
        
        # Keywords that indicate wanting to end the conversation
        exit_keywords = [
            'bye', 'goodbye', 'see you', 'not interested', 'not a good fit',
            'end conversation', 'stop', 'quit', 'no thanks', 'pass',
            'already have a job', 'found another position', 'not looking'
        ]
        
        return any(keyword in user_message_lower for keyword in exit_keywords)
    
    def get_fallback_exit_message(self, user_message: str) -> str:
        """
        Fallback exit message when OpenAI client is not available.
        
        Args:
            user_message: The user's message
            
        Returns:
            Standard exit message
        """
        return EXIT_FALLBACK_RESPONSE
    
    def get_fallback_conversation_summary(self, conversation_transcript: List[Dict[str, Any]], 
                                        previous_summary: str = "") -> str:
        """
        Fallback conversation summary when OpenAI client is not available.
        
        Args:
            conversation_transcript: List of conversation messages
            previous_summary: Previous conversation summary
            
        Returns:
            Basic conversation summary
        """
        user_messages = [msg for msg in conversation_transcript if msg.get('role') == 'user']
        assistant_messages = [msg for msg in conversation_transcript if msg.get('role') == 'assistant']
        
        summary = f"Conversation Summary:\n"
        summary += f"- Total messages: {len(conversation_transcript)}\n"
        summary += f"- User messages: {len(user_messages)}\n"
        summary += f"- Assistant responses: {len(assistant_messages)}\n"
        
        if previous_summary:
            summary += f"- Previous conversation context available\n"
        
        # Extract key topics from user messages
        topics = []
        for msg in user_messages:
            content = msg.get('content', '').lower()
            if any(word in content for word in ['requirement', 'skill', 'experience']):
                topics.append('job requirements')
            elif any(word in content for word in ['benefit', 'salary', 'pay']):
                topics.append('compensation')
            elif any(word in content for word in ['schedule', 'interview']):
                topics.append('scheduling')
            elif any(word in content for word in ['company', 'culture']):
                topics.append('company information')
        
        if topics:
            summary += f"- Topics discussed: {', '.join(set(topics))}\n"
        
        return summary
