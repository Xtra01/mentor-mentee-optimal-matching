#!/usr/bin/env python3
"""
Deep Data Analysis - Extract Samples & Identify Patterns
PhD-level analysis for algorithm improvement
"""

import pandas as pd
import numpy as np
from pathlib import Path

def detailed_sample_analysis():
    """Extract samples and provide detailed analysis"""
    
    # Load mentee data - find the Excel file dynamically
    data_dir = Path('data')
    excel_files = list(data_dir.glob('*.xlsx'))
    
    # Find the main input file (Mentor Mezun Ağı...)
    mentee_file = None
    for f in excel_files:
        if 'Başvurular' in f.name or 'Başvuru' in f.name:
            mentee_file = f
            break
    
    if not mentee_file:
        print(f"Available files: {[f.name for f in excel_files]}")
        raise FileNotFoundError(f"Could not find mentee file in {data_dir}")
    
    print(f"Loading file: {mentee_file}")
    mentee_df = pd.read_excel(str(mentee_file), sheet_name='Mentee')
    mentor_df = pd.read_excel(str(mentee_file), sheet_name='Mentor')
    
    print("\n" + "="*120)
    print("🔬 DEEP DATA ANALYSIS - SAMPLE EXTRACTION & PATTERN IDENTIFICATION")
    print("="*120)
    
    # ========== MENTEE ANALYSIS ==========
    print("\n\n📊 MENTEE DATA ANALYSIS (308 students)")
    print("-"*120)
    
    print(f"\nBasic Info:")
    print(f"  Total Mentees: {len(mentee_df)}")
    print(f"  Total Columns: {len(mentee_df.columns)}")
    print(f"  Missing Values per column:\n{mentee_df.isnull().sum()}\n")
    
    # Sample key columns
    key_mentee_cols = [
        'Bölümünüz/Your Major',
        'Şu anda yaşadığınız şehir ve ülke /The city and country you currently reside in',
        'Kariyer Hedefleriniz ( Akademi - İş Dünyası, Kurum, Sektör, Pozisyon vb.) / Your Career Goals (Academy - Business World, Institution, Sector, Position etc.)',
        'İlgi alanlarınız ve hobileriniz ( Aktif olduğunuz öğrenci kulüplerini bu alanda belirtiniz.) / Your interests and hobbies (Please indicate your active student clubs in this area.)',
        'Hangi konularda destek almak istiyorsunuz? / Which topics do you want to receive support?',
        'Bölümü - akademik geçmişi / Academic background / Field of study]',
        ' [Sektörü - alanı / Industry - Field of expertise]'
    ]
    
    print("\n📋 MENTEE SAMPLES (5 random students - ALL COLUMNS)")
    print("-"*120)
    
    sample_indices = np.random.choice(len(mentee_df), 5, replace=False)
    
    for idx, i in enumerate(sample_indices, 1):
        print(f"\n  👤 Sample {idx} - Student ID: {mentee_df.iloc[i]['ID Numaranız/ ID No']}")
        mentee_row = mentee_df.iloc[i]
        
        for col in mentee_df.columns:
            val = mentee_row[col]
            if pd.notna(val) and val != '':
                val_str = str(val)[:100] if len(str(val)) > 100 else str(val)
                print(f"     {col}: {val_str}")
    
    # ========== MENTOR ANALYSIS ==========
    print("\n\n" + "="*120)
    print("\n📊 MENTOR DATA ANALYSIS (225 alumni)")
    print("-"*120)
    
    print(f"\nBasic Info:")
    print(f"  Total Mentors: {len(mentor_df)}")
    print(f"  Total Columns: {len(mentor_df.columns)}")
    print(f"  Missing Values per column:\n{mentor_df.isnull().sum()}\n")
    
    print("\n📋 MENTOR SAMPLES (5 random mentors - ALL COLUMNS)")
    print("-"*120)
    
    sample_indices = np.random.choice(len(mentor_df), 5, replace=False)
    
    for idx, i in enumerate(sample_indices, 1):
        print(f"\n  🎓 Sample {idx} - Mentor ID: {mentor_df.iloc[i].get('ID', 'N/A')}")
        mentor_row = mentor_df.iloc[i]
        
        for col in mentor_df.columns:
            val = mentor_row[col]
            if pd.notna(val) and val != '':
                val_str = str(val)[:100] if len(str(val)) > 100 else str(val)
                print(f"     {col}: {val_str}")
    
    # ========== COLUMN-BY-COLUMN ANALYSIS ==========
    print("\n\n" + "="*120)
    print("📈 COLUMN-BY-COLUMN PATTERN ANALYSIS")
    print("="*120)
    
    # Department analysis
    print("\n\n🏫 DEPARTMENT DISTRIBUTION (Top 10)")
    print("-"*120)
    if 'Bölümünüz/Your Major' in mentee_df.columns:
        dept = mentee_df['Bölümünüz/Your Major'].value_counts().head(10)
        print(dept)
    
    # City analysis
    print("\n\n🌍 CITY DISTRIBUTION (Top 10)")
    print("-"*120)
    if 'Şu anda yaşadığınız şehir ve ülke /The city and country you currently reside in' in mentee_df.columns:
        city = mentee_df['Şu anda yaşadığınız şehir ve ülke /The city and country you currently reside in'].value_counts().head(10)
        print(city)
    
    # Career goals - text analysis
    print("\n\n🎯 CAREER GOALS - SAMPLE TEXTS (10 examples)")
    print("-"*120)
    career_col = 'Kariyer Hedefleriniz ( Akademi - İş Dünyası, Kurum, Sektör, Pozisyon vb.) / Your Career Goals (Academy - Business World, Institution, Sector, Position etc.)'
    
    if career_col in mentee_df.columns:
        career_texts = mentee_df[career_col].dropna().head(10)
        for i, text in enumerate(career_texts, 1):
            print(f"  {i}. {text[:150]}")
    
    # Support topics
    print("\n\n💡 SUPPORT TOPICS REQUESTED (10 examples)")
    print("-"*120)
    support_col = 'Hangi konularda destek almak istiyorsunuz? / Which topics do you want to receive support?'
    
    if support_col in mentee_df.columns:
        support_texts = mentee_df[support_col].dropna().head(10)
        for i, text in enumerate(support_texts, 1):
            print(f"  {i}. {text[:150]}")
    
    return mentee_df, mentor_df

if __name__ == '__main__':
    mentee_df, mentor_df = detailed_sample_analysis()
    
    print("\n\n" + "="*120)
    print("✅ DATA ANALYSIS COMPLETE")
    print("="*120)
