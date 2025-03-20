# import tkinter as tk
# from tkinter import filedialog
# from PIL import Image, ImageTk
# import cv2
# import numpy as np

# class WatermarkRemoverApp:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Watermark Remover")
        
#         # GUI Elements
#         self.canvas = tk.Canvas(root, cursor="cross")
#         self.canvas.pack(fill=tk.BOTH, expand=True)
        
#         # Variables
#         self.image = None
#         self.tk_image = None
#         self.rect = None
#         self.start_x = self.start_y = None
        
#         # Menu
#         menubar = tk.Menu(root)
#         file_menu = tk.Menu(menubar, tearoff=0)
#         file_menu.add_command(label="Open", command=self.open_image)
#         file_menu.add_command(label="Save", command=self.save_image)
#         menubar.add_cascade(label="File", menu=file_menu)
#         root.config(menu=menubar)
        
#         # Bind mouse events
#         self.canvas.bind("<ButtonPress-1>", self.on_press)
#         self.canvas.bind("<B1-Motion>", self.on_drag)
#         self.canvas.bind("<ButtonRelease-1>", self.on_release)
    
#     def open_image(self):
#         path = filedialog.askopenfilename()
#         if path:
#             self.image = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
#             self.display_image()
    
#     def display_image(self):
#         img_pil = Image.fromarray(self.image)
#         self.tk_image = ImageTk.PhotoImage(img_pil)
#         self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
#         self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
    
#     def on_press(self, event):
#         self.start_x, self.start_y = event.x, event.y
#         if self.rect:
#             self.canvas.delete(self.rect)
#         self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline='red')
    
#     def on_drag(self, event):
#         self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    
#     def on_release(self, event):
#         x0, y0 = max(0, self.start_x), max(0, self.start_y)
#         x1, y1 = min(event.x, self.image.shape[1]), min(event.y, self.image.shape[0])
#         self.process_watermark(x0, y0, x1 - x0, y1 - y0)
    
#     def process_watermark(self, x, y, w, h):
#         mask = np.zeros(self.image.shape[:2], np.uint8)
#         mask[y:y+h, x:x+w] = 255
#         inpainted = cv2.inpaint(
#             cv2.cvtColor(self.image, cv2.COLOR_RGB2BGR), 
#             mask, 
#             inpaintRadius=3, 
#             flags=cv2.INPAINT_TELEA
#         )
#         self.image = cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)
#         self.display_image()
    
#     def save_image(self):
#         if self.image is not None:
#             path = filedialog.asksaveasfilename(defaultextension=".png")
#             if path:
#                 cv2.imwrite(path, cv2.cvtColor(self.image, cv2.COLOR_RGB2BGR))

# if __name__ == "__main__":
#     root = tk.Tk()
#     app = WatermarkRemoverApp(root)
#     root.mainloop()



import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import cv2
import numpy as np
import os

