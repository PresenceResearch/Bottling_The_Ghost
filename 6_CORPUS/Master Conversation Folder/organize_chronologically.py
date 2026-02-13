import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import calendar

def get_week_number(date_obj):
    """Get ISO week number for a date"""
    return date_obj.isocalendar()[1]

def get_week_folder_name(date_obj):
    """Get week folder name in format: Week_XX (Month DD - Month DD)"""
    # Convert date to datetime for calculations if needed
    if isinstance(date_obj, datetime):
        dt = date_obj
    else:
        dt = datetime.combine(date_obj, datetime.min.time())
    
    # Get the Monday of the week (ISO week starts on Monday)
    days_since_monday = dt.weekday()
    monday = dt - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)
    
    # Format: Week_01 (Jan 02 - Jan 08)
    week_num = get_week_number(date_obj)
    month_abbr_monday = calendar.month_abbr[monday.month]
    month_abbr_sunday = calendar.month_abbr[sunday.month]
    
    week_name = f"Week_{week_num:02d} ({month_abbr_monday} {monday.day:02d} - {month_abbr_sunday} {sunday.day:02d})"
    
    return week_name

def extract_date_from_filename(filename):
    """Extract date from filename like conversation_0001_2023-02-17.json"""
    try:
        # Split by underscore and get the last part before extension
        parts = filename.stem.split('_')
        if len(parts) >= 3:
            date_str = parts[-1]  # Should be YYYY-MM-DD
            if len(date_str) == 10 and date_str.count('-') == 2:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        pass
    return None

def get_date_from_json(json_file_path):
    """Extract creation date from JSON file"""
    try:
        with open(json_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            json_data = json.load(f)
        
        create_time = json_data.get('create_time')
        if create_time:
            try:
                return datetime.fromtimestamp(create_time).date()
            except (ValueError, OSError):
                pass
    except Exception:
        pass
    return None

def get_file_date(file_path):
    """Get date from file - try filename first, then JSON content"""
    # Try to get date from filename
    date = extract_date_from_filename(file_path)
    if date:
        return date
    
    # If it's a JSON file, try to read the date from content
    if file_path.suffix == '.json':
        date = get_date_from_json(file_path)
        if date:
            return date
    
    return None

def create_chronological_structure(base_dir, chronological_dir):
    """Create YEAR/MONTH/WEEK folder structure and copy files"""
    base_path = Path(base_dir)
    chrono_path = Path(chronological_dir)
    chrono_path.mkdir(exist_ok=True)
    
    # Statistics
    files_copied = 0
    files_skipped = 0
    errors = 0
    
    # Process group folders (JSON files)
    group_folders = sorted([d for d in base_path.iterdir() 
                           if d.is_dir() and d.name.startswith('group_') and not d.name.endswith('_markdown')])
    
    print("Processing JSON files...")
    for group_folder in group_folders:
        json_files = sorted(group_folder.glob('conversation_*.json'))
        
        for json_file in json_files:
            date = get_file_date(json_file)
            if not date:
                print(f"  Could not determine date for {json_file.name}")
                files_skipped += 1
                continue
            
            # Create folder structure: YEAR/MONTH/WEEK/JSON
            year = date.year
            month = calendar.month_name[date.month]
            week_folder_name = get_week_folder_name(date)
            
            target_dir = chrono_path / str(year) / month / week_folder_name / "JSON"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy JSON file
            try:
                target_file = target_dir / json_file.name
                if not target_file.exists():
                    shutil.copy2(json_file, target_file)
                    files_copied += 1
            except Exception as e:
                print(f"  Error copying {json_file.name}: {e}")
                errors += 1
    
    # Process markdown folders
    md_folders = sorted([d for d in base_path.iterdir() 
                        if d.is_dir() and d.name.endswith('_markdown')])
    
    print("\nProcessing Markdown files...")
    for md_folder in md_folders:
        md_files = sorted(md_folder.glob('conversation_*.md'))
        
        for md_file in md_files:
            date = get_file_date(md_file)
            if not date:
                # Try to find corresponding JSON file
                group_num = md_folder.name.replace('_markdown', '')
                stem_parts = md_file.stem.split('_')
                if len(stem_parts) >= 2:
                    conv_num = stem_parts[1]
                    json_files = list((base_path / group_num).glob(f"conversation_{conv_num}*.json"))
                    if json_files:
                        date = get_file_date(json_files[0])
                
                if not date:
                    print(f"  Could not determine date for {md_file.name}")
                    files_skipped += 1
                    continue
            
            # Create folder structure: YEAR/MONTH/WEEK/MD
            year = date.year
            month = calendar.month_name[date.month]
            week_folder_name = get_week_folder_name(date)
            
            target_dir = chrono_path / str(year) / month / week_folder_name / "MD"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy Markdown file
            try:
                target_file = target_dir / md_file.name
                if not target_file.exists():
                    shutil.copy2(md_file, target_file)
                    files_copied += 1
            except Exception as e:
                print(f"  Error copying {md_file.name}: {e}")
                errors += 1
    
    print(f"\n{'='*60}")
    print(f"Organization complete!")
    print(f"  Files copied: {files_copied}")
    print(f"  Files skipped: {files_skipped}")
    print(f"  Errors: {errors}")
    print(f"\nFiles organized in: {chrono_path}")
    print(f"Structure: chronological/YEAR/MONTH/WEEK/JSON/ and .../MD/")

if __name__ == '__main__':
    import sys
    base_directory = '.'
    chronological_directory = 'chronological'
    
    if len(sys.argv) > 1:
        chronological_directory = sys.argv[1]
    
    create_chronological_structure(base_directory, chronological_directory)

