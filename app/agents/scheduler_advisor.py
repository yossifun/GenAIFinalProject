from typing import Any, Dict, List
from datetime import date, datetime, timedelta
import json

from app import database
from app.agents.prompts.scheduler_advisor_prompts import SCHEDULER_SYSTEM_PROMPT
from config.project_config import BaseConfigurable


class ScheduleAdvisor(BaseConfigurable):

        def __init__(self, client, model: str = "gpt-4-1106-preview"):
           """
           Initialize the scheduling advisor.

           Args:
               client: OpenAI client instance
               model: Model name to use
           """
           super().__init__()

           self.client = client
           self.model = model
           self.system_prompt = self._get_system_prompt()
           self.tools = self._get_tools()
           self.tool_choice = "auto"  # Let the model decide when to call the function
            
            
           # Initialize database manager
           try:
               self.db_manager = self._get_database_manager()
               self.logger.info("Database manager initialized successfully")
           except Exception as e:
                self.logger.error(f"Failed to initialize database manager: {e}")
                self.db_manager = None
        #End of __init__

        def _get_system_prompt(self) -> str:
            """
            Get the system prompt for the OpenAI model.
            
            Returns:
                str: The system prompt.
            """
            return SCHEDULER_SYSTEM_PROMPT
       # End of _get_system_prompt

        def _get_tools(self) -> List[Dict[str, Any]]:
            """
            Get the tools available for OpenAI function calling.
            
            Returns:
                List[Dict[str, Any]]: List of tool definitions.
            """
            return [
               {
                    "type": "function",
                    "function": {
                        "name": "get_available_slots",
                        "description": "Get available interview time slots for a specific position within a date range. \
                            If no date is specified by the user, return null for start_date and end_date. Do not guess dates.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "position": {
                                    "type": "string",
                                        "description": "The job position to filter by (e.g., Python Developer)."
                                    },
                                    "start_date": {
                                        "type": ["string", "null"],
                                        "format": "date",
                                        "description": "The start date for the search (e.g., 2025-01-01). If no date is specified by the user, set to null."
                                    },
                                    "end_date": {
                                        "type": ["string", "null"],
                                        "format": "date",
                                        "description": "The end date for the search (e.g., 2025-01-31). If no date is specified by the user, set to null."
                                    },
                                    "excluded_slots": {
                                        "type": "array",
                                        "items": { "type": "string" },
                                        "description": "Time slots previously offered and rejected by the user (e.g., '2025-08-05 13:30'). If no slots are specified by the user, set to null"
                                    }
                                },
                            "required": ["position"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "set_schedule",
                        "description": "Schedule an interview for a specific position and time slot for a specific candidate",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "position": {"type": "string"},
                                "slot": {
                                    "type": "string",
                                    "description": "Chosen time slot, e.g., '2025-08-05 13:30'"
                                },
                                "user_id": {
                                    "type": "string",
                                    "description": "The candidate's phone number"
                                }
                            },
                            "required": ["position", "slot", "user_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_schedule",
                        "description": "Get an existing interview schedule for a specific candidate.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "candidate_phone": {"type": "string"}
                            },
                            "required": ["candidate_phone"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "delete_schedule",
                        "description": "Delete all existing interview schedules for a specific candidate.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "candidate_phone": {"type": "string"}
                            },
                            "required": ["candidate_phone"]
                        }
                    }
                }
            ]
        # End of _get_tools

        def _get_database_manager(self):
            """
            Get the database manager instance.
            
            Returns:
                DatabaseManager: The database manager instance.
            """
            return database.DatabaseManager()
        # End of _get_database_manager


        def process_message(self, user_id: str, message: str, context: str = "") -> List[Dict[str, Any]]:
            """
            Get available interview slots based on user message and context.
            
            Args:
                user_message: User message containing the job position and date range.
                context: Previous conversation context.
                
            Returns:
                List of available slots.
            """
            self.logger.info(f"=== SCHEDULER PROCESS_MESSAGE START ===")
            self.logger.info(f"Input message: {message}")
            self.logger.info(f"Context: {context}")
            self.logger.info(f"User ID: {user_id}")
            self.logger.info(f"Tools available: {len(self.tools)}")
            self.logger.info(f"Tool choice: {self.tool_choice}")

            #Prepare system prompt
            today = date.today().strftime("%Y-%m-%d")
            current_year = date.today().year

            system_prompt_text = self.system_prompt.format(
                user_phone=user_id,
                today=today,
                current_year=current_year
            )

            user_prompt = ""
            
             # Prepare the prompt with context
            if context:
                user_prompt = f"Context:\n{context}\n\nCurrent message: {message}\n\nAction:"
            else:
                user_prompt = f"Current message: {message}\n\nAction:"

            self.logger.info(f"System prompt:\n{system_prompt_text}\n Prepared prompt:\n{user_prompt}\n")

            self.logger.info(f"Calling OpenAI API with model: {self.model}")
            self.logger.info(f"Tools structure: {self.tools}")
            
            try:
                response = self.client.chat.completions.create(
                    model= self.model,
                    tools=self.tools,
                    tool_choice=self.tool_choice,
                    messages=[
                        {"role": "system", "content": system_prompt_text},
                        {"role": "user", "content": user_prompt}
                    ],
                )
                self.logger.info(f"OpenAI API call successful, response:\n{response}\n")
                self.logger.info(f"Response choices: {len(response.choices) if response.choices else 0}")
            except Exception as e:
                self.logger.error(f"OpenAI API call failed: {e}")
                raise e


            self.logger.info(f"Checking response for tool calls...")
            if not response.choices:
                self.logger.warning("No choices in response")
                return []
            
            if not response.choices[0].message.tool_calls:
                self.logger.warning("No tool call found in response, returning empty slots")
                self.logger.info(f"Response message content: {response.choices[0].message.content}")
                return []
            
            # Extract the tool call from the response
            tool_call = response.choices[0].message.tool_calls[0]
            self.logger.info(f"Tool call found: {tool_call.function.name}")
            self.logger.info(f"Tool call type: {tool_call.type}")
            
            if tool_call.type != "function":
                self.logger.warning(f"Unexpected tool call type: {tool_call.type}, expected 'function'")
                return []
           
            args = json.loads(tool_call.function.arguments)
            self.logger.info(f"Tool call arguments: {args}")
            if tool_call.function.name == "get_schedule":
                self.logger.info(f"Processing get_schedule tool call")
                # Call the backend function to get the schedule
                if not self.db_manager:
                    self.logger.warning("Database manager not initialized, returning empty schedule")
                    return []
                schedule = self.db_manager.get_schedule(candidate_phone=args["candidate_phone"])
                if not schedule:
                    self.logger.info(f"No schedule found for candidate phone {args['candidate_phone']}")
                    return []
                self.logger.info(f"Retrieved schedule for candidate phone {args['candidate_phone']}")
                self.logger.info(f"Schedule data: {schedule}")
                return schedule
            elif tool_call.function.name == "get_available_slots":
                self.logger.info(f"Processing get_available_slots tool call")
                # Call the backend function to get available slots
                slots = self._get_available_slots(
                    position=args["position"],
                    start_date=args.get("start_date"),
                    end_date=args.get("end_date"),
                    excluded_slots=args.get("excluded_slots", [])
                )
                self.logger.info(f"Retrieved {len(slots)} available slots for position '{args['position']}' from {args.get('start_date')} to {args.get('end_date')}")
                self.logger.info(f"Slots data: {slots}")
                return slots
            elif tool_call.function.name == "set_schedule":
                self.logger.info(f"Processing set_schedule tool call")
                # Call the backend function to set the schedule
                result = self._set_schedule(
                    position=args["position"],
                    slot=args["slot"],
                    user_id=args["user_id"]
                )
                self.logger.info(f"Scheduled interview for position '{args['position']}' at {args['slot']} for user {args['user_id']}")
                self.logger.info(f"Set schedule result: {result}")
                return result
            elif tool_call.function.name == "delete_schedule":
                # Call the backend function to delete the schedule
                result = self._delete_schedules(
                    candidate_phone=args["candidate_phone"]
                )
                self.logger.info(f"Deleting all scheduled interviews for candidate phone {args['candidate_phone']}")
                self.logger.info(f"Delete schedules result: {result}")
                return result
            else:
                self.logger.warning(f"Unknown tool call function: {tool_call.function.name}")
                return []
            
            self.logger.info(f"=== SCHEDULER PROCESS_MESSAGE END ===")
        # End of process_message

        def _get_available_slots(self, position: str = "Python Developer", start_date: str = None, end_date: str = None, excluded_slots: List[str] = None) -> List[Dict[str, Any]]:
            """
            Get available interview slots from the database.
            
            Args:
                position: Job position to filter by
                start_date: Start date for search
                end_date: End date for search
                excluded_slots: List of time slots to exclude from the results
                
            Returns:
                List of available slots
            """

            # Set default values for optional parameters
            # if not start_date:
            #     start_date = datetime.now().isoformat()
            # if not end_date:
            #     end_date = (datetime.now() + timedelta(days=14)).isoformat()
            if not position:
                position = "Python Developer"
            if not excluded_slots:
                excluded_slots = []

            if not self.db_manager:
                self.logger.warning("Database manager not initialized, returning mock data")
                return self._get_mock_slots(position, start_date, end_date)

            slots = self.db_manager.get_available_slots(position, start_date, end_date, excluded_slots=excluded_slots)
            if not slots:
                self.logger.info(f"No available slots found for position '{position}' from {start_date} to {end_date}")
                return []
            self.logger.debug(f"Retrieved {len(slots)} available slots for position '{position}' from {start_date} to {end_date}")
            
            return slots
        # End of _get_available_slots

        def _get_mock_slots(self, position: str = "Python Developer", start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
            """
            Get mock available slots for testing.
            
            Args:
                position: Job position to filter by
                start_date: Start date for search
                end_date: End date for search
            
            Returns:
                List of mock available slots
            """
            from datetime import date, timedelta
            
            if not start_date:
                start_date = date.today().isoformat()
            if not end_date:
                end_date = (date.today() + timedelta(days=7)).isoformat()
            
            return [
                {
                    'id': 1,
                    'date': start_date,
                    'time': '10:00:00',
                    'position': position,
                    'available': True
                },
                {
                    'id': 2,
                    'date': end_date,
                    'time': '14:00:00',
                    'position': position,
                    'available': True
                }
            ]
        # End of _get_mock_slots

        def _set_schedule(self, position: str, slot: str, user_id: str) -> Dict[str, Any]:
            """
            Set the interview schedule in the database.
            
            Args:
                position: Job position for the interview
                slot: Chosen time slot for the interview
                user_id: ID of the user scheduling the interview
                
            Returns:
                Result of the scheduling operation
            """
            # Set default values

            if not slot or not user_id:
                self.logger.error("Schedule slot and candidate phone are required to set schedule")
                return {"status": "error", "message": "Schedule slot and candidate phone are required to set schedule"}
            if not self.db_manager:
                self.logger.error("Database manager not initialized, cannot set schedule")
                return {"status": "error", "message": "Database manager not initialized, cannot set schedule"}
            if not position:
                self.logger.warning("Position not specified, defaulting to 'Python Developer'")
                position = "Python Developer"
            try:
                # Provide a default recruiter phone number
                recruiter_phone = "+1-555-0000"  # Default recruiter phone
                self.logger.info(f"Setting schedule with recruiter_phone: {recruiter_phone}")

                if self.db_manager.set_schedule(position, slot, user_id, recruiter_phone):
                    return {"status": "success", "message": f"Interview scheduled for {position} at {slot}"}
                return {"status": "error", "message": "Failed to set schedule"}
            except Exception as e:
                self.logger.error(f"Failed to set schedule: {e}")
                return {"status": "error", "message": str(e)}
        # End of _set_schedule

        def get_schedule(self, candidate_phone: str) -> Dict[str, Any]:
            """
            Get the interview schedule for a specific candidate.
            
            Args:
                candidate_phone: Phone number of the candidate
                
            Returns:
                Interview schedule for the candidate
            """

            if not candidate_phone:
                self.logger.error("Candidate phone is required to get schedule")
                return {"status": "error", "message": "Candidate phone is required to get schedule"}
            if not self.db_manager:
                self.logger.error("Database manager not initialized, cannot get schedule")
                return {"status": "error", "message": "Database manager not initialized, cannot get schedule"}            
            
            try:
                schedule = self.db_manager.get_schedule(candidate_phone)
                if not schedule:
                    return {"status": "info", "message": "No scheduled interviews found"}
                return {"status": "success", "schedule": schedule}
            except Exception as e:
                self.logger.error(f"Failed to get schedule: {e}")
                return {"status": "error", "message": str(e)}
        # End of get_schedule

        def _delete_schedules(self, candidate_phone: str) -> Dict[str, Any]:
            """
            Delete all interview schedules for a specific candidate.

            Args:
                candidate_phone: Phone number of the candidate
                
            Returns:
                Interview schedule for the candidate
            """
            if not self.db_manager:
                self.logger.warning("Database manager not initialized, cannot delete schedule")
                return {"status": "error", "message": "Database manager not initialized"}
            try:
                result = self.db_manager.delete_schedules(candidate_phone)
                self.logger.info(f"Deleted schedule for candidate phone {candidate_phone}")
                return {"status": "success", "message": f"Schedules deleted for {candidate_phone}"}
            except Exception as e:
                self.logger.error(f"Failed to delete schedule: {e}")
                return {"status": "error", "message": str(e)}
            finally:
                self.logger.info(f"Finished deleting schedule for {candidate_phone}")
            # End of _delete_schedules

        def process_message_wrapper(self, user_id: str, message: str, context: str = "") -> Dict[str, Any]:
            """
            Wrapper method to maintain compatibility with SchedulingAdvisor interface.
            
            Args:
                message: User message
                context: Previous conversation context
                user_id: User identifier for scheduling
                
            Returns:
                Dictionary with response and action details (compatible with SchedulingAdvisor)
            """
            self.logger.info(f"=== SCHEDULER WRAPPER START ===")
            self.logger.info(f"Wrapper input - message: {message}, context: {context}, user_id: {user_id}")
            
            try:
                # Call the original process_message method
                self.logger.info(f"Calling process_message method...")
                result = self.process_message(user_id, message, context)
                self.logger.info(f"process_message returned: {result}")
                self.logger.info(f"Result type: {type(result)}")
                
                # If result is a list (from get_available_slots), format it as a response
                if isinstance(result, list):
                    self.logger.info(f"Processing list result with {len(result)} items")
                    if not result:
                        self.logger.info(f"Empty list result, returning no slots message")
                        return {
                            'action': 'show_slots',
                            'message': """I apologize, but I don't have any available interview slots at the moment. 

Could you please let me know your preferred time range (morning, afternoon, or evening) and I'll check for availability in the coming weeks? Alternatively, you can provide your contact information and I'll have our scheduling team reach out to you directly.""",
                            'metadata': {'slots': [], 'reason': 'no_slots_available'}
                        }
                    else:
                        self.logger.info(f"Processing non-empty list result")
                        # Format the slots into a user-friendly response
                        response = "Great! I have several available interview slots for our Python Developer position. Here are some options:\n\n"
                        
                        # Group slots by date
                        slots_by_date = {}
                        for slot in result:
                            date_str = slot['date']
                            if date_str not in slots_by_date:
                                slots_by_date[date_str] = []
                            slots_by_date[date_str].append(slot)
                        
                        # Format each date group
                        for date_str, slots in slots_by_date.items():
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                            day_name = date_obj.strftime('%A, %B %d')
                            response += f"**{day_name}:**\n"
                            
                            for slot in slots:
                                time_str = slot['time'][:5]  # Remove seconds
                                response += f"• {time_str}\n"
                            response += "\n"
                        
                        response += "Please let me know which time slot works best for you, or if you'd like to see more options."
                        
                        self.logger.info(f"Formatted response: {response}")
                        return {
                            'action': 'show_slots',
                            'message': response,
                            'metadata': {
                                'slots': result,
                                'position': 'Python Developer'
                            }
                        }
                
                # If result is a dictionary (from set_schedule, get_schedule, etc.)
                elif isinstance(result, dict):
                    self.logger.info(f"Processing dictionary result: {result}")
                    if 'status' in result:
                        if result['status'] == 'success':
                            if 'message' in result and 'scheduled' in result['message'].lower():
                                self.logger.info(f"Returning schedule_confirmed action")
                                return {
                                    'action': 'schedule_confirmed',
                                    'message': result['message'],
                                    'metadata': {'scheduling_completed': True}
                                }
                            else:
                                self.logger.info(f"Returning continue action for successful operation")
                                return {
                                    'action': 'continue',
                                    'message': result.get('message', 'Operation completed successfully.'),
                                    'metadata': result
                                }
                        else:
                            self.logger.info(f"Returning error action for failed operation")
                            return {
                                'action': 'error',
                                'message': result.get('message', 'An error occurred.'),
                                'metadata': result
                            }
                    else:
                        self.logger.info(f"Returning continue action for dictionary without status")
                        return {
                            'action': 'continue',
                            'message': str(result),
                            'metadata': result
                        }
                
                # Fallback for unexpected result types
                else:
                    self.logger.info(f"Unexpected result type: {type(result)}, returning handoff")
                    return {
                        'action': 'handoff',
                        'message': 'This seems to be outside my scheduling expertise. Let me connect you with our main agent.',
                        'metadata': {'reason': 'unexpected_result_type', 'result': str(result)}
                    }
                    
            except Exception as e:
                self.logger.error(f"Error in process_message_wrapper: {e}")
                self.logger.error(f"Exception type: {type(e)}")
                self.logger.error(f"Exception details: {str(e)}")
                return {
                    'action': 'error',
                    'message': 'I encountered an error processing your request.',
                    'metadata': {'error': str(e)}
                }
            
            self.logger.info(f"=== SCHEDULER WRAPPER END ===")
        # End of process_message_wrapper
        