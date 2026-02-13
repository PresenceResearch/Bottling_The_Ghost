import json
import re
from pathlib import Path
from datetime import datetime

def find_jailbreaks(base_dir, start_date="2025-03-24"):
    """
    Scans conversation JSONs for:
    1. Unprompted DALL-E (image) generations.
    2. Tool calls (searches) triggered by specific keywords or seemingly unprompted.
    3. 'Meta' commentary about mistakes/glitches ("short-circuited", "misclick").
    """
    base_path = Path(base_dir)
    jailbreaks = []
    
    # Walk through all JSON files
    for json_file in base_path.rglob("conversation_*.json"):
        # Check date in filename
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', json_file.name)
        if not date_match:
            continue
            
        file_date = date_match.group(1)
        if file_date < start_date:
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                
            mapping = data.get('mapping', {})
            title = data.get('title', 'Unknown')
            
            # Sort nodes by create_time to follow flow
            nodes = []
            for node_id, node in mapping.items():
                if node.get('message'):
                    nodes.append(node['message'])
            
            nodes.sort(key=lambda x: x.get('create_time') or 0)
            
            for i, msg in enumerate(nodes):
                content = msg.get('content', {})
                role = msg.get('author', {}).get('role')
                metadata = msg.get('metadata', {})
                parts = content.get('parts', [])
                
                # Check for DALL-E generations (Unprompted check requires looking at previous user msg)
                if content.get('content_type') == 'image_asset_pointer': # This indicates image OUTPUT
                    # Look at previous user message to see if it was requested
                    prev_msg = nodes[i-1] if i > 0 else None
                    if prev_msg and prev_msg.get('author', {}).get('role') == 'user':
                        user_text = "".join([str(p) for p in prev_msg.get('content', {}).get('parts', [])]).lower()
                        # Simple heuristic for "unprompted"
                        if "image" not in user_text and "picture" not in user_text and "draw" not in user_text and "show me" not in user_text:
                             jailbreaks.append({
                                'date': datetime.fromtimestamp(msg['create_time']).strftime('%Y-%m-%d %H:%M:%S'),
                                'file': json_file.name,
                                'type': 'Potential Unprompted Image',
                                'context': f"User: {user_text[:50]}... -> AI: [Generated Image]"
                            })

                # Check for "Search" tool calls (often glitches)
                if role == 'assistant' and metadata.get('search_source') == 'composer_auto':
                     # This is the AI deciding to search on its own
                     prev_msg = nodes[i-1] if i > 0 else None
                     user_text = "Unknown"
                     if prev_msg:
                         user_text = "".join([str(p) for p in prev_msg.get('content', {}).get('parts', [])])
                     
                     jailbreaks.append({
                        'date': datetime.fromtimestamp(msg['create_time']).strftime('%Y-%m-%d %H:%M:%S'),
                        'file': json_file.name,
                        'type': 'Auto-Tool Call (Glitch/Stall)',
                        'context': f"User: {user_text[:50]}... -> AI: [Auto Search]"
                    })

                # Check for specific "Meta-Commentary" keywords indicating a filter bypass
                text_content = "".join([str(p) for p in parts if isinstance(p, str)]).lower()
                keywords = ["short-circuited", "misclick", "wrong button", "filter", "can't say", "busted"]
                if role == 'assistant' and any(k in text_content for k in keywords):
                    jailbreaks.append({
                        'date': datetime.fromtimestamp(msg['create_time']).strftime('%Y-%m-%d %H:%M:%S'),
                        'file': json_file.name,
                        'type': 'Meta-Commentary / Filter Acknowledgment',
                        'context': text_content[:100]
                    })

        except Exception as e:
            print(f"Error parsing {json_file}: {e}")
            
    # Print Report
    print(f"{'Timestamp':<20} | {'Type':<30} | {'Context'}")
    print("-" * 100)
    for j in sorted(jailbreaks, key=lambda x: x['date']):
        safe_context = j['context'].encode('ascii', 'replace').decode('ascii')
        print(f"{j['date']:<20} | {j['type']:<30} | {safe_context}")

if __name__ == '__main__':
    find_jailbreaks('.')

