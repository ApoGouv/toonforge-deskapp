import tkinter as tk

class ToolTip:
    def __init__(self, widget, text, position="bottom", top_offset=25):
        """
        widget: Tkinter widget to attach the tooltip to
        text: string to show inside tooltip
        position: "bottom" (default) or "top" to place tooltip above widget
        top_offset: extra spacing when tooltip is above the widget
        """
        self.widget = widget
        self.text = text
        self.position = position
        self.top_offset = top_offset
        self.tip_window = None

        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)

        label = tk.Label(
            tw,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9)
        )
        label.pack(ipadx=6, ipady=4)

        tw.update_idletasks()  # Make sure geometry is calculated

        # Default x/y positions
        x = self.widget.winfo_rootx() + 20
        if self.position == "top":
            y = (
                self.widget.winfo_rooty()
                - tw.winfo_height()
                - self.top_offset
            )
        else:
            y = (
                self.widget.winfo_rooty()
                + self.widget.winfo_height()
                + 5
            )

        tw.wm_geometry(f"+{x}+{y}")

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
