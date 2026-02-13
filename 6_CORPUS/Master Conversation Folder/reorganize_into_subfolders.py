from pathlib import Path
import shutil

def reorganize_chronological_folder(chrono_path):
    """Reorganize existing files into JSON and MD subfolders"""
    chrono_path = Path(chrono_path)
    
    if not chrono_path.exists():
        print(f"Folder {chrono_path} does not exist!")
        return
    
    files_moved = 0
    errors = 0
    
    # Find all week folders
    for year_folder in chrono_path.iterdir():
        if not year_folder.is_dir():
            continue
        
        for month_folder in year_folder.iterdir():
            if not month_folder.is_dir():
                continue
            
            for week_folder in month_folder.iterdir():
                if not week_folder.is_dir():
                    continue
                
                # Skip if already has JSON/MD subfolders
                if (week_folder / "JSON").exists() or (week_folder / "MD").exists():
                    continue
                
                # Create JSON and MD subfolders
                json_dir = week_folder / "JSON"
                md_dir = week_folder / "MD"
                json_dir.mkdir(exist_ok=True)
                md_dir.mkdir(exist_ok=True)
                
                # Move files
                for file in week_folder.iterdir():
                    if file.is_file():
                        if file.suffix == '.json':
                            try:
                                shutil.move(str(file), str(json_dir / file.name))
                                files_moved += 1
                            except Exception as e:
                                print(f"Error moving {file.name}: {e}")
                                errors += 1
                        elif file.suffix == '.md':
                            try:
                                shutil.move(str(file), str(md_dir / file.name))
                                files_moved += 1
                            except Exception as e:
                                print(f"Error moving {file.name}: {e}")
                                errors += 1
    
    print(f"\nReorganization complete!")
    print(f"  Files moved: {files_moved}")
    print(f"  Errors: {errors}")

if __name__ == '__main__':
    reorganize_chronological_folder('chronological')

