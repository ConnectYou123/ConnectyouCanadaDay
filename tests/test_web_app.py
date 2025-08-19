"""
Tests for the web application functionality.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
import json

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from web_app import app

class TestWebApp(unittest.TestCase):
    """Test cases for the web application."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = app.test_client()
        self.app.testing = True
        
    def test_index_page(self):
        """Test that the index page loads."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Value Investing Stock Finder', response.data)
        
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')
        
    def test_status_endpoint(self):
        """Test the status endpoint."""
        response = self.app.get('/api/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('running', data)
        self.assertIn('progress', data)
        self.assertIn('results', data)
        
    def test_start_analysis_endpoint(self):
        """Test the start analysis endpoint."""
        response = self.app.post('/api/start-analysis')
        # Should return 200 or 400 depending on current state
        self.assertIn(response.status_code, [200, 400])
        
    def test_stop_analysis_endpoint(self):
        """Test the stop analysis endpoint."""
        response = self.app.post('/api/stop-analysis')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        
    def test_results_endpoint(self):
        """Test the results endpoint."""
        response = self.app.get('/api/results')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('results', data)
        self.assertIn('total', data)
        
    def test_reports_endpoint(self):
        """Test the reports endpoint."""
        response = self.app.get('/api/reports')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('reports', data)
        
    def test_config_endpoint(self):
        """Test the config endpoint."""
        response = self.app.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('api', data)
        self.assertIn('screening', data)
        self.assertIn('cache', data)
        
    def test_404_error(self):
        """Test 404 error handling."""
        response = self.app.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()
