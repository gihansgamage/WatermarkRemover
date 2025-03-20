import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog

def main():
    # File selection dialog
    root = tk.Tk()
    root.withdraw()
    
    # Select input image
    file_path = filedialog.askopenfilename(
        title="Select Image",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
    )
    if not file_path:
        return

    # Load image
    image = cv2.imread(file_path)
    if image is None:
        print("Error: Could not load image")
        return

    # Select ROI (Region of Interest - watermark area)
    roi = cv2.selectROI("Select Watermark Area (Drag & Press Enter)", image)
    cv2.destroyAllWindows()

    # Create mask
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    x, y, w, h = [int(i) for i in roi]
    mask[y:y+h, x:x+w] = 255  # Mark selected area for inpainting

    # Inpainting using Telea method
    inpainted_image = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    # Save output
    output_path = filedialog.asksaveasfilename(
        title="Save Processed Image",
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")]
    )
    if output_path:
        cv2.imwrite(output_path, inpainted_image)
        print(f"Image saved successfully to {output_path}")

if __name__ == "__main__":
    main()