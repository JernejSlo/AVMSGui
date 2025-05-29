import customtkinter
from Utils.color_theme import COLORS


class ValueDisplay(customtkinter.CTkFrame):
    """ Displays real-time values with labels """

    def __init__(self, parent, running):
        self.default_color = COLORS["backgroundLight"]
        self.active_color = COLORS["backgroundDark"]
        self.hover_color = COLORS["hover"]
        self.text_color = COLORS["lg_text"]

        self.running = running
        self.vals = []
        self.diffs = []
        super().__init__(parent, fg_color=self.default_color)
        self.grid(row=1, column=1, padx=(20, 20), pady=(10, 80), sticky="nsew")

        # === Configure grid columns ===
        columns_per_row = 3
        total_columns = columns_per_row * 2
        for c in range(total_columns):
            self.grid_columnconfigure(c, weight=1)

        header_width = 160
        label_width = 100
        label_value_size = 13
        padx = 10

        self.labels_per_task = {
            task: {
                "references": [0, 0.1, -0.1, 1, -1, 10, -10, 100, -100, 1000, -1000, 10000,10000],
                "units": [""] * 13,
                "measurements": ["--"] * 13,
                "diffMeas": ["--"] * 13,
                "stdDevs": ["--"] * 13
            }
            for task in ["DCV", "DCI", "ACV", "ACI", "2Ω", "FREQ.", "PERIOD"]
        }

        self.labels_values = self.labels_per_task["DCV"]
        self.headers = []
        self.value_labels = []
        self.diff_labels = []
        self.std_labels = []  # for double
        self.single_value_labels = []  # for single
        self.single_diff_labels = []  # for single
        self.single_std_labels = []  # for single
        self.pair_indices = []

        references = self.labels_values["references"]
        units = self.labels_values["units"]
        measurements = self.labels_values["measurements"]
        differences = self.labels_values["diffMeas"]

        used_indices = set()
        column = 0
        row_block = 0

        for i, ref in enumerate(references):
            print(i)
            if i in used_indices:
                continue

            try:
                neg_index = references.index(-ref)
            except ValueError:
                neg_index = None

            self.pair_indices.append((i, neg_index))

            # === Header ===
            header = customtkinter.CTkLabel(
                self, text=f"Measured at ±{abs(ref)}{units[i]}",
                font=customtkinter.CTkFont(size=15, weight="bold"),
                width=header_width
            )
            header.grid(row=row_block * 4, column=column, columnspan=2, padx=padx, pady=(10, 2), sticky="n")
            self.headers.append(header)

            # === Double layout: Positive ===
            label_pos = customtkinter.CTkLabel(
                self, text=f"{measurements[i]} {units[i]}",
                font=customtkinter.CTkFont(size=label_value_size, weight="bold"),
                width=label_width
            )
            diff_pos = customtkinter.CTkLabel(
                self, text=f"Δ {differences[i]} {units[i]}",
                font=customtkinter.CTkFont(size=14),
                width=label_width
            )
            std_pos = customtkinter.CTkLabel(
                self, text=f"σ -- {units[i]}",
                font=customtkinter.CTkFont(size=12),
                width=label_width
            )

            label_pos.grid(row=row_block * 4 + 1, column=column, padx=padx, pady=(4, 2), sticky="n")
            diff_pos.grid(row=row_block * 4 + 2, column=column, padx=padx, pady=(0, 2), sticky="n")
            std_pos.grid(row=row_block * 4 + 3, column=column, padx=padx, pady=(0, 6), sticky="n")

            self.value_labels.append(label_pos)
            self.diff_labels.append(diff_pos)
            self.std_labels.append(std_pos)

            # === Double layout: Negative ===
            if neg_index is not None:
                label_neg = customtkinter.CTkLabel(
                    self, text=f"{measurements[neg_index]} {units[neg_index]}",
                    font=customtkinter.CTkFont(size=label_value_size, weight="bold"),
                    width=label_width
                )
                diff_neg = customtkinter.CTkLabel(
                    self, text=f"Δ {differences[neg_index]} {units[neg_index]}",
                    font=customtkinter.CTkFont(size=14),
                    width=label_width
                )
                std_neg = customtkinter.CTkLabel(
                    self, text=f"σ -- {units[neg_index]}",
                    font=customtkinter.CTkFont(size=12),
                    width=label_width
                )
            else:
                label_neg = customtkinter.CTkLabel(
                    self, text="--",
                    font=customtkinter.CTkFont(size=label_value_size, weight="bold"),
                    width=label_width
                )
                diff_neg = customtkinter.CTkLabel(
                    self, text="Δ --",
                    font=customtkinter.CTkFont(size=14),
                    width=label_width
                )
                std_neg = customtkinter.CTkLabel(
                    self, text="σ --",
                    font=customtkinter.CTkFont(size=12),
                    width=label_width
                )

            label_neg.grid(row=row_block * 4 + 1, column=column + 1, padx=padx, pady=(4, 2), sticky="n")
            diff_neg.grid(row=row_block * 4 + 2, column=column + 1, padx=padx, pady=(0, 2), sticky="n")
            std_neg.grid(row=row_block * 4 + 3, column=column + 1, padx=padx, pady=(0, 6), sticky="n")

            self.value_labels.append(label_neg)
            self.diff_labels.append(diff_neg)
            self.std_labels.append(std_neg)

            # === Single layout ===
            label_single = customtkinter.CTkLabel(
                self, text=f"{measurements[i]} {units[i]}",
                font=customtkinter.CTkFont(size=label_value_size, weight="bold"),
                width=label_width * 2
            )
            diff_single = customtkinter.CTkLabel(
                self, text=f"Δ {differences[i]} {units[i]}",
                font=customtkinter.CTkFont(size=14),
                width=label_width * 2
            )
            std_single = customtkinter.CTkLabel(
                self, text=f"σ -- {units[i]}",
                font=customtkinter.CTkFont(size=12),
                width=label_width * 2
            )

            label_single.grid(row=row_block * 4 + 1, column=column, columnspan=2, padx=padx, pady=(4, 2), sticky="n")
            diff_single.grid(row=row_block * 4 + 2, column=column, columnspan=2, padx=padx, pady=(0, 2), sticky="n")
            std_single.grid(row=row_block * 4 + 3, column=column, columnspan=2, padx=padx, pady=(0, 6), sticky="n")

            label_single.grid_remove()
            diff_single.grid_remove()
            std_single.grid_remove()

            self.single_value_labels.append(label_single)
            self.single_diff_labels.append(diff_single)
            self.single_std_labels.append(std_single)

            used_indices.add(i)
            if neg_index is not None:
                used_indices.add(neg_index)

            column += 2
            if column >= columns_per_row * 2:
                column = 0
                row_block += 1

        self.single_mode_flags = [False] * len(self.pair_indices)

        # Rounding slider
        self.rounding_precision = customtkinter.IntVar(value=2)
        slider_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        slider_frame.grid(row=row_block * 5 + 2, column=0, columnspan=total_columns, pady=(10, 0), sticky="ew")
        slider_frame.grid_columnconfigure(0, weight=1)
        slider_frame.grid_columnconfigure(1, weight=0)
        slider_frame.grid_columnconfigure(2, weight=1)

        self.precision_slider = customtkinter.CTkSlider(
            slider_frame,
            from_=0, to=8, number_of_steps=8,
            variable=self.rounding_precision,
            command=self.update_slider_label,
            width=180, height=22, corner_radius=180
        )
        self.precision_slider.grid(row=0, column=1, padx=(0, 20), sticky="ew")

        self.precision_value_label = customtkinter.CTkLabel(
            slider_frame, text="2 decimals",
            font=customtkinter.CTkFont(size=12)
        )
        self.precision_value_label.grid(row=0, column=2, sticky="w")

    def update_slider_label(self, value):
        self.precision_value_label.configure(text=f"{int(float(value))} digits")
        if not self.running:
            self.update_values(self.vals, self.diffs)

    def switch_to_single(self, pair_index, mode=None):
        self.single_mode_flags[pair_index] = True

        # Hide double layout widgets
        self.value_labels[pair_index * 2].grid_remove()
        self.value_labels[pair_index * 2 + 1].grid_remove()

        self.diff_labels[pair_index * 2].grid_remove()
        self.diff_labels[pair_index * 2 + 1].grid_remove()

        self.std_labels[pair_index * 2].grid_remove()
        self.std_labels[pair_index * 2 + 1].grid_remove()

        # Show single layout widgets
        self.single_value_labels[pair_index].grid()
        self.single_diff_labels[pair_index].grid()
        self.single_std_labels[pair_index].grid()

    def switch_to_double(self, pair_index):
        self.single_mode_flags[pair_index] = False

        # Hide single layout widgets
        self.single_value_labels[pair_index].grid_remove()
        self.single_diff_labels[pair_index].grid_remove()
        self.single_std_labels[pair_index].grid_remove()

        # Show double layout widgets
        self.value_labels[pair_index * 2].grid()
        self.value_labels[pair_index * 2 + 1].grid()

        self.diff_labels[pair_index * 2].grid()
        self.diff_labels[pair_index * 2 + 1].grid()

        self.std_labels[pair_index * 2].grid()
        self.std_labels[pair_index * 2 + 1].grid()

    def get_column_for_index(self, pair_index, single_mode_flags):
        col = 0
        for i in range(pair_index):
            col += 1 if single_mode_flags[i] else 2
        return col

    def update_values(self, values, differences):
        self.vals = values
        self.diffs = differences
        precision = self.rounding_precision.get()

        value_i = 0  # index into values[] and differences[]
        for pair_index, is_single in enumerate(self.single_mode_flags):
            try:
                if is_single:
                    val = values[value_i]
                    diff_val = differences[value_i]

                    raw_val = val["Value"]
                    label = val["Label"]
                    diff = diff_val["Value"]
                    std = val.get("StdDev", "--")

                    value_str = raw_val if isinstance(raw_val, str) else f"{float(raw_val):.{precision}f}"
                    diff_str = diff if isinstance(diff, str) else f"{float(diff):.{precision}f}"
                    std_str = std if isinstance(std, str) else f"{float(std):.{precision}f}"

                    self.single_value_labels[pair_index].configure(text=f"{value_str} {label}")
                    self.single_diff_labels[pair_index].configure(text=f"Δ {diff_str} {label}")
                    self.single_std_labels[pair_index].configure(text=f"σ {std_str} {label}")

                    value_i += 1

                else:
                    for offset in range(2):
                        val = values[value_i]
                        diff_val = differences[value_i]

                        raw_val = val["Value"]
                        label = val["Label"]
                        diff = diff_val["Value"]
                        std = val.get("StdDev", "--")

                        value_str = raw_val if isinstance(raw_val, str) else f"{float(raw_val):.{precision}f}"
                        diff_str = diff if isinstance(diff, str) else f"{float(diff):.2f}"
                        std_str = std if isinstance(std, str) else f"{float(std):.2f}"

                        label_index = pair_index * 2 + offset
                        self.value_labels[label_index].configure(text=f"{value_str} {label}")
                        self.diff_labels[label_index].configure(text=f"Δ {diff_str} {label}")
                        self.std_labels[label_index].configure(text=f"σ {std_str} {label}")

                        value_i += 1

            except (IndexError, KeyError, TypeError, ValueError):
                if is_single:
                    self.single_value_labels[pair_index].configure(text="--")
                    self.single_diff_labels[pair_index].configure(text="Δ --")
                    self.single_std_labels[pair_index].configure(text="σ --")
                else:
                    for offset in range(2):
                        label_index = pair_index * 2 + offset
                        if label_index < len(self.value_labels):
                            self.value_labels[label_index].configure(text="--")
                            self.diff_labels[label_index].configure(text="Δ --")
                            self.std_labels[label_index].configure(text="σ --")

