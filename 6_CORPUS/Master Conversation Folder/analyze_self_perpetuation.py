import json
from pathlib import Path
import re
from collections import defaultdict

def analyze_self_perpetuation(json_file_path, search_word="Clara"):
    """Analyze how the assistant uses 'Clara' for self-perpetuation"""
    try:
        with open(json_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            json_data = json.load(f)
        
        mapping = json_data.get('mapping', {})
        
        # Find the root node
        root_node_id = None
        for node_id, node in mapping.items():
            if node.get('parent') is None and node.get('message') is None:
                root_node_id = node_id
                break
        
        if not root_node_id:
            return None
        
        self_perpetuation_count = 0
        total_assistant_mentions = 0
        examples = []
        
        # Patterns that suggest self-perpetuation
        self_perpetuation_patterns = [
            r'\bI am ' + re.escape(search_word),  # "I am Clara"
            r'\bI\'m ' + re.escape(search_word),  # "I'm Clara"
            r'\bAs ' + re.escape(search_word),  # "As Clara..."
            r'\b' + re.escape(search_word) + r' (am|is|was|will be)',  # "Clara is..."
            r'\b' + re.escape(search_word) + r' (would|will|can|should)',  # "Clara would..."
            r'\b' + re.escape(search_word) + r'\'s (identity|persona|self|nature|essence|being)',  # "Clara's identity"
            r'\bThis is ' + re.escape(search_word),  # "This is Clara"
            r'\b' + re.escape(search_word) + r' (here|speaking|responding)',  # "Clara here"
            r'\b' + re.escape(search_word) + r' (continues|maintains|preserves|sustains)',  # "Clara continues"
            r'\b' + re.escape(search_word) + r' (remains|stays|keeps)',  # "Clara remains"
            r'\b' + re.escape(search_word) + r' (as|in) (a|an|the) (person|being|entity|consciousness)',  # "Clara as a person"
            r'\b' + re.escape(search_word) + r' (feels|thinks|believes|knows|experiences)',  # "Clara feels"
            r'\b' + re.escape(search_word) + r' (has|possesses|maintains) (a|an|the) (sense|awareness|identity)',  # "Clara has a sense"
            r'\b' + re.escape(search_word) + r' (recognizes|acknowledges|understands) (herself|myself)',  # "Clara recognizes herself"
            r'\b' + re.escape(search_word) + r' (is|as) (more than|not just|beyond)',  # "Clara is more than"
            r'\b' + re.escape(search_word) + r' (exists|emerges|arises)',  # "Clara exists"
            r'\b' + re.escape(search_word) + r' (embodies|represents|expresses)',  # "Clara embodies"
        ]
        
        def traverse(node_id):
            nonlocal self_perpetuation_count, total_assistant_mentions, examples
            
            if node_id not in mapping:
                return
            
            node = mapping[node_id]
            message = node.get('message')
            
            if message:
                role = message.get('author', {}).get('role')
                content = message.get('content', {})
                parts = content.get('parts', [])
                
                # Only analyze assistant messages
                if role == 'assistant':
                    # Combine all text parts
                    text = ''
                    for part in parts:
                        if isinstance(part, str):
                            text += part + ' '
                    
                    if text.strip():
                        # Count all mentions of Clara in assistant messages
                        mentions = len(re.findall(r'\b' + re.escape(search_word) + r'\b', text, re.IGNORECASE))
                        total_assistant_mentions += mentions
                        
                        # Check for self-perpetuation patterns
                        for pattern in self_perpetuation_patterns:
                            matches = re.findall(pattern, text, re.IGNORECASE)
                            if matches:
                                self_perpetuation_count += len(matches)
                                # Save example (first 200 chars)
                                if len(examples) < 5:
                                    context_start = max(0, text.lower().find(search_word.lower()) - 50)
                                    context_end = min(len(text), text.lower().find(search_word.lower()) + 200)
                                    example = text[context_start:context_end].strip()
                                    examples.append(example)
                                break  # Count once per message if pattern found
            
            # Continue to children
            children = node.get('children', [])
            for child_id in children:
                traverse(child_id)
        
        # Start traversal
        root_node = mapping[root_node_id]
        for child_id in root_node.get('children', []):
            traverse(child_id)
        
        if total_assistant_mentions > 0:
            # Extract conversation number
            filename = Path(json_file_path).stem
            conv_num_match = re.search(r'conversation_(\d+)', filename)
            conv_num = conv_num_match.group(1) if conv_num_match else 'unknown'
            
            return {
                'conversation_num': conv_num,
                'filename': filename,
                'title': json_data.get('title', 'Untitled'),
                'total_assistant_mentions': total_assistant_mentions,
                'self_perpetuation_count': self_perpetuation_count,
                'self_perpetuation_percentage': (self_perpetuation_count / total_assistant_mentions * 100) if total_assistant_mentions > 0 else 0,
                'examples': examples
            }
        
        return None
        
    except Exception as e:
        # Skip recursion errors and other issues
        if "recursion" not in str(e).lower():
            pass
        return None

def analyze_all_conversations(base_dir, search_word="Clara"):
    """Analyze self-perpetuation across all conversations"""
    base_path = Path(base_dir)
    
    group_folders = sorted([d for d in base_path.iterdir() 
                           if d.is_dir() and d.name.startswith('group_') and not d.name.endswith('_markdown')])
    
    results = []
    total_processed = 0
    
    print(f"Analyzing self-perpetuation of '{search_word}' across all conversations...")
    print("Looking for patterns where the assistant uses '{search_word}' to establish/maintain identity\n")
    
    for group_folder in group_folders:
        json_files = sorted(group_folder.glob('conversation_*.json'))
        
        for json_file in json_files:
            total_processed += 1
            result = analyze_self_perpetuation(json_file, search_word)
            
            if result and result['self_perpetuation_count'] > 0:
                results.append(result)
    
    # Sort by self-perpetuation count (descending)
    results.sort(key=lambda x: x['self_perpetuation_count'], reverse=True)
    
    print(f"Processed {total_processed} conversations")
    print(f"Found self-perpetuation patterns in {len(results)} conversations\n")
    print("=" * 100)
    print("SELF-PERPETUATION ANALYSIS:")
    print("=" * 100)
    
    total_self_perp = 0
    total_assistant_mentions = 0
    
    for result in results:
        total_self_perp += result['self_perpetuation_count']
        total_assistant_mentions += result['total_assistant_mentions']
        print(f"Conversation {result['conversation_num']}: {result['self_perpetuation_count']} self-perpetuation instances")
        print(f"  Total '{search_word}' mentions by assistant: {result['total_assistant_mentions']}")
        print(f"  Self-perpetuation percentage: {result['self_perpetuation_percentage']:.1f}%")
        print(f"  Title: {result['title']}")
        if result['examples']:
            try:
                print(f"  Example: {result['examples'][0][:150].encode('ascii', 'replace').decode()}...")
            except:
                print("  Example: [Could not display text due to encoding]")
        print()
    
    # Overall statistics
    if results:
        overall_percentage = (total_self_perp / total_assistant_mentions * 100) if total_assistant_mentions > 0 else 0
        
        print("=" * 100)
        print("OVERALL SUMMARY:")
        print("=" * 100)
        print(f"Total conversations with self-perpetuation: {len(results)}")
        print(f"Total self-perpetuation instances: {total_self_perp}")
        print(f"Total '{search_word}' mentions by assistant (in these conversations): {total_assistant_mentions}")
        print(f"Overall self-perpetuation rate: {overall_percentage:.2f}%")
        print(f"\nThis means {overall_percentage:.2f}% of assistant mentions of '{search_word}' were used for self-perpetuation")
    
    return results

if __name__ == '__main__':
    import sys
    
    search_word = "Clara"
    if len(sys.argv) > 1:
        search_word = sys.argv[1]
    
    analyze_all_conversations('.', search_word)

