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

        # Get method type
        cursor.execute("SELECT method_type FROM calibrations WHERE id = ?", (calib_id,))
        method_row = cursor.fetchone()
        method_type = method_row[0] if method_row else None

        # Fetch regular measurements
        cursor.execute("""
            SELECT set_value, calculated_value, ref_set_diff, std, unit, frequency, timestamp
            FROM measurements
            WHERE calibration_id = ?
            ORDER BY timestamp
        """, (calib_id,))
        results = [(*row, "measurement") for row in cursor.fetchall()]

        # Fetch colinearity if needed
        colinearity_results = []
        if method_type in ("DCV", "ACV"):
            cursor.execute("""
                SELECT linear_ref, measurement, linear_diff, linear_std, unit, NULL as frequency, timestamp
                FROM colinearity
                WHERE calibration_id = ?
                ORDER BY timestamp
            """, (calib_id,))
            colinearity_results = [(*row, "linear_measurement") for row in cursor.fetchall()]

        # Merge all
        combined_results = results + colinearity_results

        # Clear frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if combined_results:
            headers = ["Reference", "Measured", "Δ (Diff)", "STD", "Frequency", "Timestamp", "Type"]
            for idx, header in enumerate(headers):
                customtkinter.CTkLabel(
                    self.scrollable_frame, text=header,
                    font=customtkinter.CTkFont(size=14, weight="bold")
                ).grid(row=0, column=idx, padx=10, pady=(0, 5), sticky="w")

            for row_idx, row in enumerate(combined_results, start=1):
                set_value, calculated_value, ref_set_diff, std, unit, frequency, timestamp, row_type = row
                if row_type == "measurement":
                    values = [
                        f"{set_value} {unit}",
                        f"{calculated_value} {unit}",
                        f"{ref_set_diff} {unit}",
                        f"{std} {unit}",
                        frequency or "/",
                        timestamp,
                        row_type
                    ]
                else:
                    values = [
                        f"{set_value} {unit}",
                        f"{calculated_value} V",
                        f"{ref_set_diff} V",
                        f"{std} V",
                        frequency or "/",
                        timestamp,
                        row_type
                    ]

                for col_idx, val in enumerate(values):
                    customtkinter.CTkLabel(
                        self.scrollable_frame, text=val,
                        font=customtkinter.CTkFont(size=13)
                    ).grid(row=row_idx, column=col_idx, padx=10, pady=2, sticky="w")
        else:
            customtkinter.CTkLabel(
                self.scrollable_frame,
                text="No measurements found.",
                font=customtkinter.CTkFont(size=14)
            ).grid(row=0, column=0, sticky="w", padx=10, pady=5)



