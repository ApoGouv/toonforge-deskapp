import datetime
import os
import threading
import tkinter as tk
from tkinter import HORIZONTAL, Frame, Label, Scale, filedialog, ttk

import cv2

from pipeline import CartoonPipeline
from ui.image_utils import display_image
from ui.panels.action_buttons import ActionButtons
from ui.panels.header_panel import HeaderPanel
from ui.panels.options_panel import OptionsPanel
from ui.theme import THEME
from ui.tooltip import ToolTip
from utils.fs_utils import get_save_path


class ToonForgeApp:

    SMOOTH_MODES = {
        "Bilateral": "bilateral",
        "Stylization": "stylization",
        "Gaussian Blur": "gaussian",
        "Median Filter": "median"
    }

    COLOR_MODES = {
        "K-Means": "kmeans",
        "Posterize": "posterize",
        "Median Cut": "mediancut",
        "Octree": "octree",
        "Sketch": "sketch"
    }

    BLEND_MODES = {
        "Hard": "hard",
        "Mask": "mask",
        "Overlay": "overlay"
    }

    PRESETS = {
        "Custom": {},

        "Classic Cartoon": {
            "smooth_mode": "bilateral", "smooth_val": 5,
            "color_mode": "kmeans", "color_val": 12,
            "blend_mode": "hard", "edge_val": 6,
            "denoise": True
        },
        "Vibrant Comic": {
            "smooth_mode": "stylization", "smooth_val": 4,
            "color_mode": "kmeans", "color_val": 8,
            "blend_mode": "mask", "edge_val": 11
        },
        "Ink Sketch": {
            "smooth_mode": "gaussian", "smooth_val": 10,
            "color_mode": "posterize", "color_val": 3,
            "blend_mode": "hard", "edge_val": 15,
            "denoise": True
        },
        "Pencil Sketch": {
            "smooth_mode": "gaussian", "smooth_val": 1,
            "color_mode": "sketch", "color_val": 6,
            "blend_mode": "hard", "edge_val": 3
        },
        "High-Contrast Sketch": {
            "smooth_mode": "gaussian", "smooth_val": 3,
            "color_mode": "posterize", "color_val": 2, # Black & White feel
            "blend_mode": "hard", "edge_val": 15
        },
        "Soft Watercolor": {
            "smooth_mode": "stylization", "smooth_val": 7,
            "color_mode": "mediancut", "color_val": 24,
            "blend_mode": "overlay", "edge_val": 3
        }
    }

    def __init__(self, root):
        self.root = root
        self.root.title("ToonForge – Cartoonify Images")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        self.root.configure(bg=THEME["bg_main"])

        # State
        self.pipeline = None
        self.cartoon_image = None
        self.image_path = None
        self._is_processing = False
        self._applying_preset = False

        self._setup_layout()
        self._create_widgets()
        # Disable controls until image is loaded
        self.set_ui_state(False)
        self.notify("ToonForge initialized. Awaiting image input.")
    
    # ---------------------------
    # UI Construction
    # ---------------------------
    def _setup_layout(self):
        """Organizes the main 40/60 split."""
        self.main_container = Frame(self.root, bg=THEME["bg_main"])
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.main_container.columnconfigure(0, weight=2)  # ~40%
        self.main_container.columnconfigure(1, weight=3)  # ~60%
        self.main_container.rowconfigure(0, weight=1)

        # Left Panel (Controls + Original + Logs)
        self.left_panel = Frame(self.main_container, bg=THEME["bg_main"], padx=15)
        self.left_panel.grid(row=0, column=0, sticky="nsew")

        # Right Panel (Results)
        self.right_panel = Frame(self.main_container, bg=THEME["bg_main"], padx=10)
        self.right_panel.grid(row=0, column=1, sticky="nsew")
    
    def _create_widgets(self):
        """Orchestrates widget creation."""
        self._create_header()
        self._create_action_buttons()
        self._create_options_panel()
        self._create_log_console()
        self._create_original_preview()
        self._create_step_previews()
        self._create_status_bar()

    def _create_header(self):
        """App header title and subtitle."""
        self.header = HeaderPanel(self.left_panel)
        self.header.pack(fill="x")

    def _create_action_buttons(self):
        """Action buttons: Open, Preview, Cartoonify, Save"""
        self.action_buttons = ActionButtons(self.left_panel, callbacks={
            "open": self.open_image,
            "preview": self.preview_image,
            "cartoon": self.apply_cartoon,
            "save": self.save_image
        })
        self.action_buttons.pack(fill="x", pady=5)

    def _create_options_panel(self):
        """Processing options panel with sliders and dropdowns."""
        self.options_panel = OptionsPanel(
            self.left_panel,
            presets=self.PRESETS,
            smooth_modes=self.SMOOTH_MODES,
            color_modes=self.COLOR_MODES,
            blend_modes=self.BLEND_MODES,
            callbacks={
                "preset": self.on_preset_selected,
                "smooth_mode": self.on_smoothing_mode_selected,
                "smooth_val": self.on_smoothing_strength_changed,
                "color_mode": self.on_color_mode_selected,
                "color_val": self.on_color_depth_changed,
                "blend_mode": self.on_blend_mode_selected,
                "edge_val": self.on_edge_strength_changed,
                "denoise": self.on_denoise_toggled
            }
        )
        self.options_panel.pack(fill="x")

    def _create_log_console(self):
        """Activity log console."""
        Label(self.left_panel, text="Activity Log", font=(THEME["font_family"], 9, "bold"), bg=THEME["bg_main"]).pack(anchor="w")
        self.log_console = tk.Text(self.left_panel, height=6, font=(THEME["font_mono"], 9), bg=THEME["bg_console"], fg=THEME["fg_console"], state="disabled")
        self.log_console.pack(fill="x", pady=5)

    def _create_original_preview(self):
        """Original image preview area."""
        Label(self.left_panel, text="Original Image", font=(THEME["font_family"], 9, "bold"), bg=THEME["bg_main"]).pack(pady=(10, 5), anchor="w")
        self.original_label = Label(self.left_panel, text="No image loaded", bg="#ddd", height=10)
        self.original_label.pack(fill="both", expand=True, pady=10)

    def _create_status_bar(self):
        """Status bar at the bottom of the left panel."""
        self.progress = ttk.Progressbar(self.left_panel, mode="indeterminate")
        self.status_label = Label(
            self.left_panel, 
            text="Ready", 
            font=(THEME["font_family"], 9), 
            bg=THEME["bg_main"], 
            fg=THEME["text_dim"],
            # wraplength=350,
            # justify="left"
        )
        self.status_label.pack(side="bottom", anchor="w")

    def _create_step_previews(self):
        """Creates the grid for stepped results."""
        self.right_panel.rowconfigure((0,1,2), weight=1)
        self.right_panel.columnconfigure((0,1), weight=1)

        def make_slot(row, col, title, span=1):
            f = Frame(self.right_panel, bg=THEME["bg_panel"], bd=1, relief="solid")
            f.grid(row=row, column=col, columnspan=span, sticky="nsew", padx=2, pady=2)
            Label(f, text=title, font=(THEME["font_family"], 8, "bold"), bg=THEME["bg_panel"]).pack(anchor="w")
            lbl = Label(f, bg="#eee")
            lbl.pack(fill="both", expand=True)
            return f, lbl

        self.f_gray, self.l_gray = make_slot(0, 0, "1. Grayscale")
        self.f_edge, self.l_edge = make_slot(0, 1, "2. Edge Detection")
        self.f_smooth, self.l_smooth = make_slot(1, 0, "3. Smoothed Colors")
        self.f_quant, self.l_quant = make_slot(1, 1, "4. Quantized Colors")
        self.f_final, self.l_final = make_slot(2, 0, "FINAL RESULT", span=2)

        ToolTip(self.l_gray, "Step 1: Convert image to grayscale.\nUsed for edge detection.")
        ToolTip(self.l_edge, "Step 2: Detect edges using adaptive thresholding.")
        ToolTip(self.l_smooth, "Step 3: Smooth colors while preserving boundaries.")
        ToolTip(self.l_quant, "Step 4: Reduce color palette (cartoon effect).")
        ToolTip(self.l_final, "Final result after blending colors and edges.", position="top")


    # ---------------------------
    # Core Methods
    # ---------------------------
    def notify(self, message, is_status=True, color=None):
        """Centralized logging and status updates."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_console.config(state="normal")

        # Add a tag for coloring if a color is provided
        tag_name = f"color_{color}" if color else "default"
        self.log_console.insert("end", f"[{timestamp}] {message}\n", tag_name)

        if color:
            self.log_console.tag_config(tag_name, foreground=color)

        self.log_console.see("end")
        self.log_console.config(state="disabled")
        
        if is_status:
            self.status_label.config(text=message)

    def open_image(self):
        file_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp")]
        )
        if not file_path:
            return

        self.image_path = file_path
        img = cv2.imread(file_path)

        self.pipeline = CartoonPipeline(img)
        self.cartoon_image = None

        # Clear preview slots
        for lbl in [self.l_gray, self.l_edge, self.l_smooth, self.l_quant, self.l_final]:
            lbl.config(image="", text="")

        display_image(img, self.original_label, (400, 300))

        self.notify(f"Image loaded: {os.path.basename(file_path)} ({img.shape[1]}x{img.shape[0]})")
        self.set_ui_state(True)
        self.notify("Image loaded. Adjust settings or choose a preset.")

    def save_image(self):
        if self.cartoon_image is None:
            self.notify("Error: Nothing to save.")
            return

        output_path = get_save_path(self.image_path)
        cv2.imwrite(output_path, self.cartoon_image)

        self.notify(f"Success: Result saved to {os.path.basename(output_path)}")

    def get_preview_image(self, scale=0.4):
        self.notify("Scaling image for preview...")
        h, w = self.pipeline.original.shape[:2]
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(self.pipeline.original, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def on_preset_selected(self, event=None):
        if not self.pipeline:
            self.notify("Load an image first to use presets.", color="#c0392b")
            return
        
        preset_name = self.options_panel.preset_combo.get()
        if preset_name == "Custom":
            return

        self.notify(f"Applying Preset: {preset_name}")
        settings = self.PRESETS[preset_name]

        self.options_panel.load_preset(settings)

        self.root.after(
            200,
            lambda: self.notify(f"Preset '{preset_name}' ready!", color="#4a90e2")
        )


    def on_denoise_toggled(self):
        if not self.pipeline: return
        self.pipeline.use_denoise = self.options_panel.denoise_var.get()
        # Denoising affects everything, so clear all caches
        self.pipeline.invalidate_denoise()
        self.notify(f"Denoising set to {self.pipeline.use_denoise}. Re-process to see effect.")

    # ---------------------------
    # Slider Callbacks (Selective Recompute)
    # ---------------------------
    def on_smoothing_mode_selected(self, _=None):
        if not self.pipeline:
            return
        
        selected = self.options_panel.smooth_mode.get()
        self.pipeline.smooth_mode = self.SMOOTH_MODES[selected]
        self.pipeline.invalidate_smoothing()
        self.pipeline.invalidate_quantization()

        self.notify(f"Smoothing algorithm changed to {selected}. Click Preview/Cartoonify to update.")

    def on_smoothing_strength_changed(self, _=None):
        if not self.pipeline:
            return
        val = self.options_panel.smooth_slider.get()
        self.pipeline.smooth_passes = val
        self.pipeline.invalidate_smoothing()
        self.pipeline.invalidate_quantization()

        self.notify(f"Smoothing algorithm set to {val}. Click Preview/Cartoonify to update.")

    def on_color_mode_selected(self, event=None):
        if not self.pipeline:
            return

        selected = self.options_panel.color_mode.get()
        self.pipeline.color_mode = self.COLOR_MODES[selected]
        self.pipeline.invalidate_quantization()

        self.notify(f"Color algorithm changed to {selected}. Click Preview/Cartoonify to update.")

    def on_color_depth_changed(self, _=None):
        if not self.pipeline:
            return
        val = self.options_panel.color_slider.get()
        self.pipeline.num_colors = val
        self.pipeline.invalidate_quantization()

        self.notify(f"Color Levels set to {val}. Click Preview/Cartoonify to update.")

    def on_blend_mode_selected(self, _=None):
        if not self.pipeline:
            return

        selected = self.options_panel.blend_mode.get()
        self.pipeline.blend_mode = self.BLEND_MODES[selected]

        # No invalidation needed here! 
        # The previous steps are still valid in memory.
        self.notify(f"Blend Mode changed to {selected}. Click Preview/Cartoonify to update.")

    def on_edge_strength_changed(self, _=None):
        if not self.pipeline:
            return
        val = self.options_panel.edge_slider.get()
        if val % 2 == 0:
            val += 1
        self.pipeline.edge_block = val
        self.pipeline.invalidate_edges()

        self.notify(f"Edge Strength set to {val}. Click Preview/Cartoonify to update.")

    # ---------------------------
    # Processing
    # ---------------------------
    def preview_image(self): self.run_processing(preview=True)

    def apply_cartoon(self): self.run_processing(preview=False)

    def run_processing(self, preview=True):
        if self._is_processing:
            return
        
        if not self.pipeline:
            self.notify("Please load an image first.", color="orange")
            return
        
        self._is_processing = True
        self.progress.pack(fill="x", pady=2)
        self.progress.start()
        self.set_ui_state(False)

        # Ensure step frames are visible if doing a preview
        if preview:
            for f in [self.f_gray, self.f_edge, self.f_smooth, self.f_quant]: f.grid()

        mode_str = "Preview (40% scale)" if preview else "Full Resolution"
        self.notify(f"Starting {mode_str} processing...")

        thread = threading.Thread(target=lambda: self._image_process_thread(preview), daemon=True)
        thread.start()

    def _image_process_thread(self, preview):
        try:
            if preview:
                # Use resized image for speed
                self.notify("Running stepped pipeline...")
                preview_img = self.get_preview_image(scale=0.4)
                res = self.pipeline.run_on_image(preview_img)

                self.root.after(0, lambda: self._on_processing_done(res, is_preview=True))
            else:
                # Full quality
                self.notify("Running full pipeline...")
                res = self.pipeline.combine()

                self.root.after(0, lambda: self._on_processing_done(res, is_preview=False))
        except Exception as e:
            # Capture the error message as a standard string variable
            error_msg = str(e) 
            self.root.after(0, lambda: self._on_processing_error(error_msg))

    def _on_processing_error(self, message):
        self._is_processing = False
        self.progress.stop()
        self.progress.pack_forget()
        self.set_ui_state(True)
        self.notify(f"ERROR: {message}", color="red")

    def _on_processing_done(self, results, is_preview):
        self._is_processing = False
        self.progress.stop()
        self.progress.pack_forget()
        self.set_ui_state(True)

        cartoon, gray, edges, smoothed, quantized = results
        self.cartoon_image = cartoon

        if is_preview:
            display_image(gray, self.l_gray, (250, 180))
            display_image(edges, self.l_edge, (250, 180))
            display_image(smoothed, self.l_smooth, (250, 180))
            display_image(quantized, self.l_quant, (250, 180))
            display_image(cartoon, self.l_final, (600, 350))
            self.notify("Success: Preview generated. Showing intermediate steps.")
        else:
            # Hide steps on full apply to focus on final
            for f in [self.f_gray, self.f_edge, self.f_smooth, self.f_quant]: f.grid_remove()
            display_image(cartoon, self.l_final, (800, 600))
            self.notify("Success: Full Cartoonified image ready.")

    # ---------------------------
    # UI Helpers
    # ---------------------------

    def set_ui_state(self, enabled: bool):
        # Action buttons
        self.action_buttons.set_open_enabled(True)   # ALWAYS enabled
        self.action_buttons.set_processing_enabled(enabled)

        # Options
        self.options_panel.set_state(enabled)