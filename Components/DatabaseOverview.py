import customtkinter


class DatabaseOverview(customtkinter.CTkFrame):
    """ Database overview to review past calibrations """

    def __init__(self, parent, callback):
        super().__init__(parent, fg_color="transparent")
        self.grid(row=0, column=1, rowspan=3, padx=20, pady=20, sticky="nsew")

        self.database = parent.conn
        self.selected_calibration = None
        self.callback = callback

        self.grid_rowconfigure(2, weight=1)  # Row 2 will expand (where data is)
        self.grid_columnconfigure(0, weight=1)

        # === Back Button (Chevron) ===
        self.back_button = customtkinter.CTkButton(
            self, text="‹ Back", width=80, command=self.callback  # smaller text, acts like chevron
        )
        self.back_button.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 10))

        # === Dropdown to select calibration session ===
        self.dropdown = customtkinter.CTkOptionMenu(self, values=["No data"], command=self.load_session)
        self.dropdown.grid(row=1, column=0, pady=(0, 10), sticky="ew")

        # === Frame to hold session data + scrollbar ===
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.populate_dropdown()

    def populate_dropdown(self):
        """ Query calibration sessions from database """
        cursor = self.database.cursor()
        cursor.execute("SELECT id, method_type, created_at FROM calibrations ORDER BY created_at DESC")
        results = cursor.fetchall()

        if results:
            session_names = [f"ID {row[0]}: {row[1]} at {row[2]}" for row in results]
        else:
            session_names = ["No calibrations found"]

        self.dropdown.configure(values=session_names)
        if session_names:
            self.dropdown.set(session_names[0])

    def load_session(self, session_name):
        """ Load measurements for selected session """

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

        # Clear previous
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if results:
            # --- Header Row ---
            headers = ["Set Value", "Measured", "Δ (Diff)", "STD", "Timestamp"]
            for idx, header in enumerate(headers):
                customtkinter.CTkLabel(self.scrollable_frame, text=header, font=customtkinter.CTkFont(size=14, weight="bold")).grid(
                    row=0, column=idx, padx=10, pady=(0, 5), sticky="w"
                )

            # --- Measurement Rows ---
            for row_idx, row in enumerate(results, start=1):
                set_value, calculated_value, ref_set_diff, std, timestamp = row

                customtkinter.CTkLabel(self.scrollable_frame, text=f"{set_value}", font=customtkinter.CTkFont(size=13)).grid(
                    row=row_idx, column=0, padx=10, pady=2, sticky="w"
                )
                customtkinter.CTkLabel(self.scrollable_frame, text=f"{calculated_value}", font=customtkinter.CTkFont(size=13)).grid(
                    row=row_idx, column=1, padx=10, pady=2, sticky="w"
                )
                customtkinter.CTkLabel(self.scrollable_frame, text=f"{ref_set_diff}", font=customtkinter.CTkFont(size=13)).grid(
                    row=row_idx, column=2, padx=10, pady=2, sticky="w"
                )
                customtkinter.CTkLabel(self.scrollable_frame, text=f"{std}", font=customtkinter.CTkFont(size=13)).grid(
                    row=row_idx, column=3, padx=10, pady=2, sticky="w"
                )
                customtkinter.CTkLabel(self.scrollable_frame, text=timestamp, font=customtkinter.CTkFont(size=13)).grid(
                    row=row_idx, column=4, padx=10, pady=2, sticky="w"
                )
        else:
            customtkinter.CTkLabel(self.scrollable_frame, text="No measurements found.", font=customtkinter.CTkFont(size=14)).grid(
                row=0, column=0, sticky="w", padx=10, pady=5
            )
