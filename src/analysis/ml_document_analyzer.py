"""
Machine Learning Document Analyzer for Financial Documents

This module provides intelligent document analysis capabilities for extracting
financial information relevant to value investing criteria.
"""

import re
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class FinancialMetric:
    """Represents a financial metric extracted from documents."""
    name: str
    value: Optional[float]
    unit: str
    confidence: float
    source_text: str
    criterion_relevance: List[str]

@dataclass
class DocumentAnalysisResult:
    """Results from ML document analysis."""
    company_name: Optional[str]
    document_type: str
    extracted_metrics: List[FinancialMetric]
    key_insights: List[str]
    risk_factors: List[str]
    competitive_advantages: List[str]
    overall_confidence: float
    criteria_scores: Dict[str, float]

class MLDocumentAnalyzer:
    """
    Intelligent document analyzer using machine learning techniques
    to extract financial information and evaluate against value investing criteria.
    """
    
    def __init__(self):
        self.financial_patterns = self._initialize_financial_patterns()
        self.criterion_keywords = self._initialize_criterion_keywords()
        self.risk_patterns = self._initialize_risk_patterns()
        self.competitive_advantage_patterns = self._initialize_competitive_patterns()
        
        # Initialize NLTK components
        self._initialize_nltk()
        
        # Initialize TF-IDF vectorizer for document similarity
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 3)
        )
    
    def _initialize_nltk(self):
        """Initialize NLTK components."""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            logger.info("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            logger.info("Downloading NLTK stopwords...")
            nltk.download('stopwords', quiet=True)
    
    def _initialize_financial_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for extracting financial metrics."""
        return {
            'revenue': [
                r'(?:revenue|sales|net sales|total revenue)[\s:]+\$?([\d,]+\.?\d*)\s*(?:million|billion|thousand|m|b|k)?',
                r'(?:net sales|revenue)[\s]*(?:of|was|were|is|are)?[\s]*\$?([\d,]+\.?\d*)\s*(?:million|billion|thousand|m|b|k)?',
            ],
            'profit_margin': [
                r'(?:profit margin|net margin|gross margin)[\s:]+(\d+\.?\d*)%?',
                r'(?:margin|profitability)[\s]*(?:of|was|is)?[\s]*(\d+\.?\d*)%',
            ],
            'pe_ratio': [
                r'(?:p/e ratio|price.to.earnings|pe ratio)[\s:]+(\d+\.?\d*)',
                r'(?:trading at|valued at)[\s]*(\d+\.?\d*)[\s]*(?:times|x)[\s]*earnings',
            ],
            'debt_to_equity': [
                r'(?:debt.to.equity|debt/equity|d/e ratio)[\s:]+(\d+\.?\d*)',
                r'(?:debt ratio|leverage ratio)[\s:]+(\d+\.?\d*)',
            ],
            'roe': [
                r'(?:return on equity|roe)[\s:]+(\d+\.?\d*)%?',
                r'(?:equity return|return on shareholders)[\s:]+(\d+\.?\d*)%?',
            ],
            'market_cap': [
                r'(?:market cap|market capitalization)[\s:]+\$?([\d,]+\.?\d*)\s*(?:million|billion|thousand|m|b|k)?',
                r'(?:valued at|worth)[\s]*\$?([\d,]+\.?\d*)\s*(?:million|billion|thousand|m|b|k)?',
            ],
            'growth_rate': [
                r'(?:growth rate|growth)[\s:]+(\d+\.?\d*)%?',
                r'(?:growing at|increased by)[\s]*(\d+\.?\d*)%',
            ]
        }
    
    def _initialize_criterion_keywords(self) -> Dict[str, List[str]]:
        """Initialize keywords for each value investing criterion."""
        return {
            'business_understanding': [
                'business model', 'operations', 'products', 'services', 'customers',
                'value proposition', 'revenue streams', 'strategy', 'business description'
            ],
            'competitive_moat': [
                'competitive advantage', 'moat', 'barriers to entry', 'unique position',
                'brand strength', 'network effects', 'switching costs', 'patents',
                'economies of scale', 'regulatory advantages'
            ],
            'management_quality': [
                'management', 'leadership', 'ceo', 'executives', 'board of directors',
                'governance', 'management team', 'leadership experience', 'track record'
            ],
            'financial_strength': [
                'balance sheet', 'cash flow', 'debt', 'liquidity', 'financial position',
                'working capital', 'credit rating', 'solvency', 'financial stability'
            ],
            'growth_potential': [
                'growth opportunities', 'expansion', 'new markets', 'innovation',
                'r&d', 'research and development', 'future prospects', 'scalability'
            ],
            'profitability': [
                'profit', 'margins', 'earnings', 'profitability', 'returns',
                'revenue', 'operating income', 'net income', 'ebitda'
            ],
            'valuation': [
                'valuation', 'price', 'fair value', 'intrinsic value', 'trading at',
                'multiple', 'pe ratio', 'price to book', 'enterprise value'
            ],
            'risk_factors': [
                'risks', 'challenges', 'threats', 'uncertainties', 'volatility',
                'regulatory risks', 'competition', 'market risks', 'operational risks'
            ]
        }
    
    def _initialize_risk_patterns(self) -> List[str]:
        """Initialize patterns for identifying risk factors."""
        return [
            r'(?:risk|risks|challenges|threats|uncertainties)[\s]*(?:include|are|of)?[\s]*([^.]{1,200})',
            r'(?:may be adversely affected|could impact|potential negative)[\s]*([^.]{1,200})',
            r'(?:competition|competitive pressure|market volatility)[\s]*([^.]{1,200})',
            r'(?:regulatory changes|compliance|legal proceedings)[\s]*([^.]{1,200})',
        ]
    
    def _initialize_competitive_patterns(self) -> List[str]:
        """Initialize patterns for identifying competitive advantages."""
        return [
            r'(?:competitive advantage|competitive edge|unique position)[\s]*([^.]{1,200})',
            r'(?:market leader|industry leader|dominant position)[\s]*([^.]{1,200})',
            r'(?:brand strength|strong brand|brand recognition)[\s]*([^.]{1,200})',
            r'(?:barriers to entry|switching costs|network effects)[\s]*([^.]{1,200})',
            r'(?:economies of scale|cost advantages|operational efficiency)[\s]*([^.]{1,200})',
        ]
    
    def analyze_document(self, text: str, filename: str) -> DocumentAnalysisResult:
        """
        Perform comprehensive ML analysis of a financial document.
        
        Args:
            text: The document text to analyze
            filename: Name of the document file
            
        Returns:
            DocumentAnalysisResult with extracted insights
        """
        logger.info(f"Starting ML analysis of document: {filename}")
        
        # Clean and preprocess text
        cleaned_text = self._clean_text(text)
        
        # Extract company name
        company_name = self._extract_company_name(cleaned_text)
        
        # Determine document type
        doc_type = self._classify_document_type(cleaned_text, filename)
        
        # Extract financial metrics
        financial_metrics = self._extract_financial_metrics(cleaned_text)
        
        # Extract key insights using NLP
        insights = self._extract_key_insights(cleaned_text)
        
        # Identify risk factors
        risks = self._extract_risk_factors(cleaned_text)
        
        # Identify competitive advantages
        advantages = self._extract_competitive_advantages(cleaned_text)
        
        # Calculate confidence score
        confidence = self._calculate_overall_confidence(
            financial_metrics, insights, risks, advantages
        )
        
        # Evaluate against value investing criteria
        criteria_scores = self._evaluate_criteria(
            cleaned_text, financial_metrics, insights, risks, advantages
        )
        
        result = DocumentAnalysisResult(
            company_name=company_name,
            document_type=doc_type,
            extracted_metrics=financial_metrics,
            key_insights=insights,
            risk_factors=risks,
            competitive_advantages=advantages,
            overall_confidence=confidence,
            criteria_scores=criteria_scores
        )
        
        logger.info(f"ML analysis completed with confidence: {confidence:.2f}")
        return result
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess document text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep financial symbols
        text = re.sub(r'[^\w\s\$\%\.\,\-\(\)]', ' ', text)
        
        # Normalize currency and percentage symbols
        text = re.sub(r'\$\s*', '$', text)
        text = re.sub(r'\s*%', '%', text)
        
        return text.strip()
    
    def _extract_company_name(self, text: str) -> Optional[str]:
        """Extract company name from document text."""
        # Common patterns for company names in financial documents
        patterns = [
            r'(?:company|corporation|corp|inc|ltd)[\s]*:[\s]*([A-Z][a-zA-Z\s&,\.]{2,50})',
            r'([A-Z][a-zA-Z\s&,\.]{2,50})[\s]*(?:inc|corp|corporation|limited|ltd)',
            r'(?:about|overview of)[\s]*([A-Z][a-zA-Z\s&,\.]{2,50})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company_name = match.group(1).strip()
                if len(company_name) > 3 and len(company_name) < 50:
                    return company_name
        
        return None
    
    def _classify_document_type(self, text: str, filename: str) -> str:
        """Classify the type of financial document."""
        filename_lower = filename.lower()
        text_lower = text.lower()
        
        if any(term in filename_lower for term in ['10-k', '10k', 'annual']):
            return 'Annual Report (10-K)'
        elif any(term in filename_lower for term in ['10-q', '10q', 'quarterly']):
            return 'Quarterly Report (10-Q)'
        elif any(term in filename_lower for term in ['earnings', 'results']):
            return 'Earnings Report'
        elif 'investor' in filename_lower:
            return 'Investor Presentation'
        elif any(term in text_lower for term in ['balance sheet', 'income statement', 'cash flow']):
            return 'Financial Statement'
        else:
            return 'Financial Document'
    
    def _extract_financial_metrics(self, text: str) -> List[FinancialMetric]:
        """Extract financial metrics using pattern matching and NLP."""
        metrics = []
        
        for metric_name, patterns in self.financial_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        value_str = match.group(1).replace(',', '')
                        value = float(value_str)
                        
                        # Determine unit and normalize value
                        unit, normalized_value = self._normalize_financial_value(
                            value, match.group(0)
                        )
                        
                        # Calculate confidence based on context
                        confidence = self._calculate_metric_confidence(
                            match.group(0), text, metric_name
                        )
                        
                        # Determine relevant criteria
                        relevant_criteria = self._map_metric_to_criteria(metric_name)
                        
                        metric = FinancialMetric(
                            name=metric_name,
                            value=normalized_value,
                            unit=unit,
                            confidence=confidence,
                            source_text=match.group(0),
                            criterion_relevance=relevant_criteria
                        )
                        metrics.append(metric)
                        
                    except (ValueError, IndexError):
                        continue
        
        return metrics
    
    def _normalize_financial_value(self, value: float, context: str) -> Tuple[str, float]:
        """Normalize financial values to consistent units."""
        context_lower = context.lower()
        
        if any(term in context_lower for term in ['billion', 'b']):
            return 'billions', value
        elif any(term in context_lower for term in ['million', 'm']):
            return 'millions', value
        elif any(term in context_lower for term in ['thousand', 'k']):
            return 'thousands', value
        elif '%' in context:
            return 'percentage', value
        else:
            return 'dollars', value
    
    def _calculate_metric_confidence(self, match_text: str, full_text: str, metric_name: str) -> float:
        """Calculate confidence score for extracted metrics."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on context keywords
        context_words = ['reported', 'disclosed', 'stated', 'announced', 'financial', 'fiscal']
        for word in context_words:
            if word in match_text.lower():
                confidence += 0.1
        
        # Increase confidence if metric appears multiple times
        pattern_count = len(re.findall(metric_name, full_text, re.IGNORECASE))
        confidence += min(pattern_count * 0.05, 0.2)
        
        return min(confidence, 1.0)
    
    def _map_metric_to_criteria(self, metric_name: str) -> List[str]:
        """Map financial metrics to relevant value investing criteria."""
        mapping = {
            'revenue': ['profitability', 'growth_potential', 'financial_strength'],
            'profit_margin': ['profitability', 'competitive_moat', 'financial_strength'],
            'pe_ratio': ['valuation', 'margin_of_safety'],
            'debt_to_equity': ['financial_strength', 'risk_factors'],
            'roe': ['profitability', 'management_quality', 'financial_strength'],
            'market_cap': ['valuation', 'business_understanding'],
            'growth_rate': ['growth_potential', 'competitive_moat']
        }
        return mapping.get(metric_name, [])
    
    def _extract_key_insights(self, text: str) -> List[str]:
        """Extract key business insights using NLP techniques."""
        insights = []
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Look for sentences containing insight keywords
        insight_keywords = [
            'strategy', 'competitive', 'market position', 'growth', 'innovation',
            'technology', 'customer', 'brand', 'efficiency', 'expansion'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 300:
                continue
                
            score = 0
            for keyword in insight_keywords:
                if keyword in sentence.lower():
                    score += 1
            
            # Add sentences with multiple relevant keywords
            if score >= 2:
                insights.append(sentence)
        
        # Limit to top insights
        return insights[:10]
    
    def _extract_risk_factors(self, text: str) -> List[str]:
        """Extract risk factors from document text."""
        risks = []
        
        for pattern in self.risk_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                risk_text = match.group(1) if match.lastindex else match.group(0)
                risk_text = risk_text.strip()
                
                if len(risk_text) > 20 and len(risk_text) < 200:
                    risks.append(risk_text)
        
        return risks[:8]  # Limit to top 8 risks
    
    def _extract_competitive_advantages(self, text: str) -> List[str]:
        """Extract competitive advantages from document text."""
        advantages = []
        
        for pattern in self.competitive_advantage_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                advantage_text = match.group(1) if match.lastindex else match.group(0)
                advantage_text = advantage_text.strip()
                
                if len(advantage_text) > 20 and len(advantage_text) < 200:
                    advantages.append(advantage_text)
        
        return advantages[:6]  # Limit to top 6 advantages
    
    def _calculate_overall_confidence(self, metrics: List[FinancialMetric], 
                                    insights: List[str], risks: List[str], 
                                    advantages: List[str]) -> float:
        """Calculate overall confidence score for the analysis."""
        # Base confidence from metrics
        if metrics:
            metric_confidence = sum(m.confidence for m in metrics) / len(metrics)
        else:
            metric_confidence = 0.3
        
        # Boost confidence based on extracted content
        content_score = 0.0
        if insights:
            content_score += 0.15
        if risks:
            content_score += 0.10
        if advantages:
            content_score += 0.10
        
        # Combine scores
        overall_confidence = min(metric_confidence + content_score, 1.0)
        return overall_confidence
    
    def _evaluate_criteria(self, text: str, metrics: List[FinancialMetric],
                          insights: List[str], risks: List[str], 
                          advantages: List[str]) -> Dict[str, float]:
        """Evaluate the document against value investing criteria."""
        criteria_scores = {}
        
        for criterion, keywords in self.criterion_keywords.items():
            score = 0.0
            
            # Check for keyword presence
            text_lower = text.lower()
            keyword_count = sum(1 for keyword in keywords if keyword in text_lower)
            score += min(keyword_count * 0.1, 0.5)
            
            # Add metric-based scores
            relevant_metrics = [m for m in metrics if criterion in m.criterion_relevance]
            if relevant_metrics:
                avg_metric_confidence = sum(m.confidence for m in relevant_metrics) / len(relevant_metrics)
                score += avg_metric_confidence * 0.3
            
            # Add insight-based scores
            if criterion == 'competitive_moat' and advantages:
                score += min(len(advantages) * 0.05, 0.2)
            elif criterion == 'risk_factors' and risks:
                score += min(len(risks) * 0.03, 0.15)
            elif criterion == 'business_understanding' and insights:
                score += min(len(insights) * 0.02, 0.15)
            
            criteria_scores[criterion] = min(score, 1.0)
        
        return criteria_scores

# Initialize the analyzer instance
ml_analyzer = MLDocumentAnalyzer()
