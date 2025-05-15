import tkinter as tk
import customtkinter
import gpib_ctypes
import pyvisa
import random
import threading
import time
import traceback
from colorama import init, Fore, Style
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation

from Components.ControlButtons import ControlButtons
from Components.DatabaseOverview import DatabaseOverview
from Components.Graph import GraphComponent
from Components.OutputTerminal import TerminalOutput
from Components.Sidebar import Sidebar
from Components.UpperPanel import UpperPanel
from Components.ValueDisplay import ValueDisplay
from Components.BottomTabBar import BottomTabBar

from Utils.CalibrationUtils import CalibrationUtils
from Utils.color_theme import COLORS

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk,CalibrationUtils):
    def __init__(self):

        self.skip_fake_version = False

        super().__init__()
        self.configure(fg_color=COLORS["backgroundLight"], bg_color=COLORS["backgroundLight"])

        self.default_color = COLORS["backgroundLight"]
        self.active_color = COLORS["backgroundDark"]
        self.hover_color = COLORS["hover"]
        self.text_color = COLORS["lg_text"]

        self.title("kalibrator.py")
        self.geometry(f"{1100}x{700}")

        self.running = False
        self.graph_enabled = False

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=2)
        self.grid_rowconfigure(2, weight=1)

        # Paned container for resizable layout
        self.paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6, bg=self.default_color, showhandle=True)
        self.paned.grid(row=0, column=0, rowspan=3, columnspan=2, sticky="nsew")

        # === Sidebar container (inside paned window) ===
        self.sidebar_container = customtkinter.CTkFrame(self.paned, corner_radius=0)
        self.sidebar = Sidebar(self.sidebar_container, self.update_title, self.change_scaling,
                               self.show_database_overview)
        self.sidebar.pack(fill="both", expand=True)
        self.paned.add(self.sidebar_container, minsize=140)

        # === Main Frame Split Vertically ===

        self.main_frame = customtkinter.CTkFrame(self.paned, fg_color=self.default_color,bg_color=self.default_color)
        self.paned.add(self.main_frame)

        # === Create a vertical PanedWindow inside main_frame ===
        self.vertical_pane = tk.PanedWindow(self.main_frame, orient=tk.VERTICAL, sashwidth=6, bg=self.default_color,
                                            showhandle=True,background=self.default_color)
        self.vertical_pane.pack(fill="both", expand=True)

        # === Upper and lower panels ===

        self.upper_panel = UpperPanel(self.vertical_pane,self.running,self.start_action, self.stop_action)

        self.lower_panel = customtkinter.CTkFrame(self.vertical_pane, fg_color="transparent", height=100)

        self.vertical_pane.add(self.upper_panel)
        self.vertical_pane.add(self.lower_panel)

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.paned.add(self.main_frame, minsize=400)

        # === Inside Lower Panel (Graph + Terminal toggle) ===
        self.graph = GraphComponent(self.lower_panel)
        self.terminal = TerminalOutput(self.lower_panel)

        self.graph.pack_forget()
        self.terminal.grid(row=0, column=0, sticky="nsew")

        self.lower_panel.grid_rowconfigure(0, weight=1)
        self.lower_panel.grid_columnconfigure(0, weight=1)

        # === Bottom Tab Bar ===
        self.bottom_bar = BottomTabBar(self, self.show_terminal, self.show_graph)
        self.bottom_bar.grid(row=3, column=0, columnspan=2, sticky="ew")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)


        CalibrationUtils.__init__(self,"./Utils/calibration.db")

        self.database_overview = DatabaseOverview(self, self.show_calibration_view)
        self.database_overview.grid(row=0, column=1, rowspan=3, padx=20, pady=20, sticky="nsew")
        self.database_overview.grid_remove()


        self.graph.grid_remove()

        self.selected_mode = ""
        self.show_terminal()

        self.pause_event = threading.Event()
        self.prompt_shown = False

    def show_terminal(self):
        self.graph.pack_forget()
        self.terminal.pack(fill="both", expand=True)
        self.bottom_bar.highlight_terminal()

    def show_graph(self):
        self.terminal.pack_forget()
        self.graph.pack(fill="both", expand=True)
        self.bottom_bar.highlight_graph()

        self.graph_enabled = True

    def show_calibration_view(self):
        self.database_overview.grid_remove()
        self.show_all_pages()

    def on_closing(self):
        """ Cleanup when closing the app """
        if self.conn:
            self.close()
        self.destroy()

    def hide_all_pages(self):
        """ Switch to Database Overview screen """

        # Hide calibration components
        self.bottom_bar.grid_remove()
        self.paned.grid_remove()
    def show_all_pages(self):
        """ Switch to Database Overview screen """

        # Hide calibration components
        self.bottom_bar.grid()
        self.paned.grid()

    def show_database_overview(self):
        self.hide_all_pages()
        self.database_overview.grid()

    def update_title(self, mode):
        self.show_all_pages()
        """ Update title and show graph if needed """
        self.terminal.log(f"Mode selected: {mode}")
        self.selected_mode = mode

        # Show the ValueDisplay when a mode is selected
        if not self.upper_panel.value_display.winfo_ismapped():
            self.upper_panel.value_display.grid(row=0, column=0, sticky="n")

        # Enable graph only for certain modes
        self.graph_enabled = mode in ["2Ω", "FREQ.", "PERIOD"]
        if self.graph_enabled:
            self.show_graph()
        else:
            self.show_terminal()

    def start_action(self):
        """ Start generating random values """
        if not self.running:
            self.running = True

            # Create a new calibration in database
            self.current_calibration_id = self.log_new_calibration(self.selected_mode)
            self.terminal.log(f"Started new calibration session: ID {self.current_calibration_id}")

            threading.Thread(target=self.get_calibration_values, daemon=True).start()
            self.terminal.log("Generating values...")
            self.upper_panel.controls.stop_button.configure(state="enabled",fg_color="red")
        self.upper_panel.controls.start_button.configure(state="disabled",fg_color="#B0B0B0")

    def stop_action(self):
        """ Stop generating values """
        self.running = False
        self.terminal.log("Stopped.")
        self.database_overview.populate_dropdown()
        self.upper_panel.controls.stop_button.configure(state="disabled",fg_color="#B0B0B0")
        self.upper_panel.controls.start_button.configure(state="enabled",fg_color="steel blue")

    def get_calibration_values(self):
        """ Generate one new value per second, updating values and differences with terminal logging """


        while self.running:
            # Get unit and reference for this index

            # Log before
            #self.terminal.log(f"Executing: Measure {self.sidebar.selected_mode} at index {index} (ref: {reference} {unit})")
            try:
                self.calibrate()
            except Exception as e:

                if not self.skip_fake_version:
                    print(Fore.RED + Style.BRIGHT + "Exception type: " + str(type(e)))
                    print(Fore.YELLOW + Style.BRIGHT + "Exception message: " + str(e))
                    print(Fore.CYAN + Style.BRIGHT + "Traceback:")
                    traceback_lines = traceback.format_exception(type(e), e, e.__traceback__)
                    for line in traceback_lines:
                        print(Fore.CYAN + line, end='')  # 'end' avoids double newlines

                if not self.skip_fake_version:
                    print("Returning to fake version.")
                    self.get_calibration_values = self.generate_values_no_machine
                    self.generate_values_no_machine()
                else:
                    raise e
                return
            # Generate new value
            if self.graph_enabled:
                graph_values = [{"Value": random.uniform(0, 10), "Label": "V"},
                                {"Value": random.uniform(0, 5), "Label": "A"},
                                {"Value": random.uniform(0, 1000), "Label": "Ω"}]

                self.graph.update_data(graph_values)

            # Log result
            #self.terminal.log(f"Updated index {index}: {new_value} {unit}, Δ = {difference} {unit}")
            time.sleep(1)
            self.running = False

    def generate_values_no_machine(self):
        """ Generate one new value per second, updating values and differences with terminal logging """
        total_values = len(self.upper_panel.value_display.value_labels)

        current_values = [{"Value": "--", "Label": "mV"} for _ in range(total_values)]
        difference_values = [{"Value": "--", "Label": "mV"} for _ in range(total_values)]
        index = 0

        while self.running:
            # Get unit and reference for this index
            try:
                unit = self.upper_panel.value_display.labels_values["units"][index]
                reference = self.upper_panel.value_display.labels_values["references"][index]
            except IndexError:
                unit = "mV"
                reference = 0

            # Log before
            self.terminal.log(f"Executing: Measure {self.sidebar.selected_mode} at index {index} (ref: {reference} {unit})")

            # Generate new value
            new_value = round(random.uniform(0, 1000000000), 2)/1000000
            current_values[index] = {"Value": new_value, "Label": unit}
            # Compute difference and update
            difference = round(random.uniform(-1000, 1000), 2)/1000
            difference_values[index] = {"Value": difference, "Label": unit}

            self.upper_panel.value_display.labels_values["diffMeas"][index] = difference

            # Update display
            self.upper_panel.value_display.update_values(current_values, difference_values)
            self.log_measurement(
                calibration_id=self.current_calibration_id,
                set_value=reference,
                calculated_value=new_value,
                ref_set_diff=difference,
                std=random.uniform(0.1, 0.5)  # Random fake std deviation (you can improve later)
            )
            if self.graph_enabled:
                graph_values = [{"Value": random.uniform(0, 10), "Label": "V"},
                                {"Value": random.uniform(0, 5), "Label": "A"},
                                {"Value": random.uniform(0, 1000), "Label": "Ω"}]

                self.graph.update_data(graph_values)

            # Log result
            self.terminal.log(f"Updated index {index}: {new_value} {unit}, Δ = {difference} {unit}")

            index = (index + 1) % total_values
            time.sleep(1)

            # Pause after 10th value if in "2Ω" mode
            if self.selected_mode == "2Ω" and index == 2 and not self.prompt_shown:
                self.prompt_shown = True
                self.running = False
                self.after(100, self.show_pause_popup)  # Show popup in main thread
                return  # Exit loop

    def change_scaling(self, new_scaling):
        customtkinter.set_widget_scaling(int(new_scaling.replace("%", "")) / 100)

    def show_pause_popup(self):
        popup = customtkinter.CTkToplevel(self)
        popup.title("Change measurement setup")
        popup.geometry("500x150")
        popup.transient(self)
        popup.grab_set()

        label = customtkinter.CTkLabel(popup, text="To continue calibration connect with 4 leads system (switch from 2 leads to 4).\n "
                                                   "After doing so, press continue.")
        label.pack(pady=20)

        def resume():
            popup.destroy()
            self.running = True
            threading.Thread(target=self.generate_values_no_machine, daemon=True).start()

        btn = customtkinter.CTkButton(popup, text="Continue", command=resume)
        btn.pack(pady=10)


if __name__ == "__main__":
    app = App()
    app.mainloop()
