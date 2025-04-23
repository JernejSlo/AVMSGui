import customtkinter

class Sidebar(customtkinter.CTkFrame):
    """ Sidebar with measurement buttons and UI options """
    def __init__(self, parent, mode_callback, scaling_callback, overview_callback):
        super().__init__(parent, width=140, corner_radius=0)
        self.grid(row=0, column=0, rowspan=3, sticky="nsew")

        # Title Label
        self.title_label = customtkinter.CTkLabel(self, text="CustomTkinter", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Measurement Mode Buttons
        button_labels = ["DCV", "DCI", "ACV", "ACI", "2Ω", "FREQ.", "PERIOD"]
        for i, label in enumerate(button_labels):
            btn = customtkinter.CTkButton(self, text=label, command=lambda l=label: mode_callback(l))
            btn.grid(row=i + 1, column=0, padx=20, pady=10)

        row_index = 1

        # Appearance Mode Label
        self.appearance_label = customtkinter.CTkLabel(self, text="Appearance Mode:", anchor="w")
        self.appearance_label.grid(row=len(button_labels) + row_index, column=0, padx=20, pady=(10, 0))
        row_index +=1
        # Appearance Mode Dropdown
        self.appearance_menu = customtkinter.CTkOptionMenu(self, values=["Light", "Dark", "System"],
                                                           command=customtkinter.set_appearance_mode)

        self.appearance_menu.grid(row=len(button_labels) + row_index, column=0, padx=20, pady=(5, 10))
        row_index += 1
        # UI Scaling Label
        self.scaling_label = customtkinter.CTkLabel(self, text="UI Scaling:", anchor="w")

        self.scaling_label.grid(row=len(button_labels) + row_index, column=0, padx=20, pady=(10, 0))
        row_index += 1
        # UI Scaling Dropdown
        self.scaling_menu = customtkinter.CTkOptionMenu(self, values=["80%", "90%", "100%", "110%", "120%"],
                                                        command=scaling_callback)

        self.scaling_menu.grid(row=len(button_labels) + row_index, column=0, padx=20, pady=(5, 20))
        row_index += 1
        # === New: Database Overview Button ===
        self.overview_label = customtkinter.CTkLabel(self, text="Past Calibrations:", anchor="w")

        self.overview_label.grid(row=len(button_labels) + row_index, column=0, padx=20, pady=(10, 0))

        row_index += 1
        self.overview_button = customtkinter.CTkButton(self, text="Overview", command=overview_callback)
        self.overview_button.grid(row=len(button_labels) + row_index, column=0, padx=20, pady=(10, 10))
        row_index += 1
        # Set Defaults
        self.selected_mode = "DCV"
        self.appearance_menu.set("Dark")
        customtkinter.set_appearance_mode("Dark")
        self.scaling_menu.set("100%")
