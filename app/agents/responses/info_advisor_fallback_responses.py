"""
Info Advisor Fallback Responses for the GenAI SMS Chatbot.

This module contains fallback response constants used by the InfoAdvisor when OpenAI is not available.
"""

# Generic fallback response for general inquiries
INFO_ADVISOR_GENERAL_FALLBACK_RESPONSE = """Thank you for your interest in our positions! I'd be happy to answer any questions you have about our various roles, requirements, benefits, or company culture. What would you like to know more about? I'd be happy to schedule an interview to discuss this opportunity."""

# Requirements-related responses
INFO_ADVISOR_REQUIREMENTS_RESPONSE_TEMPLATE = """For the {position} position, here are the key requirements:{requirements_list}

Would you like to know more about the benefits or schedule an interview to discuss this opportunity?"""

# Benefits-related responses
INFO_ADVISOR_BENEFITS_RESPONSE_TEMPLATE = """The {position} position offers excellent benefits:{benefits_list}

Would you like to know more about the requirements or schedule an interview to discuss this opportunity?"""

# Company information responses
INFO_ADVISOR_COMPANY_INFO_RESPONSE_TEMPLATE = """{company} is a dynamic tech company located in {location}. We offer a collaborative environment with opportunities for growth and innovation.

Would you like to know more about the {position} position or schedule an interview to discuss this opportunity?"""

# Salary-related responses
INFO_ADVISOR_SALARY_RESPONSE_TEMPLATE = """The {position} position offers {salary_info}. This is competitive for the market and based on experience.

Would you like to know more about the requirements or schedule an interview to discuss this opportunity?"""

# Greeting responses
INFO_ADVISOR_GREETING_RESPONSE_TEMPLATE = """Hello! I'm here to help you learn more about our {position} position. What would you like to know about the role, requirements, benefits, or company culture? I'd be happy to schedule an interview to discuss this opportunity."""

# Position inquiry responses
INFO_ADVISOR_POSITION_AVAILABLE_SINGLE_TEMPLATE = """Great question! We currently have a {position} position available at {company} ({location}). This is a full-time role. Would you like to know more about the requirements and responsibilities for this position? I'd be happy to schedule an interview to discuss this opportunity."""

INFO_ADVISOR_POSITION_AVAILABLE_MULTIPLE_TEMPLATE = """Great question! We currently have {count} positions available: {position_list}. Each offers unique challenges and growth opportunities. Which one interests you most? I'd be happy to schedule an interview to discuss this opportunity."""

INFO_ADVISOR_POSITION_DEFAULT_TEMPLATE = """Great question! We currently have a Python Developer position available. This is a full-time role with opportunities for growth and development. Would you like to know more about the requirements and responsibilities? I'd be happy to schedule an interview to discuss this opportunity."""

# Position unavailable responses
INFO_ADVISOR_POSITION_UNAVAILABLE_SINGLE_TEMPLATE = """We don't currently have a {unavailable} position available. However, we do have {available_list} positions open. Would you like to know more about any of these roles? I'd be happy to schedule an interview to discuss this opportunity."""

INFO_ADVISOR_POSITION_UNAVAILABLE_SINGLE_DEFAULT_TEMPLATE = """We don't currently have a {unavailable} position available. We do have a Python Developer position open though. Would you like to know more about this role? I'd be happy to schedule an interview to discuss this opportunity."""

INFO_ADVISOR_POSITION_UNAVAILABLE_MULTIPLE_TEMPLATE = """We don't currently have {unavailable_list} positions available. However, we do have {available_list} positions open. Would you like to know more about any of these roles? I'd be happy to schedule an interview to discuss this opportunity."""

INFO_ADVISOR_POSITION_UNAVAILABLE_MULTIPLE_DEFAULT_TEMPLATE = """We don't currently have {unavailable_list} positions available. We do have a Python Developer position open though. Would you like to know more about this role? I'd be happy to schedule an interview to discuss this opportunity."""
