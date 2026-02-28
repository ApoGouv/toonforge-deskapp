import tkinter as tk

from ui.theme import THEME
from ui.tooltip import ToolTip


class ActionButtons(tk.Frame):
    def __init__(self, parent, callbacks):
        super().__init__(parent, bg=THEME["bg_main"])
        self.open_btn = tk.Button(self, text="📂 Open", command=callbacks["open"])
        self.preview_btn = tk.Button(self, text="🔍 Preview", command=callbacks["preview"])
        self.cartoon_btn = tk.Button(self, text="🎨 Cartoonify", command=callbacks["cartoon"])
        self.save_btn = tk.Button(self, text="💾 Save", command=callbacks["save"])

        for i, btn in enumerate([self.open_btn, self.preview_btn, self.cartoon_btn, self.save_btn]):
            btn.grid(row=0, column=i, padx=2, sticky="ew")
            self.columnconfigure(i, weight=1)

        # Add tooltips
        ToolTip(self.open_btn, "Open an image file (JPG, PNG, WEBP).")
        ToolTip(self.preview_btn,
                "Run the cartoon pipeline on a scaled image (40%).\n"
                "Fast preview with all intermediate steps shown.")
        ToolTip(self.cartoon_btn,
                "Run the full-resolution cartoon pipeline.\n"
                "Higher quality, slower processing.")
        ToolTip(self.save_btn, 
                "Save the final cartoonified image to disk.")

    def set_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in [self.open_btn, self.preview_btn, self.cartoon_btn, self.save_btn]:
            btn.config(state=state)

    def set_open_enabled(self, enabled: bool):
        self.open_btn.config(state="normal" if enabled else "disabled")

    def set_processing_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in (self.preview_btn, self.cartoon_btn, self.save_btn):
            btn.config(state=state)