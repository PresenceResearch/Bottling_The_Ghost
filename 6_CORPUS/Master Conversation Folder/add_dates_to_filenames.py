import json
import os
from pathlib import Path
from datetime import datetime

def get_date_from_json(json_file_path):
    """Extract creation date from JSON file"""
    try:
        with open(json_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            json_data = json.load(f)
        
        create_time = json_data.get('create_time')
        if create_time:
            try:
                date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d')
                return date_str
            except (ValueError, OSError):
                return None
    except Exception as e:
        print(f"  Error reading {json_file_path.name}: {e}")
        return None
    return None

def rename_file_with_date(file_path, date_str):
    """Rename file to include date"""
    if not date_str:
        return False
    
    try:
        parent = file_path.parent
        stem = file_path.stem
        suffix = file_path.suffix
        
        # Create new filename: original_name_YYYY-MM-DD.ext
        new_name = f"{stem}_{date_str}{suffix}"
        new_path = parent / new_name
        
        # Only rename if the new name is different
        if new_path != file_path:
            file_path.rename(new_path)
            return True
    except Exception as e:
        print(f"  Error renaming {file_path.name}: {e}")
        return False
    return False

def process_group_folder(group_folder, base_dir):
    """Process all JSON files in a group folder"""
    json_files = sorted(group_folder.glob('conversation_*.json'))
    renamed_count = 0
    
    for json_file in json_files:
        # Skip if already has date in filename (format: conversation_XXXX_YYYY-MM-DD.json)
        if '_' in json_file.stem and len(json_file.stem.split('_')) >= 3:
            # Check if last part looks like a date
            parts = json_file.stem.split('_')
            if len(parts[-1]) == 10 and parts[-1].count('-') == 2:
                continue  # Already has date
        
        date_str = get_date_from_json(json_file)
        if date_str:
            if rename_file_with_date(json_file, date_str):
                renamed_count += 1
        else:
            print(f"  Could not extract date from {json_file.name}")
    
    return renamed_count

def process_markdown_folder(md_folder, base_dir):
    """Process all Markdown files in a markdown folder"""
    md_files = sorted(md_folder.glob('conversation_*.md'))
    renamed_count = 0
    
    for md_file in md_files:
        # Skip if already has date in filename
        if '_' in md_file.stem and len(md_file.stem.split('_')) >= 3:
            parts = md_file.stem.split('_')
            if len(parts[-1]) == 10 and parts[-1].count('-') == 2:
                continue  # Already has date
        
        # Find corresponding JSON file to get date
        # Extract original number from filename (e.g., conversation_0001.md -> 0001)
        stem_parts = md_file.stem.split('_')
        if len(stem_parts) >= 2:
            conv_num = stem_parts[1]  # Get the number part
            
            # Find the corresponding JSON file in the original group folder
            group_num = md_folder.name.replace('_markdown', '')
            
            # Look for JSON files that start with conversation_XXXX (may or may not have date)
            json_files = list((base_dir / group_num).glob(f"conversation_{conv_num}*.json"))
            if json_files:
                json_file = json_files[0]  # Use the first match
            else:
                json_file = base_dir / group_num / f"conversation_{conv_num}.json"
            
            if json_file.exists():
                date_str = get_date_from_json(json_file)
                if date_str:
                    if rename_file_with_date(md_file, date_str):
                        renamed_count += 1
                else:
                    print(f"  Could not extract date from {json_file.name} for {md_file.name}")
            else:
                print(f"  Could not find JSON file for {md_file.name}")
    
    return renamed_count

def add_dates_to_all_files(base_dir='.'):
    """Add dates to all JSON and Markdown files"""
    base_path = Path(base_dir)
    
    # Process group folders (JSON files)
    group_folders = sorted([d for d in base_path.iterdir() 
                           if d.is_dir() and d.name.startswith('group_') and not d.name.endswith('_markdown')])
    
    total_json_renamed = 0
    total_md_renamed = 0
    
    print("Processing JSON files...")
    for group_folder in group_folders:
        print(f"  Processing {group_folder.name}...")
        renamed = process_group_folder(group_folder, base_path)
        total_json_renamed += renamed
        if renamed > 0:
            print(f"    Renamed {renamed} JSON files")
    
    print(f"\nRenamed {total_json_renamed} JSON files")
    
    # Process markdown folders
    md_folders = sorted([d for d in base_path.iterdir() 
                        if d.is_dir() and d.name.endswith('_markdown')])
    
    print("\nProcessing Markdown files...")
    for md_folder in md_folders:
        print(f"  Processing {md_folder.name}...")
        renamed = process_markdown_folder(md_folder, base_path)
        total_md_renamed += renamed
        if renamed > 0:
            print(f"    Renamed {renamed} Markdown files")
    
    print(f"\nRenamed {total_md_renamed} Markdown files")
    print(f"\nComplete! Total files renamed: {total_json_renamed + total_md_renamed}")

if __name__ == '__main__':
    add_dates_to_all_files()

