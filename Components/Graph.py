import tkinter
import customtkinter
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from Utils.color_theme import COLORS


class GraphComponent(customtkinter.CTkFrame):
    """ Real-time updating graph component (Uses CustomTkinter default background) """

    def __init__(self, parent):
        self.default_color = COLORS["backgroundLight"]
        self.active_color = COLORS["backgroundDark"]
        self.hover_color = COLORS["hover"]
        self.text_color = COLORS["lg_text"]

        super().__init__(parent, fg_color=self.default_color)

        # Make sure GraphComponent itself fills its container
        self.grid(row=0, column=0, padx=(20, 20), pady=(10, 10), sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.default_bg_color = self.default_color
        plt.style.use("dark_background")

        # === Graph Frame ===
        self.graph_frame = customtkinter.CTkFrame(self, fg_color=self.default_color)
        self.graph_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.graph_frame.grid_rowconfigure(0, weight=1)
        self.graph_frame.grid_rowconfigure(1, weight=0)
        self.graph_frame.grid_columnconfigure(0, weight=1)

        # === Graph ===
        self.figure, self.ax = plt.subplots()
        self.figure.patch.set_facecolor(self.default_bg_color)
        self.ax.set_facecolor(self.default_bg_color)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Enable scroll zooming
        self.canvas.get_tk_widget().bind("<MouseWheel>", self.on_scroll_zoom)  # Windows
        self.canvas.get_tk_widget().bind("<Button-4>", self.on_scroll_zoom)  # Linux scroll up
        self.canvas.get_tk_widget().bind("<Button-5>", self.on_scroll_zoom)  # Linux scroll down

        # === Controls Below the Graph ===
        self.bottom_control_frame = customtkinter.CTkFrame(self.graph_frame, fg_color=self.default_color)
        self.bottom_control_frame.grid(row=1, column=0, pady=(5, 0))

        shared_btn_width = 40
        shared_btn_height = 26

        self.left_button = customtkinter.CTkButton(
            self.bottom_control_frame, text="◀", width=shared_btn_width,
            height=shared_btn_height, command=self.switch_left)
        self.left_button.grid(row=0, column=0, padx=5)

        self.display_label = customtkinter.CTkLabel(
            self.bottom_control_frame, text="Voltage", font=customtkinter.CTkFont(size=14))
        self.display_label.grid(row=0, column=1, padx=5)

        self.right_button = customtkinter.CTkButton(
            self.bottom_control_frame, text="▶", width=shared_btn_width,
            height=shared_btn_height, command=self.switch_right)
        self.right_button.grid(row=0, column=2, padx=5)

        customtkinter.CTkLabel(self.bottom_control_frame, text=" ").grid(row=0, column=3, padx=10)

        self.zoom_in_button = customtkinter.CTkButton(
            self.bottom_control_frame, text="🔍-", width=shared_btn_width,
            height=shared_btn_height, command=self.zoom_in)
        self.zoom_in_button.grid(row=0, column=4, padx=2)

        self.zoom_label = customtkinter.CTkLabel(
            self.bottom_control_frame, text="Last 50 pts", font=customtkinter.CTkFont(size=14))
        self.zoom_label.grid(row=0, column=5, padx=5)

        self.zoom_out_button = customtkinter.CTkButton(
            self.bottom_control_frame, text="🔍+", width=shared_btn_width,
            height=shared_btn_height, command=self.zoom_out)
        self.zoom_out_button.grid(row=0, column=6, padx=2)

        # === Data & Graph Animation ===
        self.time_values = []
        self.voltage_values = []
        self.current_values = []
        self.resistance_values = []

        self.selected_index = 0
        self.value_labels = ["Voltage", "Current", "Resistance"]
        self.labels = self.value_labels
        self.value_data_labels = []
        self.data_sets = [self.voltage_values, self.current_values, self.resistance_values]

        self.max_point_options = [10, 25, 50, 100, 200, None]
        self.current_zoom_index = 2
        self.max_points = self.max_point_options[self.current_zoom_index]

        self.ani = FuncAnimation(self.figure, self.update_graph, interval=1000)

    def update_data(self, values):
        """ Store new data points and update the graph """
        self.time_values.append(len(self.time_values))
        for i, val in enumerate(values):
            self.data_sets[i].append(val["Value"])
            raw_val = val['Value']
            if isinstance(raw_val, str):
                value_str = raw_val
            else:
                value_str = f"{float(raw_val):.2f}"

            self.value_data_labels[i].configure(text=f"{value_str} {val['Label']}")

    def update_graph(self, frame):
        """ Update the graph display """
        self.ax.clear()
        data = self.data_sets[self.selected_index]
        time = self.time_values

        if self.max_points is not None:
            data = data[-self.max_points:]
            time = time[-self.max_points:]

        self.ax.clear()
        self.ax.plot(time, data, label=self.labels[self.selected_index], color="cyan")
        self.ax.legend()
        self.canvas.draw()

    def switch_left(self):
        """ Switch to previous data type """
        self.selected_index = (self.selected_index - 1) % len(self.labels)
        self.display_label.configure(text=self.labels[self.selected_index])

    def switch_right(self):
        """ Switch to next data type """
        self.selected_index = (self.selected_index + 1) % len(self.labels)
        self.display_label.configure(text=self.labels[self.selected_index])

    def zoom_in(self):
        """ Show fewer points """
        if self.current_zoom_index > 0:
            self.current_zoom_index -= 1
            self.max_points = self.max_point_options[self.current_zoom_index]
            self.update_zoom_label()

    def zoom_out(self):
        """ Show more points """
        if self.current_zoom_index < len(self.max_point_options) - 1:
            self.current_zoom_index += 1
            self.max_points = self.max_point_options[self.current_zoom_index]
            self.update_zoom_label()

    def update_zoom_label(self):
        if self.max_points is None:
            self.zoom_label.configure(text="All points")
        else:
            self.zoom_label.configure(text=f"Last {self.max_points} pts")
    def on_scroll_zoom(self, event):
        """ Scroll wheel zoom in/out on the graph """
        if hasattr(event, "delta"):  # Windows
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        elif hasattr(event, "num"):  # Linux
            if event.num == 4:
                self.zoom_in()
            elif event.num == 5:
                self.zoom_out()
