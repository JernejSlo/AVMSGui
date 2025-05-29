import random
import traceback
from colorama import Fore, Style


class GenerationAndDisplayUtils():

    def __init__(self):
        pass

    def generate_values_no_machine(self):
        """Generate all values in one step, update display and log for simulated mode"""
        references = self.upper_panel.value_display.labels_values["references"]
        units = self.upper_panel.value_display.labels_values["units"]

        current_values = []
        difference_values = []

        j = 0
        pair_index = 0
        total_pairs = len(self.upper_panel.value_display.pair_indices)

        while j < len(references) and pair_index < total_pairs:
            try:
                ref = references[j]
                unit = units[j]
            except IndexError:
                ref = 0
                unit = "mV"

            # Adjust unit based on mode
            if self.sidebar.selected_mode in ("DCV", "ACV"):
                unit = unit[:-1] + "V"
            elif self.sidebar.selected_mode in ("DCI", "ACI"):
                unit = unit[:-1] + "A"

            r1 = abs(ref)
            r2 = abs(references[j + 1]) if j + 1 < len(references) else None
            is_pair = r1 == r2 and r1 != 0

            if is_pair:
                # Generate 2 values (positive + negative)
                for _ in range(2):
                    new_value = round(random.uniform(0, 1000000000), 2) / 1000000
                    difference = round(random.uniform(-1000, 1000), 2) / 1000

                    current_values.append({"Value": new_value, "Label": unit})
                    difference_values.append({"Value": difference, "Label": unit})

                    self.upper_panel.value_display.labels_values["diffMeas"][j] = difference

                    self.terminal.log(
                        f"Index {j} - Simulated {self.sidebar.selected_mode}: {new_value} {unit}, Δ = {difference} {unit} (ref: {references[j]} {unit})"
                    )

                    self.log_measurement(
                        calibration_id=self.current_calibration_id,
                        set_value=references[j],
                        calculated_value=new_value,
                        ref_set_diff=difference,
                        std=random.uniform(0.1, 0.5)
                    )

                    j += 1
            else:
                # Generate 1 value (single)
                new_value = round(random.uniform(0, 1000000000), 2) / 1000000
                difference = round(random.uniform(-1000, 1000), 2) / 1000

                current_values.append({"Value": new_value, "Label": unit})
                difference_values.append({"Value": difference, "Label": unit})

                self.upper_panel.value_display.labels_values["diffMeas"][j] = difference

                self.terminal.log(
                    f"Index {j} - Simulated {self.sidebar.selected_mode}: {new_value} {unit}, Δ = {difference} {unit} (ref: {ref} {unit})"
                )

                self.log_measurement(
                    calibration_id=self.current_calibration_id,
                    set_value=ref,
                    calculated_value=new_value,
                    ref_set_diff=difference,
                    std=random.uniform(0.1, 0.5)
                )

                j += 1

            pair_index += 1

        # Update the UI
        self.upper_panel.value_display.update_values(current_values, difference_values)

        if self.graph_enabled:
            graph_values = [{"Value": random.uniform(0, 10), "Label": "V"},
                            {"Value": random.uniform(0, 5), "Label": "A"},
                            {"Value": random.uniform(0, 1000), "Label": "Ω"}]
            self.graph.update_data(graph_values)

        # Show pause if in 2Ω mode
        if self.selected_mode == "2Ω" and not self.prompt_shown:
            self.prompt_shown = True
            self.running = False
            self.after(100, self.show_pause_popup)

    def get_calibration_values(self):
        """Run calibration once, log and update values. Falls back to fake values on error."""
        try:
            self.calibrate()  # Should generate all values in one go
        except Exception as e:
            if not self.skip_fake_version:
                print(Fore.RED + Style.BRIGHT + "Exception type: " + str(type(e)))
                print(Fore.YELLOW + Style.BRIGHT + "Exception message: " + str(e))
                print(Fore.CYAN + Style.BRIGHT + "Traceback:")
                traceback_lines = traceback.format_exception(type(e), e, e.__traceback__)
                for line in traceback_lines:
                    print(Fore.CYAN + line, end='')

                print("Returning to fake version.")
                self.get_calibration_values = self.generate_values_no_machine
                self.generate_values_no_machine()
            else:
                raise e
            return

        # Simulate graph update (fake example)
        if self.graph_enabled:
            graph_values = [
                {"Value": random.uniform(0, 10), "Label": "V"},
                {"Value": random.uniform(0, 5), "Label": "A"},
                {"Value": random.uniform(0, 1000), "Label": "Ω"}
            ]
            self.graph.update_data(graph_values)

        self.running = False
