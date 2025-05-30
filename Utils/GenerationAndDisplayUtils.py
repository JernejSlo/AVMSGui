import random
import time
import traceback
from colorama import Fore, Style


class GenerationAndDisplayUtils():

    def __init__(self):
        pass

    def generate_values_no_machine(self):
        """Generate values one by one with display updating gradually."""

        if not self.running:
            return

        total_values = len(self.upper_panel.value_display.labels_values["references"])
        current_values = []
        difference_values = []
        std_values = []

        for index in range(total_values):
            if self.interrupt("Generation interrupted."):
                return

            try:
                unit = self.upper_panel.value_display.labels_values["units"][index]
                reference = self.upper_panel.value_display.labels_values["references"][index]
            except IndexError:
                unit = "mV"
                reference = 0

            if self.sidebar.selected_mode in ("DCV", "ACV"):
                unit = unit[:-1] + "V"
            elif self.sidebar.selected_mode in ("DCI", "ACI"):
                unit = unit[:-1] + "A"
            if index == 4 and self.selected_mode == "RES" and not self.prompt_shown:
                self.prompt_shown = True
                self.running = False
                self.after(100, self.show_pause_popup)
            new_value = round(random.uniform(0, 1000000000), 2) / 1000000
            difference = round(random.uniform(-1000, 1000), 2) / 1000
            std = round(random.uniform(0.01, 0.3), 3)

            current_values.append({"Value": new_value, "Label": unit})
            difference_values.append({"Value": difference, "Label": unit})
            std_values.append({"Value": std, "Label": unit})

            self.upper_panel.value_display.labels_values["diffMeas"][index] = difference

            self.terminal.log(
                f"Index {index} - Simulated {self.sidebar.selected_mode}: {new_value} {unit}, Δ = {difference} {unit}, σ = {std} "
                f"(ref: {reference} {unit})"
            )

            self.log_measurement(
                calibration_id=self.current_calibration_id,
                set_value=reference,
                calculated_value=new_value,
                ref_set_diff=difference,
                std=std,
                unit = unit,
                frequency=None
            )

            self.upper_panel.value_display.update_values(current_values, difference_values, std_values)
            self.update_idletasks()

            # Only simulate linear refs if mode is DCV or ACV
            if self.selected_mode in ["DCV", "ACV"]:
                simulated_refs = [i for i in range(1, 6)]
                simulated_meas = [round(r + random.uniform(-0.1, 0.1), 5) for r in simulated_refs]
                simulated_diffs = [round(m - r, 5) for m, r in zip(simulated_meas, simulated_refs)]
                simulated_stds = [round(random.uniform(0.001, 0.01), 5) for _ in simulated_refs]
                simulated_units = [unit] * len(simulated_refs)

                for i in range(len(simulated_refs)):
                    self.log_linear_refs(
                        calibration_id=self.current_calibration_id,
                        set_value=simulated_refs[i],
                        calculated_value=simulated_meas[i],
                        ref_set_diff=simulated_diffs[i],
                        std=simulated_stds[i],
                        unit=simulated_units[i]
                    )

            time.sleep(0.1)

            if self.interrupt("Generation interrupted."):
                return



        self.stop_action()

    def interrupt(self,message):
        if not self.running:
            self.terminal.log(message)
            return True

    def generate_values_no_machine(self):
        """Generate values one by one with display updating gradually."""

        if not self.running:
            return

        total_values = len(self.upper_panel.value_display.labels_values["references"])
        current_values = []
        difference_values = []
        std_values = []

        for index in range(total_values):
            if self.interrupt("Generation interrupted."):
                return

            try:
                unit = self.upper_panel.value_display.labels_values["units"][index]
                reference = self.upper_panel.value_display.labels_values["references"][index]
            except IndexError:
                unit = "mV"
                reference = 0

            if self.sidebar.selected_mode in ("DCV", "ACV"):
                unit = unit[:-1] + "V"
            elif self.sidebar.selected_mode in ("DCI", "ACI"):
                unit = unit[:-1] + "A"
            if index == 4 and self.selected_mode == "RES" and not self.prompt_shown:
                self.prompt_shown = True
                self.running = False
                self.after(100, self.show_pause_popup)
            new_value = round(random.uniform(0, 1000000000), 2) / 1000000
            difference = round(random.uniform(-1000, 1000), 2) / 1000
            std = round(random.uniform(0.01, 0.3), 3)

            current_values.append({"Value": new_value, "Label": unit})
            difference_values.append({"Value": difference, "Label": unit})
            std_values.append({"Value": std, "Label": unit})

            self.upper_panel.value_display.labels_values["diffMeas"][index] = difference

            self.terminal.log(
                f"Index {index} - Simulated {self.sidebar.selected_mode}: {new_value} {unit}, Δ = {difference} {unit}, σ = {std} "
                f"(ref: {reference} {unit})"
            )

            self.log_measurement(
                calibration_id=self.current_calibration_id,
                set_value=reference,
                calculated_value=new_value,
                ref_set_diff=difference,
                std=std,
                unit=unit,
                frequency=None
            )

            self.upper_panel.value_display.update_values(current_values, difference_values, std_values)
            self.update_idletasks()

            # Only simulate linear refs if mode is DCV or ACV
            if self.selected_mode in ["DCV", "ACV"]:
                simulated_refs = [i for i in range(1, 6)]
                simulated_meas = [round(r + random.uniform(-0.1, 0.1), 5) for r in simulated_refs]
                simulated_diffs = [round(m - r, 5) for m, r in zip(simulated_meas, simulated_refs)]
                simulated_stds = [round(random.uniform(0.001, 0.01), 5) for _ in simulated_refs]
                simulated_units = [unit] * len(simulated_refs)

                for i in range(len(simulated_refs)):
                    self.log_linear_refs(
                        calibration_id=self.current_calibration_id,
                        set_value=simulated_refs[i],
                        calculated_value=simulated_meas[i],
                        ref_set_diff=simulated_diffs[i],
                        std=simulated_stds[i],
                        unit=simulated_units[i]
                    )

            time.sleep(0.1)

            if self.interrupt("Generation interrupted."):
                return

        self.stop_action()
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
        self.log_all()

        if self.selected_mode in ["ACV", "DCV"]:
            graph_values = []
            for i in range(len(self.measParameters["linearRefs"])):
                lref = self.measParameters["linearRefs"][i]
                lmeas = self.measParameters["linearMeas"][i]
                unit = self.measParameters["linearUnits"][i]
                graph_values.append(
                    {"Value": lmeas, "Label": unit, "Step": lref}
                )

            self.graph.update_data(graph_values)

        self.running = False
