import tkinter as tk

from ui.theme import THEME


class HeaderPanel(tk.Frame):
    """App header title and subtitle."""
    def __init__(self, parent):
        super().__init__(parent, bg=THEME["bg_main"])
        tk.Label(self, text="🖌 ToonForge", font=(THEME["font_family"], 18, "bold"), bg=THEME["bg_main"]).pack(anchor="w")
        tk.Label(self, text="Turn your photos into cartoons", font=(THEME["font_family"], 10), 
                 bg=THEME["bg_main"], fg=THEME["text_dim"]).pack(anchor="w", pady=(0, 10))