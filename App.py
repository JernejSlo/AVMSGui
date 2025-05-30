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

import screeninfo

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk,CalibrationUtils,GenerationAndDisplayUtils):
    def __init__(self):

        self.selected_mode = ""
        self.skip_fake_version = False
        super().__init__()
        self.configure(fg_color=COLORS["backgroundLight"], bg_color=COLORS["backgroundLight"])

        self.default_color = COLORS["backgroundLight"]
        self.active_color = COLORS["backgroundDark"]
        self.hover_color = COLORS["hover"]
        self.text_color = COLORS["lg_text"]

        self.title("Calibration App.py")

        screen = screeninfo.get_monitors()[0]
        #width, height = screen.width, screen.height
        #self.geometry(f"{width}x{height-300}+0+0")
        self.state('zoomed')
        self.update()
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
        self.graph = GraphComponent(self.lower_panel,self.selected_mode)
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

        self.show_terminal()

        self.pause_event = threading.Event()
        self.prompt_shown = False

        self.upper_panel.content_box.grid_remove()
        self.upper_panel.content_box.grid_remove()

        self.show_input_popup()

    def get_pairs(self):
        total_refs = len(self.measParameters["references"])
        count = 0
        i = 0
        while i < total_refs:
            r1 = abs(self.measParameters["references"][i])
            r2 = abs(self.measParameters["references"][i + 1]) if i + 1 < total_refs else None
            r3 = abs(self.measParameters["references"][i + 2]) if i + 2 < total_refs else None

            is_triple = r1 == r2 == r3
            is_pair = r1 == r2 and not is_triple

            if is_triple:
                i += 3
            elif is_pair:
                i += 2
            else:
                i += 1
            count += 1

        total_blocks = count
        return total_blocks

    def update_display_label(self, mode):
        j = 0
        total_blocks_required = self.get_pairs()  # how many are needed based on current data
        total_blocks_available = len(self.upper_panel.value_display.pair_indices)  # always 7 for now

        # Step 1: Hide all headers and all labels
        for i in range(total_blocks_available):
            self.upper_panel.value_display.headers[i].grid_remove()

            for label_list in (
                    self.upper_panel.value_display.single_value_labels,
                    self.upper_panel.value_display.single_diff_labels,
                    self.upper_panel.value_display.single_std_labels,
                    self.upper_panel.value_display.value_labels,
                    self.upper_panel.value_display.diff_labels,
                    self.upper_panel.value_display.std_labels,
            ):
                for k in range(3):
                    idx = i * 3 + k
                    if idx < len(label_list):
                        label_list[idx].grid_remove()

        # Step 2: Re-show the blocks you need
        for block_index in range(total_blocks_required):
            if j >= len(self.measParameters["references"]):
                break

            references = self.measParameters["references"]
            units = self.measParameters["units"]
            unit = units[j]
            ref = references[j]
            r1 = abs(ref)
            r2 = abs(references[j + 1]) if j + 1 < len(references) else None
            r3 = abs(references[j + 2]) if j + 2 < len(references) else None

            is_triple = (r1 == r2 == r3)
            is_pair = (r1 == r2) and not is_triple

            if is_triple:

                unique_freqs = list(dict.fromkeys(self.measParameters['frequencies']))
                freq_text = ", ".join(f"{f}" for f in unique_freqs)
                text = f"Measured at {r1} {unit} at {freq_text}"
                print(self.measParameters["units"])

                self.upper_panel.value_display.switch_to_triple(block_index)
                self.upper_panel.value_display.headers[block_index].configure(
                    text=text
                )
                self.upper_panel.value_display.headers[block_index].grid()
                j += 3
            elif is_pair:
                self.upper_panel.value_display.switch_to_double(block_index)
                self.upper_panel.value_display.headers[block_index].configure(
                    text=f"Measured at ±{r1} {unit}"
                )
                self.upper_panel.value_display.headers[block_index].grid()
                j += 2
            else:
                self.upper_panel.value_display.switch_to_single(block_index)
                self.upper_panel.value_display.headers[block_index].configure(
                    text=f"Measured at {ref} {unit}"
                )
                self.upper_panel.value_display.headers[block_index].grid()
                j += 1

    def clear_values(self):
        """Clear all displayed measurement, difference, and standard deviation values."""

        # Clear standard (multi-label) layout
        for i, label in enumerate(self.upper_panel.value_display.value_labels):
            label.configure(text="--")
        for i, label in enumerate(self.upper_panel.value_display.diff_labels):
            label.configure(text="Δ --")
        for i, label in enumerate(self.upper_panel.value_display.std_labels):
            label.configure(text="σ --")

        # Clear single layout
        for i, label in enumerate(self.upper_panel.value_display.single_value_labels):
            label.configure(text="--")
        for i, label in enumerate(self.upper_panel.value_display.single_diff_labels):
            label.configure(text="Δ --")
        for i, label in enumerate(self.upper_panel.value_display.single_std_labels):
            label.configure(text="σ --")

        # Reset stored values
        self.vals = []
        self.diffs = []
        self.stds = []

    def show_terminal(self):
        self.graph.pack_forget()
        self.terminal.pack(fill="both", expand=True)
        self.bottom_bar.highlight_terminal()

    def show_graph(self):
        if self.selected_mode in ["ACV","DCV"]:
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

        if not self.running:
            self.graph.update_mode(mode)
            self.graph.update_graph()
            self.changeMeasParam(mode)
            self.show_all_pages()
            """ Update title and show graph if needed """
            self.terminal.log(f"Mode selected: {mode}")

            if mode == "RES" and mode != self.selected_mode:
                self.show_pause_popup("HP34401A multimeter -> Fluke 5522A calibrator\n\n"
                                      "Connect ONLY (disconnect other leads)\n\n"
                                      "Sense/Ratio Ref HI -> NORMAL HI\n"
                                      "Sense/Ratio Ref LO -> NORMAL LO\n\n"
                                      "Input HI -> NORMAL HI\n"
                                      "Input LO -> NORMAL LO\n")
            if mode in ["ACI","DCI"] and self.selected_mode not in ["ACI","DCI"]:
                self.show_pause_popup("HP34401A multimeter -> Fluke 5522A calibrator\n\n"
                                      "Connect ONLY (disconnect other leads)\n\n"
                                      "Input I -> AUX HI\n"
                                      "Input LO -> AUX LO\n")
            if mode in ["ACV", "DCV","FREQ."] and self.selected_mode not in ["ACV", "DCV","FREQ."]:
                self.show_pause_popup("HP34401A multimeter -> Fluke 5522A calibrator\n\n"
                                      "Connect ONLY (disconnect other leads)\n\n"
                                      "Input HI -> NORMAL HI\n"
                                      "Input LO -> NORMAL LO\n")


            self.selected_mode = mode


            # Show the ValueDisplay when a mode is selected
            if not self.upper_panel.value_display.winfo_ismapped():
                self.upper_panel.content_box.grid(row=0, column=0)

            # Enable graph only for certain modes
            self.graph_enabled = mode in ["DCV","ACV"]
            self.show_terminal()


            self.update_display_label(mode)
            self.clear_values()

    def start_action(self):
        """ Start generating random values """
        if not self.running:
            self.clear_values()
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
        self.upper_panel.controls.stop_button.configure(state="disabled", fg_color="#B0B0B0")
        self.upper_panel.controls.start_button.configure(state="enabled", fg_color="steel blue")

    def change_scaling(self, new_scaling):
        customtkinter.set_widget_scaling(int(new_scaling.replace("%", "")) / 100)

    def show_input_popup(self, message="Enter addresses for HP 34401A and FLUKE 5522A or use default:", show_default=True):
        self.update_idletasks()
        m_x = self.winfo_width() / 2
        m_y = self.winfo_height() / 2

        popup = customtkinter.CTkToplevel(self)
        popup.title("Enter Addresses")
        popup.geometry(f"600x300+{int(m_x - 250)}+{int(m_y - 150)}")
        popup.transient(self)
        popup.grab_set()

        label = customtkinter.CTkLabel(popup, text=message, text_color="white",)
        label.pack(pady=(20, 10))

        entry1 = customtkinter.CTkEntry(popup, placeholder_text="HP 34401A address")
        entry1.pack(pady=10)

        entry2 = customtkinter.CTkEntry(popup, placeholder_text="FLUKE 5522A address")
        entry2.pack(pady=10)

        def confirm_inputs():
            self.custom_address_chosen = True
            hp_val = entry1.get().strip()
            fluke_val = entry2.get().strip()

            valid = True

            if hp_val:
                if hp_val.isdigit():
                    self.hpadress = f"GPIB0::{hp_val}::INSTR"
                else:
                    entry1.configure(placeholder_text="Enter a number!", text="")
                    valid = False

            if fluke_val:
                if fluke_val.isdigit():
                    self.flukeadress = f"GPIB0::{fluke_val}::INSTR"
                else:
                    entry2.configure(placeholder_text="Enter a number!", text="")
                    valid = False

            if valid:
                popup.destroy()

        btn_confirm = customtkinter.CTkButton(popup, text="Confirm", command=confirm_inputs)
        btn_confirm.pack(pady=10)

        if show_default:
            def use_default():
                self.hpadress = 22
                self.flukeadress = 4
                popup.destroy()

            btn_default = customtkinter.CTkButton(popup, text="Use Default", command=use_default)
            btn_default.pack(pady=(0, 10))

    def show_pause_popup(self,message="To continue calibration connect with 4 leads system (switch from 2 leads to 4).\n "
                                                     ):
        self.update_idletasks()
        m_x = self.winfo_width() / 2
        m_y = self.winfo_height() / 2
        print(m_x,m_y)
        popup = customtkinter.CTkToplevel(self)
        popup.title("Change measurement setup")
        popup.geometry(f"500x250+{int(m_x - 250)}+{int(m_y - 125)}")
        popup.transient(self)
        popup.grab_set()

        label = customtkinter.CTkLabel(popup, text=f"{message}\n After doing so, press continue.")
        label.pack(pady=20)

        def resume():
            popup.destroy()
            threading.Thread(target=self.generate_values_no_machine, daemon=True).start()

        btn = customtkinter.CTkButton(popup, text="Continue", command=resume)
        btn.pack(pady=10)


if __name__ == "__main__":
    app = App()
    app.mainloop()
