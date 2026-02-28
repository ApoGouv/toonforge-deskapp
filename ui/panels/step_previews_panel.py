# ui/panels/step_previews_panel.py

from tkinter import Frame, Label
from ui.theme import THEME
from ui.tooltip import ToolTip
from ui.image_utils import display_image


class StepPreviewsPanel(Frame):
    """
    Displays intermediate and final image previews.
    Pipeline-agnostic UI component.
    """

    def __init__(self, parent):
        super().__init__(parent, bg=THEME["bg_main"])
        self._build_layout()
        self._build_slots()

    # ---------------------------
    # Layout
    # ---------------------------

    def _build_layout(self):
        self.rowconfigure((0, 1, 2), weight=1)
        self.columnconfigure((0, 1), weight=1)

    def _build_slots(self):
        self.slots = {}

        def make_slot(row, col, key, title, span=1):
            frame = Frame(self, bg=THEME["bg_panel"], bd=1, relief="solid")
            frame.grid(
                row=row,
                column=col,
                columnspan=span,
                sticky="nsew",
                padx=2,
                pady=2
            )

            Label(
                frame,
                text=title,
                font=(THEME["font_family"], 8, "bold"),
                bg=THEME["bg_panel"]
            ).pack(anchor="w")

            label = Label(frame, bg="#eee")
            label.pack(fill="both", expand=True)

            self.slots[key] = {
                "frame": frame,
                "label": label
            }

        # Fixed CV-style steps (for now)
        make_slot(0, 0, "gray",   "1. Grayscale")
        make_slot(0, 1, "edge",   "2. Edge Detection")
        make_slot(1, 0, "smooth", "3. Smoothed Colors")
        make_slot(1, 1, "quant",  "4. Quantized Colors")
        make_slot(2, 0, "final",  "FINAL RESULT", span=2)

        # Tooltips (still UI-only)
        ToolTip(self.slots["gray"]["label"],
                "Step 1: Convert image to grayscale.\nUsed for edge detection.")
        ToolTip(self.slots["edge"]["label"],
                "Step 2: Detect edges using adaptive thresholding.")
        ToolTip(self.slots["smooth"]["label"],
                "Step 3: Smooth colors while preserving boundaries.")
        ToolTip(self.slots["quant"]["label"],
                "Step 4: Reduce color palette (cartoon effect).")
        ToolTip(self.slots["final"]["label"],
                "Final result after blending colors and edges.",
                position="top")

    # ---------------------------
    # Public API (used by main window)
    # ---------------------------

    def clear(self):
        """Clear all preview images."""
        for slot in self.slots.values():
            slot["label"].config(image="", text="")

    def show_steps(self, enabled: bool):
        """Show or hide intermediate steps (not final)."""
        for key, slot in self.slots.items():
            if key == "final":
                continue

            if enabled:
                slot["frame"].grid()
            else:
                slot["frame"].grid_remove()

    def update_preview(self, *, gray, edge, smooth, quant, final):
        """Update all step previews (used for preview mode)."""
        display_image(gray,   self.slots["gray"]["label"],   (250, 180))
        display_image(edge,   self.slots["edge"]["label"],   (250, 180))
        display_image(smooth, self.slots["smooth"]["label"], (250, 180))
        display_image(quant,  self.slots["quant"]["label"],  (250, 180))
        display_image(final,  self.slots["final"]["label"],  (600, 350))

    def update_final_only(self, final):
        """Show only the final result (used for full apply)."""
        display_image(final, self.slots["final"]["label"], (800, 600))