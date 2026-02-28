import cv2
from PIL import Image, ImageTk

def display_image(img, target_label, max_size=(300, 300)):
    """
    Display an image (NumPy array) in a Tkinter Label.
    Automatically converts BGR (OpenCV) to RGB (PIL) if needed.
    """
    if img.ndim == 3 and img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    pil_img = Image.fromarray(img)
    pil_img.thumbnail(max_size, Image.LANCZOS)
    tk_img = ImageTk.PhotoImage(pil_img)

    target_label.configure(image=tk_img, text="")
    target_label.image = tk_img