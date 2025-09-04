#!/usr/bin/env python3
"""
InfoAdvisor Fallback Manager.

This module centralizes all fallback logic for the InfoAdvisor,
providing robust responses when the primary AI systems are unavailable.
"""

from typing import Dict, Any, List
import logging

from app.agents.responses import (
    INFO_ADVISOR_GENERAL_FALLBACK_RESPONSE,
    INFO_ADVISOR_REQUIREMENTS_RESPONSE_TEMPLATE,
    INFO_ADVISOR_BENEFITS_RESPONSE_TEMPLATE,
    INFO_ADVISOR_COMPANY_INFO_RESPONSE_TEMPLATE,
    INFO_ADVISOR_SALARY_RESPONSE_TEMPLATE,
    INFO_ADVISOR_GREETING_RESPONSE_TEMPLATE,
    INFO_ADVISOR_POSITION_AVAILABLE_SINGLE_TEMPLATE,
    INFO_ADVISOR_POSITION_AVAILABLE_MULTIPLE_TEMPLATE,
    INFO_ADVISOR_POSITION_DEFAULT_TEMPLATE,
    INFO_ADVISOR_POSITION_UNAVAILABLE_SINGLE_TEMPLATE,
    INFO_ADVISOR_POSITION_UNAVAILABLE_SINGLE_DEFAULT_TEMPLATE,
    INFO_ADVISOR_POSITION_UNAVAILABLE_MULTIPLE_TEMPLATE,
    INFO_ADVISOR_POSITION_UNAVAILABLE_MULTIPLE_DEFAULT_TEMPLATE
)

from config.project_config import BaseConfigurable


