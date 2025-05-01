import os
import shutil
import sys
import csv

def move_images(csv_file, source_folder, dest_folder):
    # Create destination folder if it doesn't exist
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
        print(f"Created destination folder: {dest_folder}")
    
    # Read the CSV file
    moved_count = 0
    skipped_count = 0
    
    try:
        with open(csv_file, 'r') as file:
            # Use csv reader to properly handle the CSV format
            csv_reader = csv.reader(file)
            
            # Skip header row if exists
            try:
                header = next(csv_reader)
            except StopIteration:
                print("Warning: Empty CSV file")
                return
            
            # Process each data row
            for row in csv_reader:
                if row and len(row) > 0:
                    # Extract just the image filename from the first column
                    image_filename = row[0].strip()
                    
                    source_path = os.path.join(source_folder, image_filename)
                    dest_path = os.path.join(dest_folder, image_filename)
                    
                    # Check if file exists in source
                    if not os.path.isfile(source_path):
                        print(f"Warning: {image_filename} not found in source folder")
                        continue
                    
                    # Check if file already exists in destination
                    if os.path.isfile(dest_path):
                        print(f"Skipping {image_filename} - already exists in destination")
                        skipped_count += 1
                        continue
                    
                    # Move the file (using copy2 to preserve metadata)
                    try:
                        shutil.copy2(source_path, dest_path)
                        print(f"Moved: {image_filename}")
                        moved_count += 1
                    except Exception as e:
                        print(f"Error moving {image_filename}: {e}")
    
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return
    
    print(f"\nSummary:")
    print(f"Files moved: {moved_count}")
    print(f"Files skipped (already exist): {skipped_count}")

def main():
    # Default folders
    source_folder = "dataset"
    dest_folder = "dataset_testing"
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python script.py <csv_file> [source_folder] [dest_folder]")
        print(f"Default source folder: {source_folder}")
        print(f"Default destination folder: {dest_folder}")
        return
    
    csv_file = sys.argv[1]
    
    if len(sys.argv) >= 3:
        source_folder = sys.argv[2]
    
    if len(sys.argv) >= 4:
        dest_folder = sys.argv[3]
    
    print(f"Moving images listed in {csv_file} from {source_folder} to {dest_folder}...")
    move_images(csv_file, source_folder, dest_folder)

if __name__ == "__main__":
    main()