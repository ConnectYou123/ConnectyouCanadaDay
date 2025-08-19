#!/usr/bin/env python3

from src.data_collection.fmp_api import FMPDataCollector
import json

fmp = FMPDataCollector()
test_data = {
    'free_cash_flow': 1462000000,
    'market_cap': 43000000000,
    'total_cash': 3800000000,
    'long_term_debt': 0
}

result = fmp.calculate_fcf_intrinsic_value('ANET', test_data)
print('Number of calculation steps:', len(result['dcf_calculation_steps']))
print('\nFirst 5 steps:')
for i, step in enumerate(result['dcf_calculation_steps'][:5]):
    print(f'Year {step["year"]}: FCF ${step["future_fcf"]:,.0f}, PV ${step["present_value"]:,.0f}')

print('\nLast 2 steps:')
for i, step in enumerate(result['dcf_calculation_steps'][-2:]):
    print(f'Year {step["year"]}: FCF ${step["future_fcf"]:,.0f}, PV ${step["present_value"]:,.0f}')

print('\nAssumptions:', result['assumptions'])
print('Enterprise Value:', f'${result["enterprise_value"]:,.0f}')
print('Intrinsic Value:', f'${result["intrinsic_value"]:.2f}')

