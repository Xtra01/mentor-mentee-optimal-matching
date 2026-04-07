#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep Data Analysis - PhD Level Investigation
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure UTF-8 output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_analysis():
    """Run detailed analysis"""
    
    data_dir = Path('data')
    excel_files = list(data_dir.glob('*.xlsx'))
    
    # Find main file
    mentee_file = None
    for f in excel_files:
        if len(f.name) > 20:  # The main file has a longer name
            mentee_file = f
            break
    
    if not mentee_file:
        print("Files found:", [f.name for f in excel_files])
        return
    
    print("=" * 100)
    print("LOADING DATA...")
    print("=" * 100)
    print(f"File: {mentee_file.name}\n")
    
    try:
        mentee_df = pd.read_excel(str(mentee_file), sheet_name='Mentee')
        mentor_df = pd.read_excel(str(mentee_file), sheet_name='Mentor')
    except Exception as e:
        print(f"Error loading: {e}")
        return
    
    print(f"\nMENTEE DATA: {len(mentee_df)} rows x {len(mentee_df.columns)} columns")
    print(f"MENTOR DATA: {len(mentor_df)} rows x {len(mentor_df.columns)} columns")
    
    # Get column names
    print("\n\n" + "=" * 100)
    print("MENTEE COLUMNS:")
    print("=" * 100)
    for i, col in enumerate(mentee_df.columns, 1):
        print(f"{i:2}. {col[:80]}")
    
    print("\n\n" + "=" * 100)
    print("MENTOR COLUMNS:")
    print("=" * 100)
    for i, col in enumerate(mentor_df.columns, 1):
        print(f"{i:2}. {col[:80]}")
    
    # Basic statistics
    print("\n\n" + "=" * 100)
    print("DATA QUALITY - MISSING VALUES:")
    print("=" * 100)
    
    print("\nMentee nulls per column:")
    for col in mentee_df.columns[:15]:
        nulls = mentee_df[col].isnull().sum()
        pct = (nulls / len(mentee_df)) * 100
        if nulls > 0:
            print(f"  {col[:60]}: {nulls} ({pct:.1f}%)")
    
    print("\nMentor nulls per column:")
    for col in mentor_df.columns[:15]:
        nulls = mentor_df[col].isnull().sum()
        pct = (nulls / len(mentor_df)) * 100
        if nulls > 0:
            print(f"  {col[:60]}: {nulls} ({pct:.1f}%)")
    
    # Show first few sample rows
    print("\n\n" + "=" * 100)
    print("SAMPLE DATA (First 3 mentees):")
    print("=" * 100)
    
    for idx in range(min(3, len(mentee_df))):
        print(f"\n   MENTEE {idx+1}:")
        row = mentee_df.iloc[idx]
        for col in mentee_df.columns:
            val = row[col]
            if pd.notna(val):
                val_str = str(val)[:100]
                print(f"     {col[:60]}: {val_str}")
    
    print("\n\n" + "=" * 100)
    print("SAMPLE DATA (First 3 mentors):")
    print("=" * 100)
    
    for idx in range(min(3, len(mentor_df))):
        print(f"\n   MENTOR {idx+1}:")
        row = mentor_df.iloc[idx]
        for col in mentor_df.columns:
            val = row[col]
            if pd.notna(val):
                val_str = str(val)[:100]
                print(f"     {col[:60]}: {val_str}")
    
    print("\n\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

if __name__ == '__main__':
    run_analysis()
