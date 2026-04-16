"""
Tests for the Flask application API endpoints.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestIndexRoute:
    """Tests for the index route."""
    
    def test_index_page_loads(self, client):
        """Test that the index page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200


class TestGenerateEndpoint:
    """Tests for /api/generate endpoint."""
    
    @patch('core.generator.expand_prompt')
    def test_successful_generation(self, mock_expand, client):
        """Test successful prompt generation."""
        mock_expand.return_value = "Generated prompt text"
        
        response = client.post('/api/generate',
                              json={
                                  'user_text': 'Create a blog post',
                                  'model': 'mistral'
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'generated_prompt' in data
        assert data['generated_prompt'] == "Generated prompt text"
    
    def test_missing_user_text(self, client):
        """Test error when user_text is missing."""
        response = client.post('/api/generate',
                              json={'model': 'mistral'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_missing_model(self, client):
        """Test error when model is missing."""
        response = client.post('/api/generate',
                              json={'user_text': 'Test'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_invalid_user_text(self, client):
        """Test error with invalid user text."""
        response = client.post('/api/generate',
                              json={
                                  'user_text': 'ab',  # Too short
                                  'model': 'mistral'
                              })
        
        assert response.status_code == 400

    @patch('core.generator.expand_prompt')
    def test_custom_model_handling(self, mock_expand, client):
        """Test generation with custom model."""
        mock_expand.return_value = "Custom model prompt"
        
        response = client.post('/api/generate',
                              json={
                                  'user_text': 'Test prompt',
                                  'model': 'custom',
                                  'custom_model_id': 'my/custom-model'
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['model_used'] == 'my/custom-model'


class TestRefineEndpoint:
    """Tests for /api/refine endpoint."""
    
    @patch('core.generator.refine_prompt')
    def test_successful_refinement(self, mock_refine, client):
        """Test successful prompt refinement."""
        mock_refine.return_value = "Refined prompt"
        
        response = client.post('/api/refine',
                              json={
                                  'previous_prompt': 'Original prompt',
                                  'feedback': 'Make it shorter',
                                  'model': 'mistral'
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['generated_prompt'] == "Refined prompt"
    
    def test_missing_fields(self, client):
        """Test error when required fields are missing."""
        response = client.post('/api/refine',
                              json={'previous_prompt': 'Test'})
        
        assert response.status_code == 400


class TestAnalyzeQualityEndpoint:
    """Tests for /api/analyze-quality endpoint."""
    
    @patch('core.generator.analyze_prompt_quality')
    def test_successful_analysis(self, mock_analyze, client):
        """Test successful quality analysis."""
        mock_analyze.return_value = {
            'score': 85,
            'rating_class': 'excellent',
            'issues': [],
            'suggestions': ['Add examples'],
            'metrics': {'tokens': 50, 'words': 10, 'characters': 60, 'sentences': 3},
            'checks': {'has_context': True, 'has_examples': False, 'has_structure': True, 'has_output_format': True},
            'model': 'gpt4'
        }
        
        response = client.post('/api/analyze-quality',
                              json={
                                  'prompt': 'Test prompt to analyze',
                                  'model': 'gpt4'
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['score'] == 85
        assert 'metrics' in data
    
    def test_missing_prompt(self, client):
        """Test error when prompt is missing."""
        response = client.post('/api/analyze-quality',
                              json={})
        
        assert response.status_code == 400


class TestHistoryEndpoints:
    """Tests for history-related endpoints."""
    
    @patch('builtins.open')
    @patch('os.path.exists')
    def test_save_history(self, mock_exists, mock_open, client):
        """Test saving prompt to history."""
        mock_exists.return_value = False
        
        response = client.post('/api/history/save',
                              json={
                                  'prompt': 'Test prompt',
                                  'model': 'mistral',
                                  'user_input': 'Original input'
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('os.path.exists')
    @patch('builtins.open')
    def test_get_history(self, mock_open, mock_exists, client):
        """Test retrieving history."""
        mock_exists.return_value = True
        mock_history = [
            {
                'id': 1,
                'prompt': 'Test',
                'model': 'mistral',
                'timestamp': '2024-01-01T00:00:00',
                'favorite': False
            }
        ]
        
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps(mock_history)
        mock_open.return_value = mock_file
        
        with patch('json.load', return_value=mock_history):
            response = client.get('/api/history')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)


class TestABTestEndpoint:
    """Tests for /api/ab-test endpoint."""
    
    @patch('core.generator.expand_prompt')
    def test_ab_test_generation(self, mock_expand, client):
        """Test A/B test variation generation."""
        mock_expand.return_value = "Generated variation"
        
        response = client.post('/api/ab-test',
                              json={
                                  'input': 'Create a prompt',
                                  'model': 'mistral'
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'variations' in data
        assert len(data['variations']) == 3
        
        # Verify each variation has required fields
        for variation in data['variations']:
            assert 'id' in variation
            assert 'prompt' in variation
            assert 'strategy' in variation
            assert 'stats' in variation


class TestTemplatesEndpoint:
    """Tests for /api/templates endpoint."""
    
    @patch('os.path.exists')
    @patch('builtins.open')
    def test_get_templates(self, mock_open, mock_exists, client):
        """Test retrieving templates."""
        mock_exists.return_value = True
        mock_templates = {
            'coding': {
                'name': 'Code Generation',
                'description': 'Generate code'
            }
        }
        
        with patch('yaml.safe_load', return_value=mock_templates):
            response = client.get('/api/templates')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'coding' in data