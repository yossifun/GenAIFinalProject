"""
Info Advisor Agent for the GenAI SMS Chatbot.

This agent is responsible for handling candidate questions, providing
information about the position, and maintaining conversation engagement.
"""

import logging
from typing import Dict, Any, List, Optional

from app.embedding import EmbeddingManager
from app.agents.info_advisor_fallback_manager import InfoAdvisorFallbackManager
from app.agents.prompts.info_advisor_prompts import (
    INFO_ADVISOR_SYSTEM_PROMPT,
    AI_RESPONSE_PROMPT_TEMPLATE
)

from config.project_config import BaseConfigurable


class InfoAdvisor(BaseConfigurable):
    """
    Info advisor that handles candidate questions and maintains engagement.
    """
    
    def __init__(self, client, model: str):
        """
        Initialize the info advisor.
        
        Args:
            client: OpenAI client instance
            model: Model name to use
        """
        super().__init__()
        self.client = client
        self.model = model
        self.system_prompt = self._get_system_prompt()
        
        # Initialize embedding manager for job information
        try:
            self.embedding_manager = EmbeddingManager()
            self.logger.info("Embedding manager initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding manager: {e}")
            self.embedding_manager = None
        
        # Initialize fallback manager
        self.fallback_manager = InfoAdvisorFallbackManager()
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the info advisor."""
        return INFO_ADVISOR_SYSTEM_PROMPT

    def get_available_positions(self) -> List[str]:
        """Get a list of available job positions."""
        if not self.embedding_manager:
            self.logger.warning("Embedding manager not available, using fallback")
            return self.fallback_manager._get_available_positions()
        return self.embedding_manager.get_available_positions()

    def _get_relevant_job_info(self, query: str, n_results: int = 3, position_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get relevant job information from the embedding system.
        
        Args:
            query: Search query
            n_results: Number of results to return
            position_filter: Optional position title to filter by
            
        Returns:
            List of relevant job information documents
        """
        try:
            if self.embedding_manager:
                return self.embedding_manager.search_similar_documents(query, n_results, position_filter)
            else:
                self.logger.warning("Embedding manager not available, using fallback")
                return []
        except Exception as e:
            self.logger.error(f"Error getting relevant job info: {str(e)}")
            return []
    
    def generate_response(self, user_message: str, context: str = "") -> str:
        """
        Generate a response to the user's message using VectorDB information.
        
        Args:
            user_message: The user's message
            context: Previous conversation context
            
        Returns:
            Generated response
        """
        try:
            if not self.client:
                self.logger.warning("OpenAI client not available, using fallback response")
                return self.fallback_manager.get_fallback_response(user_message, [])
            
            # Detect positions mentioned in the query
            detected_positions = self.fallback_manager._detect_positions_in_query(user_message)
            
            # Get relevant information from VectorDB
            if detected_positions:
                # If specific positions are mentioned, search for each one
                all_relevant_info = []
                for position in detected_positions:
                    position_info = self._get_relevant_job_info(user_message, n_results=2, position_filter=position)
                    all_relevant_info.extend(position_info)
                
                # Remove duplicates based on content
                unique_info = []
                seen_content = set()
                for info in all_relevant_info:
                    content_hash = hash(info['content'])
                    if content_hash not in seen_content:
                        unique_info.append(info)
                        seen_content.add(content_hash)
                
                relevant_info = unique_info[:4]  # Limit to top 4 results
            else:
                # No specific position mentioned, search broadly
                relevant_info = self._get_relevant_job_info(user_message, n_results=3)
            
            # Generate AI response with context
            return self._generate_ai_response_with_context(user_message, relevant_info, context, detected_positions)
                
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return self.fallback_manager.get_fallback_response(user_message, [])
    
    def _generate_ai_response_with_context(self, user_message: str, relevant_info: List[Dict[str, Any]], context: str = "", detected_positions: List[str] = None) -> str:
        """
        Generate AI response using VectorDB context.
        
        Args:
            user_message: The user's message
            relevant_info: Relevant information from VectorDB
            context: Previous conversation context
            detected_positions: List of detected positions
            
        Returns:
            AI-generated response
        """
        # Prepare context from VectorDB
        context_info = ""
        positions_mentioned = set()
        
        for i, info in enumerate(relevant_info, 1):
            context_info += f"Information {i}:\n{info['content']}\n\n"
            position_title = info['metadata'].get('position_title', 'Unknown')
            positions_mentioned.add(position_title)
        
        # Create position context
        position_context = ""
        if detected_positions:
            position_context = f"Positions mentioned in query: {', '.join(detected_positions)}. "
        elif positions_mentioned:
            position_context = f"Relevant positions found: {', '.join(positions_mentioned)}. "
        
        prompt = AI_RESPONSE_PROMPT_TEMPLATE.format(
            user_message=user_message,
            position_context=position_context,
            context_info=context_info,
            context=context
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
 