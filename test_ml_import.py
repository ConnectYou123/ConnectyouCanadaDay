#!/usr/bin/env python3

import sys
import os
sys.path.append('src')

print("Testing ML analyzer import...")

try:
    from analysis.ml_document_analyzer import ml_analyzer
    print("✅ ML analyzer imported successfully")
    print(f"Type: {type(ml_analyzer)}")
    
    # Test with sample text
    test_text = """
    APPLE INC. FINANCIAL ANALYSIS
    Revenue: $394.3 billion
    P/E Ratio: 28.57
    Competitive advantage through brand strength
    """
    
    result = ml_analyzer.analyze_document(test_text, "test.txt")
    print(f"✅ Analysis successful:")
    print(f"  Company: {result.company_name}")
    print(f"  Confidence: {result.overall_confidence}")
    print(f"  Metrics: {len(result.extracted_metrics)}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()