class InfoAdvisorFallbackManager:
    """Manages fallback responses and logic for the InfoAdvisor."""
    
    def __init__(self):
        """Initialize the fallback manager."""
        super().__init__()
        self.fallback_job_info = self._get_fallback_job_information()
    
    def _get_fallback_job_information(self) -> Dict[str, Any]:
        """Get fallback job information when embedding system is not available."""
        return {
            'title': 'Python Developer',
            'company': 'TechCorp Solutions',
            'location': 'Remote/Hybrid (San Francisco, CA)',
            'requirements': [
                '3+ years of Python development experience',
                'Experience with Django, Flask, or FastAPI',
                'Knowledge of SQL databases (PostgreSQL preferred)',
                'Experience with cloud platforms (AWS, Azure, or GCP)',
                'Understanding of RESTful APIs and microservices',
                'Familiarity with Git and version control',
                'Strong problem-solving and communication skills'
            ],
            'benefits': [
                'Competitive salary ($120k - $180k based on experience)',
                'Comprehensive health, dental, and vision insurance',
                '401(k) with company matching',
                'Flexible work hours and remote work options',
                'Professional development budget',
                'Unlimited PTO',
                'Stock options'
            ]
        }
    
    def get_fallback_response(self, user_message: str, available_positions: List[Dict[str, str]] = None) -> str:
        """
        Generate fallback response when OpenAI client is not available.
        
        Args:
            user_message: The user's message
            available_positions: List of available positions from embedding manager
            
        Returns:
            Fallback response
        """
        try:
            intent = self._analyze_intent(user_message)
            detected_positions = self._detect_positions_in_query(user_message)
            
            if intent == "requirements":
                return self._respond_to_requirements(detected_positions, available_positions)
            elif intent == "benefits":
                return self._respond_to_benefits(detected_positions, available_positions)
            elif intent == "company":
                return self._respond_to_company(detected_positions, available_positions)
            elif intent == "salary":
                return self._respond_to_salary(detected_positions, available_positions)
            elif intent == "greeting":
                return self._respond_to_greeting(detected_positions, available_positions)
            elif intent == "position_inquiry":
                return self._respond_to_position_inquiry(detected_positions, available_positions)
            else:
                return self._get_generic_fallback_response()
                
        except Exception as e:
            self.logger.error(f"Error generating fallback response: {e}")
            return self._get_generic_fallback_response()
    
    def _analyze_intent(self, user_message: str) -> str:
        """
        Analyze user intent from message.
        
        Args:
            user_message: The user's message
            
        Returns:
            Detected intent
        """
        try:
            # Try to use OpenAI for intent analysis first
            # If that fails, fall back to keyword-based analysis
            return self._analyze_intent_keyword_based(user_message)
        except Exception as e:
            self.logger.warning(f"OpenAI intent analysis failed, using keyword fallback: {e}")
            return self._analyze_intent_keyword_based(user_message)
    
    def _analyze_intent_keyword_based(self, user_message: str) -> str:
        """
        Analyze intent using keyword matching when AI is unavailable.
        
        Args:
            user_message: The user's message
            
        Returns:
            Detected intent
        """
        user_message_lower = user_message.lower()
        
        # Requirements-related keywords
        if any(keyword in user_message_lower for keyword in ['requirement', 'skill', 'experience', 'qualification', 'need', 'must have']):
            return "requirements"
        
        # Benefits-related keywords
        if any(keyword in user_message_lower for keyword in ['benefit', 'salary', 'pay', 'compensation', 'insurance', 'pto', 'vacation', 'perk']):
            return "benefits"
        
        # Company-related keywords
        if any(keyword in user_message_lower for keyword in ['company', 'culture', 'team', 'office', 'location', 'remote', 'hybrid']):
            return "company"
        
        # Salary-related keywords
        if any(keyword in user_message_lower for keyword in ['salary', 'pay', 'compensation', 'money', 'earn', 'income']):
            return "salary"
        
        # Greeting keywords
        if any(keyword in user_message_lower for keyword in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return "greeting"
        
        # Position inquiry keywords
        if any(keyword in user_message_lower for keyword in ['position', 'job', 'role', 'opening', 'available', 'hiring', 'recruiting']):
            return "position_inquiry"
        
        # Default to general inquiry
        return "general"
    
    def _detect_positions_in_query(self, user_message: str) -> List[str]:
        """
        Detect position titles mentioned in the user's query.
        
        Args:
            user_message: The user's message
            
        Returns:
            List of detected position titles
        """
        user_message_lower = user_message.lower()
        detected_positions = []
        
        # Position keywords and their corresponding titles
        position_keywords = {
            'python': 'Python Developer',
            'java': 'Java Developer',
            'frontend': 'Frontend Developer',
            'front-end': 'Frontend Developer',
            'backend': 'Backend Developer',
            'back-end': 'Backend Developer',
            'fullstack': 'Full Stack Developer',
            'full-stack': 'Full Stack Developer',
            'full stack': 'Full Stack Developer',
            'data scientist': 'Data Scientist',
            'data engineer': 'Data Engineer',
            'devops': 'DevOps Engineer',
            'qa': 'QA Engineer',
            'test': 'QA Engineer',
            'testing': 'QA Engineer',
            'product manager': 'Product Manager',
            'project manager': 'Project Manager',
            'developer': 'Developer',
            'engineer': 'Engineer',
            'analyst': 'Data Analyst'
        }
        
        # Check for position keywords
        for keyword, position in position_keywords.items():
            if keyword in user_message_lower:
                detected_positions.append(position)
        
        # Check for software development related terms
        software_dev_keywords = ['software development', 'software engineer', 'software developer', 'programming', 'coding', 'development']
        if any(keyword in user_message_lower for keyword in software_dev_keywords):
            # If asking about software development, include all available developer positions
            available_positions = self._get_available_positions()
            for pos in available_positions:
                if 'developer' in pos['title'].lower() or 'engineer' in pos['title'].lower():
                    detected_positions.append(pos['title'])
        
        # Check for DevOps specifically
        if 'devops' in user_message_lower:
            detected_positions.append('DevOps Engineer')
        
        # Remove duplicates while preserving order
        unique_positions = []
        for position in detected_positions:
            if position not in unique_positions:
                unique_positions.append(position)
        
        return unique_positions
    
    def _get_available_positions(self) -> List[Dict[str, str]]:
        """
        Get list of available positions from fallback data.
        
        Returns:
            List of available positions
        """
        return [self.fallback_job_info]
    
    def _respond_to_requirements(self, detected_positions: List[str], available_positions: List[Dict[str, str]] = None) -> str:
        """Generate response about job requirements."""
        if available_positions and len(available_positions) > 0:
            position = available_positions[0]
            requirements = position.get('requirements', [])
            if requirements:
                req_list = "\n• " + "\n• ".join(requirements[:5])  # Limit to 5 requirements
                return INFO_ADVISOR_REQUIREMENTS_RESPONSE_TEMPLATE.format(
                    position=position['title'],
                    requirements_list=req_list
                )
        
        # Fallback to default requirements
        requirements = self.fallback_job_info['requirements']
        req_list = "\n• " + "\n• ".join(requirements[:5])
        return INFO_ADVISOR_REQUIREMENTS_RESPONSE_TEMPLATE.format(
            position=self.fallback_job_info['title'],
            requirements_list=req_list
        )
    
    def _respond_to_benefits(self, detected_positions: List[str], available_positions: List[Dict[str, str]] = None) -> str:
        """Generate response about job benefits."""
        if available_positions and len(available_positions) > 0:
            position = available_positions[0]
            benefits = position.get('benefits', [])
            if benefits:
                benefit_list = "\n• " + "\n• ".join(benefits[:5])  # Limit to 5 benefits
                return INFO_ADVISOR_BENEFITS_RESPONSE_TEMPLATE.format(
                    position=position['title'],
                    benefits_list=benefit_list
                )
        
        # Fallback to default benefits
        benefits = self.fallback_job_info['benefits']
        benefit_list = "\n• " + "\n• ".join(benefits[:5])
        return INFO_ADVISOR_BENEFITS_RESPONSE_TEMPLATE.format(
            position=self.fallback_job_info['title'],
            benefits_list=benefit_list
        )
    
    def _respond_to_company(self, detected_positions: List[str], available_positions: List[Dict[str, str]] = None) -> str:
        """Generate response about company information."""
        if available_positions and len(available_positions) > 0:
            position = available_positions[0]
            return INFO_ADVISOR_COMPANY_INFO_RESPONSE_TEMPLATE.format(
                company=position['company'],
                location=position['location'],
                position=position['title']
            )
        
        # Fallback to default company info
        return INFO_ADVISOR_COMPANY_INFO_RESPONSE_TEMPLATE.format(
            company=self.fallback_job_info['company'],
            location=self.fallback_job_info['location'],
            position=self.fallback_job_info['title']
        )
    
    def _respond_to_salary(self, detected_positions: List[str], available_positions: List[Dict[str, str]] = None) -> str:
        """Generate response about salary information."""
        if available_positions and len(available_positions) > 0:
            position = available_positions[0]
            # Look for salary info in the position data
            for benefit in position.get('benefits', []):
                if 'salary' in benefit.lower() or '$' in benefit:
                    return INFO_ADVISOR_SALARY_RESPONSE_TEMPLATE.format(
                        position=position['title'],
                        salary_info=benefit
                    )
        
        # Fallback to default salary info
        return INFO_ADVISOR_SALARY_RESPONSE_TEMPLATE.format(
            position=self.fallback_job_info['title'],
            salary_info="competitive salary ($120k - $180k based on experience)"
        )
    
    def _respond_to_greeting(self, detected_positions: List[str], available_positions: List[Dict[str, str]] = None) -> str:
        """Generate response to greetings."""
        if available_positions and len(available_positions) > 0:
            position = available_positions[0]
            return INFO_ADVISOR_GREETING_RESPONSE_TEMPLATE.format(position=position['title'])
        
        # Fallback to default greeting
        return INFO_ADVISOR_GREETING_RESPONSE_TEMPLATE.format(position=self.fallback_job_info['title'])
    
    def _respond_to_position_inquiry(self, detected_positions: List[str], available_positions: List[Dict[str, str]] = None) -> str:
        """Generate response to position inquiries."""
        if not available_positions:
            available_positions = [self.fallback_job_info]
        
        # Initialize variables
        specific_positions = []
        unavailable_positions = []
        
        # Check if user asked about specific positions
        if detected_positions:
            
            for requested_pos in detected_positions:
                is_available = False
                for available_pos in available_positions:
                    # More sophisticated matching - check for exact matches or contained matches
                    if (requested_pos == available_pos['title'] or 
                        requested_pos in available_pos['title'] or 
                        available_pos['title'] in requested_pos or
                        # Handle cases like "DevOps Engineer" vs "Engineer"
                        (requested_pos.lower() in available_pos['title'].lower() and len(requested_pos) > 3) or
                        (available_pos['title'].lower() in requested_pos.lower() and len(requested_pos) > 3)):
                        is_available = True
                        specific_positions.append(available_pos)
                        break
                if not is_available:
                    unavailable_positions.append(requested_pos)
            
            if unavailable_positions:
                # User asked about positions we don't have
                if len(unavailable_positions) == 1:
                    unavailable = unavailable_positions[0].title()
                    if specific_positions:
                        available_list = ", ".join([pos['title'] for pos in specific_positions])
                        return INFO_ADVISOR_POSITION_UNAVAILABLE_SINGLE_TEMPLATE.format(
                            unavailable=unavailable,
                            available_list=available_list
                        )
                    else:
                        return INFO_ADVISOR_POSITION_UNAVAILABLE_SINGLE_DEFAULT_TEMPLATE.format(unavailable=unavailable)
                else:
                    unavailable_list = ", ".join([pos.title() for pos in unavailable_positions])
                    if specific_positions:
                        available_list = ", ".join([pos['title'] for pos in specific_positions])
                        return INFO_ADVISOR_POSITION_UNAVAILABLE_MULTIPLE_TEMPLATE.format(
                            unavailable_list=unavailable_list,
                            available_list=available_list
                        )
                    else:
                        return INFO_ADVISOR_POSITION_UNAVAILABLE_MULTIPLE_DEFAULT_TEMPLATE.format(unavailable_list=unavailable_list)
        
        # User asked about available positions in general
        if specific_positions:
            if len(specific_positions) == 1:
                position = specific_positions[0]
                return INFO_ADVISOR_POSITION_AVAILABLE_SINGLE_TEMPLATE.format(
                    position=position['title'],
                    company=position['company'],
                    location=position['location']
                )
            else:
                position_list = ", ".join([f"{pos['title']}" for pos in specific_positions])
                return INFO_ADVISOR_POSITION_AVAILABLE_MULTIPLE_TEMPLATE.format(
                    count=len(specific_positions),
                    position_list=position_list
                )
        else:
            return INFO_ADVISOR_POSITION_DEFAULT_TEMPLATE
    
    def _get_generic_fallback_response(self) -> str:
        """Get a generic fallback response."""
        return INFO_ADVISOR_GENERAL_FALLBACK_RESPONSE
