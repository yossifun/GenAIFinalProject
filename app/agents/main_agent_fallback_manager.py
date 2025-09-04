"""
Fallback Manager for the GenAI SMS Chatbot.

This class handles all fallback logic when primary methods (like OpenAI calls) fail,
providing reliable alternatives for core functionality.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from app.agents.responses import (
    MAIN_AGENT_WELCOME_BACK_RESPONSE,
    MAIN_AGENT_WELCOME_BACK_NO_HISTORY_RESPONSE,
    MAIN_AGENT_WELCOME_INITIAL_RESPONSE
)

from config.project_config import BaseConfigurable

class MainAgentFallbackManager(BaseConfigurable):
    """
    Manages fallback logic for when primary methods fail.
    
    This class provides reliable alternatives for:
    - Phone number extraction
    - Action decision making
    - Time slot selection detection
    - Conversation summarization
    - Post-scheduling messages
    """
    
    def __init__(self):
        """Initialize the fallback manager."""
        super().__init__()
        self.logger.info("Fallback manager initialized")
    
    def extract_phone_number_with_regex(self, text: str) -> Optional[str]:
        """
        Extract phone number from text using regex patterns (fallback method).
        
        Args:
            text: Text containing potential phone number
            
        Returns:
            Extracted phone number or None
        """
        # Common phone number patterns
        patterns = [
            r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # (123) 456-7890
            r'\+?1?[-.\s]?([0-9]{3})[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',        # 123-456-7890
            r'([0-9]{10})',                                                      # 1234567890
            r'\+?([0-9]{11})',                                                   # +11234567890
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Clean up the phone number
                phone = ''.join(match.groups())
                if len(phone) == 10:
                    self.logger.info(f"Regex extracted 10-digit phone number: {phone}")
                    return phone
                elif len(phone) == 11 and phone.startswith('1'):
                    self.logger.info(f"Regex extracted 11-digit phone number, removing leading 1: {phone[1:]}")
                    return phone[1:]
        
        # If no pattern matches, try to extract any sequence of 10 digits
        digits_only = re.sub(r'\D', '', text)
        if len(digits_only) == 10:
            self.logger.info(f"Regex extracted 10-digit sequence: {digits_only}")
            return digits_only
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            self.logger.info(f"Regex extracted 11-digit sequence, removing leading 1: {digits_only[1:]}")
            return digits_only[1:]
        
        self.logger.info(f"No valid phone number found in text: {text}")
        return None
    
    def decide_action(self, user_message: str) -> str:
        """
        Fallback action decision when OpenAI client is not available.
        
        Args:
            user_message: The current user message
            
        Returns:
            Action to take based on simple keyword matching
        """
        user_message_lower = user_message.lower()
        
        # Simple keyword-based decision logic
        if any(word in user_message_lower for word in ['schedule', 'interview', 'meeting', 'book']):
            return "schedule"
        elif any(word in user_message_lower for word in ['reschedule', 'change time', 'different time', 'move interview', 'change interview']):
            # Handle rescheduling requests
            return "schedule"
        elif any(word in user_message_lower for word in ['cancel', 'cancel interview', 'cancel meeting', 'not interested']):
            # Handle cancellation requests
            return "end"
        elif any(word in user_message_lower for word in ['bye', 'end', 'stop', 'goodbye', 'thank you, bye']):
            return "end"
        elif any(word in user_message_lower for word in ['yes', 'interested', 'sounds good', 'great', 'perfect']):
            # If user shows interest, push for scheduling
            return "schedule"
        
        # Default to continue if unclear
        return "continue"

    def get_registration_message(self, user_name: str, user_phone: str) -> str:
        """
        Generate a registration message when OpenAI is not available.

        Args:
            user_name: The name of the user
            user_phone: The phone number of the user

        Returns:
            Registration message
        """
        if user_name and user_phone:
            return f"Thank you for providing your details, {user_name}. We will contact you at {user_phone}."
        elif user_name:
            return f"Thank you for providing your name, {user_name}. Please share your phone number."
        elif user_phone:
            return f"Thank you for providing your phone number, {user_phone}. Please share your name."
        else:
            return "Thank you for your interest. Please provide your name and phone number."

    def generate_post_scheduling_message(self, schedule_result: Dict[str, Any]) -> str:
        """
        Generate a post-scheduling message when OpenAI is not available.
        
        Args:
            schedule_result: Result from scheduling operation
            
        Returns:
            Post-scheduling message
        """
        if not schedule_result:
            return "Scheduling completed. Is there anything else I can help you with?"
        
        # Extract key information
        position = schedule_result.get('position', 'the position')
        date = schedule_result.get('date', 'the scheduled date')
        time = schedule_result.get('time', 'the scheduled time')
        
        if position and date and time:
            message = f"Perfect! Your interview for {position} has been scheduled for {date} at {time}. You'll receive a confirmation email with all the details. Is there anything else you'd like to know?"
        else:
            message = "Your interview has been scheduled successfully. You'll receive a confirmation email with all the details. Is there anything else I can help you with?"
        
        self.logger.info(f"Generated fallback post-scheduling message: {message}")
        return message
    
    def get_welcome_message(self, user_type: str, previous_job_interest: str = None, 
                          scheduled_interview: Dict = None) -> str:
        """
        Get fallback welcome message when dynamic generation fails.
        
        Args:
            user_type: Type of user
            previous_job_interest: User's previous job interest
            scheduled_interview: Details of scheduled interview
            
        Returns:
            Fallback welcome message
        """

        
        if user_type == "returning_with_interview":
            if scheduled_interview and previous_job_interest:
                # Use a more personalized message when we have the data
                return f"Welcome back! I see you're still interested in {previous_job_interest} positions. Your interview for {scheduled_interview.get('position', 'the position')} is scheduled for {scheduled_interview.get('date', 'the scheduled date')} at {scheduled_interview.get('time', 'the scheduled time')}. How can I help you today?"
            return MAIN_AGENT_WELCOME_BACK_RESPONSE
        elif user_type == "returning_user":
            if previous_job_interest:
                return f"Welcome back! I remember you were interested in {previous_job_interest} positions. How can I help you today?"
            return MAIN_AGENT_WELCOME_BACK_NO_HISTORY_RESPONSE
        else:
            return MAIN_AGENT_WELCOME_INITIAL_RESPONSE
