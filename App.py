import tkinter
import customtkinter
import pyvisa
import random
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation

from Components.ControlButtons import ControlButtons
from Components.Graph import GraphComponent
from Components.OutputTerminal import TerminalOutput
from Components.Sidebar import Sidebar
from Components.ValueDisplay import ValueDisplay

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("kalibrator.py")
        self.geometry(f"{1100}x{700}")

        self.running = False
        self.graph_enabled = False

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=2)
        self.grid_rowconfigure(2, weight=1)

        # UI Components
        self.sidebar = Sidebar(self, self.update_title, self.change_scaling)
        self.terminal = TerminalOutput(self)
        self.value_display = ValueDisplay(self)
        self.graph = GraphComponent(self)
        self.controls = ControlButtons(self, self.start_action, self.stop_action)



        self.graph.grid_remove()

    def update_title(self, mode):
        """ Update title and show graph if needed """
        self.terminal.log(f"Mode selected: {mode}")
        self.selected_mode = mode
        self.graph_enabled = mode in ["2Ω", "FREQ.", "PERIOD"]

        if self.graph_enabled:
            self.graph.grid()
        else:
            self.graph.grid_remove()

    def start_action(self):
        """ Start generating random values """
        if not self.running:
            self.running = True
            threading.Thread(target=self.generate_values, daemon=True).start()
            self.terminal.log("Generating values...")

    def stop_action(self):
        """ Stop generating values """
        self.running = False
        self.terminal.log("Stopped.")

    def generate_values(self):
        """ Generate one new value per second, updating values and differences with terminal logging """
        total_values = len(self.value_display.value_labels)

        current_values = [{"Value": "--", "Label": "mV"} for _ in range(total_values)]
        difference_values = [{"Value": "--", "Label": "mV"} for _ in range(total_values)]
        index = 0

        while self.running:
            # Get unit and reference for this index
            try:
                unit = self.value_display.labels_values["units"][index]
                reference = self.value_display.labels_values["references"][index]
            except IndexError:
                unit = "mV"
                reference = 0

            # Log before
            self.terminal.log(f"Executing: Measure {self.sidebar.selected_mode} at index {index} (ref: {reference} {unit})")

            # Generate new value
            new_value = round(random.uniform(0, 1000), 2)
            current_values[index] = {"Value": new_value, "Label": unit}
            # Compute difference and update
            difference = round(random.uniform(-1000, 1000), 2)/1000
            difference_values[index] = {"Value": difference, "Label": unit}

            self.value_display.labels_values["differences"][index] = difference

            # Update display
            self.value_display.update_values(current_values, difference_values)

            if self.graph_enabled:
                graph_values = [{"Value": random.uniform(0, 10), "Label": "V"},
                                {"Value": random.uniform(0, 5), "Label": "A"},
                                {"Value": random.uniform(0, 1000), "Label": "Ω"}]

                self.graph.update_data(graph_values)

            # Log result
            self.terminal.log(f"Updated index {index}: {new_value} {unit}, Δ = {difference} {unit}")

            index = (index + 1) % total_values
            time.sleep(1)

    def change_scaling(self, new_scaling):
        customtkinter.set_widget_scaling(int(new_scaling.replace("%", "")) / 100)


if __name__ == "__main__":
    app = App()
    app.mainloop()
