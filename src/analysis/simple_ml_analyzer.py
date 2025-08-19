"""
Simplified ML Document Analyzer for Financial Documents
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class SimpleMLAnalyzer:
    """Simplified ML document analyzer that focuses on reliable extraction."""
    
    def __init__(self):
        self.financial_patterns = self._initialize_patterns()
        self.company_patterns = [
            r'([A-Z][a-zA-Z\s&,\.]{2,50})[\s]*(?:inc\.?|corp\.?|corporation|limited|ltd\.?)',
            r'(?:company|corporation|corp|inc)[\s]*:[\s]*([A-Z][a-zA-Z\s&,\.]{2,50})',
            r'^([A-Z][A-Z\s]+(?:INC\.?|CORP\.?|CORPORATION))',
        ]
    
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Initialize financial extraction patterns."""
        return {
            'revenue': [
                r'revenue[\s:]*\$?([\d,]+\.?\d*)\s*(?:billion|million|thousand|b|m|k)?',
                r'sales[\s:]*\$?([\d,]+\.?\d*)\s*(?:billion|million|thousand|b|m|k)?',
            ],
            'pe_ratio': [
                r'p[\/\-]?e[\s]*ratio[\s:]*(\d+\.?\d*)',
                r'price.to.earnings[\s:]*(\d+\.?\d*)',
            ],
            'profit_margin': [
                r'(?:gross|profit|net)[\s]*margin[\s:]*(\d+\.?\d*)%?',
            ],
            'roe': [
                r'return on equity[\s:]*(\d+\.?\d*)%?',
                r'roe[\s:]*(\d+\.?\d*)%?',
            ],
            'market_cap': [
                r'market cap(?:italization)?[\s:]*\$?([\d,]+\.?\d*)\s*(?:trillion|billion|million|t|b|m)?',
            ],
            'debt_ratio': [
                r'debt.to.equity[\s:]*(\d+\.?\d*)',
                r'debt ratio[\s:]*(\d+\.?\d*)',
            ]
        }
    
    def analyze_document(self, text: str, filename: str) -> Dict:
        """Analyze document and extract key information."""
        try:
            logger.info(f"Analyzing document: {filename}")
            
            # Extract company name
            company_name = self._extract_company_name(text)
            logger.info(f"Extracted company name: {company_name}")
            
            # Extract financial metrics
            metrics = self._extract_metrics(text)
            logger.info(f"Extracted {len(metrics)} financial metrics")
            
            # Analyze qualitative factors
            competitive_advantages = self._find_competitive_advantages(text)
            risk_factors = self._find_risk_factors(text)
            key_insights = self._find_key_insights(text)
            
            # Calculate confidence
            confidence = self._calculate_confidence(company_name, metrics, competitive_advantages)
            
            result = {
                'company_name': company_name,
                'document_type': self._classify_document(text, filename),
                'extracted_metrics': metrics,
                'competitive_advantages': competitive_advantages,
                'risk_factors': risk_factors,
                'key_insights': key_insights,
                'overall_confidence': confidence,
                'success': True
            }
            
            logger.info(f"Analysis completed successfully with confidence: {confidence}")
            return result
            
        except Exception as e:
            logger.error(f"Error in document analysis: {e}")
            return {
                'company_name': None,
                'document_type': 'Unknown',
                'extracted_metrics': [],
                'competitive_advantages': [],
                'risk_factors': [],
                'key_insights': [],
                'overall_confidence': 0.0,
                'success': False,
                'error': str(e)
            }
    
    def _extract_company_name(self, text: str) -> Optional[str]:
        """Extract company name from document."""
        for pattern in self.company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up the name
                name = re.sub(r'\s+', ' ', name)
                if 2 < len(name) < 50:
                    logger.info(f"Found company name with pattern: {name}")
                    return name
        return None
    
    def _extract_metrics(self, text: str) -> List[Dict]:
        """Extract financial metrics from text."""
        metrics = []
        
        for metric_name, patterns in self.financial_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        value_str = match.group(1).replace(',', '')
                        value = float(value_str)
                        
                        # Determine unit
                        full_match = match.group(0).lower()
                        if 'trillion' in full_match or ' t' in full_match:
                            unit = 'trillions'
                        elif 'billion' in full_match or ' b' in full_match:
                            unit = 'billions'
                        elif 'million' in full_match or ' m' in full_match:
                            unit = 'millions'
                        elif '%' in full_match or 'percent' in full_match:
                            unit = 'percentage'
                        else:
                            unit = 'units'
                        
                        metrics.append({
                            'name': metric_name,
                            'value': value,
                            'unit': unit,
                            'confidence': 0.8,
                            'source_text': match.group(0)[:100]
                        })
                        
                    except (ValueError, IndexError):
                        continue
        
        return metrics
    
    def _find_competitive_advantages(self, text: str) -> List[str]:
        """Find competitive advantages mentioned in text."""
        advantages = []
        patterns = [
            r'competitive advantage[^.]{1,100}',
            r'brand strength[^.]{1,100}',
            r'market leader[^.]{1,100}',
            r'switching costs?[^.]{1,100}',
            r'economies of scale[^.]{1,100}',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                advantage = match.group(0).strip()
                if advantage and len(advantage) > 10:
                    advantages.append(advantage)
        
        return advantages[:5]  # Limit to top 5
    
    def _find_risk_factors(self, text: str) -> List[str]:
        """Find risk factors mentioned in text."""
        risks = []
        patterns = [
            r'risk[^.]{1,100}',
            r'challenge[^.]{1,100}',
            r'competition[^.]{1,100}',
            r'regulatory[^.]{1,100}',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                risk = match.group(0).strip()
                if risk and len(risk) > 10:
                    risks.append(risk)
        
        return risks[:5]  # Limit to top 5
    
    def _find_key_insights(self, text: str) -> List[str]:
        """Find key business insights."""
        insights = []
        sentences = re.split(r'[.!?]+', text)
        
        insight_keywords = ['strategy', 'growth', 'innovation', 'market', 'customer', 'technology']
        
        for sentence in sentences:
            sentence = sentence.strip()
            if 20 < len(sentence) < 200:
                score = sum(1 for keyword in insight_keywords if keyword in sentence.lower())
                if score >= 2:
                    insights.append(sentence)
        
        return insights[:5]  # Limit to top 5
    
    def _classify_document(self, text: str, filename: str) -> str:
        """Classify document type."""
        filename_lower = filename.lower()
        text_lower = text.lower()
        
        if 'annual' in filename_lower or '10-k' in filename_lower:
            return 'Annual Report'
        elif 'earnings' in filename_lower or 'quarterly' in filename_lower:
            return 'Earnings Report'
        elif 'financial' in text_lower and 'statement' in text_lower:
            return 'Financial Statement'
        else:
            return 'Financial Document'
    
    def _calculate_confidence(self, company_name: Optional[str], metrics: List[Dict], advantages: List[str]) -> float:
        """Calculate overall confidence score."""
        confidence = 0.4  # Base confidence
        
        if company_name:
            confidence += 0.3
        
        if metrics:
            confidence += min(len(metrics) * 0.05, 0.2)
        
        if advantages:
            confidence += min(len(advantages) * 0.02, 0.1)
        
        return min(confidence, 1.0)

# Create instance
simple_ml_analyzer = SimpleMLAnalyzer()


