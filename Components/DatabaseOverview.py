import customtkinter
from Utils.color_theme import COLORS


class DatabaseOverview(customtkinter.CTkFrame):
    """ Database overview to review past calibrations """

    def __init__(self, parent, callback):
        self.default_color = COLORS["backgroundLight"]
        self.active_color = COLORS["backgroundDark"]
        self.hover_color = COLORS["hover"]
        self.text_color = COLORS["lg_text"]

        super().__init__(parent, fg_color=self.default_color, bg_color=self.default_color)
        self.grid(row=0, column=1, rowspan=3, padx=20, pady=20, sticky="nsew")

        self.database = parent.conn
        self.selected_calibration = None
        self.callback = callback

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # === Back Button ===
        self.back_button = customtkinter.CTkButton(
            self, text="‹ Back", width=80, command=self.callback
        )
        self.back_button.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 10))

        # === Dropdown (Custom Scrollable) ===
        self.dropdown_frame = customtkinter.CTkFrame(self, fg_color=self.default_color)
        self.dropdown_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self.dropdown_button = customtkinter.CTkButton(
            self.dropdown_frame, text="Select Session", command=self.toggle_dropdown
        )
        self.dropdown_button.pack(fill="x")

        self.dropdown_list_frame = None
        self.dropdown_open = False
        self.dropdown_values = ["No data"]

        # === Scrollable Frame ===
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self, fg_color=self.default_color, bg_color=self.default_color)
        self.scrollable_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.populate_dropdown()

    def toggle_dropdown(self):
        if self.dropdown_open:
            self.dropdown_list_frame.destroy()
            self.dropdown_open = False
        else:
            self.dropdown_list_frame = customtkinter.CTkScrollableFrame(self, height=150, fg_color=self.default_color)
            self.dropdown_list_frame.grid(row=3, column=0, sticky="ew")
            self.dropdown_open = True

            for option in self.dropdown_values:
                btn = customtkinter.CTkButton(
                    self.dropdown_list_frame,
                    text=option,
                    anchor="w",
                    command=lambda opt=option: self.select_dropdown_option(opt),
                    fg_color="transparent",
                    hover_color=self.hover_color,
                    text_color=self.text_color
                )
                btn.pack(fill="x", pady=1)

    def select_dropdown_option(self, option):
        self.dropdown_button.configure(text=option)
        self.load_session(option)
        if self.dropdown_list_frame:
            self.dropdown_list_frame.destroy()
            self.dropdown_open = False

    def populate_dropdown(self):
        cursor = self.database.cursor()
        cursor.execute("SELECT id, method_type, created_at FROM calibrations ORDER BY created_at DESC")
        results = cursor.fetchall()

        if results:
            self.dropdown_values = [f"ID {row[0]}: {row[1]} at {row[2]}" for row in results]
        else:
            self.dropdown_values = ["No calibrations found"]

        self.dropdown_button.configure(text=self.dropdown_values[0])

    def load_session(self, session_name):
        if session_name.startswith("ID "):
            calib_id = int(session_name.split(":")[0].replace("ID", "").strip())
        else:
            return

        cursor = self.database.cursor()
        cursor.execute("""
            SELECT set_value, calculated_value, ref_set_diff, std, timestamp
            FROM measurements
            WHERE calibration_id = ?
            ORDER BY timestamp
        """, (calib_id,))
        results = cursor.fetchall()

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if results:
            headers = ["Set Value", "Measured", "Δ (Diff)", "STD", "Frequency (Hz)", "Timestamp"]
            for idx, header in enumerate(headers):
                customtkinter.CTkLabel(
                    self.scrollable_frame, text=header,
                    font=customtkinter.CTkFont(size=14, weight="bold")
                ).grid(row=0, column=idx, padx=10, pady=(0, 5), sticky="w")

            for row_idx, row in enumerate(results, start=1):
                set_value, calculated_value, ref_set_diff, std,frequency, timestamp = row

                customtkinter.CTkLabel(self.scrollable_frame, text=f"{set_value}", font=customtkinter.CTkFont(size=13)).grid(
                    row=row_idx, column=0, padx=10, pady=2, sticky="w")
                customtkinter.CTkLabel(self.scrollable_frame, text=f"{calculated_value}", font=customtkinter.CTkFont(size=13)).grid(
                    row=row_idx, column=1, padx=10, pady=2, sticky="w")
                customtkinter.CTkLabel(self.scrollable_frame, text=f"{ref_set_diff}", font=customtkinter.CTkFont(size=13)).grid(
                    row=row_idx, column=2, padx=10, pady=2, sticky="w")
                customtkinter.CTkLabel(self.scrollable_frame, text=f"{std}", font=customtkinter.CTkFont(size=13)).grid(
                    row=row_idx, column=3, padx=10, pady=2, sticky="w")
                customtkinter.CTkLabel(self.scrollable_frame, text=f"{frequency}", font=customtkinter.CTkFont(size=13)).grid(
                    row=row_idx, column=4, padx=10, pady=2, sticky="w")
                customtkinter.CTkLabel(self.scrollable_frame, text=timestamp, font=customtkinter.CTkFont(size=13)).grid(
                    row=row_idx, column=5, padx=10, pady=2, sticky="w")
        else:
            customtkinter.CTkLabel(
                self.scrollable_frame,
                text="No measurements found.",
                font=customtkinter.CTkFont(size=14)
            ).grid(row=0, column=0, sticky="w", padx=10, pady=5)
