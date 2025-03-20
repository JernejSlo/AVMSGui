import tkinter
import tkinter.messagebox
import customtkinter
import pyvisa
import random
import threading
import time

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("kalibrator.py")
        self.geometry(f"{1100}x{580}")

        self.running = False  # Control flag for generating values
        # Configure grid layout (3 columns, 3 rows)
        self.grid_columnconfigure(0, weight=0)  # Sidebar (fixed size)
        self.grid_columnconfigure(1, weight=1)  # Expanding main section
        self.grid_rowconfigure(0, weight=1)  # Terminal section
        self.grid_rowconfigure(1, weight=2)  # Value displays
        self.grid_rowconfigure(2, weight=1)  # Start/Stop buttons

        # Sidebar (Left - Buttons & Options)
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=3, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="CustomTkinter",
                                                 font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        button_labels = ["DCV", "DCI", "ACV", "ACI", "2Ω", "FREQ.", "PERIOD"]
        self.selected_mode = "DCV"  # Default selection

        for i, label in enumerate(button_labels):
            btn = customtkinter.CTkButton(self.sidebar_frame, text=label, command=lambda l=label: self.update_title(l))
            btn.grid(row=i + 1, column=0, padx=20, pady=10)

        self.appearance_mode_optionsmenu = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                                       values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionsmenu.grid(row=8, column=0, padx=20, pady=(10, 10))

        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=9, column=0, padx=20, pady=(10, 0))

        self.scaling_optionsmenu = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                               values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionsmenu.grid(row=10, column=0, padx=20, pady=(10, 20))

        # Title Label (Top)
        self.title_label = customtkinter.CTkLabel(self, text=self.selected_mode, font=customtkinter.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=1, padx=20, pady=10, sticky="n")

        # Terminal/Log Output (Row 0, Column 1)
        self.terminal_frame = customtkinter.CTkFrame(self, height=120, corner_radius=0, fg_color="transparent")
        self.terminal_frame.grid(row=0, column=1, rowspan=1, padx=(20, 20), pady=(50, 10), sticky="nsew")

        self.terminal_label = customtkinter.CTkLabel(self.terminal_frame, text="Output", anchor="w", justify="left")
        self.terminal_label.grid(row=0, column=0, padx=24, pady=(10, 0), sticky="w")

        self.textbox = customtkinter.CTkTextbox(self.terminal_frame, width=900, height=80)
        self.textbox.grid(row=1, column=0, padx=(0, 0), pady=(2, 10), sticky="nsew")

        # Value Display Section (Row 1, Column 1) - Centered values with labels above
        self.values_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.values_frame.grid(row=1, column=1, padx=(20, 20), pady=(10, 10), sticky="nsew")
        self.values_frame.grid_columnconfigure((0, 1, 2), weight=1)  # Center items

        # Labels above values
        self.label_1 = customtkinter.CTkLabel(self.values_frame, text="Voltage", font=customtkinter.CTkFont(size=16))
        self.label_1.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="n")

        self.label_2 = customtkinter.CTkLabel(self.values_frame, text="Current", font=customtkinter.CTkFont(size=16))
        self.label_2.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="n")

        self.label_3 = customtkinter.CTkLabel(self.values_frame, text="Resistance", font=customtkinter.CTkFont(size=16))
        self.label_3.grid(row=0, column=2, padx=10, pady=(10, 0), sticky="n")

        # Value displays
        self.value_display_1 = customtkinter.CTkLabel(self.values_frame, text="--", font=customtkinter.CTkFont(size=18))
        self.value_display_1.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.value_display_2 = customtkinter.CTkLabel(self.values_frame, text="--", font=customtkinter.CTkFont(size=18))
        self.value_display_2.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.value_display_3 = customtkinter.CTkLabel(self.values_frame, text="--", font=customtkinter.CTkFont(size=18))
        self.value_display_3.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

        # Start & Stop Buttons (Row 2, Column 1)
        self.buttons_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.grid(row=2, column=1, padx=(20, 20), pady=(10, 20), sticky="nsew")
        self.buttons_frame.grid_columnconfigure((0, 1), weight=1)  # Center buttons

        self.start_button = customtkinter.CTkButton(self.buttons_frame, text="Start", command=self.start_action)
        self.start_button.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        self.stop_button = customtkinter.CTkButton(self.buttons_frame, text="Stop", command=self.stop_action, fg_color="red")
        self.stop_button.grid(row=0, column=1, padx=20, pady=10, sticky="ew")

        # Set default values
        self.textbox.insert("0.0", "Ready...\n")

        # Set default values
        self.appearance_mode_optionsmenu.set("Dark")
        self.scaling_optionsmenu.set("100%")

    def update_title(self, mode):
        """ Update title text based on selected mode """
        self.selected_mode = mode
        self.title_label.configure(text=mode)

    def start_action(self):
        """ Start generating random values every second """
        if not self.running:
            self.running = True
            self.textbox.insert("end", "Generating values...\n")
            self.textbox.yview_moveto(1)  # Scroll to the latest output
            threading.Thread(target=self.generate_values, daemon=True).start()

    def stop_action(self):
        """ Stop generating values """
        self.running = False
        self.textbox.insert("end", "Stopped.\n")
        self.textbox.yview_moveto(1)

    def generate_values(self):
        """ Generate random values and update labels every second """
        while self.running:
            value_1 = round(random.uniform(0, 10), 2)  # Random voltage
            value_2 = round(random.uniform(0, 5), 2)   # Random current
            value_3 = round(random.uniform(0, 1000), 2)  # Random resistance

            # Update UI
            self.value_display_1.configure(text=f"{value_1} V")
            self.value_display_2.configure(text=f"{value_2} A")
            self.value_display_3.configure(text=f"{value_3} Ω")

            # Append to terminal
            self.textbox.insert("end", f"New values: {value_1}V, {value_2}A, {value_3}Ω\n")
            self.textbox.yview_moveto(1)

            time.sleep(1)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)
if __name__ == "__main__":
    app = App()
    app.mainloop()
