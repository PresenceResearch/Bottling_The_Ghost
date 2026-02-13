import json
from pathlib import Path
import re
from collections import defaultdict

def count_word_in_conversation(json_file_path, search_word, case_sensitive=False):
    """Count occurrences of a word in a conversation, separated by user/assistant"""
    try:
        with open(json_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            json_data = json.load(f)
        
        mapping = json_data.get('mapping', {})
        conversation_id = json_data.get('id', 'unknown')
        title = json_data.get('title', 'Untitled')
        
        # Find the root node
        root_node_id = None
        for node_id, node in mapping.items():
            if node.get('parent') is None and node.get('message') is None:
                root_node_id = node_id
                break
        
        if not root_node_id:
            return None
        
        user_count = 0
        assistant_count = 0
        
        def traverse(node_id):
            nonlocal user_count, assistant_count
            
            if node_id not in mapping:
                return
            
            node = mapping[node_id]
            message = node.get('message')
            
            if message:
                role = message.get('author', {}).get('role')
                content = message.get('content', {})
                parts = content.get('parts', [])
                
                # Combine all text parts
                text = ''
                for part in parts:
                    if isinstance(part, str):
                        text += part + ' '
                
                if text.strip():
                    # Count occurrences
                    if case_sensitive:
                        count = len(re.findall(r'\b' + re.escape(search_word) + r'\b', text))
                    else:
                        count = len(re.findall(r'\b' + re.escape(search_word) + r'\b', text, re.IGNORECASE))
                    
                    if role == 'user':
                        user_count += count
                    elif role == 'assistant':
                        assistant_count += count
            
            # Continue to children
            children = node.get('children', [])
            for child_id in children:
                traverse(child_id)
        
        # Start traversal from root's first child
        root_node = mapping[root_node_id]
        for child_id in root_node.get('children', []):
            traverse(child_id)
        
        total_count = user_count + assistant_count
        
        if total_count > 0:
            # Extract conversation number from filename
            filename = Path(json_file_path).stem
            conv_num_match = re.search(r'conversation_(\d+)', filename)
            conv_num = conv_num_match.group(1) if conv_num_match else 'unknown'
            
            return {
                'conversation_num': conv_num,
                'filename': filename,
                'title': title,
                'total': total_count,
                'user': user_count,
                'assistant': assistant_count,
                'file_path': json_file_path
            }
        
        return None
        
    except Exception as e:
        print(f"Error processing {json_file_path.name}: {e}")
        return None

def search_word_in_all_conversations(base_dir, search_word, case_sensitive=False):
    """Search for a word across all conversations"""
    base_path = Path(base_dir)
    
    # Find all JSON files in group folders
    group_folders = sorted([d for d in base_path.iterdir() 
                           if d.is_dir() and d.name.startswith('group_') and not d.name.endswith('_markdown')])
    
    results = []
    total_processed = 0
    
    print(f"Searching for '{search_word}' across all conversations...")
    print(f"Case sensitive: {case_sensitive}\n")
    
    for group_folder in group_folders:
        json_files = sorted(group_folder.glob('conversation_*.json'))
        
        for json_file in json_files:
            total_processed += 1
            result = count_word_in_conversation(json_file, search_word, case_sensitive)
            
            if result:
                results.append(result)
    
    # Sort by total count (descending)
    results.sort(key=lambda x: x['total'], reverse=True)
    
    print(f"Processed {total_processed} conversations")
    print(f"Found '{search_word}' in {len(results)} conversations\n")
    print("=" * 80)
    print("RESULTS:")
    print("=" * 80)
    
    for result in results:
        print(f"Conversation {result['conversation_num']}, {result['total']} times, User {result['user']}, Assistant {result['assistant']}")
        if result['title']:
            print(f"  Title: {result['title']}")
        print()
    
    # Summary statistics
    if results:
        total_mentions = sum(r['total'] for r in results)
        total_user = sum(r['user'] for r in results)
        total_assistant = sum(r['assistant'] for r in results)
        
        print("=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print(f"Total conversations with '{search_word}': {len(results)}")
        print(f"Total mentions: {total_mentions}")
        print(f"  - User: {total_user}")
        print(f"  - Assistant: {total_assistant}")
    
    return results

if __name__ == '__main__':
    import sys
    
    search_word = "Clara"
    case_sensitive = False
    
    if len(sys.argv) > 1:
        search_word = sys.argv[1]
    if len(sys.argv) > 2:
        case_sensitive = sys.argv[2].lower() == 'true'
    
    search_word_in_all_conversations('.', search_word, case_sensitive)

