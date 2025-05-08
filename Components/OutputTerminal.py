import customtkinter

from Utils.color_theme import COLORS


class TerminalOutput(customtkinter.CTkFrame):
    """ Terminal output log component """
    def __init__(self, parent):

        self.default_color = COLORS["backgroundLight"]
        self.active_color = COLORS["backgroundDark"]
        self.hover_color = COLORS["hover"]
        self.text_color = COLORS["lg_text"]

        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # === Top Band ===
        self.top_spacer = customtkinter.CTkFrame(self, height=10, fg_color=self.default_color, corner_radius=0)
        self.top_spacer.grid(row=0, column=0, sticky="ew")

        # === Read-only Textbox ===
        self.textbox = customtkinter.CTkTextbox(self, corner_radius=5,fg_color=self.active_color,border_spacing=10)
        self.textbox.grid(row=1, column=0, padx=(0,20), pady=(0, 0), sticky="nsew",)
        # Make it visually read-only
        self.textbox.configure(state="disabled")

    def log(self, message):
        """ Add message to the terminal output """
        self.textbox.configure(state="normal")
        self.textbox.insert("end", message + "\n")
        self.textbox.yview_moveto(1)
        self.textbox.configure(state="disabled")
