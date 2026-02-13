import json
import os
from pathlib import Path
from datetime import datetime

def extract_conversation(json_data):
    """Extract conversation messages from JSON structure"""
    title = json_data.get('title', 'Untitled Conversation')
    mapping = json_data.get('mapping', {})
    
    # Find the root node (node with no parent)
    root_node_id = None
    for node_id, node in mapping.items():
        if node.get('parent') is None and node.get('message') is None:
            root_node_id = node_id
            break
    
    if not root_node_id:
        return title, []
    
    # Traverse the conversation tree
    messages = []
    current_node_id = root_node_id
    
    def traverse(node_id, depth=0):
        if node_id not in mapping:
            return
        
        node = mapping[node_id]
        message = node.get('message')
        
        if message:
            role = message.get('author', {}).get('role')
            if role in ['user', 'assistant']:  # Skip system messages
                content = message.get('content', {})
                parts = content.get('parts', [])
                # Handle both string and dict parts (e.g., images)
                text_parts = []
                for part in parts:
                    if isinstance(part, str) and part.strip():
                        text_parts.append(part)
                    elif isinstance(part, dict):
                        # Handle image attachments or other structured content
                        if part.get('content_type') == 'image_asset_pointer':
                            text_parts.append(f"[Image: {part.get('asset_pointer', 'image')}]")
                        else:
                            # Try to extract any text from dict
                            text_parts.append(f"[{part.get('content_type', 'attachment')}]")
                
                text = '\n'.join(text_parts)
                
                if text.strip():  # Only add non-empty messages
                    create_time = message.get('create_time')
                    timestamp = None
                    if create_time:
                        try:
                            timestamp = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                    
                    messages.append({
                        'role': role,
                        'content': text,
                        'timestamp': timestamp
                    })
        
        # Continue to children
        children = node.get('children', [])
        for child_id in children:
            traverse(child_id, depth + 1)
    
    # Start traversal from root's first child
    root_node = mapping[root_node_id]
    for child_id in root_node.get('children', []):
        traverse(child_id)
    
    return title, messages

def convert_to_markdown(json_file_path, output_dir):
    """Convert a single JSON file to Markdown"""
    try:
        with open(json_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                json_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"  JSON decode error in {json_file_path.name}: {e}")
                return False
        
        title, messages = extract_conversation(json_data)
        
        # Create markdown content
        md_content = f"# {title}\n\n"
        
        if json_data.get('create_time'):
            try:
                create_time = datetime.fromtimestamp(json_data['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                md_content += f"**Created:** {create_time}\n\n"
            except:
                pass
        
        md_content += "---\n\n"
        
        for i, msg in enumerate(messages, 1):
            role_label = "**You:**" if msg['role'] == 'user' else "**Assistant:**"
            md_content += f"{role_label}\n\n"
            
            if msg['timestamp']:
                md_content += f"*{msg['timestamp']}*\n\n"
            
            md_content += f"{msg['content']}\n\n"
            md_content += "---\n\n"
        
        # Save markdown file
        json_filename = Path(json_file_path).stem
        md_filename = json_filename + '.md'
        output_path = Path(output_dir) / md_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return True
    except Exception as e:
        print(f"Error converting {json_file_path}: {e}")
        return False

def convert_all_conversations(base_dir='.'):
    """Convert all JSON files in group folders to Markdown"""
    base_path = Path(base_dir)
    group_folders = sorted([d for d in base_path.iterdir() if d.is_dir() and d.name.startswith('group_')])
    
    total_converted = 0
    total_errors = 0
    
    for group_folder in group_folders:
        print(f"Processing {group_folder.name}...")
        json_files = sorted(group_folder.glob('conversation_*.json'))
        
        # Create markdown folder for this group
        md_folder = base_path / f"{group_folder.name}_markdown"
        md_folder.mkdir(exist_ok=True)
        
        for json_file in json_files:
            if convert_to_markdown(json_file, md_folder):
                total_converted += 1
            else:
                total_errors += 1
        
        print(f"  Converted {len(json_files)} files in {group_folder.name}")
    
    print(f"\nConversion complete!")
    print(f"   Total converted: {total_converted}")
    print(f"   Errors: {total_errors}")
    print(f"\nMarkdown files are in folders named 'group_XXX_markdown'")

if __name__ == '__main__':
    convert_all_conversations()

