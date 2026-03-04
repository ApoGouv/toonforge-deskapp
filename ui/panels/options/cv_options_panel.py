import tkinter as tk
from tkinter import ttk
from ui.theme import THEME
from ui.tooltip import ToolTip
from ui.panels.options.base_options_panel import BaseOptionsPanel


class CVOptionsPanel(BaseOptionsPanel):
    """
    Options panel specifically for the CV pipeline.
    Directly manipulates pipeline state.
    """

    def build_panel(self):
        self._applying_preset = False

        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self.presets = self.pipeline.presets
        self.smooth_modes = self.pipeline.smooth_modes
        self.color_modes = self.pipeline.color_modes
        self.blend_modes = self.pipeline.blend_modes

        self._create_widgets()
        self._apply_tooltips()

    # ---------------------------------------------------------
    # UI CREATION
    # ---------------------------------------------------------

    def _create_widgets(self):

        # Preset
        self.preset_combo = self._add_combobox(
            "Style Preset:",
            list(self.presets.keys()),
            self._on_preset_selected,
            0,
            default="Custom",
            span=2,
            affects_preset=False,
        )

        # Smoothing
        self.smooth_mode = self._add_combobox(
            "Smoothing Type",
            list(self.smooth_modes.keys()),
            self._on_smoothing_mode_selected,
            1,
        )

        self.smooth_slider = self._add_slider(
            1, 10, self._on_smoothing_strength_changed, 1, 2, default=self.pipeline.smooth_passes
        )

        # Color
        self.color_mode = self._add_combobox(
            "Color Mode",
            list(self.color_modes.keys()),
            self._on_color_mode_selected,
            2,
        )

        self.color_slider = self._add_slider(
            2, 40, self._on_color_depth_changed, 2, 2, default=self.pipeline.num_colors
        )

        # Blend & Edge
        self.blend_mode = self._add_combobox(
            "Blend Mode",
            list(self.blend_modes.keys()),
            self._on_blend_mode_selected,
            3,
        )

        self.edge_slider = self._add_slider(
            3, 15, self._on_edge_strength_changed, 3, 2,
            default=self.pipeline.edge_block,
            resIncStep=2
        )

        # Denoise
        self.denoise_var = tk.BooleanVar(value=self.pipeline.use_denoise)

        self.denoise_check = ttk.Checkbutton(
            self,
            text="Deep Denoise (High Quality / Slower)",
            variable=self.denoise_var,
            command=self._on_denoise_toggled,
        )

        self.denoise_check.grid(row=4, column=0, columnspan=2, sticky="w", padx=5)

    # ---------------------------------------------------------
    # CALLBACKS (NOW INSIDE PANEL)
    # ---------------------------------------------------------

    def _on_preset_selected(self, event=None):
        preset_name = self.preset_combo.get()
        if preset_name == "Custom":
            return

        settings = self.presets[preset_name]
        self.load_preset(settings)

    def _on_smoothing_mode_selected(self, event=None):
        self._mark_custom_if_needed()
        key = self.smooth_mode.get()
        self.pipeline.set_option("smooth_mode", self.smooth_modes[key])

    def _on_color_mode_selected(self, event=None):
        self._mark_custom_if_needed()
        key = self.color_mode.get()
        self.pipeline.set_option("color_mode", self.color_modes[key])

    def _on_blend_mode_selected(self, event=None):
        self._mark_custom_if_needed()
        key = self.blend_mode.get()
        self.pipeline.set_option("blend_mode", self.blend_modes[key])

    def _on_smoothing_strength_changed(self, value):
        self._mark_custom_if_needed()
        self.pipeline.set_option("smooth_passes", int(float(value)))

    def _on_color_depth_changed(self, value):
        self._mark_custom_if_needed()
        self.pipeline.set_option("num_colors", int(float(value)))

    def _on_edge_strength_changed(self, value):
        self._mark_custom_if_needed()
        self.pipeline.set_option("edge_block", int(float(value)))

    def _on_denoise_toggled(self):
        self.pipeline.set_option("denoise", self.denoise_var.get())
        self._mark_custom_if_needed()

    # ---------------------------------------------------------
    # PRESET HANDLING
    # ---------------------------------------------------------

    def load_preset(self, settings: dict):
        self._applying_preset = True

        inv_smooth = {v: k for k, v in self.smooth_modes.items()}
        inv_color = {v: k for k, v in self.color_modes.items()}
        inv_blend = {v: k for k, v in self.blend_modes.items()}

        # ---- Denoise ----
        self.denoise_var.set(settings.get("denoise", False))
        self.pipeline.set_option("denoise", settings.get("denoise", False))

        # ---- Comboboxes ----
        self.smooth_mode.set(inv_smooth[settings["smooth_mode"]])
        self.pipeline.set_option("smooth_mode", settings["smooth_mode"])

        self.color_mode.set(inv_color[settings["color_mode"]])
        self.pipeline.set_option("color_mode", settings["color_mode"])

        self.blend_mode.set(inv_blend[settings["blend_mode"]])
        self.pipeline.set_option("blend_mode", settings["blend_mode"])

        # ---- Sliders ----
        self.smooth_slider.set(settings["smooth_val"])
        self.pipeline.set_option("smooth_passes", settings["smooth_val"])

        self.color_slider.set(settings["color_val"])
        self.pipeline.set_option("num_colors", settings["color_val"])

        self.edge_slider.set(settings["edge_val"])
        self.pipeline.set_option("edge_block", settings["edge_val"])

        self.after(150, self._finish_preset)

    def _finish_preset(self):
        self._applying_preset = False

    def _mark_custom_if_needed(self):
        if not self._applying_preset and self.preset_combo.get() != "Custom":
            self.preset_combo.set("Custom")

    # ---------------------------------------------------------
    # UI HELPERS (UNCHANGED LOGIC)
    # ---------------------------------------------------------

    def _add_combobox(self, label_text, options, callback, row, default=None, span=1, affects_preset=True):
        tk.Label(self, text=label_text, bg=THEME["bg_main"], anchor="w").grid(
            row=row, column=0, sticky="w", pady=5
        )

        combo = ttk.Combobox(self, values=options, state="readonly", width=15)
        combo.grid(row=row, column=1, columnspan=span, padx=5, sticky="ew")

        if default:
            combo.set(default)

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
            command=callback,
            highlightthickness=0,
            font=(THEME["font_family"], 8),
        )
        slider.grid(row=row, column=col, sticky="ew", padx=5)

        if default is not None:
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