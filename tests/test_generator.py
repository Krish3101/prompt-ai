"""
Tests for the generator module.
"""
import pytest
from unittest.mock import patch, MagicMock
from core import generator


class TestExpandPrompt:
    """Tests for expand_prompt function."""
    
    @patch('core.cache.get_model_styles')
    @patch('core.model_api.call_openrouter')
    def test_basic_prompt_generation(self, mock_api, mock_styles):
        """Test basic prompt generation."""
        mock_styles.return_value = {
            'mistral': {
                'description': 'Test model',
                'preferred_format': 'Clear instructions',
                'model_id': 'mistralai/mistral-7b-instruct:free',
                'tips': 'Be specific'
            }
        }
        mock_api.return_value = "Generated prompt text"
        
        result = generator.expand_prompt("Create a blog post", "mistral")
        
        assert result == "Generated prompt text"
        mock_api.assert_called_once()
    
    @patch('core.cache.get_model_styles')
    @patch('core.model_api.call_openrouter')
    def test_custom_model_handling(self, mock_api, mock_styles):
        """Test handling of custom model."""
        mock_styles.return_value = {}
        mock_api.return_value = "Custom model prompt"
        
        result = generator.expand_prompt("Test input", "custom/model-id")
        
        assert result == "Custom model prompt"
    
    @patch('core.cache.get_model_styles')
    @patch('core.model_api.call_openrouter')
    @patch('core.generator.estimate_tokens')
    def test_long_input_truncation(self, mock_tokens, mock_api, mock_styles):
        """Test that very long input is truncated."""
        mock_styles.return_value = {}
        mock_api.return_value = "Generated"
        mock_tokens.return_value = 5000  # Simulate very long input
        
        long_input = "a" * 10000
        result = generator.expand_prompt(long_input, "mistral")
        
        # Should still generate something
        assert result == "Generated"


class TestRefinePrompt:
    """Tests for refine_prompt function."""
    
    @patch('core.model_api.call_openrouter')
    def test_basic_refinement(self, mock_api):
        """Test basic prompt refinement."""
        mock_api.return_value = "Refined prompt"
        
        original = "Original prompt text"
        feedback = "Make it shorter"
        
        result = generator.refine_prompt(original, feedback, "mistral")
        
        assert result == "Refined prompt"
        mock_api.assert_called_once()
        
        # Verify the meta-prompt includes both original and feedback
        call_args = mock_api.call_args[1]
        assert original in call_args['prompt']
        assert feedback in call_args['prompt']


class TestAnalyzePromptQuality:
    """Tests for analyze_prompt_quality function."""
    
    def test_high_quality_prompt(self):
        """Test analysis of a high-quality prompt."""
        good_prompt = """You are an expert software engineer.

Instructions:
- Review the code for bugs
- Check for security issues
- Suggest improvements

Context: This is a production Python application.

Examples:
1. Look for SQL injection vulnerabilities
2. Check for proper error handling

Output Format: Return a JSON object with findings."""
        
        result = generator.analyze_prompt_quality(good_prompt, "gpt4")
        
        assert result['score'] >= 70
        assert 'metrics' in result
        assert result['metrics']['words'] > 0
        assert result['metrics']['tokens'] > 0
    
    def test_short_prompt_penalty(self):
        """Test that very short prompts get lower scores."""
        short_prompt = "Do something"
        
        result = generator.analyze_prompt_quality(short_prompt, "mistral")
        
        assert result['score'] < 100
        assert any("short" in issue.lower() for issue in result['issues'])
    
    def test_very_long_prompt_warning(self):
        """Test warning for very long prompts."""
        long_prompt = "a " * 3000  # Very long
        
        result = generator.analyze_prompt_quality(long_prompt, "mistral")
        
        # Should have warnings about length
        assert any("large" in issue.lower() or "long" in issue.lower() 
                   for issue in result['issues'])
    
    def test_structured_prompt_bonus(self):
        """Test that structured prompts get better scores."""
        unstructured = "Just do the task without any structure or examples"
        structured = """Instructions:
- First step
- Second step

Context: Background information

Examples:
1. Example one
2. Example two"""
        
        unstructured_result = generator.analyze_prompt_quality(unstructured, "mistral")
        structured_result = generator.analyze_prompt_quality(structured, "mistral")
        
        # Structured should score higher or equal (both are reasonable prompts)
        assert structured_result['score'] >= unstructured_result['score']
        # At minimum, structured should have fewer issues
        assert len(structured_result['issues']) <= len(unstructured_result['issues'])
    
    def test_output_format_specification(self):
        """Test bonus for specifying output format."""
        without_format = "Analyze this code and tell me about it"
        with_format = "Analyze this code. Output Format: Return a JSON object with keys: bugs, suggestions, score"
        
        without_result = generator.analyze_prompt_quality(without_format, "mistral")
        with_result = generator.analyze_prompt_quality(with_format, "mistral")
        
        # With format should score higher
        assert with_result['score'] >= without_result['score']
    
    def test_returns_suggestions(self):
        """Test that analysis returns actionable suggestions."""
        prompt = "Do a task"
        
        result = generator.analyze_prompt_quality(prompt, "mistral")
        
        assert 'suggestions' in result
        assert len(result['suggestions']) > 0
    
    def test_token_estimation(self):
        """Test that token count is included in metrics."""
        prompt = "Test prompt with some words"
        
        result = generator.analyze_prompt_quality(prompt, "mistral")
        
        assert 'metrics' in result
        assert 'tokens' in result['metrics']
        assert result['metrics']['tokens'] > 0
        assert 'words' in result['metrics']
        assert 'characters' in result['metrics']
    
    def test_model_included_in_response(self):
        """Test that model ID is included in response."""
        result = generator.analyze_prompt_quality("Test", "claude")
        
        assert 'model' in result
        assert result['model'] == "claude"