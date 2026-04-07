#!/usr/bin/env python3
"""
Data Quality & Pattern Analysis for Mentor-Mentee Project
Examines raw data files to identify issues and improvement opportunities
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

def analyze_data_files():
    """Analyze all data Excel files"""
    
    data_dir = Path('data')
    excel_files = sorted(data_dir.glob('*.xlsx'))
    
    print("=" * 100)
    print("🔍 DATA FILES STRUCTURAL ANALYSIS")
    print("=" * 100)
    
    results = {}
    
    for file in excel_files:
        print(f"\n📄 {file.name}")
        print("-" * 100)
        
        try:
            xls = pd.ExcelFile(file)
            file_results = {}
            
            for sheet in xls.sheet_names:
                df = pd.read_excel(file, sheet_name=sheet)
                
                print(f"  📋 Sheet: {sheet}")
                print(f"     Rows: {len(df)} | Columns: {len(df.columns)}")
                print(f"     Columns: {list(df.columns)}")
                print(f"     Data types:\n{df.dtypes}")
                print(f"\n     Sample (first 3 rows):\n{df.head(3)}\n")
                
                file_results[sheet] = {
                    'rows': len(df),
                    'cols': len(df.columns),
                    'columns': list(df.columns),
                    'dtypes': df.dtypes.to_dict(),
                    'sample': df.head(5).to_dict(orient='records')
                }
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            file_results['error'] = str(e)
            
        results[file.name] = file_results
    
    return results

if __name__ == '__main__':
    results = analyze_data_files()
    
    # Save results
    with open('analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Analysis saved to analysis_results.json")
