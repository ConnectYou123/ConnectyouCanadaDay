"""
Unit tests for the value investing criteria module.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from analysis.criteria import ValueInvestingCriteria, Criterion

class TestValueInvestingCriteria(unittest.TestCase):
    """Test cases for ValueInvestingCriteria class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.criteria = ValueInvestingCriteria()
        
    def test_evaluate_pe_ratio_excellent(self):
        """Test PE ratio evaluation for excellent value (PE <= 15)."""
        data = {'pe_ratio': 10}
        result = self.criteria.evaluate_pe_ratio(data)
        self.assertEqual(result, 1.0)
        
    def test_evaluate_pe_ratio_good(self):
        """Test PE ratio evaluation for good value (15 < PE <= 30)."""
        data = {'pe_ratio': 25}
        result = self.criteria.evaluate_pe_ratio(data)
        self.assertEqual(result, 0.5)
        
    def test_evaluate_pe_ratio_poor(self):
        """Test PE ratio evaluation for poor value (PE > 30)."""
        data = {'pe_ratio': 35}
        result = self.criteria.evaluate_pe_ratio(data)
        self.assertEqual(result, 0)
        
    def test_evaluate_pe_ratio_none(self):
        """Test PE ratio evaluation when data is missing."""
        data = {'pe_ratio': None}
        result = self.criteria.evaluate_pe_ratio(data)
        self.assertEqual(result, 0)
        
    def test_evaluate_gross_margin_excellent(self):
        """Test gross margin evaluation for excellent profitability (>40%)."""
        data = {'gross_margin': 45}
        result = self.criteria.evaluate_gross_margin(data)
        self.assertEqual(result, 1.0)
        
    def test_evaluate_gross_margin_good(self):
        """Test gross margin evaluation for good profitability (30-40%)."""
        data = {'gross_margin': 35}
        result = self.criteria.evaluate_gross_margin(data)
        self.assertEqual(result, 0.5)
        
    def test_evaluate_gross_margin_poor(self):
        """Test gross margin evaluation for poor profitability (<30%)."""
        data = {'gross_margin': 25}
        result = self.criteria.evaluate_gross_margin(data)
        self.assertEqual(result, 0)
        
    def test_evaluate_roe_excellent(self):
        """Test ROE evaluation for excellent efficiency (>30%)."""
        data = {'roe': 35}
        result = self.criteria.evaluate_roe(data)
        self.assertEqual(result, 1.0)
        
    def test_evaluate_roe_good(self):
        """Test ROE evaluation for good efficiency (20-30%)."""
        data = {'roe': 25}
        result = self.criteria.evaluate_roe(data)
        self.assertEqual(result, 0.5)
        
    def test_evaluate_debt_coverage_excellent(self):
        """Test debt coverage evaluation when FCF covers debt."""
        data = {'fcf_3year_sum': 1000000, 'long_term_debt': 800000}
        result = self.criteria.evaluate_debt_coverage(data)
        self.assertEqual(result, 1.0)
        
    def test_evaluate_debt_coverage_no_debt(self):
        """Test debt coverage evaluation when there's no debt."""
        data = {'fcf_3year_sum': 1000000, 'long_term_debt': 0}
        result = self.criteria.evaluate_debt_coverage(data)
        self.assertEqual(result, 1.0)
        
    def test_evaluate_debt_coverage_poor(self):
        """Test debt coverage evaluation when FCF doesn't cover debt."""
        data = {'fcf_3year_sum': 500000, 'long_term_debt': 1000000}
        result = self.criteria.evaluate_debt_coverage(data)
        self.assertEqual(result, 0)
        
    def test_get_all_criteria(self):
        """Test that all criteria are properly defined."""
        criteria_list = self.criteria.get_all_criteria()
        self.assertIsInstance(criteria_list, list)
        self.assertGreater(len(criteria_list), 0)
        
        for criterion in criteria_list:
            self.assertIsInstance(criterion, Criterion)
            self.assertIsInstance(criterion.name, str)
            self.assertIsInstance(criterion.description, str)
            self.assertIsInstance(criterion.category, str)
            self.assertIsInstance(criterion.evaluation_function, type(lambda: None))
            
    def test_evaluate_company(self):
        """Test complete company evaluation."""
        company_data = {
            'pe_ratio': 20,
            'gross_margin': 45,
            'roe': 35,
            'fcf_3year_sum': 1000000,
            'long_term_debt': 800000
        }
        
        results = self.criteria.evaluate_company(company_data)
        
        self.assertIn('PE Ratio', results)
        self.assertIn('Gross Margin', results)
        self.assertIn('Return on Equity', results)
        self.assertIn('Debt Coverage', results)
        self.assertIn('overall_score', results)
        
        # Check that overall score is calculated
        self.assertIsInstance(results['overall_score'], float)
        self.assertGreaterEqual(results['overall_score'], 0)
        self.assertLessEqual(results['overall_score'], 1)

if __name__ == '__main__':
    unittest.main()
