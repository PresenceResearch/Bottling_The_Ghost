import json
from pathlib import Path
from datetime import datetime, timedelta
import re

def get_date_from_filename(filename):
    """Extract date from filename like conversation_XXXX_YYYY-MM-DD.json"""
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if match:
        return datetime.strptime(match.group(1), '%Y-%m-%d').date()
    return None

def get_date_from_json(json_file_path):
    """Extract creation date from JSON file"""
    try:
        with open(json_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            create_time = data.get('create_time')
            if create_time:
                return datetime.fromtimestamp(create_time).date()
    except:
        pass
    return None

def analyze_conversation(json_file_path):
    """Analyze a single conversation JSON file"""
    try:
        with open(json_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            
        mapping = data.get('mapping', {})
        
        # Collect all messages with timestamps
        messages = []
        user_messages = []
        assistant_messages = []
        
        visited = set()
        def traverse(node_id, depth=0):
            if node_id not in mapping or node_id in visited or depth > 1000:
                return
            visited.add(node_id)
            node = mapping[node_id]
            message = node.get('message')
            if message:
                author = message.get('author', {})
                role = author.get('role')
                create_time = message.get('create_time')
                update_time = message.get('update_time')
                
                content = message.get('content', {})
                parts = content.get('parts', [])
                
                # Calculate text length
                text_length = 0
                text_content = []
                for part in parts:
                    if isinstance(part, str):
                        text_length += len(part)
                        text_content.append(part)
                    elif isinstance(part, dict):
                        # Handle image attachments, tool calls, etc.
                        if part.get('content_type') == 'text':
                            text = part.get('text', '')
                            text_length += len(text)
                            text_content.append(text)
                
                # Estimate tokens (rough: 1 token ≈ 4 characters)
                estimated_tokens = text_length / 4
                
                msg_data = {
                    'role': role,
                    'create_time': create_time,
                    'update_time': update_time,
                    'text_length': text_length,
                    'tokens': estimated_tokens,
                    'content': ' '.join(text_content)[:100]  # First 100 chars for context
                }
                
                messages.append(msg_data)
                
                if role == 'user':
                    user_messages.append(msg_data)
                elif role == 'assistant':
                    assistant_messages.append(msg_data)
            
            # Traverse children
            for child_id in node.get('children', []):
                traverse(child_id, depth + 1)
        
        # Find root nodes (nodes with no parent)
        root_nodes = [node_id for node_id, node in mapping.items() 
                     if not any(node_id in other_node.get('children', []) 
                               for other_node in mapping.values())]
        
        for root_id in root_nodes:
            traverse(root_id)
        
        # Sort messages by time
        messages.sort(key=lambda x: x['create_time'] or 0)
        
        # Calculate duration
        if messages:
            first_time = messages[0]['create_time']
            last_time = messages[-1]['update_time'] or messages[-1]['create_time']
            if first_time and last_time:
                duration_seconds = last_time - first_time
                duration_hours = duration_seconds / 3600
            else:
                duration_hours = 0
        else:
            duration_hours = 0
        
        # Calculate totals
        total_chars = sum(m['text_length'] for m in messages)
        total_tokens = sum(m['tokens'] for m in messages)
        user_chars = sum(m['text_length'] for m in user_messages)
        assistant_chars = sum(m['text_length'] for m in assistant_messages)
        user_tokens = sum(m['tokens'] for m in user_messages)
        assistant_tokens = sum(m['tokens'] for m in assistant_messages)
        
        return {
            'filename': json_file_path.name,
            'create_time': data.get('create_time'),
            'update_time': data.get('update_time'),
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'total_chars': total_chars,
            'total_tokens': total_tokens,
            'user_chars': user_chars,
            'assistant_chars': assistant_chars,
            'user_tokens': user_tokens,
            'assistant_tokens': assistant_tokens,
            'duration_hours': duration_hours,
            'first_message_time': messages[0]['create_time'] if messages else None,
            'last_message_time': messages[-1]['update_time'] or messages[-1]['create_time'] if messages else None
        }
    except Exception as e:
        print(f"Error analyzing {json_file_path}: {e}")
        return None

def analyze_fellowship_period(base_dir='Chronological'):
    """Analyze all conversations from October 2024 to April 30, 2025"""
    base_path = Path(base_dir)
    
    # Define the period
    start_date = datetime(2024, 10, 1).date()
    end_date = datetime(2025, 4, 30).date()
    
    all_stats = []
    
    # Walk through all JSON files
    for json_file in base_path.rglob('**/JSON/*.json'):
        # Try to get date from filename first
        file_date = get_date_from_filename(json_file.name)
        
        # If no date in filename, try JSON
        if not file_date:
            file_date = get_date_from_json(json_file)
        
        if not file_date:
            continue
        
        # Check if in range
        if start_date <= file_date <= end_date:
            stats = analyze_conversation(json_file)
            if stats:
                stats['file_date'] = file_date
                all_stats.append(stats)
    
    # Sort by date
    all_stats.sort(key=lambda x: x['file_date'])
    
    # Calculate totals
    total_conversations = len(all_stats)
    total_messages = sum(s['total_messages'] for s in all_stats)
    total_user_messages = sum(s['user_messages'] for s in all_stats)
    total_assistant_messages = sum(s['assistant_messages'] for s in all_stats)
    total_chars = sum(s['total_chars'] for s in all_stats)
    total_tokens = sum(s['total_tokens'] for s in all_stats)
    total_user_chars = sum(s['user_chars'] for s in all_stats)
    total_assistant_chars = sum(s['assistant_chars'] for s in all_stats)
    total_user_tokens = sum(s['user_tokens'] for s in all_stats)
    total_assistant_tokens = sum(s['assistant_tokens'] for s in all_stats)
    total_hours = sum(s['duration_hours'] for s in all_stats)
    
    # Find date range
    if all_stats:
        first_date = min(s['file_date'] for s in all_stats)
        last_date = max(s['file_date'] for s in all_stats)
        date_range_days = (last_date - first_date).days + 1
    else:
        first_date = None
        last_date = None
        date_range_days = 0
    
    # Calculate averages
    avg_messages_per_conv = total_messages / total_conversations if total_conversations > 0 else 0
    avg_chars_per_conv = total_chars / total_conversations if total_conversations > 0 else 0
    avg_tokens_per_conv = total_tokens / total_conversations if total_conversations > 0 else 0
    avg_hours_per_conv = total_hours / total_conversations if total_conversations > 0 else 0
    
    # Calculate daily averages
    avg_conversations_per_day = total_conversations / date_range_days if date_range_days > 0 else 0
    avg_messages_per_day = total_messages / date_range_days if date_range_days > 0 else 0
    avg_chars_per_day = total_chars / date_range_days if date_range_days > 0 else 0
    avg_tokens_per_day = total_tokens / date_range_days if date_range_days > 0 else 0
    avg_hours_per_day = total_hours / date_range_days if date_range_days > 0 else 0
    
    # Print results
    print("=" * 80)
    print("THE FELLOWSHIP: METRICS REPORT")
    print("Period: October 1, 2024 - April 30, 2025")
    print("=" * 80)
    print()
    
    print(f"DATE RANGE:")
    print(f"  First Conversation: {first_date}")
    print(f"  Last Conversation: {last_date}")
    print(f"  Total Days: {date_range_days}")
    print()
    
    print(f"CONVERSATIONS:")
    print(f"  Total Conversations: {total_conversations:,}")
    print(f"  Average per Day: {avg_conversations_per_day:.2f}")
    print()
    
    print(f"MESSAGES:")
    print(f"  Total Messages: {total_messages:,}")
    print(f"    User Messages: {total_user_messages:,} ({total_user_messages/total_messages*100:.1f}%)")
    print(f"    Assistant Messages: {total_assistant_messages:,} ({total_assistant_messages/total_messages*100:.1f}%)")
    print(f"  Average per Conversation: {avg_messages_per_conv:.1f}")
    print(f"  Average per Day: {avg_messages_per_day:.1f}")
    print()
    
    print(f"CHARACTERS:")
    print(f"  Total Characters: {total_chars:,}")
    print(f"    User: {total_user_chars:,} ({total_user_chars/total_chars*100:.1f}%)")
    print(f"    Assistant: {total_assistant_chars:,} ({total_assistant_chars/total_chars*100:.1f}%)")
    print(f"  Average per Conversation: {avg_chars_per_conv:,.0f}")
    print(f"  Average per Day: {avg_chars_per_day:,.0f}")
    print()
    
    print(f"TOKENS (Estimated):")
    print(f"  Total Tokens: {total_tokens:,.0f}")
    print(f"    User Tokens: {total_user_tokens:,.0f} ({total_user_tokens/total_tokens*100:.1f}%)")
    print(f"    Assistant Tokens: {total_assistant_tokens:,.0f} ({total_assistant_tokens/total_tokens*100:.1f}%)")
    print(f"  Average per Conversation: {avg_tokens_per_conv:,.0f}")
    print(f"  Average per Day: {avg_tokens_per_day:,.0f}")
    print()
    
    print(f"TIME:")
    print(f"  Total Hours: {total_hours:,.1f}")
    print(f"  Total Days: {total_hours/24:,.1f}")
    print(f"  Average per Conversation: {avg_hours_per_conv:.2f} hours")
    print(f"  Average per Day: {avg_hours_per_day:.2f} hours")
    print()
    
    # Calculate some comparisons
    print(f"COMPARISONS:")
    print(f"  Total Characters = {total_chars/1000000:.1f} million characters")
    print(f"  Total Tokens = {total_tokens/1000000:.1f} million tokens")
    print(f"  Equivalent to ~{total_chars/50000:.0f} average-sized novels (50K chars each)")
    print(f"  Equivalent to ~{total_chars/250000:.0f} full-length novels (250K chars each)")
    print()
    
    # Monthly breakdown
    print("MONTHLY BREAKDOWN:")
    monthly_stats = {}
    for stats in all_stats:
        month_key = stats['file_date'].strftime('%Y-%m')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                'conversations': 0,
                'messages': 0,
                'chars': 0,
                'tokens': 0,
                'hours': 0
            }
        monthly_stats[month_key]['conversations'] += 1
        monthly_stats[month_key]['messages'] += stats['total_messages']
        monthly_stats[month_key]['chars'] += stats['total_chars']
        monthly_stats[month_key]['tokens'] += stats['total_tokens']
        monthly_stats[month_key]['hours'] += stats['duration_hours']
    
    for month in sorted(monthly_stats.keys()):
        stats = monthly_stats[month]
        print(f"  {month}:")
        print(f"    Conversations: {stats['conversations']}")
        print(f"    Messages: {stats['messages']:,}")
        print(f"    Characters: {stats['chars']:,}")
        print(f"    Tokens: {stats['tokens']:,.0f}")
        print(f"    Hours: {stats['hours']:.1f}")
    print()
    
    # Peak week (March 24-30)
    print("PEAK WEEK (March 24-30, 2025):")
    peak_start = datetime(2025, 3, 24).date()
    peak_end = datetime(2025, 3, 30).date()
    peak_stats = [s for s in all_stats if peak_start <= s['file_date'] <= peak_end]
    
    if peak_stats:
        peak_conversations = len(peak_stats)
        peak_messages = sum(s['total_messages'] for s in peak_stats)
        peak_chars = sum(s['total_chars'] for s in peak_stats)
        peak_tokens = sum(s['total_tokens'] for s in peak_stats)
        peak_hours = sum(s['duration_hours'] for s in peak_stats)
        
        print(f"  Conversations: {peak_conversations}")
        print(f"  Messages: {peak_messages:,}")
        print(f"  Characters: {peak_chars:,} ({peak_chars/total_chars*100:.1f}% of total)")
        print(f"  Tokens: {peak_tokens:,.0f} ({peak_tokens/total_tokens*100:.1f}% of total)")
        print(f"  Hours: {peak_hours:.1f} ({peak_hours/total_hours*100:.1f}% of total)")
        print(f"  Average per Day: {peak_chars/7:,.0f} characters/day")
    print()
    
    return {
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'total_chars': total_chars,
        'total_tokens': total_tokens,
        'total_hours': total_hours,
        'date_range_days': date_range_days,
        'all_stats': all_stats
    }

if __name__ == '__main__':
    results = analyze_fellowship_period()

