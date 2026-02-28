import tkinter as tk
from tkinter import ttk
from ui.theme import THEME
from ui.tooltip import ToolTip


class OptionsPanel(tk.Frame):
    def __init__(
        self, parent, presets, smooth_modes, color_modes, blend_modes, callbacks
    ):
        super().__init__(parent, bg=THEME["bg_main"], pady=10)
        self.presets = presets
        
        self.smooth_modes = smooth_modes
        self.color_modes = color_modes
        self.blend_modes = blend_modes
        
        self.callbacks = callbacks

        self._applying_preset = False

        self.columnconfigure(2, weight=1)

        # Create widgets
        self._create_widgets()
        self._apply_tooltips()

    def _create_widgets(self):
        # Preset
        self.preset_combo = self._add_combobox(
            "Style Preset:",
            list(self.presets.keys()),
            self.callbacks["preset"],
            0,
            default="Custom",
            span=2,
            affects_preset=False,
        )

        # Smoothing
        self.smooth_mode = self._add_combobox(
            "Smoothing Type",
            list(self.smooth_modes.keys()),
            self.callbacks["smooth_mode"],
            1,
        )
        self.smooth_slider = self._add_slider(
            1, 10, self.callbacks["smooth_val"], 1, 2, default=5
        )

        # Color
        self.color_mode = self._add_combobox(
            "Color Mode", list(self.color_modes.keys()), self.callbacks["color_mode"], 2
        )
        self.color_slider = self._add_slider(
            2, 40, self.callbacks["color_val"], 2, 2, default=20
        )

        # Blend & Edge
        self.blend_mode = self._add_combobox(
            "Blend Mode", list(self.blend_modes.keys()), self.callbacks["blend_mode"], 3
        )
        self.edge_slider = self._add_slider(
            3, 15, self.callbacks["edge_val"], 3, 2, default=9, resIncStep=2
        )

        # Denoising
        self.denoise_var = tk.BooleanVar(value=False)
        self.denoise_check = ttk.Checkbutton(
            self,
            text="Deep Denoise (High Quality / Slower)",
            variable=self.denoise_var,
            command=self.callbacks["denoise"],
        )
        self.denoise_check.grid(row=4, column=0, columnspan=2, sticky="w", padx=5)
    
    def load_preset(self, settings: dict):
      """"Populate UI controls from a preset without triggering Custom mode."""
      self._applying_preset = True

      # Reverse maps
      inv_smooth = {v: k for k, v in self.smooth_modes.items()}
      inv_color = {v: k for k, v in self.color_modes.items()}
      inv_blend = {v: k for k, v in self.blend_modes.items()}

      # ---- Denoise ----
      self.denoise_var.set(settings.get("denoise", False))
      self.callbacks["denoise"]()

      # ---- Comboboxes (manual callback) ----
      self.smooth_mode.set(inv_smooth[settings["smooth_mode"]])
      self.callbacks["smooth_mode"]()

      self.color_mode.set(inv_color[settings["color_mode"]])
      self.callbacks["color_mode"]()

      self.blend_mode.set(inv_blend[settings["blend_mode"]])
      self.callbacks["blend_mode"]()

      # ---- Sliders (callbacks auto-fire) ----
      # Handle Sliders (These DO trigger callbacks on .set())
      # We do NOT call the on_change functions manually here to avoid double-processing
      self.smooth_slider.set(settings["smooth_val"])
      self.color_slider.set(settings["color_val"])
      self.edge_slider.set(settings["edge_val"])

      # Allow event loop to settle
      # Wait for the event queue to clear before allowing 'Custom' mode
      # 100-200ms is usually enough to swallow all 'Value Changed' events
      self.after(150, self._finish_preset)

    def _finish_preset(self):
      self._applying_preset = False

    def _mark_custom_if_needed(self):
      if not self._applying_preset and self.preset_combo.get() != "Custom":
          self.preset_combo.set("Custom")

    def set_state(self, enabled: bool):
        """Enable or disable all controls in the panel."""
        state = "normal" if enabled else "disabled"

        # Sliders and Comboboxes
        for w in [
            self.smooth_slider,
            self.color_slider,
            self.edge_slider,
            self.smooth_mode,
            self.color_mode,
            self.blend_mode,
            self.preset_combo,
            self.denoise_check,
        ]:
            try:
                w.config(state=state)
            except:
                pass  # ttk widgets sometimes behave differently

    def _add_combobox(self, label_text, options, callback, row, default=None, span=1, affects_preset=True):
        tk.Label(self, text=label_text, bg=THEME["bg_main"], anchor="w").grid(
            row=row, column=0, sticky="w", pady=5
        )
        combo = ttk.Combobox(self, values=options, state="readonly", width=15)
        combo.grid(row=row, column=1, columnspan=span, padx=5, sticky="ew")
        if default:
            combo.set(default)

        if affects_preset:
            # Bind selection event with _mark_custom_if_needed
            combo.bind(
                "<<ComboboxSelected>>",
                lambda event: (
                    self._mark_custom_if_needed(),
                    callback(event)
                )
            )
        else:
            combo.bind("<<ComboboxSelected>>", callback)
        return combo

    def _add_slider(self, from_, to, callback, row, col, default=None, resIncStep=1):
        slider = tk.Scale(
            self,
            from_=from_,
            to=to,
            resolution=resIncStep,
            orient=tk.HORIZONTAL,
            bg=THEME["bg_main"],
            command=lambda v: (
                self._mark_custom_if_needed(),
                callback(v)
            ),
            highlightthickness=0,
            font=(THEME["font_family"], 8),
        )
        slider.grid(row=row, column=col, sticky="ew", padx=5)
        if default:
            slider.set(default)
        return slider

    def _apply_tooltips(self):
        ToolTip(
            self.smooth_slider,
            "Controls how much the colors are smoothed.\nHigher = softer, painterly look.",
        )
        ToolTip(
            self.color_slider,
            "Number of color regions in the final image.\nHigher = more detail, lower = posterized look.",
        )
        ToolTip(
            self.edge_slider,
            "Controls thickness and intensity of outlines.\nHigher = bolder edges.",
        )
        ToolTip(
            self.smooth_mode,
            "Selects the smoothing algorithm.\nSome are faster than others.",
        )
        ToolTip(
            self.color_mode,
            "Selects how colors are reduced.\nDifferent algorithms give different styles.",
        )
        ToolTip(
            self.blend_mode,
            "Hard: Sharp black lines.\nMask: Pure colors with cut-out edges.\nOverlay: Subtle lines blended into colors.",
        )
        ToolTip(
            self.preset_combo,
            "Choose a pre-configured style.\nThis will automatically move all sliders for you!",
        )
