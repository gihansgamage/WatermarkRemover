import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import cv2
import numpy as np
import os

class AdvancedWatermarkRemoverPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Watermark Remover Pro v2.0")
        self.root.geometry("1200x800")
        self.setup_variables()
        self.create_ui()
        self.bind_events()
        
    def setup_variables(self):
        self.history = []
        self.undo_stack = []
        self.redo_stack = []
        self.original_image = None
        self.processed_image = None
        self.mask = None
        self.zoom_level = 1.0
        self.selected_tool = "rectangle"
        self.brush_size = 10
        self.last_point = None
        self.inpaint_radius = 7
        self.working_image = None
        self.display_image = None
        self.mask_preview = None

    def create_ui(self):
        self.create_menu()
        self.create_toolbar()
        self.create_main_interface()
        self.create_statusbar()
        self.create_side_panel()

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
            ("rectangle", "⬜ Area Select", self.select_rectangle_tool),
            ("brush", "🖌️ Brush", self.select_brush_tool),
            ("eraser", "🧹 Eraser", self.select_eraser_tool),
            ("zoom-in", "🔍 Zoom In", lambda: self.adjust_zoom(1.2)),
            ("zoom-out", "🔎 Zoom Out", lambda: self.adjust_zoom(0.8)),
            ("undo", "↩️ Undo", self.undo),
            ("redo", "↪️ Redo", self.redo),
        ]
        
        for tool in tools:
            btn = ttk.Button(toolbar, text=tool[1], command=tool[2])
            btn.pack(side=tk.LEFT, padx=2, pady=2)
            
        self.brush_slider = ttk.Scale(toolbar, from_=1, to=50, 
                                    command=lambda v: self.update_brush_size(int(float(v))))
        self.brush_slider.set(self.brush_size)
        self.brush_slider.pack(side=tk.LEFT, padx=10)
        
        self.radius_slider = ttk.Scale(toolbar, from_=1, to=20, 
                                     command=lambda v: self.update_inpaint_radius(int(float(v))))
        self.radius_slider.set(self.inpaint_radius)
        self.radius_slider.pack(side=tk.LEFT, padx=10)

    def create_main_interface(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        self.canvas = tk.Canvas(main_frame, cursor="cross", bg='#2e2e2e')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbars
        self.hscroll = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.vscroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.hscroll.set, yscrollcommand=self.vscroll.set)
        
        self.hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.vscroll.pack(side=tk.RIGHT, fill=tk.Y)

    def create_side_panel(self):
        side_panel = ttk.Frame(self.root, width=200)
        side_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(side_panel, text="Tools Settings").pack(pady=5)
        ttk.Separator(side_panel).pack(fill=tk.X)
        
        # Preview window
        self.preview_label = ttk.Label(side_panel)
        self.preview_label.pack(pady=10)

    def create_statusbar(self):
        self.statusbar = ttk.Label(self.root, text="Ready", anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.root.bind("<Control-z>", self.undo)
        self.root.bind("<Control-y>", self.redo)
        self.root.bind("<Control-o>", lambda e: self.open_image())
        self.root.bind("<Control-s>", lambda e: self.save_image())

    # Improved image processing methods
    def process_inpainting(self):
        if self.original_image is None or self.mask is None:
            return
            
        self.push_undo_state()
        
        try:
            # Convert to BGR for OpenCV
            img_bgr = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2BGR)
            
            # Use different algorithms based on mask size
            if np.sum(self.mask) < 10000:  # Small area
                inpainted = cv2.inpaint(img_bgr, self.mask, self.inpaint_radius, cv2.INPAINT_TELEA)
            else:  # Large area
                inpainted = cv2.inpaint(img_bgr, self.mask, self.inpaint_radius, cv2.INPAINT_NS)
            
            self.processed_image = cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)
            self.update_display()
            
        except Exception as e:
            messagebox.showerror("Processing Error", str(e))

    def update_brush_size(self, size):
        self.brush_size = max(1, min(50, size))
        self.update_cursor()

    def update_inpaint_radius(self, radius):
        self.inpaint_radius = max(1, min(20, radius))

    def update_cursor(self):
        if self.selected_tool == "brush":
            self.canvas.config(cursor="circle")
        elif self.selected_tool == "eraser":
            self.canvas.config(cursor="dotbox")
        else:
            self.canvas.config(cursor="cross")

    # Enhanced drawing methods
    def draw_on_mask(self, x, y, erase=False):
        if self.original_image is None:
            return
            
        img_x = int(x / self.zoom_level)
        img_y = int(y / self.zoom_level)
        
        if self.mask is None:
            self.mask = np.zeros(self.original_image.shape[:2], dtype=np.uint8)
        
        color = 0 if erase else 255
        cv2.circle(self.mask, (img_x, img_y), self.brush_size, color, -1)
        self.update_preview()

    def update_preview(self):
        if self.processed_image is not None and self.mask is not None:
            preview = self.processed_image.copy()
            preview[self.mask == 255] = [255, 0, 0]  # Red mask preview
            self.display_image(preview)


    # Improved image handling
    def open_image(self):
        path = filedialog.askopenfilename()
        if not path:
            return
            
        try:
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise ValueError("Unsupported image format")
                
            if len(img.shape) == 2:  # Grayscale
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            else:  # Color
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            self.original_image = img
            self.processed_image = img.copy()
            self.mask = None
            self.reset_zoom()
            self.update_display()
            
        except Exception as e:
            messagebox.showerror("Loading Error", f"Failed to load image: {str(e)}")

    def save_image(self):
        if self.processed_image is None:
            return
            
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ('PNG', '*.png'),
                ('JPEG', '*.jpg;*.jpeg'),
                ('WebP', '*.webp'),
                ('All Files', '*.*')
            ]
        )
        
        if path:
            try:
                img = Image.fromarray(self.processed_image)
                img.save(path, quality=95)
                messagebox.showinfo("Success", "Image saved successfully!")
            except Exception as e:
                messagebox.showerror("Saving Error", f"Failed to save image: {str(e)}")

    # Enhanced zoom and scroll
    def adjust_zoom(self, factor):
        self.zoom_level = max(0.1, min(5.0, self.zoom_level * factor))
        self.update_display()

    def update_display(self):
        if self.processed_image is None:
            return
            
        img = Image.fromarray(self.processed_image)
        w, h = img.size
        new_size = (int(w * self.zoom_level), int(h * self.zoom_level))
        img = img.resize(new_size, Image.LANCZOS)
        
        self.tk_image = ImageTk.PhotoImage(img)
        self.canvas.config(scrollregion=(0, 0, *new_size))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.update_preview()

    # Improved undo/redo system
    def push_undo_state(self):
        self.undo_stack.append({
            'image': self.processed_image.copy(),
            'mask': self.mask.copy() if self.mask is not None else None
        })
        self.redo_stack.clear()

    def undo(self, event=None):
        if self.undo_stack:
            state = self.undo_stack.pop()
            self.redo_stack.append({
                'image': self.processed_image.copy(),
                'mask': self.mask.copy() if self.mask is not None else None
            })
            self.processed_image = state['image']
            self.mask = state['mask']
            self.update_display()

    def redo(self, event=None):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append({
                'image': self.processed_image.copy(),
                'mask': self.mask.copy() if self.mask is not None else None
            })
            self.processed_image = state['image']
            self.mask = state['mask']
            self.update_display()

    def reset_zoom(self):
        self.zoom_level = 1.0
        self.update_display()

    def adjust_zoom(self, factor):
        self.zoom_level = max(0.1, min(5.0, self.zoom_level * factor))
        self.update_display()

    # Event handlers
    def on_press(self, event):
        self.last_point = (event.x, event.y)
        if self.selected_tool in ["brush", "eraser"]:
            self.draw_on_mask(event.x, event.y, erase=(self.selected_tool == "eraser"))
        elif self.selected_tool == "rectangle":
            self.start_rect_selection(event)

    def on_drag(self, event):
        if self.selected_tool in ["brush", "eraser"]:
            self.draw_on_mask(event.x, event.y, erase=(self.selected_tool == "eraser"))
        elif self.selected_tool == "rectangle":
            self.update_rect_selection(event)

    def on_release(self, event):
        if self.selected_tool == "rectangle":
            self.process_rect_selection(event)
        self.process_inpainting()

    def on_right_click(self, event):
        if self.selected_tool in ["brush", "eraser"]:
            self.selected_tool = "eraser" if self.selected_tool == "brush" else "brush"
            self.update_cursor()

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedWatermarkRemoverPro(root)
    root.mainloop()