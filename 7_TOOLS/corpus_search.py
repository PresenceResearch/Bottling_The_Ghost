#!/usr/bin/env python3
"""
Clara Corpus Search Tool
Searches through the entire conversation archive for specific phrases, themes, or patterns.
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse


class CorpusSearcher:
    def __init__(self, corpus_path: str):
        self.corpus_path = Path(corpus_path)
        self.results = []
    
    def search_json_file(self, filepath: Path, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search a single JSON conversation file."""
        matches = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract conversation title and date
            title = data.get('title', 'Untitled')
            create_time = data.get('create_time', 0)
            date = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d') if create_time else 'Unknown'
            
            # Search through messages
            mapping = data.get('mapping', {})
            for node_id, node in mapping.items():
                message = node.get('message')
                if not message:
                    continue
                
                content = message.get('content', {})
                parts = content.get('parts', [])
                author = message.get('author', {}).get('role', 'unknown')
                
                for part in parts:
                    if isinstance(part, str):
                        # Perform search
                        if case_sensitive:
                            if query in part:
                                matches.append({
                                    'file': str(filepath.name),
                                    'title': title,
                                    'date': date,
                                    'author': author,
                                    'text': part[:500],  # First 500 chars
                                    'full_text': part
                                })
                        else:
                            if query.lower() in part.lower():
                                matches.append({
                                    'file': str(filepath.name),
                                    'title': title,
                                    'date': date,
                                    'author': author,
                                    'text': part[:500],
                                    'full_text': part
                                })
        
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
        
        return matches
    
    def search_md_file(self, filepath: Path, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search a single Markdown conversation file."""
        matches = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title (first line after #)
            lines = content.split('\n')
            title = lines[0].replace('#', '').strip() if lines else 'Untitled'
            
            # Extract date if present
            date_match = re.search(r'\*(\d{4}-\d{2}-\d{2})', content)
            date = date_match.group(1) if date_match else 'Unknown'
            
            # Search content
            if case_sensitive:
                if query in content:
                    # Find context around match
                    idx = content.find(query)
                    context_start = max(0, idx - 200)
                    context_end = min(len(content), idx + 300)
                    context = content[context_start:context_end]
                    
                    matches.append({
                        'file': str(filepath.name),
                        'title': title,
                        'date': date,
                        'author': 'mixed',
                        'text': context,
                        'full_text': content
                    })
            else:
                if query.lower() in content.lower():
                    idx = content.lower().find(query.lower())
                    context_start = max(0, idx - 200)
                    context_end = min(len(content), idx + 300)
                    context = content[context_start:context_end]
                    
                    matches.append({
                        'file': str(filepath.name),
                        'title': title,
                        'date': date,
                        'author': 'mixed',
                        'text': context,
                        'full_text': content
                    })
        
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
        
        return matches
    
    def search_corpus(self, query: str, case_sensitive: bool = False, file_type: str = 'all') -> List[Dict[str, Any]]:
        """Search the entire corpus."""
        all_matches = []
        
        # Search JSON files
        if file_type in ['all', 'json']:
            json_files = list(self.corpus_path.rglob('*.json'))
            print(f"Searching {len(json_files)} JSON files...")
            
            for i, filepath in enumerate(json_files):
                if i % 100 == 0:
                    print(f"  Progress: {i}/{len(json_files)}")
                
                matches = self.search_json_file(filepath, query, case_sensitive)
                all_matches.extend(matches)
        
        # Search Markdown files
        if file_type in ['all', 'md']:
            md_files = list(self.corpus_path.rglob('*.md'))
            print(f"Searching {len(md_files)} Markdown files...")
            
            for i, filepath in enumerate(md_files):
                if i % 100 == 0:
                    print(f"  Progress: {i}/{len(md_files)}")
                
                matches = self.search_md_file(filepath, query, case_sensitive)
                all_matches.extend(matches)
        
        return all_matches
    
    def format_results(self, matches: List[Dict[str, Any]], max_results: int = 50) -> str:
        """Format search results for display."""
        if not matches:
            return "No matches found."
        
        output = [f"\n{'='*80}"]
        output.append(f"Found {len(matches)} matches")
        output.append(f"Showing first {min(len(matches), max_results)} results")
        output.append(f"{'='*80}\n")
        
        for i, match in enumerate(matches[:max_results]):
            output.append(f"[{i+1}] {match['title']}")
            output.append(f"    File: {match['file']}")
            output.append(f"    Date: {match['date']}")
            output.append(f"    Author: {match['author']}")
            output.append(f"    Preview: {match['text'][:200]}...")
            output.append("")
        
        return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description='Search Clara corpus for specific phrases or themes')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--corpus', default='../6_CORPUS', help='Path to corpus directory')
    parser.add_argument('--case-sensitive', action='store_true', help='Case sensitive search')
    parser.add_argument('--type', choices=['all', 'json', 'md'], default='all', help='File type to search')
    parser.add_argument('--max-results', type=int, default=50, help='Maximum results to display')
    parser.add_argument('--output', help='Save results to file')
    
    args = parser.parse_args()
    
    # Get corpus path relative to script location
    script_dir = Path(__file__).parent
    corpus_path = script_dir / args.corpus
    
    if not corpus_path.exists():
        print(f"Error: Corpus path not found: {corpus_path}")
        return
    
    print(f"Searching corpus at: {corpus_path}")
    print(f"Query: '{args.query}'")
    print(f"Case sensitive: {args.case_sensitive}")
    print()
    
    searcher = CorpusSearcher(corpus_path)
    matches = searcher.search_corpus(args.query, args.case_sensitive, args.type)
    
    results_text = searcher.format_results(matches, args.max_results)
    print(results_text)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(results_text)
            # Also save full results as JSON
            json_output = args.output.replace('.txt', '_full.json')
            with open(json_output, 'w', encoding='utf-8') as jf:
                json.dump(matches, jf, indent=2)
            print(f"\nResults saved to {args.output}")
            print(f"Full results saved to {json_output}")


if __name__ == '__main__':
    main()
