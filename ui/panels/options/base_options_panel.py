import tkinter as tk
from abc import ABC, abstractmethod

class BaseOptionsPanel(tk.Frame, ABC):
    """
    Abstract base class for pipeline options panels.
    Each pipeline can implement its own subclass.
    """

    def __init__(self, parent, pipeline):
        super().__init__(parent)
        self.pipeline = pipeline
        self.build_panel()

    @abstractmethod
    def build_panel(self):
        """Populate the panel with widgets."""
        pass

    def set_state(self, enabled: bool):
        """Enable/disable all interactive controls in the panel."""
        state = "normal" if enabled else "disabled"

        def recurse(widget):
            for child in widget.winfo_children():
                try:
                    child.configure(state=state)
                except tk.TclError:
                    pass
                recurse(child)

        recurse(self)