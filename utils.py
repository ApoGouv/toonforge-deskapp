from PIL import Image, ImageTk
import cv2
import os

def display_image(img, target_label, max_size=(300, 300)):
    # Convert BGR (OpenCV) → RGB (PIL)
    if img.ndim == 3 and img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    pil_img = Image.fromarray(img)
    pil_img.thumbnail(max_size, Image.LANCZOS)
    tk_img = ImageTk.PhotoImage(pil_img)

    target_label.configure(image=tk_img, text="")
    target_label.image = tk_img

def get_save_path(original_path):
    base, ext = os.path.splitext(original_path)
    counter = 1
    output_path = f"{base}_cartoon{ext}"
    while os.path.exists(output_path):
        output_path = f"{base}_cartoon_{counter}{ext}"
        counter += 1
    return output_path