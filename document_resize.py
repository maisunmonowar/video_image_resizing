import argparse
import os
import shutil
from PIL import Image, ImageEnhance, ImageOps

def compress_and_enhance_document(input_path, output_path, max_dimension=1920):
    """
    Resizes, enhances contrast, and compresses an image for document storage.
    """
    try:
        with Image.open(input_path) as img:
            # Handle EXIF orientation (e.g. photos taken sideways on phones)
            img = ImageOps.exif_transpose(img)

            # Convert to RGB (required for saving as JPEG, drops alpha channel from PNGs)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize if the image is too large, maintaining aspect ratio
            ratio = min(max_dimension / float(img.size[0]), max_dimension / float(img.size[1]))
            if ratio < 1.0:
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Enhance contrast slightly to make text more readable
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2) # 20% more contrast

            # Save with reduced quality for smaller file size constraint
            # 70 is generally a good balance between size and readability for documents
            img.save(output_path, "JPEG", quality=70, optimize=True)
            return True
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Resize, compress, and archive document photos.")
    parser.add_argument("--path", required=True, help="Path to the folder containing document photos.")
    args = parser.parse_args()

    # 1. Validate input path
    folder_path = args.path
    if not os.path.isdir(folder_path):
        print(f"Error: The path '{folder_path}' is not a valid directory.")
        return

    # 2. Get the 'delete later' path from the OS environment variable
    delete_later_env_var = "DELETE_LATER_PATH" 
    # NOTE: This is a 'delete later' folder, handled by a different script.
    delete_later_path = os.environ.get(delete_later_env_var)
    
    if not delete_later_path:
        print(f"Error: The OS environment variable '{delete_later_env_var}' is not set.")
        print(f"Please set it to the directory where original files should be moved for later deletion.")
        print(f"Example (PowerShell): $env:{delete_later_env_var}=\"C:\\Path\\To\\DeleteLater\"")
        return

    # Create the 'delete later' directory if it doesn't exist
    if not os.path.exists(delete_later_path):
        try:
            os.makedirs(delete_later_path, exist_ok=True)
            print(f"Created 'delete later' directory at: {delete_later_path}")
        except Exception as e:
            print(f"Error creating 'delete later' directory: {e}")
            return

    # Supported image formats
    supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')

    # 3. Process each image in the directory
    for filename in os.listdir(folder_path):
        if not filename.lower().endswith(supported_extensions):
            continue
            
        parts = filename.split('.', 1)
        if len(parts) == 2:
            base_name = parts[0]
            rest = '.' + parts[1]
        else:
            base_name = filename
            rest = ".jpg"
        
        # Skip files that were already processed (base name ends with an underscore)
        if base_name.endswith('_'):
            continue

        input_path = os.path.join(folder_path, filename)
        
        # Create output path (rename before first dot. e.g. photos.MP.jpg -> photos_.MP.jpg)
        actual_ext = os.path.splitext(filename)[1].lower()
        if actual_ext in ('.jpg', '.jpeg'):
            output_filename = f"{base_name}_{rest}"
        else:
            output_filename = f"{base_name}_.jpg" # Force extension to jpg if original was png/bmp/etc.
            
        output_path = os.path.join(folder_path, output_filename)

        # Skip if there is evidence it has already been processed
        if os.path.exists(output_path):
            print(f"Skipping {filename}... (Processed version '{output_filename}' already exists)")
            continue

        print(f"Processing {filename}...")
        success = compress_and_enhance_document(input_path, output_path)

        # 4. Move original file to the 'delete later' folder if processing was successful
        if success:
            dest_path = os.path.join(delete_later_path, filename)
            
            # Handle filename collisions in the delete later folder
            counter = 1
            while os.path.exists(dest_path):
                arch_name, arch_ext = os.path.splitext(filename)
                dest_path = os.path.join(delete_later_path, f"{arch_name}_{counter}{arch_ext}")
                counter += 1

            try:
                shutil.move(input_path, dest_path)
                print(f"  -> Saved optimized version as: {output_filename}")
                print(f"  -> Original moved to: {dest_path}")
            except Exception as e:
                print(f"  -> Error moving original file: {e}")
        else:
            print(f"  -> Failed to process {filename}")

if __name__ == "__main__":
    main()
