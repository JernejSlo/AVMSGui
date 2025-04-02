import customtkinter


class ControlButtons(customtkinter.CTkFrame):
    """ Start and Stop button controls (Centered) """
    def __init__(self, parent, start_callback, stop_callback):
        super().__init__(parent, fg_color="transparent")
        self.grid(row=2, column=1, padx=(20, 20), pady=(10, 20), sticky="n")

        # Create inner frame to center buttons
        self.button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=0, column=0, padx=20, pady=10)

        # Start Button
        self.start_button = customtkinter.CTkButton(self.button_frame, text="Start", command=start_callback, width=120)
        self.start_button.grid(row=0, column=0, padx=10, pady=10)

        # Stop Button
        self.stop_button = customtkinter.CTkButton(self.button_frame, text="Stop", command=stop_callback, fg_color="red", width=120)
        self.stop_button.grid(row=0, column=1, padx=10, pady=10)
