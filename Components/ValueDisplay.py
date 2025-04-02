import customtkinter


class ValueDisplay(customtkinter.CTkFrame):
    """ Displays real-time values with labels """
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid(row=1, column=1, padx=(20, 20), pady=(10, 10), sticky="nsew")

        # === Configure grid columns ===
        columns_per_row = 3
        total_columns = columns_per_row * 2
        for c in range(total_columns):
            self.grid_columnconfigure(c, weight=1)

        # === Layout settings ===
        header_width = 160
        label_width = 100
        padx = 10

        # === Measurement definitions ===
        self.labels_per_task = {
            task: {
                "references": [0, 0.1, -0.1, 1, -1, 10, -10, 100, -100, 1000, -1000],
                "units": ["mV"] * 11,
                "measurements": ["--"] * 11,
                "differences": ["--"] * 11
            }
            for task in ["DCV", "DCI", "ACV", "ACI", "2Ω", "FREQ.", "PERIOD"]
        }

        self.labels_values = self.labels_per_task["DCV"]
        self.value_labels = []
        self.diff_labels = []

        references = self.labels_values["references"]
        units = self.labels_values["units"]
        measurements = self.labels_values["measurements"]
        differences = self.labels_values["differences"]

        used_indices = set()
        column = 0
        row_block = 0

        for i, ref in enumerate(references):
            if i in used_indices:
                continue

            try:
                neg_index = references.index(-ref)
            except ValueError:
                neg_index = None

            is_pair = (
                neg_index is not None and
                neg_index != i and
                neg_index not in used_indices and
                ref > 0
            )

            if is_pair:
                # Header
                customtkinter.CTkLabel(
                    self, text=f"Measured at ±{ref}",
                    font=customtkinter.CTkFont(size=15, weight="bold"),
                    width=header_width
                ).grid(row=row_block * 3, column=column, columnspan=2, padx=padx, pady=(10, 2), sticky="n")

                # Value labels
                label_pos = customtkinter.CTkLabel(
                    self, text=f"{measurements[i]} {units[i]}",
                    font=customtkinter.CTkFont(size=19, weight="bold"),
                    width=label_width
                )
                label_neg = customtkinter.CTkLabel(
                    self, text=f"{measurements[neg_index]} {units[neg_index]}",
                    font=customtkinter.CTkFont(size=19, weight="bold"),
                    width=label_width
                )
                label_pos.grid(row=row_block * 3 + 1, column=column, padx=padx, pady=(4, 2), sticky="n")
                label_neg.grid(row=row_block * 3 + 1, column=column + 1, padx=padx, pady=(4, 2), sticky="n")

                # Difference labels
                diff_pos = customtkinter.CTkLabel(
                    self, text=f"Δ {differences[i]} {units[i]}",
                    font=customtkinter.CTkFont(size=14),
                    width=label_width
                )
                diff_neg = customtkinter.CTkLabel(
                    self, text=f"Δ {differences[neg_index]} {units[neg_index]}",
                    font=customtkinter.CTkFont(size=14),
                    width=label_width
                )
                diff_pos.grid(row=row_block * 3 + 2, column=column, padx=padx, pady=(0, 8), sticky="n")
                diff_neg.grid(row=row_block * 3 + 2, column=column + 1, padx=padx, pady=(0, 8), sticky="n")

                self.value_labels.extend([label_pos, label_neg])
                self.diff_labels.extend([diff_pos, diff_neg])
                used_indices.update({i, neg_index})
                column += 2

            else:
                # Single-entry header
                customtkinter.CTkLabel(
                    self, text=f"Measured at {ref}",
                    font=customtkinter.CTkFont(size=15, weight="bold"),
                    width=header_width
                ).grid(row=row_block * 3, column=column, columnspan=2, padx=padx, pady=(10, 2), sticky="n")

                val_label = customtkinter.CTkLabel(
                    self, text=f"{measurements[i]} {units[i]}",
                    font=customtkinter.CTkFont(size=19, weight="bold"),
                    width=label_width
                )
                val_label.grid(row=row_block * 3 + 1, column=column, columnspan=2, padx=padx, pady=(4, 2), sticky="n")

                diff_label = customtkinter.CTkLabel(
                    self, text=f"Δ {differences[i]} {units[i]}",
                    font=customtkinter.CTkFont(size=14),
                    width=label_width
                )
                diff_label.grid(row=row_block * 3 + 2, column=column, columnspan=2, padx=padx, pady=(0, 8), sticky="n")

                self.value_labels.append(val_label)
                self.diff_labels.append(diff_label)
                used_indices.add(i)
                column += 2

            if column >= columns_per_row * 2:
                column = 0
                row_block += 1

    def update_values(self, values, differences):
        """ Update the displayed values and differences """
        for i, val in enumerate(values):
            try:
                # Extract value and label
                raw_val = val["Value"]
                label = val["Label"]
                diff_val = differences[i]["Value"]

                # Format value
                if isinstance(raw_val, str):
                    value_str = raw_val
                else:
                    value_str = f"{float(raw_val):.2f}"

                # Format difference
                if isinstance(diff_val, str):
                    diff_str = diff_val
                else:
                    diff_str = f"{float(diff_val):.2f}"

                # Update labels
                self.value_labels[i].configure(text=f"{value_str} {label}")
                self.diff_labels[i].configure(text=f"Δ {diff_str} {label}")

            except (IndexError, KeyError, TypeError, ValueError):
                # Fallback in case of mismatch or formatting error
                self.value_labels[i].configure(text="--")
                self.diff_labels[i].configure(text="Δ --")
