import os

def get_save_path(original_path):
    base, ext = os.path.splitext(original_path)
    counter = 1
    output_path = f"{base}_cartoon{ext}"
    while os.path.exists(output_path):
        output_path = f"{base}_cartoon_{counter}{ext}"
        counter += 1
    return output_path