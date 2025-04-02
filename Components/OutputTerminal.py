import customtkinter


class TerminalOutput(customtkinter.CTkFrame):
    """ Terminal output log component """
    def __init__(self, parent):
        super().__init__(parent, height=120, corner_radius=0, fg_color="transparent")
        self.grid(row=0, column=1, rowspan=1, padx=(20, 20), pady=(0, 10), sticky="nsew")

        self.terminal_label = customtkinter.CTkLabel(self, text="Output", anchor="w", justify="left")
        self.terminal_label.grid(row=0, column=0, padx=24, pady=(10, 0), sticky="w")

        self.textbox = customtkinter.CTkTextbox(self, width=900, height=80)
        self.textbox.grid(row=1, column=0, padx=(0, 0), pady=(2, 10), sticky="nsew")

    def log(self, message):
        """ Add message to the terminal output """
        self.textbox.insert("end", message + "\n")
        self.textbox.yview_moveto(1)