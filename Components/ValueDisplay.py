import customtkinter

class ValueDisplay(customtkinter.CTkFrame):
    """ Displays real-time values with labels """
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid(row=1, column=1, padx=(20, 20), pady=(10, 10), sticky="nsew")
        self.grid_columnconfigure((0, 1, 2), weight=1)


        self.labels_per_task = {
            "DCV": {
                "references": [0,0.1,-0.1,1,-1,10,-10,100,-100,1000, -1000],
                "units": ["mV","mV","mV","mV","mV","mV","mV","mV","mV","mV","mV",],
                "measurements": ["--","--","--","--","--","--","--","--","--","--","--",],
                "differences": [0,0,0,0,0,0,0,0,0,0,0]
            },
            "DCI": {
                "references": [0,0.1,-0.1,1,-1,10,-10,100,-100,1000, -1000],
                "units": ["mV","mV","mV","mV","mV","mV","mV","mV","mV","mV","mV",],
                "measurements": ["--","--","--","--","--","--","--","--","--","--","--",],
                "differences": [0,0,0,0,0,0,0,0,0,0,0]
            },
            "ACV": {
                "references": [0,0.1,-0.1,1,-1,10,-10,100,-100,1000, -1000],
                "units": ["mV","mV","mV","mV","mV","mV","mV","mV","mV","mV","mV",],
                "measurements": ["--","--","--","--","--","--","--","--","--","--","--",],
                "differences": [0,0,0,0,0,0,0,0,0,0,0]
            },
            "ACI": {
                "references": [0,0.1,-0.1,1,-1,10,-10,100,-100,1000, -1000],
                "units": ["mV","mV","mV","mV","mV","mV","mV","mV","mV","mV","mV",],
                "measurements": ["--","--","--","--","--","--","--","--","--","--","--",],
                "differences": [0,0,0,0,0,0,0,0,0,0,0]
            },
            "2Ω": {
                "references": [0,0.1,-0.1,1,-1,10,-10,100,-100,1000, -1000],
                "units": ["mV","mV","mV","mV","mV","mV","mV","mV","mV","mV","mV",],
                "measurements": ["--","--","--","--","--","--","--","--","--","--","--",],
                "differences": [0,0,0,0,0,0,0,0,0,0,0]
            },
            "FREQ.": {
                "references": [0,0.1,-0.1,1,-1,10,-10,100,-100,1000, -1000],
                "units": ["mV","mV","mV","mV","mV","mV","mV","mV","mV","mV","mV",],
                "measurements": ["--","--","--","--","--","--","--","--","--","--","--",],
                "differences": [0,0,0,0,0,0,0,0,0,0,0]
            },
            "PERIOD": {
                "references": [0,0.1,-0.1,1,-1,10,-10,100,-100,1000, -1000],
                "units": ["mV","mV","mV","mV","mV","mV","mV","mV","mV","mV","mV",],
                "measurements": ["--","--","--","--","--","--","--","--","--","--","--",],
                "differences": [0,0,0,0,0,0,0,0,0,0,0]
            },
        }

        self.labels_values = self.labels_per_task["DCV"]
        self.value_labels = []
        self.diff_labels = []

        label_width = 80
        header_width = 160  # For columnspan=2 headers

        padx_d = 40
        padx_s = 40

        columns_per_row = 3  # Controls how many paired groups per row
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
                header = customtkinter.CTkLabel(
                    self, text=f"Measured at ±{ref}",
                    font=customtkinter.CTkFont(size=16),
                    width=header_width
                )
                header.grid(row=row_block * 3, column=column, columnspan=2, padx=padx_d, pady=(10, 2), sticky="n")

                # Values
                label_pos = customtkinter.CTkLabel(
                    self, text=f"{measurements[i]} {units[i]}",
                    font=customtkinter.CTkFont(size=18), width=label_width
                )
                label_neg = customtkinter.CTkLabel(
                    self, text=f"{measurements[neg_index]} {units[neg_index]}",
                    font=customtkinter.CTkFont(size=18), width=label_width
                )
                label_pos.grid(row=row_block * 3 + 1, column=column, padx=padx_d, pady=(2, 2), sticky="n")
                label_neg.grid(row=row_block * 3 + 1, column=column + 1, padx=padx_d, pady=(2, 2), sticky="n")

                # Differences
                diff_pos = customtkinter.CTkLabel(
                    self, text=f"Δ {differences[i]} {units[i]}",
                    font=customtkinter.CTkFont(size=14), width=label_width
                )
                diff_neg = customtkinter.CTkLabel(
                    self, text=f"Δ {differences[neg_index]} {units[neg_index]}",
                    font=customtkinter.CTkFont(size=14), width=label_width
                )
                diff_pos.grid(row=row_block * 3 + 2, column=column, padx=padx_d, pady=(2, 10), sticky="n")
                diff_neg.grid(row=row_block * 3 + 2, column=column + 1, padx=padx_d, pady=(2, 10), sticky="n")

                self.value_labels.extend([label_pos, label_neg])
                self.diff_labels.extend([diff_pos, diff_neg])
                used_indices.update({i, neg_index})
                column += 2

            else:
                # Header
                customtkinter.CTkLabel(
                    self, text=f"Measured at {ref}",
                    font=customtkinter.CTkFont(size=16), width=label_width,
                ).grid(row=row_block * 3, column=column, padx=padx_s, pady=(10, 2), sticky="n")

                # Value
                val_label = customtkinter.CTkLabel(
                    self, text=f"{measurements[i]} {units[i]}",
                    font=customtkinter.CTkFont(size=18), width=header_width,
                )
                val_label.grid(row=row_block * 3 + 1, column=column, padx=padx_s, pady=(2, 2), sticky="n")

                # Difference
                diff_label = customtkinter.CTkLabel(
                    self, text=f"Δ {differences[i]} {units[i]}",
                    font=customtkinter.CTkFont(size=14), width=label_width,
                )
                diff_label.grid(row=row_block * 3 + 2, column=column, padx=padx_s, pady=(2, 10), sticky="n")

                self.value_labels.append(val_label)
                self.diff_labels.append(diff_label)
                used_indices.add(i)
                column += 2

            # Wrap to next row if needed
            if column >= columns_per_row * 2:
                column = 0
                row_block += 1

    def update_values(self, values):
        """ Update the displayed values """
        for i, val in enumerate(values):
            self.value_labels[i].configure(text=val)