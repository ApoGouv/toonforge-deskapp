import datetime
import os
import threading
import tkinter as tk
from tkinter import HORIZONTAL, Frame, Label, Scale, filedialog, ttk

import cv2

from pipelines.pipeline_manager import PipelineManager
from pipelines.pipeline_controller import PipelineController
from ui.image_utils import display_image
from ui.panels.action_buttons import ActionButtons
from ui.panels.header_panel import HeaderPanel
from ui.panels.step_previews_panel import StepPreviewsPanel
from ui.theme import THEME
from ui.tooltip import ToolTip
from utils.fs_utils import get_save_path


class ToonForgeApp:

    def __init__(self, root):
        self.root = root
        self.root.title("ToonForge – Cartoonify Images")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        self.root.configure(bg=THEME["bg_main"])

        # --------------------------------
        # Core architecture
        # --------------------------------
        self.pipeline_manager = PipelineManager()
        self.pipeline_controller = PipelineController(self.pipeline_manager)

        # Set default pipeline cv or animegan
        self.pipeline_manager.set_pipeline("cv")

        # --------------------------------
        # State
        # --------------------------------
        self.cartoon_image = None
        self.image_path = None
        self._is_processing = False

        # --------------------------------
        # Options panel placeholder
        # --------------------------------
        self.options_panel = None

        # --------------------------------
        # Layout
        # --------------------------------
        self._setup_layout()
        self._create_widgets()
        self._sync_ui_with_pipeline()

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
        self._create_pipeline_selector()
        self._create_original_preview()

        self.options_container = Frame(self.left_panel, bg=THEME["bg_main"])
        self.options_container.pack(fill="x", pady=5)
        self._create_options_panel()

        self._create_log_console()
        self._create_progress_indicator()
        self._create_step_previews()

    def _sync_ui_with_pipeline(self):
        pm = self.pipeline_manager

        # ---- Action Buttons ----
        self.action_buttons.set_preview_visible(pm.supports_preview)
        self.action_buttons.set_cartoon_enabled(
            True
        )  # Always allowed once image exists

        # ---- Refresh Options Panel ----
        self._create_options_panel()

        # ---- Step Previews ----
        self.step_previews.show_steps(pm.supports_preview)

    def _create_pipeline_selector(self):
        Label(
            self.left_panel,
            text="Pipeline",
            font=(THEME["font_family"], 9, "bold"),
            bg=THEME["bg_main"],
        ).pack(anchor="w", pady=(10, 2))

        self.pipeline_combo = ttk.Combobox(
            self.left_panel,
            state="readonly",
            values=[
                "Classic (CV)",
                "Anime (AI)",
            ],
        )
        self.pipeline_combo.current(0)
        self.pipeline_combo.pack(fill="x")

        self.pipeline_combo.bind("<<ComboboxSelected>>", self.on_pipeline_changed)

    def _create_header(self):
        """App header title and subtitle."""
        self.header = HeaderPanel(self.left_panel)
        self.header.pack(fill="x")

    def _create_action_buttons(self):
        """Action buttons: Open, Preview, Cartoonify, Save"""
        self.action_buttons = ActionButtons(
            self.left_panel,
            callbacks={
                "open": self.open_image,
                "preview": self.preview_image,
                "cartoon": self.apply_cartoon,
                "save": self.save_image,
            },
        )
        self.action_buttons.pack(fill="x", pady=5)

    def _create_options_panel(self):
        """Creates the options panel dynamically based on the current pipeline."""
        # Destroy old panel if exists
        if self.options_panel:
            self.options_panel.destroy()

        pipeline = self.pipeline_manager.pipeline
        if not pipeline:
            return
        
        self.options_panel = pipeline.create_options_panel(self.options_container)
        self.options_panel.pack(fill="x")


    def _create_log_console(self):
        """Activity log console."""
        Label(
            self.left_panel,
            text="Activity Log",
            font=(THEME["font_family"], 9, "bold"),
            bg=THEME["bg_main"],
        ).pack(anchor="w")
        self.log_console = tk.Text(
            self.left_panel,
            height=6,
            font=(THEME["font_mono"], 9),
            bg=THEME["bg_console"],
            fg=THEME["fg_console"],
            state="disabled",
        )
        self.log_console.pack(fill="x", pady=5)

    def _create_original_preview(self):
        """Original image preview area."""
        Label(
            self.left_panel,
            text="Original Image",
            font=(THEME["font_family"], 9, "bold"),
            bg=THEME["bg_main"],
        ).pack(pady=(10, 5), anchor="w")
        self.original_label = Label(
            self.left_panel, text="No image loaded", bg="#ddd", height=10
        )
        self.original_label.pack(fill="both", expand=True, pady=10)

    def _create_progress_indicator(self):
        """Indeterminate progress indicator shown during processing."""
        self.progress = ttk.Progressbar(self.left_panel, mode="indeterminate")
        # DO NOT pack here – controlled dynamically

    def _create_step_previews(self):
        """Creates the grid for stepped results."""
        self.step_previews = StepPreviewsPanel(self.right_panel)
        self.step_previews.pack(fill="both", expand=True)

    # ---------------------------
    # Core Methods
    # ---------------------------
    def notify(self, message, color=None):
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

    def open_image(self):
        file_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp")],
        )
        if not file_path:
            return

        self.image_path = file_path
        img = cv2.imread(file_path)

        self.pipeline_manager.set_image(img)
        self.cartoon_image = None

        # Clear preview slots
        self.step_previews.clear()

        display_image(img, self.original_label, (400, 300))

        self.notify(
            f"Image loaded: {os.path.basename(file_path)} ({img.shape[1]}x{img.shape[0]})"
        )

        self._sync_ui_with_pipeline()
        self.set_ui_state(True)
        self.notify("Image loaded. Adjust settings or choose a preset.")

    def save_image(self):
        if self.cartoon_image is None:
            self.notify("Error: Nothing to save.", color="red")
            return

        output_path = get_save_path(self.image_path)
        cv2.imwrite(output_path, self.cartoon_image)

        self.notify(f"Success: Result saved to {os.path.basename(output_path)}")

    def on_pipeline_changed(self, event=None):
        selection = self.pipeline_combo.get()

        pipeline_map = {
            "Classic (CV)": "cv",
            "Anime (AI)": "animegan",
        }

        key = pipeline_map.get(selection)
        if not key:
            return

        self.pipeline_manager.set_pipeline(key)

        # Re-attach image if already loaded
        if self.image_path:
            img = cv2.imread(self.image_path)
            self.pipeline_manager.set_image(img)

        # Reset UI
        self.cartoon_image = None
        self.step_previews.clear()

        self._sync_ui_with_pipeline()
        self.set_ui_state(bool(self.image_path))

        self.notify(f"Switched to pipeline: {selection}")

    # ---------------------------
    # Processing
    # ---------------------------
    def preview_image(self):
        self.run_processing(preview=True)

    def apply_cartoon(self):
        self.run_processing(preview=False)

    def run_processing(self, preview=True):
        if self._is_processing:
            return

        if not self._require_image(
            "Please load an image first.",
            notify=True,
        ):
            return

        self._is_processing = True
        self.progress.pack(fill="x", pady=4, side="bottom")
        self.progress.start()
        self.set_ui_state(False)

        # Ensure step frames are visible if doing a preview
        if preview:
            self.step_previews.show_steps(self.pipeline_manager.supports_preview)

        mode_str = "Preview (40% scale)" if preview else "Full Resolution"
        self.notify(f"Starting {mode_str} processing...")

        thread = threading.Thread(
            target=lambda: self._image_process_thread(preview), daemon=True
        ).start()

    def _image_process_thread(self, preview):
        try:
            results = self.pipeline_controller.process(preview=preview)
            self.root.after(
                0, lambda: self._on_processing_done(results, is_preview=preview)
            )
        except Exception as e:
            # Capture the error message as a standard string variable
            error_msg = str(e)
            self.root.after(0, lambda: self._on_processing_error(error_msg))

    def _on_processing_done(self, results, is_preview):
        self._is_processing = False
        self.progress.stop()
        self.progress.pack_forget()
        self.set_ui_state(True)

        final = results["final"]
        steps = results["steps"]
        self.cartoon_image = final

        if is_preview and steps:
            self.step_previews.show_steps(True)
            self.step_previews.update_from_steps(steps, final)
            self.notify("Success: Preview generated. Showing intermediate steps.")
        else:
            # Hide steps on full apply to focus on final
            self.step_previews.show_steps(False)
            self.step_previews.update_final_only(final)
            self.notify("Success: Full Cartoonified image ready.")

    def _on_processing_error(self, message):
        self._is_processing = False
        self.progress.stop()
        self.progress.pack_forget()
        self.set_ui_state(True)
        self.notify(f"ERROR: {message}", color="red")

    # ---------------------------
    # UI Helpers
    # ---------------------------

    def _require_image(
        self,
        message: str | None = None,
        notify: bool = False,
        color: str = "#c0392b",
    ) -> bool:
        """
        Guard helper to ensure an image is loaded before continuing.

        Returns:
            True if image exists, False otherwise.
        """
        pipeline = self.pipeline_manager.pipeline

        if pipeline is None or not pipeline.has_image:
            if notify:
                self.notify(
                    message or "Please load an image first.",
                    color=color,
                )
            return False

        return True

    def set_ui_state(self, enabled: bool):
        pm = self.pipeline_manager

        # ---- Action buttons ----
        self.action_buttons.set_open_enabled(True)
        self.action_buttons.set_processing_enabled(enabled)

        if not pm.supports_preview:
            self.action_buttons.set_preview_enabled(False)

        # ---- Options ----
        self.options_panel.set_state(enabled)
        