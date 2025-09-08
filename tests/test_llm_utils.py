import pytest
import json
from unittest.mock import patch, MagicMock
from src.llm_utils import get_llm_judgment, build_analysis_prompt, parse_llm_response, call_groq_api, call_gemini_api

class TestLLMUtils:
    
    def test_build_analysis_prompt(self):
        company_name = "Test Corp"
        company_summary = "2023: 1,000,000 (+10%); 2022: 900,000 (+5%)"
        peer_context = {"peer_count": 5, "median_revenue": 950000}
        
        prompt = build_analysis_prompt(company_name, company_summary, peer_context)
        assert company_name in prompt
        assert "1,000,000" in prompt
        assert "5" in prompt
        assert "JSON" in prompt

    def test_parse_llm_response_valid_json(self):
        valid_response = '{"verdict": "plausible", "explanation": "Test", "confidence": 0.8}'
        result = parse_llm_response(valid_response)
        assert result['verdict'] == 'plausible'
        assert result['explanation'] == 'Test'
        assert result['confidence'] == 0.8

    def test_parse_llm_response_invalid_json(self):
        invalid_response = "This is not JSON but contains plausible"
        result = parse_llm_response(invalid_response)
        assert result['verdict'] == 'plausible'
        assert 'This is not JSON' in result['explanation']

    @patch('src.llm_utils.call_gemini_api')
    @patch('src.llm_utils.call_groq_api')
    def test_get_llm_judgment_gemini_fallback(self, mock_groq, mock_gemini):
        # Groq fails
        mock_groq.return_value = None
        # Gemini succeeds
        mock_gemini.return_value = '{"verdict": "plausible", "explanation": "Gemini fallback", "confidence": 0.85}'
        
        result = get_llm_judgment("Test Corp", "Summary", {})
        
        assert result['verdict'] == 'plausible'
        assert result['confidence'] == 0.85
        mock_groq.assert_called_once()
        mock_gemini.assert_called_once()

    @patch('src.llm_utils.call_gemini_api')
    @patch('src.llm_utils.call_groq_api')
    def test_get_llm_judgment_groq_fallback(self, mock_groq, mock_gemini):
        """Test LLM judgment flow: Groq succeeds, Gemini not called."""
        # Mock Groq success, Gemini should NOT be called
        mock_groq_response = '{"verdict": "plausible", "explanation": "Groq test", "confidence": 0.85}'
        mock_groq.return_value = mock_groq_response
        mock_gemini.return_value = '{"verdict": "implausible"}'  

        result = get_llm_judgment("Test Corp", "Summary", {})

        assert result['verdict'] == 'plausible'
        assert result['confidence'] == 0.85
        mock_groq.assert_called_once()
        mock_gemini.assert_not_called()  

    @patch('src.llm_utils.call_gemini_api')
    @patch('src.llm_utils.call_groq_api')
    def test_get_llm_judgment_mock_fallback(self, mock_groq, mock_gemini):
        mock_gemini.return_value = None
        mock_groq.return_value = None
        result = get_llm_judgment("Test Corp", "Summary", {})
        assert result['verdict'] in ["plausible", "implausible", "uncertain"]
        assert 'explanation' in result
        assert 'confidence' in result
        mock_gemini.assert_called_once()
        mock_groq.assert_called_once()

    @patch('src.llm_utils.requests.post')
    def test_call_groq_api_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"verdict": "plausible"}'}}]
        }
        mock_post.return_value = mock_response
        result = call_groq_api("test prompt")
        assert result == '{"verdict": "plausible"}'
        mock_post.assert_called_once()

    @patch('src.llm_utils.requests.post')
    def test_call_groq_api_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_post.return_value = mock_response
        result = call_groq_api("test prompt")
        assert result is None
        mock_post.assert_called_once()

    @patch('src.llm_utils.os.getenv', return_value='test_key')
    @patch('google.generativeai.GenerativeModel')
    @patch('google.generativeai.configure')
    def test_call_gemini_api_success(self, mock_configure, mock_model_class, mock_getenv):
        """Test Gemini API call without hitting the real API."""
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value.text = '{"verdict": "plausible"}'
        mock_model_class.return_value = mock_model_instance
        
        result = call_gemini_api("test prompt")
        assert result == '{"verdict": "plausible"}'

    @patch('src.llm_utils.os.getenv')
    def test_call_gemini_api_no_key(self, mock_getenv):
        mock_getenv.return_value = None
        result = call_gemini_api("test prompt")
        assert result is None

    def test_call_gemini_api_mock_mode(self):
        with patch('src.llm_utils.USE_MOCK', True):
            result = call_gemini_api("test prompt")
            assert result is None
