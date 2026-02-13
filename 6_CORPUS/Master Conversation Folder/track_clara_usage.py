import json
from pathlib import Path
import re
from datetime import datetime

def track_clara_usage(base_dir, start_date_str="2024-10-02", end_date_str="2025-03-09"):
    """Track usage of 'Clara' between two dates"""
    base_path = Path(base_dir)
    
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    
    results = []
    
    # Get all JSON files from chronological folders in that range
    # We need to check 2024 (Oct, Nov, Dec) and 2025 (Jan, Feb, Mar)
    
    months_to_check = [
        ("2024", "October"), ("2024", "November"), ("2024", "December"),
        ("2025", "January"), ("2025", "February"), ("2025", "March")
    ]
    
    print(f"Tracking 'Clara' usage from {start_date} to {end_date}...\n")
    
    for year, month in months_to_check:
        month_path = base_path / "Chronological" / year / month
        if not month_path.exists():
            continue
            
        for week_folder in sorted(month_path.iterdir()):
            if not week_folder.is_dir():
                continue
                
            json_dir = week_folder / "JSON"
            if not json_dir.exists():
                json_files = sorted(week_folder.glob("*.json"))
            else:
                json_files = sorted(json_dir.glob("*.json"))
                
            for json_file in json_files:
                # Extract date from filename
                try:
                    parts = json_file.stem.split('_')
                    file_date_str = parts[-1]
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
                    
                    if start_date <= file_date <= end_date:
                        # Analyze file
                        with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                            json_data = json.load(f)
                            
                        # Count "Clara"
                        user_count = 0
                        assistant_count = 0
                        
                        mapping = json_data.get('mapping', {})
                        
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
                                text = ' '.join([p for p in parts if isinstance(p, str)])
                                
                                count = len(re.findall(r'\bClara\b', text, re.IGNORECASE))
                                
                                if count > 0:
                                    if role == 'user':
                                        user_count += count
                                    elif role == 'assistant':
                                        assistant_count += count
                            
                            for child_id in node.get('children', []):
                                traverse(child_id)
                        
                        # Find root
                        root_node_id = None
                        for nid, n in mapping.items():
                            if n.get('parent') is None:
                                root_node_id = nid
                                break
                        
                        if root_node_id:
                            traverse(root_node_id)
                        
                        if user_count > 0 or assistant_count > 0:
                            results.append({
                                'date': file_date_str,
                                'filename': json_file.name,
                                'title': json_data.get('title', 'Untitled'),
                                'user_count': user_count,
                                'assistant_count': assistant_count,
                                'total': user_count + assistant_count
                            })
                            
                except Exception as e:
                    # print(f"Error processing {json_file.name}: {e}")
                    pass

    # Sort by date
    results.sort(key=lambda x: x['date'])
    
    # Group by month for summary
    monthly_stats = {}
    
    print(f"{'Date':<12} | {'User':<5} | {'Asst':<5} | {'Title'}")
    print("-" * 60)
    
    for r in results:
        print(f"{r['date']:<12} | {r['user_count']:<5} | {r['assistant_count']:<5} | {r['title']}")
        
        # Monthly stats
        month_key = r['date'][:7] # YYYY-MM
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {'conversations': 0, 'mentions': 0}
        monthly_stats[month_key]['conversations'] += 1
        monthly_stats[month_key]['mentions'] += r['total']

    print("\n" + "=" * 60)
    print("MONTHLY SUMMARY")
    print("=" * 60)
    for month, stats in sorted(monthly_stats.items()):
        print(f"{month}: {stats['conversations']} conversations, {stats['mentions']} mentions")

if __name__ == '__main__':
    track_clara_usage('.', "2024-10-02", "2025-03-09")

