import tkinter as tk
from .base_options_panel import BaseOptionsPanel
from ui.theme import THEME


class EmptyOptionsPanel(BaseOptionsPanel):
    """Fallback panel for pipelines without configurable options."""

    def build_panel(self):
        label = tk.Label(
            self,
            text="This pipeline has no configurable options.",
            bg=THEME["bg_panel"],
            fg=THEME["text_dim"],
        )
        label.pack(pady=20)