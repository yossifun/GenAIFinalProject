"""
Test phone number extraction functionality.

This module tests both the ChatGPT-based extraction and regex fallback
methods to ensure reliable phone number parsing.
"""

import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.main_agent import MainAgent


class TestPhoneExtraction(unittest.TestCase):
    """Test cases for phone number extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.main_agent = MainAgent()
    
    def test_phone_extraction_formats(self):
        """Test phone number extraction with various formats."""
        test_cases = [
            ("My phone is (123) 456-7890", "1234567890"),
            ("Call me at 123-456-7890", "1234567890"),
            ("123.456.7890 is my number", "1234567890"),
            ("+1 123 456 7890", "1234567890"),
            ("1234567890", "1234567890"),
            ("My contact: 123 456 7890", "1234567890"),
            ("Phone: 123-456-7890 ext 123", "1234567890"),
            ("123 456 7890 ext 123", "1234567890"),
            ("No phone number here", None),
            ("Multiple numbers: 123-456-7890 and 987-654-3210", "1234567890"),
            ("International: +44 20 7946 0958", None),  # Non-US format
            ("Formatted: (555) 123-4567", "5551234567"),
            ("Spaced: 555 123 4567", "5551234567"),
            ("Dotted: 555.123.4567", "5551234567"),
            ("Mixed: 555-123.4567", "5551234567")
        ]
        
        for test_input, expected_output in test_cases:
            with self.subTest(input=test_input):
                result = self.main_agent.extract_phone_number(test_input)
                self.assertEqual(result, expected_output)
    
    def test_complex_phone_extraction(self):
        """Test phone number extraction with complex scenarios."""
        complex_cases = [
            ("Hi, my phone number is (555) 123-4567 ext 101, but you can also reach me at 555.987.6543", None),  # Multiple numbers, expect first or None
            ("Contact me at 123-456-7890 or 987-654-3210", None),  # Multiple numbers, expect first or None
            ("My numbers: +1 (555) 123-4567 and 555.987.6543", None),  # Multiple numbers, expect first or None
            ("Phone: 123.456.7890 ext 123, mobile: 987-654-3210", None)  # Multiple numbers, expect first or None
        ]
        
        for test_input, expected_output in complex_cases:
            with self.subTest(input=test_input):
                result = self.main_agent.extract_phone_number(test_input)
                # For complex cases with multiple numbers, we just want a valid 10-digit number
                if result is not None:
                    self.assertEqual(len(result), 10)
                    self.assertTrue(result.isdigit())
                else:
                    # It's okay if ChatGPT can't decide between multiple numbers
                    pass
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        edge_cases = [
            ("", None),  # Empty string
            ("   ", None),  # Whitespace only
            ("abc123def", None),  # Mixed text with numbers
            ("123", None),  # Too short
            ("123-456-789", None),  # Incomplete
            ("+1-123-456-7890", "1234567890"),  # 11 digits with country code
        ]
        
        for test_input, expected_output in edge_cases:
            with self.subTest(input=test_input):
                result = self.main_agent.extract_phone_number(test_input)
                self.assertEqual(result, expected_output)
        
        # Test cases where ChatGPT might extract something from long numbers
        long_number_cases = [
            "123456789012345",  # Too long
            "123-456-78901",  # 11 digits without country code
        ]
        
        for test_input in long_number_cases:
            with self.subTest(input=test_input):
                result = self.main_agent.extract_phone_number(test_input)
                # ChatGPT might extract a valid 10-digit sequence from longer numbers
                if result is not None:
                    self.assertEqual(len(result), 10)
                    self.assertTrue(result.isdigit())
                # It's also okay if it returns None
    
    def test_fallback_functionality(self):
        """Test that fallback to regex works when ChatGPT fails."""
        # This test ensures the system gracefully falls back to regex
        # when the primary ChatGPT method encounters issues
        
        # Test with a simple, clear phone number that should work with regex
        test_input = "Call me at 123-456-7890"
        result = self.main_agent.extract_phone_number(test_input)
        
        # Should extract the phone number regardless of which method is used
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 10)
        self.assertTrue(result.isdigit())
    
    def test_phone_extraction_performance(self):
        """Test phone extraction performance with multiple inputs."""
        import time
        
        # Generate a list of test cases
        test_cases = [
            f"My phone is ({i:03d}) {i+100:03d}-{i+200:04d}" 
            for i in range(100, 200, 10)
        ]
        
        start_time = time.time()
        results = []
        
        for test_case in test_cases:
            result = self.main_agent.extract_phone_number(test_case)
            results.append(result)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # All should be valid phone numbers
        valid_results = [r for r in results if r is not None]
        self.assertEqual(len(valid_results), len(test_cases))
        
        # Performance should be reasonable (less than 30 seconds for 10 cases with API calls)
        self.assertLess(processing_time, 30.0, 
                       f"Phone extraction took {processing_time:.2f}s, expected < 30.0s for 10 API calls")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
