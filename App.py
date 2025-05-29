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
from Utils.GenerationAndDisplayUtils import GenerationAndDisplayUtils
from Utils.color_theme import COLORS

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk,CalibrationUtils,GenerationAndDisplayUtils):
    def __init__(self):

        self.skip_fake_version = True
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
                               self.show_database_overview,self.clear_values)
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

        self.upper_panel.content_box.grid_remove()

    def update_display_label(self, mode):
        j = 0
        for i, header in enumerate(self.upper_panel.value_display.headers):
            references = self.measParameters["references"]
            units = self.measParameters["units"]

            if j >= len(references):
                header.grid_remove()
                for z in range(j,len(self.upper_panel.value_display.value_labels)):
                    self.upper_panel.value_display.value_labels[z].grid_remove()
                    self.upper_panel.value_display.diff_labels[z].grid_remove()
                continue
            else:
                header.grid()
                for z in range(j, len(self.upper_panel.value_display.value_labels)):
                    self.upper_panel.value_display.value_labels[z].grid()
                    self.upper_panel.value_display.diff_labels[z].grid()

            print(references)
            print(mode)
            print(len(self.upper_panel.value_display.headers))
            ref = references[j]
            r1 = abs(references[j])
            if j >= len(references)-1:
                r2 = "13412412341234132"
            else:
                r2 = abs(references[j+1])
            text_prefix = "Measured at"

            is_pair = True if r1==r2 else False
            if r1 == 0: is_pair = False
            if is_pair:
                value_text = f"{text_prefix} ±{abs(ref)}"
                print("Switching to double")
                self.switch_to_double(i)
            else:
                value_text = f"{text_prefix} {ref}"
                print("switching to single")
                self.switch_to_single(i,self.title)
            unit = units[j]
            header.configure(text=f"{value_text} {unit}")
            j = j+2 if is_pair else j+1

    def switch_to_double(self, pair_index):
        """Switch a single value display back to double (±) format"""
        i, neg_index = self.upper_panel.value_display.pair_indices[pair_index]
        unit = self.upper_panel.value_display.labels_values["units"][i]
        ref = self.upper_panel.value_display.labels_values["references"][i]
        header = self.upper_panel.value_display.headers[pair_index]

        # Update header
        header.configure(text=f"Measured at ±{abs(ref)} {unit}")

        # Positive value and diff labels
        val_pos = self.upper_panel.value_display.value_labels[pair_index * 2]
        diff_pos = self.upper_panel.value_display.diff_labels[pair_index * 2]

        val_pos.grid_configure(columnspan=1, column=(pair_index % 3) * 2)
        diff_pos.grid_configure(columnspan=1, column=(pair_index % 3) * 2)

        # Restore negative side
        val_neg = self.upper_panel.value_display.value_labels[pair_index * 2 + 1]
        diff_neg = self.upper_panel.value_display.diff_labels[pair_index * 2 + 1]

        val_neg.grid()  # Re-show
        diff_neg.grid()

        val_neg.grid_configure(column=(pair_index % 3) * 2 + 1)
        diff_neg.grid_configure(column=(pair_index % 3) * 2 + 1)

    def switch_to_single(self, pair_index, mode):
        """Transform a value pair into a single centered display"""
        i, neg_index = self.upper_panel.value_display.pair_indices[pair_index]
        unit = self.upper_panel.value_display.labels_values["units"][i]
        ref = self.upper_panel.value_display.labels_values["references"][i]
        header = self.upper_panel.value_display.headers[pair_index]

        # Update header
        header.configure(text=f"Measured at {ref} {unit}")

        # Center value and diff labels across both columns
        val_label = self.upper_panel.value_display.value_labels[pair_index * 2]
        diff_label = self.upper_panel.value_display.diff_labels[pair_index * 2]

        val_label.grid_configure(columnspan=2)
        diff_label.grid_configure(columnspan=2)

        # Hide the "negative" label if it exists
        if pair_index * 2 + 1 < len(self.upper_panel.value_display.value_labels):
            self.upper_panel.value_display.value_labels[pair_index * 2 + 1].grid_remove()
            self.upper_panel.value_display.diff_labels[pair_index * 2 + 1].grid_remove()

    def clear_values(self):
        """Clear all displayed measurement and difference values."""
        for val_label in self.upper_panel.value_display.value_labels:
            val_label.configure(text="--")

        for diff_label in self.upper_panel.value_display.diff_labels:
            diff_label.configure(text="Δ --")

        self.vals = []
        self.diffs = []
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

        self.changeMeasParam(mode)

        # Show the ValueDisplay when a mode is selected
        if not self.upper_panel.value_display.winfo_ismapped():
            self.upper_panel.content_box.grid(row=0, column=0)

        # Enable graph only for certain modes
        self.graph_enabled = mode in ["2Ω", "FREQ.", "PERIOD"]
        if self.graph_enabled:
            self.show_graph()
        else:
            self.show_terminal()

        self.update_display_label(mode)

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
