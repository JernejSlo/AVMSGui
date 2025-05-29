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

            new_value = round(random.uniform(0, 1000000000), 2) / 1000000
            difference = round(random.uniform(-1000, 1000), 2) / 1000
            std_values = round(random.uniform(-1000, 1000), 2) / 1000
            current_values.append({"Value": new_value, "Label": unit})
            difference_values.append({"Value": difference, "Label": unit})

            self.upper_panel.value_display.labels_values["diffMeas"][index] = difference

            self.terminal.log(
                f"Index {index} - Simulated {self.sidebar.selected_mode}: {new_value} {unit}, Δ = {difference} {unit} "
                f"(ref: {reference} {unit})"
            )

            self.log_measurement(
                calibration_id=self.current_calibration_id,
                set_value=reference,
                calculated_value=new_value,
                ref_set_diff=difference,
                std=random.uniform(0.1, 0.5),
                frequency=None
            )

            self.upper_panel.value_display.update_values(current_values, difference_values,std_values)
            time.sleep(0.1)

        if self.interrupt("Generation interrupted."):
            return

            if self.graph_enabled:
                graph_values = [{"Value": random.uniform(0, 10), "Label": "V", "Step": len(self.graph.time_values) }]
                self.graph.update_data(graph_values)

        if self.selected_mode == "2Ω" and not self.prompt_shown:
            self.prompt_shown = True
            self.running = False
            self.after(100, self.show_pause_popup)

    def interrupt(self,message):
        if not self.running:
            self.terminal.log(message)
            return True

    def log_all(self):
        self.measParameters = {
            "numOfMeas": 5,
            "references": [0, 100, -100, 1, -1, 10, -10, 100, -100, 1000, -1000],
            "range": [0.1, 0.1, 0.1, 1, 1, 10, 10, 100, 100, 1000, 1000],
            "units": ["mV", "mV", "mV", "V", "V", "V", "V", "V", "V", "V", "V"],
            "measurements": [None, None, None, None, None, None, None, None, None, None, None],
            "frequencies": ["100 Hz", "1 kHz", "10 kHz"],
            "diffMeas": [None, None, None, None, None, None, None, None, None, None, None],
            "stdVars": [None, None, None, None, None, None, None, None, None, None, None],
            "linearRefs": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "linearMeas": [None, None, None, None, None, None, None, None, None, None],
            "diffLinearMeas": [None, None, None, None, None, None, None, None, None, None],
            "linearStdVars": [None, None, None, None, None, None, None, None, None, None],
            "measType": "",
            "dirType": ""
        }
        meas = self.measParameters
        for i in range(len(meas["linearRefs"])):
            freq = meas["frequencies"][i]
            new_value = meas["measurements"][i]
            stdVar = meas["stdVars"][i]
            diffMeas = meas["diffMeas"][i]
            ref = meas["references"][i]
            self.log_measurement(
                calibration_id=self.current_calibration_id,
                set_value=ref,
                calculated_value=new_value,
                ref_set_diff=diffMeas,
                std=stdVar,
                frequency=None
            )

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

        if self.graph_enabled:
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
