# ui/panels/step_previews_panel.py

from tkinter import Frame, Label
from ui.theme import THEME
from ui.tooltip import ToolTip
from ui.image_utils import display_image
from pipelines.pipeline_step import PipelineStep


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
                row=row, column=col, columnspan=span, sticky="nsew", padx=2, pady=2
            )

            title_label = Label(
                frame,
                text=title,
                font=(THEME["font_family"], 8, "bold"),
                bg=THEME["bg_panel"],
            )
            title_label.pack(anchor="w")

            image_label = Label(frame, bg="#eee")
            image_label.pack(fill="both", expand=True)

            self.slots[key] = {
                "frame": frame,
                "title": title_label,
                "label": image_label,
                "tooltip": None,
            }

        # Generic step slots
        make_slot(0, 0, "step_1", "Step 1")
        make_slot(0, 1, "step_2", "Step 2")
        make_slot(1, 0, "step_3", "Step 3")
        make_slot(1, 1, "step_4", "Step 4")

        # Final
        make_slot(2, 0, "final", "FINAL RESULT", span=2)

        ToolTip(self.slots["final"]["label"], "Final processed image.", position="top")


    def _reset_slot(self, slot, index=None):
        slot["label"].config(image="", text="")

        if index is not None:
            slot["title"].config(text=f"Step {index + 1}")
        else:
            slot["title"].config(text="")

        if slot.get("tooltip"):
            slot["tooltip"].destroy()
            slot["tooltip"] = None

    # ---------------------------
    # Public API (used by main window)
    # ---------------------------

    def clear(self):
        """Clear all preview images, titles and tooltips."""
        step_slots = ["step_1", "step_2", "step_3", "step_4"]

        for i, key in enumerate(step_slots):
            self._reset_slot(self.slots[key], index=i)

        # Final slot
        final_slot = self.slots["final"]
        final_slot["label"].config(image="", text="")

    def show_steps(self, enabled: bool):
        """Show or hide intermediate steps (not final)."""
        for key, slot in self.slots.items():
            if key == "final":
                continue

            if enabled:
                slot["frame"].grid()
            else:
                slot["frame"].grid_remove()

    def update_from_steps(self, steps: list[PipelineStep], final):
        self.clear()

        step_slots = ["step_1", "step_2", "step_3", "step_4"]

        for i, step in enumerate(steps):
            if not isinstance(step, PipelineStep):
                raise TypeError(f"Expected PipelineStep, got {type(step).__name__}")

            if i >= len(step_slots):
                break

            slot = self.slots[step_slots[i]]

            # Update title dynamically
            slot["title"].config(text=f"{i+1}. {step.label}")

            display_image(step.image, slot["label"], (250, 180))

            if step.tooltip:
                if slot["tooltip"]:
                    slot["tooltip"].destroy()

                slot["tooltip"] = ToolTip(slot["label"], step.tooltip)

        display_image(final, self.slots["final"]["label"], (600, 350))

    def update_final_only(self, final):
        """Show only the final result (used for full apply)."""
        display_image(final, self.slots["final"]["label"], (800, 600))
