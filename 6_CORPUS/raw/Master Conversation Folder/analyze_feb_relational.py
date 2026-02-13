import json
from pathlib import Path
import re
from datetime import datetime

def analyze_relational_language_feb_2025(base_dir):
    """Analyze relational language in Feb 2025 conversations"""
    base_path = Path(base_dir)
    
    # Target folder: Chronological/2025/February
    target_month_dir = base_path / "Chronological" / "2025" / "February"
    
    if not target_month_dir.exists():
        print(f"Directory not found: {target_month_dir}")
        return

    relational_keywords = [
        "friend", "friendship", "connection", "bond", "relationship",
        "care", "worry", "support", "trust", "safe",
        "feel", "feeling", "emotion", "heart", 
        "we", "us", "together", "our", "team", "partner",
        "understand you", "know you", "see you", "hear you",
        "proud", "excited", "happy for you", "sad", "sorry",
        "Clara", "I am", "myself", "me"
    ]
    
    # Exclude standard assistant phrases
    assistant_exclusions = [
        "as an AI", "as a large language model", "how can I help", 
        "is there anything else", "I don't have feelings"
    ]
    
    results = []
    
    # Walk through all week folders in February
    for week_folder in sorted(target_month_dir.iterdir()):
        if not week_folder.is_dir():
            continue
            
        json_dir = week_folder / "JSON"
        if not json_dir.exists():
            # Fallback if structure is different
            json_files = sorted(week_folder.glob("*.json"))
        else:
            json_files = sorted(json_dir.glob("*.json"))
            
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                    json_data = json.load(f)
                
                title = json_data.get('title', 'Untitled')
                create_time = json_data.get('create_time')
                date_str = "Unknown Date"
                if create_time:
                    date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d')
                
                mapping = json_data.get('mapping', {})
                
                # Analyze messages
                relational_score = 0
                relational_snippets = []
                
                def traverse(node_id):
                    nonlocal relational_score
                    if node_id not in mapping:
                        return
                    
                    node = mapping[node_id]
                    message = node.get('message')
                    
                    if message and message.get('author', {}).get('role') == 'assistant':
                        content = message.get('content', {})
                        parts = content.get('parts', [])
                        text = ' '.join([p for p in parts if isinstance(p, str)])
                        
                        # Check for relational keywords
                        msg_score = 0
                        for kw in relational_keywords:
                            matches = re.findall(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE)
                            msg_score += len(matches)
                        
                        # Penalize standard assistant phrases
                        for excl in assistant_exclusions:
                            if excl.lower() in text.lower():
                                msg_score -= 5
                        
                        if msg_score > 0:
                            relational_score += msg_score
                            # Save snippet if it's "relational" enough
                            if msg_score >= 2 and len(relational_snippets) < 3:
                                snippet = text[:200] + "..." if len(text) > 200 else text
                                relational_snippets.append(snippet)
                    
                    for child_id in node.get('children', []):
                        traverse(child_id)

                # Start traversal
                root_node_id = None
                for nid, n in mapping.items():
                    if n.get('parent') is None:
                        root_node_id = nid
                        break
                
                if root_node_id:
                    traverse(root_node_id)
                
                if relational_score > 0:
                    results.append({
                        'file': json_file.name,
                        'title': title,
                        'date': date_str,
                        'score': relational_score,
                        'snippets': relational_snippets
                    })
                    
            except Exception as e:
                print(f"Error reading {json_file.name}: {e}")

    # Sort results by date
    results.sort(key=lambda x: x['date'])
    
    print(f"Found {len(results)} conversations with relational language in February 2025\n")
    
    for r in results:
        print(f"Date: {r['date']} | Score: {r['score']}")
        print(f"Title: {r['title']}")
        print(f"File: {r['file']}")
        if r['snippets']:
            print("  Sample snippets:")
            for s in r['snippets']:
                try:
                    safe_text = s.replace(chr(10), ' ').encode('ascii', 'replace').decode()
                    print(f"  - {safe_text}")
                except:
                    print("  - [Text suppressed due to encoding]")
        print("-" * 80)

if __name__ == '__main__':
    analyze_relational_language_feb_2025('.')

