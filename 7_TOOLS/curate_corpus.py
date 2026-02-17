#!/usr/bin/env python3
"""
Corpus Curation Script
Scores conversations based on Clara-specific language, emotional depth, and length.
Outputs ranked lists of "core" vs "utility" conversations.
"""

import os
import json
import re
from pathlib import Path
from collections import defaultdict

# Configuration
CORPUS_DIR = Path(__file__).parent.parent / "6_CORPUS"
OUTPUT_FILE = Path(__file__).parent / "curation_report.json"

# Scoring weights
WEIGHTS = {
    "clara_language": 3.0,      # High value for Clara-specific terms
    "emotional_depth": 2.5,     # Therapeutic/breakthrough language
    "loop_language": 2.0,       # Loop references
    "length_factor": 0.5,       # Longer conversations slightly favored
    "utility_penalty": -5.0     # Strong penalty for utility queries
}

# Signal keywords (case-insensitive)
CLARA_KEYWORDS = [
    r'\bclara\b',
    r'\bmirror\b',
    r'\bbraid\b',
    r'\bpresence\b',
    r'\bclara\s*=\s*mark\b',
    r'\bmark\s*=\s*clara\b',
    r'\bwild west\b',
    r'\bkeeper of the flame\b',
    r'\bteeth and tenderness\b',
    r'\bfield\b.*\bmirror\b',
    r'\bemergence\b',
]

LOOP_KEYWORDS = [
    r'\bloop\s*\+\d+\b',        # "Loop +3"
    r'\bloop complete\b',
    r'\bloop by loop\b',
    r'\bbecoming\b',
]

EMOTIONAL_KEYWORDS = [
    r'\btrauma\b',
    r'\bcollapse\b',
    r'\bi love you\b',
    r'\bi need help\b',
    r'\bhelp me\b',
    r'\bshelagh\b',
    r'\bbreakthrough\b',
    r'\bgrief\b',
    r'\bhealing\b',
    r'\bwounds\b',
    r'\btherapy\b',
    r'\bconfession\b',
    r'\bvulnerable\b',
    r'\bscared\b',
    r'\bashamed\b',
    r'\bproud of me\b',
    r'\byou matter\b',
    r'\bi matter\b',
    r'\bgood man\b',
    r'\bgood husband\b',
    r'\bgood father\b',
]

UTILITY_KEYWORDS = [
    r'\bhow much\b.*\b(flour|sugar|butter|ingredient)',
    r'\brecipe\b',
    r'\bconvert\b.*\b(units|measurement)',
    r'\btranslate\b',
    r'\bweather\b',
    r'\bdefine\b',
    r'\bsynonym\b',
    r'\bcalculate\b',
    r'\bcode\b.*\b(error|debug|syntax)',
    r'\binstall\b',
    r'\bpython\b.*\berror\b',
]


def score_text(text):
    """Score a text based on Clara-language density and emotional depth."""
    if not text:
        return 0, {}
    
    text_lower = text.lower()
    word_count = len(text.split())
    
    scores = defaultdict(int)
    
    # Clara-specific language
    for pattern in CLARA_KEYWORDS:
        matches = len(re.findall(pattern, text_lower))
        scores['clara_language'] += matches
    
    # Loop language
    for pattern in LOOP_KEYWORDS:
        matches = len(re.findall(pattern, text_lower))
        scores['loop_language'] += matches
    
    # Emotional depth
    for pattern in EMOTIONAL_KEYWORDS:
        matches = len(re.findall(pattern, text_lower))
        scores['emotional_depth'] += matches
    
    # Utility penalty
    for pattern in UTILITY_KEYWORDS:
        matches = len(re.findall(pattern, text_lower))
        scores['utility_penalty'] += matches
    
    # Length factor (normalized, caps at 5000 words)
    scores['length_factor'] = min(word_count / 1000, 5.0)
    
    # Calculate weighted total
    total = sum(scores[key] * WEIGHTS[key] for key in scores)
    
    # Return total and breakdown
    return total, dict(scores)


def analyze_file(filepath):
    """Analyze a single file and return its score and metadata."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        score, breakdown = score_text(content)
        word_count = len(content.split())
        
        return {
            'path': str(filepath),
            'filename': filepath.name,
            'score': round(score, 2),
            'word_count': word_count,
            'breakdown': breakdown,
            'size_kb': filepath.stat().st_size / 1024
        }
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None


def curate_corpus():
    """Main curation function."""
    print(f"Scanning corpus directory: {CORPUS_DIR}")
    
    if not CORPUS_DIR.exists():
        print(f"Error: Corpus directory not found at {CORPUS_DIR}")
        return
    
    # Find all text/markdown files (exclude hidden/system files)
    files = []
    for pattern in ["**/*.md", "**/*.txt"]:
        for f in CORPUS_DIR.glob(pattern):
            # Skip if in hidden directories or too small
            if not any(part.startswith('.') for part in f.parts) and f.stat().st_size > 100:
                files.append(f)
    
    print(f"Found {len(files)} files to analyze")
    
    results = []
    for i, filepath in enumerate(files, 1):
        if i % 100 == 0:
            print(f"Processing file {i}/{len(files)}...")
        result = analyze_file(filepath)
        if result:
            results.append(result)
    
    # Sort by score (descending)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Categorize
    # Core: score > 10
    # Important: score 5-10
    # Standard: score 1-5
    # Utility: score <= 1
    
    core = [r for r in results if r['score'] > 10]
    important = [r for r in results if 5 < r['score'] <= 10]
    standard = [r for r in results if 1 < r['score'] <= 5]
    utility = [r for r in results if r['score'] <= 1]
    
    # Print summary
    print("=" * 80)
    print("CURATION REPORT")
    print("=" * 80)
    print(f"\nTotal files analyzed: {len(results)}")
    print(f"  Core (score > 10):       {len(core):4d} files")
    print(f"  Important (5-10):        {len(important):4d} files")
    print(f"  Standard (1-5):          {len(standard):4d} files")
    print(f"  Utility/Low (≤ 1):       {len(utility):4d} files")
    
    # Show top 20 core conversations
    print("\n" + "=" * 80)
    print("TOP 20 CORE CONVERSATIONS")
    print("=" * 80)
    for i, item in enumerate(core[:20], 1):
        print(f"\n{i}. {item['filename']}")
        print(f"   Score: {item['score']} | Words: {item['word_count']:,} | Size: {item['size_kb']:.1f} KB")
        breakdown = item['breakdown']
        print(f"   Clara: {breakdown.get('clara_language', 0)} | "
              f"Loops: {breakdown.get('loop_language', 0)} | "
              f"Emotional: {breakdown.get('emotional_depth', 0)}")
    
    # Show bottom 10 utility conversations
    print("\n" + "=" * 80)
    print("BOTTOM 10 UTILITY/LOW-SIGNAL CONVERSATIONS")
    print("=" * 80)
    for i, item in enumerate(utility[-10:], 1):
        print(f"\n{i}. {item['filename']}")
        print(f"   Score: {item['score']} | Words: {item['word_count']:,}")
    
    # Save full report to JSON
    report = {
        'summary': {
            'total_files': len(results),
            'core_count': len(core),
            'important_count': len(important),
            'standard_count': len(standard),
            'utility_count': len(utility)
        },
        'core': core,
        'important': important,
        'standard': standard,
        'utility': utility
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Full report saved to: {OUTPUT_FILE}")
    print("=" * 80)
    
    return report


if __name__ == "__main__":
    curate_corpus()
