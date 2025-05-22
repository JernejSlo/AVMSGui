import customtkinter
from Utils.color_theme import COLORS


class Sidebar(customtkinter.CTkFrame):
    """ Sidebar with measurement buttons and UI options """
    def __init__(self, parent, mode_callback, scaling_callback, overview_callback, clear_values_callback):

        self.default_color = COLORS["backgroundLight"]
        self.active_color = COLORS["backgroundDark"]
        self.hover_color = COLORS["hover"]
        self.text_color = COLORS["lg_text"]
        super().__init__(parent, width=140, corner_radius=0, fg_color=self.default_color, bg_color=self.default_color)
        self.grid(row=0, column=0, rowspan=3, sticky="nsew")

        # Title Label
        self.title_label = customtkinter.CTkLabel(self, text="CustomTkinter", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Measurement Mode Buttons
        button_labels = ["DCV", "DCI", "ACV", "ACI", "2Ω", "FREQ.", "PERIOD"]
        for i, label in enumerate(button_labels):
            btn = customtkinter.CTkButton(self, text=label, command=lambda l=label: mode_callback(l))
            btn.grid(row=i + 1, column=0, padx=20, pady=10)

        row_index = len(button_labels) + 1

        # === Clear Button ===
        self.clear_button = customtkinter.CTkButton(self, text="Clear", command=clear_values_callback)
        self.clear_button.grid(row=row_index, column=0, padx=20, pady=(10, 10))
        row_index += 1

        # UI Scaling Label
        self.scaling_label = customtkinter.CTkLabel(self, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=row_index, column=0, padx=20, pady=(10, 0))
        row_index += 1

        # UI Scaling Dropdown
        self.scaling_menu = customtkinter.CTkOptionMenu(self, values=["80%", "90%", "100%", "110%", "120%"],
                                                        command=scaling_callback)
        self.scaling_menu.grid(row=row_index, column=0, padx=20, pady=(5, 20))
        row_index += 1

        # Overview Section
        self.overview_label = customtkinter.CTkLabel(self, text="Past Calibrations:", anchor="w")
        self.overview_label.grid(row=row_index, column=0, padx=20, pady=(10, 0))
        row_index += 1

        self.overview_button = customtkinter.CTkButton(self, text="Overview", command=overview_callback)
        self.overview_button.grid(row=row_index, column=0, padx=20, pady=(10, 10))
        row_index += 1

        # Set Defaults
        self.selected_mode = ""
        self.scaling_menu.set("100%")
