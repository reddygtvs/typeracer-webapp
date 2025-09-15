#!/usr/bin/env python3
"""
Test all 19 chart endpoints
"""
import requests
import json

# All 19 chart endpoints
ALL_CHARTS = [
    'wpm-distribution',
    'accuracy-distribution', 
    'performance-over-time',
    'daily-performance',
    'rolling-average',
    'rank-distribution',
    'hourly-performance',
    'wpm-vs-accuracy',
    'win-rate-monthly',
    'top-texts',
    'consistency-score',
    'accuracy-by-rank',
    'cumulative-accuracy',
    'wpm-by-rank-boxplot',
    'racers-impact',
    'frequent-texts-improvement',
    'top-texts-distribution',
    'win-rate-after-win',
    'fastest-slowest-races',
    'time-between-races'
]

def test_all_charts():
    # Load full race data
    with open('race_data.csv', 'r') as f:
        csv_data = f.read()
    
    print(f"Testing all {len(ALL_CHARTS)} charts...")
    print("=" * 50)
    
    working = []
    failing = []
    
    for i, chart in enumerate(ALL_CHARTS):
        print(f"Testing {i+1}/{len(ALL_CHARTS)}: {chart}...")
        
        try:
            response = requests.post(f"http://localhost:8000/charts/{chart}",
                                   json={"csv_data": csv_data},
                                   timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ {chart}: SUCCESS")
                working.append(chart)
            else:
                print(f"  ❌ {chart}: HTTP {response.status_code}")
                failing.append(chart)
                
        except Exception as e:
            print(f"  ❌ {chart}: ERROR - {str(e)}")
            failing.append(chart)
    
    print("\n" + "=" * 50)
    print(f"RESULTS: {len(working)}/{len(ALL_CHARTS)} charts working ({len(working)/len(ALL_CHARTS)*100:.1f}%)")
    print(f"Working: {working}")
    print(f"Failing: {failing}")

if __name__ == "__main__":
    test_all_charts()