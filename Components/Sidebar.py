import customtkinter
from Utils.color_theme import COLORS


class Sidebar(customtkinter.CTkFrame):
    """ Sidebar with measurement buttons and UI options """
    def __init__(self, parent, mode_callback, scaling_callback, overview_callback, clear_values_callback):
        self.default_color = COLORS["backgroundLight"]
        self.active_button_color = "#103857"  # Slightly darker than default blue
        self.hover_color = COLORS["hover"]
        self.text_color = COLORS["lg_text"]
        self.button_bg = COLORS["button_bg"]

        super().__init__(parent, width=140, corner_radius=0, fg_color=self.default_color, bg_color=self.default_color)
        self.grid(row=0, column=0, rowspan=3, sticky="nsew")

        self.mode_callback = mode_callback
        self.mode_buttons = {}
        self.active_button = None

        # Title Label
        self.title_label = customtkinter.CTkLabel(self, text="CustomTkinter", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Measurement Mode Buttons
        button_labels = ["DCV", "DCI", "ACV", "ACI", "2Ω", "FREQ."]
        for i, label in enumerate(button_labels):
            btn = customtkinter.CTkButton(
                self,
                text=label,
                command=lambda l=label: self.set_active_mode(l),
                hover_color=self.hover_color,
            )
            btn.grid(row=i + 1, column=0, padx=20, pady=10)
            self.mode_buttons[label] = btn

        row_index = len(button_labels) + 1

        # === Clear Button ===
        self.clear_button = customtkinter.CTkButton(self, text="Clear", command=clear_values_callback)
        self.clear_button.grid(row=row_index, column=0, padx=20, pady=(10, 10))
        row_index += 1

        # UI Scaling Label
        self.scaling_label = customtkinter.CTkLabel(self, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=row_index, column=0, padx=20, pady=(10, 0))
        row_index += 1

        # UI Scaling Dropdown (adjusted to not overlap)
        self.scaling_menu = customtkinter.CTkOptionMenu(
            self,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=scaling_callback,
            dropdown_fg_color=self.default_color,
            dropdown_hover_color=self.hover_color
        )

        self.scaling_menu.grid(row=row_index, column=0, padx=20, pady=(5, 20))
        row_index += 1

        # Overview Section
        self.overview_label = customtkinter.CTkLabel(self, text="Past Calibrations:", anchor="w")
        self.overview_label.grid(row=row_index, column=0, padx=20, pady=(10, 0))
        row_index += 1

        self.overview_button = customtkinter.CTkButton(self, text="Overview", command=overview_callback)
        self.overview_button.grid(row=row_index, column=0, padx=20, pady=(10, 10))
        row_index += 1

        # Defaults
        self.selected_mode = ""
        self.scaling_menu.set("100%")

    def set_active_mode(self, mode):
        # Reset previous button to theme default
        if self.active_button:
            self.active_button.configure(fg_color=self.button_bg)

        # Highlight new one
        self.selected_mode = mode
        self.active_button = self.mode_buttons[mode]
        self.active_button.configure(fg_color=self.active_button_color)

        # Trigger external mode update
        self.mode_callback(mode)
