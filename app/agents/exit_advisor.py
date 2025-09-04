"""
Exit Advisor Agent for the GenAI SMS Chatbot.

This agent is responsible for confirming when it's appropriate to end a conversation
and generating polite exit messages.
"""

import logging
from typing import Dict, Any, List, Optional
from app.mongodb_manager import global_mongodb_manager
from app.agents.exit_advisor_fallback_manager import ExitAdvisorFallbackManager

from config.project_config import BaseConfigurable

class ExitAdvisor(BaseConfigurable):
    """
    Exit advisor that handles conversation endings gracefully.
    """
    
    def __init__(self, client, model: str):
        """
        Initialize the exit advisor.
        
        Args:
            client: OpenAI client instance
            model: Model name to use
        """
        super().__init__()
        self.client = client
        self.model = model
        self.system_prompt = self._get_system_prompt()
        
        # Initialize fallback manager
        self.fallback_manager = ExitAdvisorFallbackManager()
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the exit advisor."""
        return """You are an Exit Advisor for a job candidate chatbot system. Your role is to:

1. Determine if a candidate wants to end the conversation
2. Confirm their intent to end the conversation
3. Generate polite and professional exit messages
4. Create comprehensive conversation summaries
5. Leave the door open for future contact

Be respectful, professional, and understanding. Always thank the candidate for their time."""
    
    def confirm_exit(self, user_message: str, context: str = "") -> bool:
        """
        Confirm if the user wants to end the conversation.
        
        Args:
            user_message: The user's message
            context: Previous conversation context
            
        Returns:
            True if the user wants to end the conversation, False otherwise
        """
        try:
            if not self.client:
                self.logger.warning("OpenAI client not available, using fallback logic")
                return self.fallback_manager.get_fallback_exit_confirmation(user_message)
            
            # Analyze the user's intent
            prompt = f"""Analyze this user message and determine if they want to end the conversation:

User message: "{user_message}"
Context: {context}

Look for indicators like:
- Explicit statements of disinterest
- Goodbye messages
- Statements about not being interested
- Requests to stop or end the conversation

Respond with ONLY "yes" if they want to end the conversation, or "no" if they want to continue."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().lower()
            should_exit = result == "yes"
            
            self.logger.info(f"Exit advisor determined should_exit: {should_exit}")
            return should_exit
            
        except Exception as e:
            self.logger.error(f"Error in exit confirmation: {str(e)}")
            return self.fallback_manager.get_fallback_exit_confirmation(user_message)
    

    
    def generate_exit_message(self, user_message: str, context: str = "") -> str:
        """
        Generate a polite exit message.
        
        Args:
            user_message: The user's message that triggered the exit
            context: Previous conversation context
            
        Returns:
            Polite exit message
        """
        try:
            if not self.client:
                self.logger.warning("OpenAI client not available, using fallback exit message")
                return self.fallback_manager.get_fallback_exit_message(user_message)
            
            # Generate a personalized exit message
            prompt = f"""Generate a polite and professional exit message for a job candidate who wants to end the conversation.

User message: "{user_message}"
Context: {context}

The message should:
- Thank them for their time and interest
- Be professional and respectful
- Leave the door open for future contact
- Wish them well in their job search
- Be concise but warm

Exit message:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            exit_message = response.choices[0].message.content.strip()
            self.logger.info("Generated exit message using OpenAI")
            return exit_message
            
        except Exception as e:
            self.logger.error(f"Error generating exit message: {str(e)}")
            return self.fallback_manager.get_fallback_exit_message(user_message)
    

    
    def generate_conversation_summary(self, conversation_transcript: List[Dict[str, Any]], 
                                   previous_summary: str = "", phone_number: str = "") -> str:
        """
        Generate a comprehensive summary of the conversation.
        
        Args:
            conversation_transcript: List of conversation messages
            previous_summary: Previous conversation summary from MongoDB
            phone_number: User's phone number for context
            
        Returns:
            Generated conversation summary
        """
        try:
            if not self.client:
                self.logger.warning("OpenAI client not available, using fallback summary")
                return self.fallback_manager.get_fallback_conversation_summary(conversation_transcript, previous_summary)
            
            # Prepare conversation text
            conversation_text = ""
            for message in conversation_transcript:
                role = message.get('role', 'unknown')
                content = message.get('content', '')
                conversation_text += f"{role.upper()}: {content}\n"
            
            # Create summary prompt
            prompt = f"""Create a comprehensive summary of this job candidate conversation.

Phone Number: {phone_number}
Previous Summary: {previous_summary if previous_summary else "No previous conversation"}

Current Conversation:
{conversation_text}

Please create a summary that includes:
1. Candidate's job interests and preferences
2. Key questions asked and information provided
3. Candidate's level of interest and engagement
4. Any specific requirements or concerns mentioned
5. Overall assessment of candidate fit
6. Next steps or recommendations

Summary:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional recruiter creating conversation summaries. Be concise but comprehensive."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            self.logger.info("Generated conversation summary using OpenAI")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating conversation summary: {str(e)}")
            return self.fallback_manager.get_fallback_conversation_summary(conversation_transcript, previous_summary)
    

    
    def save_conversation_to_mongodb(self, phone_number: str, conversation_transcript: List[Dict[str, Any]], 
                                   conversation_summary: str) -> bool:
        """
        Save conversation transcript and summary to MongoDB.
        
        Args:
            phone_number: User's phone number
            conversation_transcript: List of conversation messages
            conversation_summary: Generated conversation summary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Save conversation transcript
            transcript_saved = global_mongodb_manager.save_conversation_transcript(phone_number, conversation_transcript)
            
            # Update conversation summary
            summary_saved = global_mongodb_manager.update_conversation_summary(phone_number, conversation_summary)
            
            if transcript_saved and summary_saved:
                self.logger.info(f"Successfully saved conversation data for {phone_number}")
                return True
            else:
                self.logger.warning(f"Failed to save some conversation data for {phone_number}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving conversation to MongoDB: {str(e)}")
            return False
    
    def process_conversation_end(self, phone_number: str, conversation_transcript: List[Dict[str, Any]], 
                               user_message: str = "") -> Dict[str, Any]:
        """
        Process the end of a conversation - generate summary and save to MongoDB.
        
        Args:
            phone_number: User's phone number
            conversation_transcript: List of conversation messages
            user_message: Final user message that triggered the exit
            
        Returns:
            Dictionary with exit message and summary
        """
        try:
            # Get previous conversation summary
            previous_summary = global_mongodb_manager.get_user_conversation_summary(phone_number) or ""
            
            # Generate new conversation summary
            conversation_summary = self.generate_conversation_summary(
                conversation_transcript, previous_summary, phone_number
            )
            
            # Save to MongoDB
            saved = self.save_conversation_to_mongodb(phone_number, conversation_transcript, conversation_summary)
            
            # Generate exit message WITHOUT including the summary in the message
            exit_message = self.generate_exit_message(user_message, "")  # Empty context to avoid showing summary
            
            return {
                "exit_message": exit_message,
                "conversation_summary": conversation_summary,
                "saved_to_mongodb": saved
            }
            
        except Exception as e:
            self.logger.error(f"Error processing conversation end: {str(e)}")
            return {
                "exit_message": self.fallback_manager.get_fallback_exit_message(user_message),
                "conversation_summary": "Error generating summary",
                "saved_to_mongodb": False
            }
