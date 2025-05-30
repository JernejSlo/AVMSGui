import customtkinter
from Utils.color_theme import COLORS


class ValueDisplay(customtkinter.CTkFrame):
    """ Displays real-time values with labels, supporting single, double, and triple layouts."""

    def __init__(self, parent, running):
        super().__init__(parent, fg_color=COLORS["backgroundLight"])

        self.running = running
        self.vals = []
        self.diffs = []
        self.stds = []
        self.single_mode_flags = []
        self.triple_mode_flags = []

        self.grid(row=1, column=1, padx=(20, 20), pady=(10, 80), sticky="nsew")

        columns_per_row = 3
        total_columns = columns_per_row * 3
        for c in range(total_columns):
            self.grid_columnconfigure(c, weight=1)

        header_width = 160
        label_width = 100
        label_value_size = 13
        padx = 10

        self.labels_values = {
            "references": [0, 0.1, -0.1, 1, -1, 2, -2, 3, -3],
            "units": ["V"] * 9,
            "measurements": ["--"] * 9,
            "diffMeas": ["--"] * 9,
            "stdDevs": ["--"] * 9
        }

        self.headers = []
        self.value_labels = []
        self.diff_labels = []
        self.std_labels = []

        self.single_value_labels = []
        self.single_diff_labels = []
        self.single_std_labels = []

        self.pair_indices = []

        used_indices = set()
        column = 0
        row_block = 0

        num_blocks = 7  # Always create 7 blocks
        column = 0
        row_block = 0

        for block_index in range(num_blocks):
            self.pair_indices.append((None, None, None))  # Dummy placeholders

            header = customtkinter.CTkLabel(self, text=f"Measured at --",
                                            font=customtkinter.CTkFont(size=15, weight="bold"),
                                            width=header_width)
            header.grid(row=row_block * 4, column=column, columnspan=3, padx=padx, pady=(10, 2), sticky="n")
            self.headers.append(header)

            for offset in range(3):
                val_lbl = customtkinter.CTkLabel(self, text="--",
                                                 font=customtkinter.CTkFont(size=label_value_size, weight="bold"),
                                                 width=label_width)
                diff_lbl = customtkinter.CTkLabel(self, text="Δ --",
                                                  font=customtkinter.CTkFont(size=14),
                                                  width=label_width)
                std_lbl = customtkinter.CTkLabel(self, text="σ --",
                                                 font=customtkinter.CTkFont(size=12),
                                                 width=label_width)

                val_lbl.grid(row=row_block * 4 + 1, column=column + offset, padx=padx, pady=(4, 2), sticky="n")
                diff_lbl.grid(row=row_block * 4 + 2, column=column + offset, padx=padx, pady=(0, 2), sticky="n")
                std_lbl.grid(row=row_block * 4 + 3, column=column + offset, padx=padx, pady=(0, 6), sticky="n")

                self.value_labels.append(val_lbl)
                self.diff_labels.append(diff_lbl)
                self.std_labels.append(std_lbl)

            single_val = customtkinter.CTkLabel(self, text="--",
                                                font=customtkinter.CTkFont(size=label_value_size, weight="bold"),
                                                width=label_width * 3)
            single_diff = customtkinter.CTkLabel(self, text="Δ --",
                                                 font=customtkinter.CTkFont(size=14),
                                                 width=label_width * 3)
            single_std = customtkinter.CTkLabel(self, text="σ --",
                                                font=customtkinter.CTkFont(size=12),
                                                width=label_width * 3)

            single_val.grid(row=row_block * 4 + 1, column=column, columnspan=3, padx=padx, pady=(4, 2), sticky="n")
            single_diff.grid(row=row_block * 4 + 2, column=column, columnspan=3, padx=padx, pady=(0, 2), sticky="n")
            single_std.grid(row=row_block * 4 + 3, column=column, columnspan=3, padx=padx, pady=(0, 6), sticky="n")

            single_val.grid_remove()
            single_diff.grid_remove()
            single_std.grid_remove()

            self.single_value_labels.append(single_val)
            self.single_diff_labels.append(single_diff)
            self.single_std_labels.append(single_std)

            column += 3
            if column >= total_columns:
                column = 0
                row_block += 1

        self.single_mode_flags = [False] * num_blocks
        self.triple_mode_flags = [False] * num_blocks

        # Slider
        self.rounding_precision = customtkinter.IntVar(value=2)
        slider_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        slider_frame.grid(row=row_block * 5 + 3, column=0, columnspan=total_columns, pady=(10, 0), sticky="ew")
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
            self.update_values(self.vals, self.diffs, self.stds)

    def switch_to_single(self, pair_index):
        self.single_mode_flags[pair_index] = True
        self.triple_mode_flags[pair_index] = False

        for offset in range(3):
            self.value_labels[pair_index * 3 + offset].grid_remove()
            self.diff_labels[pair_index * 3 + offset].grid_remove()
            self.std_labels[pair_index * 3 + offset].grid_remove()

        self.single_value_labels[pair_index].grid()
        self.single_diff_labels[pair_index].grid()
        self.single_std_labels[pair_index].grid()

    def switch_to_double(self, pair_index):
        self.single_mode_flags[pair_index] = False
        self.triple_mode_flags[pair_index] = False

        self.single_value_labels[pair_index].grid_remove()
        self.single_diff_labels[pair_index].grid_remove()
        self.single_std_labels[pair_index].grid_remove()

        for offset in range(2):
            self.value_labels[pair_index * 3 + offset].grid()
            self.diff_labels[pair_index * 3 + offset].grid()
            self.std_labels[pair_index * 3 + offset].grid()

        self.value_labels[pair_index * 3 + 2].grid_remove()
        self.diff_labels[pair_index * 3 + 2].grid_remove()
        self.std_labels[pair_index * 3 + 2].grid_remove()

    def switch_to_triple(self, pair_index):
        self.single_mode_flags[pair_index] = False
        self.triple_mode_flags[pair_index] = True

        self.single_value_labels[pair_index].grid_remove()
        self.single_diff_labels[pair_index].grid_remove()
        self.single_std_labels[pair_index].grid_remove()

        for offset in range(3):
            self.value_labels[pair_index * 3 + offset].grid()
            self.diff_labels[pair_index * 3 + offset].grid()
            self.std_labels[pair_index * 3 + offset].grid()

    def update_values(self, values, differences, stds):
        self.vals = values
        self.diffs = differences
        self.stds = stds

        precision = self.rounding_precision.get()
        value_i = 0

        for pair_index in range(len(self.pair_indices)):
            try:
                if self.single_mode_flags[pair_index]:
                    val = values[value_i]
                    diff = differences[value_i]
                    std = stds[value_i]
                    label = val["Label"]

                    self.single_value_labels[pair_index].configure(
                        text=f"{float(val['Value']):.{precision}f} {label}")
                    self.single_diff_labels[pair_index].configure(
                        text=f"Δ {float(diff['Value']):.{precision}f} {label}")
                    self.single_std_labels[pair_index].configure(
                        text=f"σ {float(std['Value']):.{precision}f} {label}")

                    value_i += 1

                else:
                    count = 3 if self.triple_mode_flags[pair_index] else 2
                    for offset in range(count):
                        val = values[value_i]
                        diff = differences[value_i]
                        std = stds[value_i]
                        label = val["Label"]

                        self.value_labels[pair_index * 3 + offset].configure(
                            text=f"{float(val['Value']):.{precision}f} {label}")
                        self.diff_labels[pair_index * 3 + offset].configure(
                            text=f"Δ {float(diff['Value']):.{precision}f} {label}")
                        self.std_labels[pair_index * 3 + offset].configure(
                            text=f"σ {float(std['Value']):.{precision}f} {label}")

                        value_i += 1

            except Exception:
                pass
