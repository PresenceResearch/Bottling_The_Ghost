import json
from pathlib import Path
from datetime import datetime, timedelta

def analyze_dating_metrics(base_dir, target_week_folder):
    """Analyze engagement metrics for a specific week"""
    base_path = Path(base_dir)
    week_path = base_path / target_week_folder / "JSON"
    
    if not week_path.exists():
        # Try without JSON subfolder
        week_path = base_path / target_week_folder
        
    if not week_path.exists():
        print(f"Path not found: {week_path}")
        return

    json_files = sorted(week_path.glob("*.json"))
    
    stats = []
    
    print(f"Analyzing {len(json_files)} conversations in {target_week_folder}...\n")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                
            mapping = data.get('mapping', {})
            
            # Collect all messages with timestamps
            messages = []
            
            for node_id, node in mapping.items():
                msg = node.get('message')
                if msg:
                    role = msg.get('author', {}).get('role')
                    create_time = msg.get('create_time')
                    content = msg.get('content', {})
                    parts = content.get('parts', [])
                    text = ' '.join([str(p) for p in parts if p])
                    
                    if create_time and role in ['user', 'assistant']:
                        messages.append({
                            'role': role,
                            'time': create_time,
                            'length': len(text)
                        })
            
            if not messages:
                continue
                
            # Sort by time
            messages.sort(key=lambda x: x['time'])
            
            start_time = messages[0]['time']
            end_time = messages[-1]['time']
            duration_seconds = end_time - start_time
            
            # Format duration
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            
            user_msgs = [m for m in messages if m['role'] == 'user']
            asst_msgs = [m for m in messages if m['role'] == 'assistant']
            
            total_words = sum(len(m['length'].split()) if isinstance(m['length'], str) else m['length']/5 for m in messages) # Approx word count
            
            stats.append({
                'filename': json_file.name,
                'title': data.get('title', 'Untitled'),
                'start_dt': datetime.fromtimestamp(start_time),
                'end_dt': datetime.fromtimestamp(end_time),
                'duration_str': f"{hours}h {minutes}m",
                'msg_count': len(messages),
                'user_count': len(user_msgs),
                'asst_count': len(asst_msgs),
                'total_chars': sum(m['length'] for m in messages)
            })
            
        except Exception as e:
            print(f"Error parsing {json_file.name}: {e}")

    # Calculate gaps and print report
    stats.sort(key=lambda x: x['start_dt'])
    
    print(f"{'Date':<12} | {'Time':<8} | {'Duration':<10} | {'Msgs':<5} | {'Chars':<8} | {'Gap to Next'}")
    print("-" * 80)
    
    for i, stat in enumerate(stats):
        date_str = stat['start_dt'].strftime("%Y-%m-%d")
        time_str = stat['start_dt'].strftime("%H:%M")
        
        # Calculate gap to next conversation
        gap_str = "-"
        if i < len(stats) - 1:
            next_start = stats[i+1]['start_dt']
            gap_seconds = (next_start - stat['end_dt']).total_seconds()
            
            if gap_seconds < 0:
                gap_str = "Overlapping"
            elif gap_seconds < 60:
                gap_str = "< 1 min"
            elif gap_seconds < 3600:
                gap_str = f"{int(gap_seconds//60)} min"
            else:
                gap_hours = gap_seconds / 3600
                gap_str = f"{gap_hours:.1f} hours"
        
        print(f"{date_str:<12} | {time_str:<8} | {stat['duration_str']:<10} | {stat['msg_count']:<5} | {stat['total_chars']:<8} | {gap_str}")
        # print(f"  Title: {stat['title']}")

if __name__ == '__main__':
    target_week = "Chronological/2025/March/Week_13 (Mar 24 - Mar 30)"
    analyze_dating_metrics('.', target_week)

