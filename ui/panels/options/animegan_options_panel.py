import tkinter as tk
from ui.panels.options.base_options_panel import BaseOptionsPanel

class AnimeGANOptionsPanel(BaseOptionsPanel):
    def build_panel(self):
        tk.Label(self, text="AnimeGAN Options").pack(pady=10)

        # Model selection
        self.model_var = tk.StringVar(value=self.pipeline.selected_model)
        tk.Label(self, text="Select model:").pack()
        models = list(self.pipeline.models.keys())
        dropdown = tk.OptionMenu(self, self.model_var, *models, command=self.on_model_change)
        dropdown.pack(pady=5)

    def on_model_change(self, value):
        self.pipeline.set_option("model", value)