class AdvancedWatermarkRemover:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Watermark Remover Pro")
        self.root.geometry("1000x700")
        
        # State management
        self.history = []
        self.current_step = -1
        self.undo_stack = []
        self.redo_stack = []
        
        # Image variables
        self.original_image = None
        self.processed_image = None
        self.mask = None
        self.zoom_level = 1.0
        
        # Tool variables
        self.selected_tool = "rectangle"
        self.brush_size = 10
        self.last_draw = None
        
        # GUI Setup
        self.create_menu()
        self.create_toolbar()
        self.create_main_interface()
        self.create_statusbar()
        
        # Bind keyboard shortcuts
        self.root.bind("<Control-z>", self.undo)
        self.root.bind("<Control-y>", self.redo)
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_image, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        
        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=lambda: self.adjust_zoom(1.2))
        view_menu.add_command(label="Zoom Out", command=lambda: self.adjust_zoom(0.8))
        view_menu.add_command(label="Reset Zoom", command=self.reset_zoom)
        
        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        menubar.add_cascade(label="View", menu=view_menu)
        
        self.root.config(menu=menubar)
    
    def create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        tools = [
            ("rectangle", "⬜ Rectangle Select", self.select_rectangle_tool),
            ("brush", "🖌️ Brush", self.select_brush_tool),
            ("zoom-in", "🔍 Zoom In", lambda: self.adjust_zoom(1.2)),
            ("zoom-out", "🔎 Zoom Out", lambda: self.adjust_zoom(0.8)),
            ("undo", "↩️ Undo", self.undo),
            ("redo", "↪️ Redo", self.redo),
        ]
        
        for tool in tools:
            btn = ttk.Button(toolbar, text=tool[1], command=tool[2])
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Brush size control
        self.brush_slider = ttk.Scale(toolbar, from_=1, to=50, 
                                     command=lambda v: setattr(self, 'brush_size', int(float(v))))
        self.brush_slider.set(self.brush_size)
        self.brush_slider.pack(side=tk.LEFT, padx=10)
        
    def create_main_interface(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(main_frame, cursor="cross", bg='#2e2e2e')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
    
    def create_statusbar(self):
        self.statusbar = ttk.Label(self.root, text="Ready", anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_status(self, text):
        self.statusbar.config(text=text)
    
    # ... [Previous open_image, display_image, save_image methods] ...

    def select_rectangle_tool(self):
        self.selected_tool = "rectangle"
        self.canvas.config(cursor="cross")
    
    def select_brush_tool(self):
        self.selected_tool = "brush"
        self.canvas.config(cursor="circle")

    def on_press(self, event):
        self.last_draw = (event.x, event.y)
        if self.selected_tool == "brush":
            self.draw_brush(event.x, event.y)

    def on_drag(self, event):
        if self.selected_tool == "brush":
            self.draw_brush(event.x, event.y)
        elif self.selected_tool == "rectangle":
            self.draw_rectangle(event.x, event.y)

    def draw_brush(self, x, y):
        if self.original_image is None:
            return
        
        # Convert canvas coordinates to image coordinates
        img_x = int(x / self.zoom_level)
        img_y = int(y / self.zoom_level)
        
        # Create temporary mask
        if self.mask is None:
            self.mask = np.zeros(self.original_image.shape[:2], dtype=np.uint8)
        
        # Draw on mask
        cv2.circle(self.mask, (img_x, img_y), self.brush_size, 255, -1)
        
        # Show preview
        temp_image = self.processed_image.copy()
        temp_image[self.mask == 255] = [255, 0, 0]  # Highlight selected area
        self.display_image(temp_image)

    def draw_rectangle(self, x, y):
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, x, y,
            outline='red', width=2
        )

    def on_release(self, event):
        if self.selected_tool == "rectangle":
            self.process_rectangle_selection()
            self.canvas.delete(self.rect)
        elif self.selected_tool == "brush":
            self.process_brush_selection()
    
    def process_rectangle_selection(self):
        # Convert canvas coordinates to image coordinates
        x0 = int(self.start_x / self.zoom_level)
        y0 = int(self.start_y / self.zoom_level)
        x1 = int(event.x / self.zoom_level)
        y1 = int(event.y / self.zoom_level)
        
        # Create mask
        if self.mask is None:
            self.mask = np.zeros(self.original_image.shape[:2], dtype=np.uint8)
        self.mask[y0:y1, x0:x1] = 255
        
        # Process immediately
        self.process_inpainting()
    
    def process_brush_selection(self):
        self.process_inpainting()
        self.mask = None  # Reset mask after processing
    
    def process_inpainting(self):
        if self.original_image is None or self.mask is None:
            return
        
        # Save state for undo
        self.push_undo_state()
        
        # Advanced inpainting with parameters
        inpainted = cv2.inpaint(
            cv2.cvtColor(self.original_image, cv2.COLOR_RGB2BGR),
            self.mask,
            inpaintRadius=7,
            flags=cv2.INPAINT_NS
        )
        
        self.processed_image = cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)
        self.display_image(self.processed_image)
    
    # ... [Undo/redo, zoom, and utility methods] ...

    def push_undo_state(self):
        if self.processed_image is not None:
            self.undo_stack.append(self.processed_image.copy())
            self.redo_stack.clear()
    
    def undo(self, event=None):
        if len(self.undo_stack) > 0:
            self.redo_stack.append(self.processed_image.copy())
            self.processed_image = self.undo_stack.pop()
            self.display_image(self.processed_image)
    
    def redo(self, event=None):
        if len(self.redo_stack) > 0:
            self.undo_stack.append(self.processed_image.copy())
            self.processed_image = self.redo_stack.pop()
            self.display_image(self.processed_image)
    
    def adjust_zoom(self, factor):
        self.zoom_level *= factor
        self.display_image(self.processed_image if self.processed_image is not None else self.original_image)
    
    def reset_zoom(self):
        self.zoom_level = 1.0
        self.display_image(self.processed_image if self.processed_image is not None else self.original_image)
    
    def on_mousewheel(self, event):
        if event.delta > 0:
            self.adjust_zoom(1.2)
        else:
            self.adjust_zoom(0.8)
    
    def display_image(self, image=None):
        if image is None:
            return
        
        # Resize based on zoom level
        height, width = image.shape[:2]
        new_width = int(width * self.zoom_level)
        new_height = int(height * self.zoom_level)
        
        img_pil = Image.fromarray(image).resize((new_width, new_height))
        self.tk_image = ImageTk.PhotoImage(img_pil)
        
        self.canvas.config(width=new_width, height=new_height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
    
    # ... [Rest of the methods] ...

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedWatermarkRemover(root)
    root.mainloop()