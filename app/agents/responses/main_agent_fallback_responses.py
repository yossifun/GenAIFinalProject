"""
Predefined response constants for the MainAgent.

This module contains all the static response messages used by the MainAgent
to maintain readability and consistency across the application.
"""

# Registration responses
MAIN_AGENT_WELCOME_BACK_RESPONSE = """Welcome back! I found your previous conversation history. 

I see you have a scheduled interview. Would you like to:
- Reschedule your interview for a different time?
- Cancel your interview?
- Continue with your scheduled interview as planned?
- Ask questions about the position or company?

How can I help you today?"""

MAIN_AGENT_WELCOME_BACK_NO_HISTORY_RESPONSE = """Welcome back! 

How can I help you today? Are you still interested in scheduling an interview? maybe our positions, or do you have new questions?"""

MAIN_AGENT_NEW_USER_REGISTRATION_RESPONSE = """Great! I've registered your phone number. 

What type of job are you looking for? For example:
- Python Developer
- Frontend Developer
- Data Scientist
- DevOps Engineer
- Or any other position you're interested in

This will help me provide you with the most relevant information."""

MAIN_AGENT_WELCOME_INITIAL_RESPONSE = """Welcome to our job candidate chatbot! 

To get started, please provide your name and phone number so I can help you more effectively.

You can format it however you prefer, for example:
- (123) 456-7890
- 123-456-7890
- 1234567890"""

MAIN_AGENT_JOB_INTEREST_CONFIRMATION_RESPONSE = """Perfect! I've noted that you're interested in {job_interest} positions.

I'm here to help you learn about our available positions, requirements, benefits, and company culture. What would you like to know more about?

You can ask me about:
- Available job positions
- Job requirements and skills needed
- Benefits and compensation
- Company culture and work environment
- Interview scheduling"""

# Error and fallback responses
MAIN_AGENT_REGISTRATION_FALLBACK_RESPONSE = "I apologize, but I need to complete your registration first. Please provide your phone number."

MAIN_AGENT_ERROR_RESPONSE = "I apologize, but I encountered an error. Could you please try again?"

# Default conversation summary
MAIN_AGENT_NO_PREVIOUS_CONVERSATION = "No previous conversation found"