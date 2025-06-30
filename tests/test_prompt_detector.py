"""Test prompt detection functionality"""

import unittest
from libs.dashboard.prompt_detector import ClaudePromptDetector, PromptType, PromptInfo


class TestClaudePromptDetector(unittest.TestCase):
    
    def setUp(self):
        self.detector = ClaudePromptDetector()
    
    def test_detect_numbered_selection(self):
        """Test detection of numbered selection prompts"""
        content = """
Do you want to make this edit to VideoProcessingService.kt?
❯ 1. Yes
  2. Yes, and don't ask again this session (shift+tab)
  3. No, and tell Claude what to do differently (esc)
"""
        
        prompt_info = self.detector.detect_prompt(content)
        self.assertIsNotNone(prompt_info)
        self.assertEqual(prompt_info.type, PromptType.NUMBERED_SELECTION)
        self.assertEqual(len(prompt_info.options), 3)
        self.assertIn("Yes", prompt_info.options[0][1])
    
    def test_detect_binary_choice_yn(self):
        """Test detection of y/n prompts"""
        content = "Do you want to continue? (y/n)"
        
        prompt_info = self.detector.detect_prompt(content)
        self.assertIsNotNone(prompt_info)
        self.assertEqual(prompt_info.type, PromptType.BINARY_CHOICE)
        self.assertEqual(len(prompt_info.options), 2)
    
    def test_detect_true_false(self):
        """Test detection of true/false prompts"""
        content = "Enable advanced features? (true/false)"
        
        prompt_info = self.detector.detect_prompt(content)
        self.assertIsNotNone(prompt_info)
        self.assertEqual(prompt_info.type, PromptType.TRUE_FALSE)
        self.assertEqual(prompt_info.options[0][0], "true")
        self.assertEqual(prompt_info.options[1][0], "false")
    
    def test_detect_text_input(self):
        """Test detection of text input prompts"""
        content = "Enter your name:"
        
        prompt_info = self.detector.detect_prompt(content)
        self.assertIsNotNone(prompt_info)
        self.assertEqual(prompt_info.type, PromptType.TEXT_INPUT)
        self.assertIn("name", prompt_info.metadata.get("field_name", "").lower())
    
    def test_detect_terminal_settings(self):
        """Test detection of terminal settings prompts"""
        content = "Configure terminal settings for optimal display"
        
        prompt_info = self.detector.detect_prompt(content)
        self.assertIsNotNone(prompt_info)
        self.assertEqual(prompt_info.type, PromptType.TERMINAL_SETTINGS)
    
    def test_detect_login_redirect(self):
        """Test detection of login/authentication prompts"""
        content = "Login required to continue. Please sign in."
        
        prompt_info = self.detector.detect_prompt(content)
        self.assertIsNotNone(prompt_info)
        self.assertEqual(prompt_info.type, PromptType.LOGIN_REDIRECT)
    
    def test_detect_confirmation(self):
        """Test detection of confirmation prompts"""
        content = "Are you sure you want to proceed with this action?"
        
        prompt_info = self.detector.detect_prompt(content)
        self.assertIsNotNone(prompt_info)
        self.assertEqual(prompt_info.type, PromptType.CONFIRMATION)
    
    def test_no_detection_regular_text(self):
        """Test that regular text doesn't trigger detection"""
        content = "This is just regular output from Claude Code without any prompts."
        
        prompt_info = self.detector.detect_prompt(content)
        self.assertIsNone(prompt_info)
    
    def test_is_waiting_for_input_true(self):
        """Test waiting for input detection - positive cases"""
        test_cases = [
            "Select an option: ❯",
            "Enter value: ",
            "Choose [1/2]: ",
            "Continue? (y/n): ",
        ]
        
        for content in test_cases:
            with self.subTest(content=content):
                result = self.detector.is_waiting_for_input(content)
                self.assertTrue(result, f"Should detect waiting for input: {content}")
    
    def test_is_waiting_for_input_false(self):
        """Test waiting for input detection - negative cases"""
        test_cases = [
            "Processing complete.",
            "File saved successfully.",
            "Building project...",
            "",
        ]
        
        for content in test_cases:
            with self.subTest(content=content):
                result = self.detector.is_waiting_for_input(content)
                self.assertFalse(result, f"Should not detect waiting for input: {content}")
    
    def test_clean_content(self):
        """Test content cleaning functionality"""
        content_with_ansi = "\x1b[31mError:\x1b[0m Choose option (1/2)"
        cleaned = self.detector._clean_content(content_with_ansi)
        
        self.assertNotIn("\x1b", cleaned)
        self.assertIn("Choose option", cleaned)
    
    def test_extract_question(self):
        """Test question extraction"""
        content = """
Some output here
Do you want to continue with this operation?
[1] Yes
[2] No
"""
        
        question = self.detector._extract_question(content)
        self.assertIn("Do you want to continue", question)
        self.assertTrue(question.endswith("?"))
    
    def test_numbered_selection_variations(self):
        """Test different numbered selection formats"""
        test_cases = [
            # [1] format
            "[1] Option A\n[2] Option B\n[3] Option C",
            # 1. format
            "1. First choice\n2. Second choice",
            # 1) format
            "1) Accept\n2) Reject\n3) Skip",
            # ❯ format
            "❯ 1. Yes\n  2. No\n  3. Cancel",
        ]
        
        for content in test_cases:
            with self.subTest(content=content):
                prompt_info = self.detector.detect_prompt(content)
                self.assertIsNotNone(prompt_info, f"Should detect numbered selection: {content}")
                self.assertEqual(prompt_info.type, PromptType.NUMBERED_SELECTION)
                self.assertGreaterEqual(len(prompt_info.options), 2)
    
    def test_confidence_scores(self):
        """Test that confidence scores are reasonable"""
        # High confidence case
        content = "❯ 1. Yes\n  2. No\n  3. Cancel"
        prompt_info = self.detector.detect_prompt(content)
        self.assertIsNotNone(prompt_info)
        self.assertGreaterEqual(prompt_info.confidence, 0.8)
        
        # Lower confidence case
        content = "Maybe continue?"
        prompt_info = self.detector.detect_prompt(content)
        if prompt_info:  # May or may not detect
            self.assertLessEqual(prompt_info.confidence, 0.6)


if __name__ == '__main__':
    unittest.main()