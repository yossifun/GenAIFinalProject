"""
Main Agent for the GenAI SMS Chatbot.
All prompts are loaded from main_agent_prompts.py.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib import response
from openai import OpenAI
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.agents.exit_advisor import ExitAdvisor
from app.agents.scheduler_advisor import ScheduleAdvisor
from app.agents.info_advisor import InfoAdvisor
from app.agents.main_agent_fallback_manager import MainAgentFallbackManager
from app.agents.prompts.main_agent_prompts import (
    MAIN_SYSTEM_PROMPT,
    CANDIDATE_NAME_EXTRACTION_PROMPT,
    CANDIDATE_PHONE_NUMBER_EXTRACTION_PROMPT,
    DYNAMIC_WELCOME_MESSAGE_PROMPT,
    WELCOME_AND_REGISTRATION_PROMPT,
    DYNAMIC_JOB_INTEREST_PROMPT,
    POST_SCHEDULING_MESSAGE_PROMPT,
    REGISTRATION_PROMPT
)
from app.agents.responses import (
    MAIN_AGENT_JOB_INTEREST_CONFIRMATION_RESPONSE,
    MAIN_AGENT_REGISTRATION_FALLBACK_RESPONSE,
    MAIN_AGENT_ERROR_RESPONSE
)
from app.mongodb_manager import global_mongodb_manager
from config.project_config import BaseConfigurable
import streamlit as st



class MainAgent(BaseConfigurable):
    REGISTRATION_STEP_WELCOME = "welcome"
    REGISTRATION_STEP_JOB_INTEREST = "job_interest"
    REGISTRATION_STEP_COMPLETE = "complete"

    def __init__(self, client=None, model=None, mongodb_mgr=None):
        super().__init__()
        self.model = model or self.config.get_model()
        self.client = client or self.config.get_client()
        self.mongodb_client_manager = mongodb_mgr or global_mongodb_manager
        self.system_prompt = MAIN_SYSTEM_PROMPT

        self.exit_advisor = ExitAdvisor(self.client, self.config.get_fine_tune_model())
        self.scheduler = ScheduleAdvisor(self.client, self.model)
        self.info_advisor = InfoAdvisor(self.client, self.model)
        self.fallback_manager = MainAgentFallbackManager()

        self.conversation_history: List[Dict[str, Any]] = []
        self.current_phone_number: Optional[str] = None
        self.current_name: Optional[str] = None
        self.user_registered: bool = False
        self.registration_step: str = self.REGISTRATION_STEP_WELCOME

        self.logger.info("Main agent initialized successfully.")

    # ------------------------- Registration -------------------------
    def generate_registration_message(self, user_message: str, message_context: str) -> str:
        if not self.client:
            self.logger.warning("LLM client unavailable. Returning fallback registration message.")
            return "Hi! Could you please tell me your full name and phone number to proceed?"

        current_hour = datetime.now().hour
        time_of_day = "morning" if 5 <= current_hour < 12 else "afternoon" if 12 <= current_hour < 17 else "evening"

        attempt_count = sum(1 for msg in self.conversation_history if msg['role'] == 'assistant') + 1

        chat_history = [{"role": msg['role'], "content": msg['content']} for msg in self.conversation_history[-5:]]
        prompt_text = WELCOME_AND_REGISTRATION_PROMPT.format(
            user_name=self.current_name or "unknown",
            user_phone=self.current_phone_number or "unknown",
            time_of_day=time_of_day,
            attempt_count=attempt_count
        )
        chat_history.append({"role": "user", "content": prompt_text})
        self.logger.debug(f"Registration prompt:\n{prompt_text}")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "You are a helpful recruitment assistant."}] + chat_history,
                max_tokens=120,
                temperature=0.9
            )
            message = response.choices[0].message.content.strip()
            self.logger.info("Generated registration message.")
            return message if message else "Hi! Could you please tell me your full name and phone number to proceed?"
        except Exception as e:
            self.logger.error(f"Error generating registration message: {e}")
            return "Hi! Could you please tell me your full name and phone number to proceed?"

    # ------------------------- Conversation Processor -------------------------
    def process_message(self, user_message: str) -> Dict[str, Any]:
        try:
            message_context = self.get_conversation_context(self.conversation_history, self.current_phone_number)
            self.logger.debug(f"Conversation context:\n{message_context}")

            self.conversation_history.append({"role": "user", "content": user_message})
            self.logger.debug(f"User message: {user_message}")

             # ---------------- Decide action ----------------
            action = self.decide_action(user_message, message_context)
            self.logger.info(f"Decided action: {action}")

             # Prepare response data structure
            response_data = {
                'action': action,
                'message': user_message,
                'context': message_context,
                'metadata': {
                    'name': self.current_name,
                    'phone_number': self.current_phone_number,
                    'user_registered': self.user_registered,
                    'action': action
                }
            }

             # ---------------- Generate response ----------------
            if action == "continue" or (action != "end" and not self.user_registered):

                # ---------------- Registration flow ----------------
                if not self.user_registered or self.registration_step != self.REGISTRATION_STEP_COMPLETE:
                    response_data = self.handle_registration(
                        user_message, message_context, self.current_name,
                        self.current_phone_number, self.user_registered, self.registration_step
                    )
                    self.conversation_history.append({"role": "assistant", "content": response_data['message']})
                    self.logger.info(f"Processed registration step: {self.registration_step}")

                    # Enrich metadata for sidebar & Streamlit state
                    reg_meta = response_data.setdefault("metadata", {})
                    reg_meta.setdefault("name", self.current_name or "N/A")
                    reg_meta.setdefault("phone_number", self.current_phone_number or "N/A")
                    # user_exists may already be set in handle_registration; keep it or compute
                    if "user_exists" not in reg_meta:
                        try:
                            reg_meta["user_exists"] = bool(
                                self.current_phone_number and self.mongodb_client_manager and
                                self.mongodb_client_manager.user_exists(self.current_phone_number)
                            )
                        except Exception as e:
                            self.logger.debug(f"user_exists lookup failed: {e}")
                            reg_meta["user_exists"] = False

                    reg_meta.setdefault("registration_step", self.registration_step)
                    reg_meta.setdefault("scheduled_interview", "N/A")
                    reg_meta["available_positions"] = self._safe_get_available_positions()
                    reg_meta["action"] = action

                    # Mirror into Streamlit (if available)
                    self._update_streamlit_state(reg_meta)

                else:
                    # Get response from info advisor
                    response_text = self.info_advisor.generate_response(user_message, message_context)
                    self.conversation_history.append({"role": "assistant", "content": response_text})
                    response_data['message'] = response_text

                    # Build metadata for sidebar & Streamlit
                    metadata = {
                        "user_registered": self.user_registered,
                        "registration_step": self.registration_step,
                        "conversation_length": len(self.conversation_history),
                        "name": self.current_name or "N/A",
                        "phone_number": self.current_phone_number or "N/A",
                        "action": action
                    }
                    # user_exists
                    try:
                        metadata["user_exists"] = bool(
                            self.current_phone_number and self.mongodb_client_manager and
                            self.mongodb_client_manager.user_exists(self.current_phone_number)
                        )
                    except Exception as e:
                        self.logger.debug(f"user_exists lookup failed: {e}")
                        metadata["user_exists"] = False

                    metadata["scheduled_interview"] = "N/A"
                    metadata["available_positions"] = self._safe_get_available_positions()

                    # Mirror into Streamlit
                    self._update_streamlit_state(metadata)

            if action == "schedule" and self.user_registered and self.current_phone_number:
                self.logger.info("Processing scheduling request.")
                schedule_result = self.scheduler.process_message_wrapper(
                    user_message, message_context, self.current_phone_number
                )
                response_data['message'] = schedule_result['message']
                response_data['action'] = schedule_result['action']
                response_data['metadata'].update(schedule_result.get('metadata', {}))

                # Handle handoff to main agent if needed
                if schedule_result['action'] == 'handoff':
                    response_data['action'] = 'continue'
                    # Let the info advisor handle the response
                    info_response = self.info_advisor.generate_response(user_message, message_context)
                    response_data['message'] = info_response
                
                # Handle post-scheduling conversation flow
                elif schedule_result['action'] == 'schedule_confirmed':
                    # After successful scheduling, ask if there's anything else they need
                    response_data['message'] = self._generate_post_scheduling_message(schedule_result)
                    response_data['action'] = 'continue'  # Keep conversation open instead of ending
                    response_data['metadata']['scheduling_completed'] = True

                # Format interview info for sidebar
                pos = schedule_result.get("metadata", {}).get("position", "Role")
                slot = schedule_result.get("metadata", {}).get("slot", "time")
                scheduled_str = f"{pos} at {slot}" if pos and slot else "N/A"

                self.conversation_history.append({"role": "assistant", "content":  response_data['message']})
                self.logger.debug(f"Assistant response (schedule): {response_data['message']}")

                metadata = {
                    "user_registered": self.user_registered,
                    "registration_step": self.registration_step,
                    "conversation_length": len(self.conversation_history),
                    "name": self.current_name or "N/A",
                    "phone_number": self.current_phone_number or "N/A",
                    "user_exists": True,  # if we got here with a phone, treat as known
                    "scheduled_interview": scheduled_str,
                    "available_positions": self._safe_get_available_positions(),
                    "action": action
                }

                # Mirror into Streamlit
                self._update_streamlit_state(metadata)

            if action == "end":

                # Capture before reset so sidebar still shows the last known info
                metadata = {
                    "user_registered": self.user_registered,
                    "registration_step": self.registration_step,
                    "conversation_length": len(self.conversation_history),
                    "name": self.current_name or "N/A",
                    "phone_number": self.current_phone_number or "N/A",
                    'action': action
                }                
                try:
                    metadata["user_exists"] = bool(
                        self.current_phone_number and self.mongodb_client_manager and
                        self.mongodb_client_manager.user_exists(self.current_phone_number)
                    )
                except Exception as e:
                    self.logger.debug(f"user_exists lookup failed: {e}")
                    metadata["user_exists"] = False

                metadata["scheduled_interview"] = "N/A"
                metadata["available_positions"] = self._safe_get_available_positions()

                # Process conversation end with MongoDB integration
                if self.current_phone_number:
                    end_result = self.exit_advisor.process_conversation_end(
                        self.current_phone_number, 
                        self.conversation_history, 
                        user_message
                    )
                    response_data['message'] = end_result['exit_message']
                    response_data['metadata']['conversation_summary'] = end_result['conversation_summary']
                    response_data['metadata']['saved_to_mongodb'] = end_result['saved_to_mongodb']                    
                    
                else:
                    # Fallback if no phone number
                    response = self.exit_advisor.generate_exit_message(user_message, message_context)
                    response_data['message'] = response
                
                self.conversation_history.append({"role": "assistant", "content": response_data['message']})
                self.logger.debug(f"Assistant response (end): {response_data['message']}")

                # Mirror into Streamlit *before* reset
                self._update_streamlit_state(metadata)

                # Reset internal state
                self.reset_conversation()


            if action not in ["continue", "schedule", "end"]:
                response_text = MAIN_AGENT_ERROR_RESPONSE
                self.logger.warning(f"Unknown action '{action}' produced fallback response.")
                self.conversation_history.append({"role": "assistant", "content": response_text})
                response_data['message'] = response_text

                metadata = {
                    "user_registered": self.user_registered,
                    "registration_step": self.registration_step,
                    "conversation_length": len(self.conversation_history),
                    "name": self.current_name or "N/A",
                    "phone_number": self.current_phone_number or "N/A",
                    "user_exists": False,
                    "scheduled_interview": "N/A",
                    "available_positions": self._safe_get_available_positions(),
                    "action": f"Unknown action reported: {action}"
                }
                self._update_streamlit_state(metadata)
            
            self.logger.info(f"Processed message with action: {response_data['action']} for phone: {self.current_phone_number}")
            return response_data
   

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return {
                "action": "continue",
                "message": MAIN_AGENT_ERROR_RESPONSE,
                "metadata": {"error": str(e)}
            }
        

    def reset_conversation(self):
        """Reset the conversation history and registration state."""
        self.conversation_history = []
        self.current_name = None
        self.current_phone_number = None
        self.user_registered = False
        self.registration_step = self.REGISTRATION_STEP_WELCOME
        self.logger.info("Conversation history and registration state reset")


    def decide_action(self, user_message: str, context: str = "") -> str:
        """
        Decide the appropriate action based on user message and context.
        
        Args:
            user_message: The current user message
            context: Previous conversation context

        Returns:
            Action to take: "continue", "schedule", or "end"
        """
        try:
            if not self.client:
                self.logger.warning("OpenAI client not available, using fallback logic")
                return self.fallback_manager.decide_action(user_message)

            system_prompt_text = self.system_prompt.format(
                user_name=self.current_name or "unknown",
                user_phone=self.current_phone_number or "unknown"
            )

            # Prepare the prompt with context
            if context:
                prompt = f"Context:\n{context}\n\nCurrent message: {user_message}\n\nAction:"
            else:
                prompt = f"Current message: {user_message}\n\nAction:"

            self.logger.debug(f"Deciding action with system prompt:\n{system_prompt_text}\n\nUser prompt:\n{prompt}\n")

            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt_text},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )

            action = response.choices[0].message.content.strip().lower()

            # Validate action
            if action not in ["continue", "schedule", "end"]:
                self.logger.warning(f"Invalid action '{action}' received, defaulting to 'continue'")
                action = "continue"
            elif not self.user_registered and action != "end":
                self.logger.info("User not registered, forcing 'continue' action.")
                action = "continue"

            self.logger.info(f"Main agent decided action: {action}")
            return action

        except Exception as e:
            self.logger.error(f"Error in main agent decision: {str(e)}")
            return self.fallback_manager.decide_action(user_message)

 
    # ------------------------- Conversation Context -------------------------
    def get_conversation_context(self, conversation_history: List[Dict[str, Any]], current_phone_number: Optional[str] = None) -> str:
        context_parts = []

        if current_phone_number and self.mongodb_client_manager:
            previous_summary = self.mongodb_client_manager.get_user_conversation_summary(current_phone_number)
            if previous_summary:
                context_parts.append(f"Previous conversation summary: {previous_summary}")
                self.logger.debug("Added previous conversation summary to context.")

        recent_messages = conversation_history[-6:]
        for msg in recent_messages:
            role = "User" if msg.get('role') == 'user' else "Assistant"
            content = msg.get('content', '')
            context_parts.append(f"{role}: {content}")

        return "\n".join(context_parts)

    # ------------------------- Registration Handling -------------------------
    def handle_registration(self, user_message: str, message_context: str,
                            current_name: Optional[str], current_phone: Optional[str],
                            user_registered: bool, registration_step: str) -> Dict[str, Any]:
        """
        Handles registration flow:
        1. Extracts candidate name and phone
        2. Updates current state
        3. Returns appropriate assistant message + enriched metadata
        """
        self.logger.debug(f"Handling registration. Step: {registration_step}, User message: {user_message}")

        # Extract name if unknown
        if not current_name:
            candidate_name = self.extract_candidate_name(user_message, message_context)
            if candidate_name != "none":
                self.current_name = candidate_name
                self.logger.info(f"Extracted candidate name: {candidate_name}")
            else:
                self.logger.debug("Candidate name not found in message.")

        # Extract phone if unknown
        if not current_phone:
            candidate_phone = self.extract_candidate_phone(user_message, message_context)
            if candidate_phone != "none":
                self.current_phone_number = candidate_phone
                self.logger.info(f"Extracted candidate phone: {candidate_phone}")
            else:
                self.logger.debug("Candidate phone not found in message.")

        # Determine registration state
        if self.current_name and self.current_phone_number:
            self.user_registered = True
            self.registration_step = self.REGISTRATION_STEP_COMPLETE
            self.logger.info("Registration complete.")
        else:
            self.user_registered = False
            self.registration_step = self.REGISTRATION_STEP_WELCOME
            self.logger.debug(f"Registration step remains: {self.registration_step}")

        # Generate assistant message
        message = self.generate_registration_message(user_message, message_context)
        self.logger.debug(f"Generated registration message: {message}")

        # Determine if user is new or returning
        is_returning = False
        if self.user_registered and self.current_phone_number:
            is_returning = self.mongodb_client_manager.user_exists(self.current_phone_number)
            if is_returning:
                self.logger.info(f"User {self.current_phone_number} is returning.")
            else:
                self.logger.info(f"User {self.current_phone_number} is new.")

        if self.user_registered and not is_returning:
            self.logger.info(f"Creating new user with phone number: {self.current_phone_number}")
            self.mongodb_client_manager.create_new_user(self.current_phone_number)

        # Lookup scheduled interview (or return N/A)
        if self.user_registered and self.current_phone_number:
            scheduled_interview = self.scheduler.get_schedule(self.current_phone_number)
        else:
            scheduled_interview = None

        scheduled_str = "N/A"
        if scheduled_interview and isinstance(scheduled_interview, dict) \
            and 'date' in scheduled_interview and 'time' in scheduled_interview \
                and scheduled_interview['date'] and scheduled_interview['time']:
            # Combine date + time into a datetime object
            dt = datetime.strptime(
                f"{scheduled_interview['date']} {scheduled_interview['time']}",
                "%Y-%m-%d %H:%M"
            )
            scheduled_str = dt.strftime("%Y-%m-%d %H:%M")
        else:
            scheduled_str = "N/A"

        return {
            "action": "continue",
            "message": message,
            "metadata": {
                "user_registered": self.user_registered,
                "registration_step": self.registration_step,
                "candidate_name": self.current_name or "Unknown",
                "phone_number": self.current_phone_number or "Unknown",
                "user_type": "Returning" if is_returning else "New",
                "scheduled_interview": scheduled_str
            }
        }

    # ------------------------- Candidate Data Extraction -------------------------
    def extract_candidate_name(self, user_message: str, message_context: str) -> str:
        """
        Extract candidate's name using the LLM and the prompt from prompts file.
        Returns 'none' if name not found.
        """
        system_prompt = CANDIDATE_NAME_EXTRACTION_PROMPT
        # Prepare the prompt with context
        if message_context:
            prompt = f"Context:\n{message_context}\n\nCurrent message: {user_message}\n\nAction:"
        else:
            prompt = f"Current message: {user_message}\n\nAction:"

        self.logger.debug(f"Extracting candidate name with prompt:\n{system_prompt}\nUser message: {user_message}")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User message: {prompt}\n\nExtract the candidate's name only."}
                ],
                max_tokens=30,
                temperature=0.0
            )
            name = response.choices[0].message.content.strip() if response.choices else "none"
            self.logger.debug(f"Extracted name: {name}")
            return name or "none"
        except Exception as e:
            self.logger.error(f"Error extracting candidate name: {e}")
            return "none"

    def extract_candidate_phone(self, user_message: str, message_context: str) -> str:
        """
        Extract candidate's phone number using the LLM and the prompt from prompts file.
        Returns 'none' if phone not found.
        """
        system_prompt = CANDIDATE_PHONE_NUMBER_EXTRACTION_PROMPT
        # Prepare the prompt with context
        if message_context:
            prompt = f"Context:\n{message_context}\n\nCurrent message: {user_message}\n\nAction:"
        else:
            prompt = f"Current message: {user_message}\n\nAction:"

        self.logger.debug(f"Extracting candidate phone with prompt:\n{system_prompt}\nUser message: {user_message}")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=20,
                temperature=0.1
            )
            phone = response.choices[0].message.content.strip() if response.choices else "none"
            self.logger.debug(f"Extracted phone: {phone}")
            return phone or "none"
        except Exception as e:
            self.logger.error(f"Error extracting candidate phone: {e}")
            return "none"    
    
    
    def _safe_get_available_positions(self) -> list:
        """Best-effort fetch of available positions for sidebar display."""
        try:
            positions = self.info_advisor.get_available_positions()
            return [p for p in positions if p.get('title') != 'All Positions']
        except Exception as e:
            self.logger.debug(f"Could not fetch available positions: {e}")
            return []

    def _update_streamlit_state(self, metadata: Dict[str, Any]) -> None:
        """Mirror key values into Streamlit session_state if Streamlit is available."""
        try:
            import streamlit as st
        except Exception:
            # Not running in Streamlit (e.g., tests) – silently skip
            self.logger.debug("Streamlit not available; skipping session_state update.")
            return

        name = metadata.get("name", self.current_name)
        phone = metadata.get("phone_number", self.current_phone_number)
        if name:
            st.session_state["candidate_name"] = name
        if phone:
            st.session_state["candidate_phone"] = phone

        if "user_exists" in metadata:
            st.session_state["is_returning"] = bool(metadata["user_exists"])

        if "scheduled_interview" in metadata:
            st.session_state["interview"] = metadata["scheduled_interview"]

        if "registration_step" in metadata:
            st.session_state["registration_step"] = metadata["registration_step"]

        if "available_positions" in metadata:
            st.session_state["available_positions"] = metadata["available_positions"]
        if "action" in metadata:
            st.session_state["action"] = metadata["action"]
        

    def _normalize_interview_info(self, info):
        """Ensure interview info is always a dict with date+time or None."""
        if not info:
            return None
        if isinstance(info, dict):
            date = info.get("date")
            time = info.get("time")
            if date and time:
                return {"date": date, "time": time}
            return None
        # If it came back as a string (like "none"), ignore it
        return None
    
    def _generate_post_scheduling_message(self, schedule_result: Dict[str, Any]) -> str:
        """
        Generate a post-scheduling message that guides the conversation to a natural conclusion.
        
        Args:
            schedule_result: Result from scheduling advisor
            
        Returns:
            Post-scheduling message
        """
        try:
            if not self.client:
                return self.fallback_manager.generate_post_scheduling_message(schedule_result)
            
            # Extract scheduling details
            position = schedule_result.get('metadata', {}).get('position', 'Python Developer')
            slot = schedule_result.get('metadata', {}).get('slot', 'scheduled time')
            
            prompt = POST_SCHEDULING_MESSAGE_PROMPT.format(position=position, slot=slot)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional recruiter managing post-scheduling conversation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating post-scheduling message: {str(e)}")
            return self.fallback_manager.generate_post_scheduling_message(schedule_result)
    