import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from tkintermapview import TkinterMapView
from customtkinter import CTkFrame, CTk, set_appearance_mode, set_default_color_theme, CTkEntry, CTkButton, CTkTextbox, CTkOptionMenu, StringVar, CTkLabel, CTkOptionMenu, CTkSegmentedButton, CTkTabview, CTkFont, CTkToplevel, CTkScrollableFrame
import os.path
import shutil
import pickle
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from pyproj import Proj, Transformer
from PIL import Image, ImageTk
from datetime import datetime, timedelta
import audioread


matplotlib.use('TkAgg')

set_appearance_mode("Light")  # Modes: "System" (standard), "Dark", "Light"
set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

class LandingPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)  

        self.controller = controller

        # configure grid layout (4x4)
        self.grid_columnconfigure((1,2,3), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)  

        # create sidebar frame with widgets
        self.sidebar_frame = CTkFrame(self, width=140)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=(10,0), pady=10)
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        self.logo_label = CTkLabel(self.sidebar_frame, text="Do you want to create a new project or load an existing one?", font=CTkFont(size=12, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_button_2 = CTkButton(self.sidebar_frame, text="Create", command=self.create_button)
        self.sidebar_button_2.grid(row=1, column=0, padx=20, pady= (0, 5))
        self.sidebar_button_3 = CTkButton(self.sidebar_frame, text="Load", command=self.load_project_button)
        self.sidebar_button_3.grid(row=2, column=0, padx=20, pady=5)

        self.toplevel_window = None

    def create_button(self):
            print("create_button click")
            if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
                self.toplevel_window = ToplevelWindow(self, controller=self.master)  # create window if its None or destroyed
            else:
                self.toplevel_window.focus()  # if window exists focus it
    
    def load_project_button(self):
            print("load_project_button click")
            file_path = filedialog.askopenfilename(filetypes=[("Pickle files", "*.pkl")])

            project_name = os.path.splitext(os.path.basename(file_path))[0]  # Use the actual project name here.
            print(project_name)

            if self.controller.load_project_settings(project_name):
                self.controller.show_frame(Dashboard)
            else:
                print("Error loading the project.")

    def dashboard_button_event(self):
            print("sidebar_button click")
            self.master.show_frame(Dashboard)

class ToplevelWindow(CTkToplevel):
    def __init__(self, parent, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("600x400")
        self.controller = controller

        # Set the window to be always on top
        self.attributes('-topmost', True)

        # configure grid layout (4x4)
        self.grid_columnconfigure((0,1,2,3), weight=1)
        self.grid_rowconfigure((0, 1, 2,3,4,5,6), weight=1)  

        # Update the main window title
        self.title("Create new project")

        self.project_name_label = CTkLabel(self, text="Project name:", font=CTkFont(size=12), height = 1)
        self.project_name_label.grid(row=0, column=0, padx=(10,5), pady=(10, 0))
        self.project_name = CTkEntry(self, placeholder_text="Enter project name", corner_radius=10)
        self.project_name.grid(row=0, column=1, padx=(0,5), pady=(10, 0))

        # create buttons
        self.epsg_entry_label = CTkLabel(self, text="EPSG code:", font=CTkFont(size=12), height = 1)
        self.epsg_entry_label.grid(row=1, column=0, padx=(10,5), pady=(10, 0))
        self.epsg_entry = CTkEntry(self, placeholder_text="Enter code", corner_radius=10)
        self.epsg_entry.grid(row=1, column=1, padx=(0,5), pady=(10, 0))
        self.epsg_entry_check = CTkButton(self, text="Check", command=self.check_epsg_code)
        self.epsg_entry_check.grid(row=1, column=2, padx=(0,5), pady=(10, 0))

        # loading the metadata
        self.meta_data_label = CTkLabel(self, text="Load meta data", font=CTkFont(size=12), height = 1)
        self.meta_data_label.grid(row=2, column=0, padx=(10,5), pady=(10, 0))
        self.meta_data_load = CTkButton(self, text="Browse", command=self.load_csv_button)
        self.meta_data_load.grid(row=2, column=1, padx=(0,5), pady=(10, 0))
        self.meta_data_textbox = CTkTextbox(self, wrap="word", height = 1)
        self.meta_data_textbox.grid(row=2, column=2, columnspan=3, padx=(0, 10), pady=(10, 0), sticky="ew")

        # setting the audio location
        self.data_location_label = CTkLabel(self, text="Audio directory", font=CTkFont(size=12), height = 1)
        self.data_location_label.grid(row=3, column=0, padx=(10,5), pady=(10, 0))
        self.data_location_button = CTkButton(self, text="Browse", command=self.data_location)
        self.data_location_button.grid(row=3, column=1, padx = (0,5), pady=(10, 0))
        self.data_location_textbox = CTkTextbox(self, wrap="word", height = 1)
        self.data_location_textbox.grid(row=3, column=2, columnspan=3, padx=(0, 10), pady=(10,0), sticky="ew")

        # setting the model location
        self.model_label = CTkLabel(self, text="Model", font=CTkFont(size=12), height = 1)
        self.model_label.grid(row=4, column=0, padx=(10,5), pady=(10, 0))
        self.model_location_button = CTkButton(self, text="Browse", command=self.model_location)
        self.model_location_button.grid(row=4, column=1, padx = (0,5), pady=(10, 0))
        self.model_textbox = CTkTextbox(self, wrap="word", height = 1)
        self.model_textbox.grid(row=4, column=2, padx=(0, 10), columnspan=3, pady=(10, 0), sticky="ew")

        # defining the naming convention
        self.naming_dropdown_label = CTkLabel(self, text="Naming convention", font=CTkFont(size=12), height = 1)
        self.naming_dropdown_label.grid(row=5, column=0, padx=(10,5), pady=(10, 0))

        naming_optionmenu_var = StringVar(value="Select")  # set initial value
        self.naming_combobox = CTkOptionMenu(self, values=["(site)_(datetime)", "(datetime)"],
                                        command=self.naming_optionmenu_callback, variable=naming_optionmenu_var)
        self.naming_combobox.grid(row=5, column=1, padx = (0,5), pady=(10, 0))
        self.naming_dropdown_textbox = CTkTextbox(self, wrap="word", height = 1)
        self.naming_dropdown_textbox.grid(row=5, column=2, columnspan=3, padx=(0, 10), pady=(10,0), sticky="ew")

        # defining the date convention
        self.date_dropdown_label = CTkLabel(self, text="Date convention", font=CTkFont(size=12), height = 1)
        self.date_dropdown_label.grid(row=6, column=0, padx=(10,5), pady=(10, 10))

        optionmenu_var = StringVar(value="Select")  # set initial value
        self.combobox = CTkOptionMenu(self, values=["AudioMoth - legacy", "AudioMoth - standard"],
                                        command=self.date_optionmenu_callback, variable=optionmenu_var)
        self.combobox.grid(row=6, column=1, padx = (0,5), pady=(10, 10))
        self.date_dropdown_textbox = CTkTextbox(self, wrap="word", height = 1)
        self.date_dropdown_textbox.grid(row=6, column=2, columnspan=3, padx=(0, 10), pady=(10,10), sticky="ew")

        # the save button
        self.save_button = CTkButton(self, text="Save", command=self.save_settings)
        self.save_button.grid(row=7, column=4, padx=10, pady=10, columnspan = 2)

    def date_optionmenu_callback(self, choice):
        print("optionmenu dropdown clicked:", choice)
        self.date_dropdown_textbox.insert("end", f"{choice}")

    def naming_optionmenu_callback(self, choice):
        print("optionmenu dropdown clicked:", choice)
        self.naming_dropdown_textbox.insert("end", f"{choice}")

    def load_csv_button(self):
        print("load_button click")
        self.attributes('-topmost', False)  # Disable topmost
        self.file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        self.attributes('-topmost', True)  # Re-enable topmost
        file_to_display = os.path.basename(self.file_path)

        if self.file_path:
                # add text to display
                self.meta_data_textbox.insert("end", f"{file_to_display}") 

    def data_location(self):
        print('file location button')
        self.attributes('-topmost', False)  # Disable topmost
        data_folder_selected = filedialog.askdirectory()
        self.attributes('-topmost', True)  # Re-enable topmost
        if data_folder_selected:
            self.data_location_textbox.insert("end", f"{data_folder_selected}")

    def model_location(self):
        print('model location button')
        self.attributes('-topmost', False)  # Disable topmost
        self.model_selected = filedialog.askdirectory()
        self.attributes('-topmost', True)  # Re-enable topmost
        model_to_display = os.path.basename(self.model_selected)
        if self.model_selected:
            self.model_textbox.insert("end", f"{model_to_display}")

    def check_epsg_code(self):
        # Read the EPSG codes from the .txt file and store them in a set
        with open("epsg_codes.txt", "r") as f:
            self.epsg_codes = {line.strip() for line in f}
        
        self.entered_code = self.epsg_entry.get().strip()
        
        if self.entered_code in self.epsg_codes:
                messagebox.showinfo("Info", "EPSG code exists!")
        else:
                messagebox.showwarning("Warning", "EPSG code does not exist, please check and try again.")
       
    def save_settings(self):
        print('Saving settings')

        # Read the EPSG codes from the .txt file and store them in a set
        with open("epsg_codes.txt", "r") as f:
            self.epsg_codes = {line.strip() for line in f}

        # Gather all the settings
        settings = {
            'meta_data': self.meta_data_textbox.get("1.0", "end-1c"),
            'EPSG_code':  self.epsg_entry.get(),
            'data_location': self.data_location_textbox.get("1.0", "end-1c"),
            'model': self.model_textbox.get("1.0", "end-1c"),
            'date_convention': self.date_dropdown_textbox.get("1.0", "end-1c"),
            'name_convention': self.naming_dropdown_textbox.get("1.0", "end-1c")
        }

        # Get project name from the CTkEntry widget
        project_name = self.project_name.get().strip()

        if not project_name:
            messagebox.showwarning("Warning", "Please enter a project name.")
            return
        elif " " in project_name:
            messagebox.showwarning("Warning", "Project name should not contain spaces.")
            return
        elif not settings['meta_data']:
            messagebox.showwarning("Warning", "Please load meta data.")
            return
        elif not settings['data_location']:
            messagebox.showwarning("Warning", "Please specify an audio directory.")
            return
        elif not settings['model']:
            messagebox.showwarning("Warning", "Please specify a model.")
            return
        elif not settings['date_convention']:
            messagebox.showwarning("Warning", "Please choose a date convention.")
            return
        elif not settings['name_convention']:
            messagebox.showwarning("Warning", "Please choose a naming convention.")
            return
        elif self.epsg_entry.get() not in self.epsg_codes:
            messagebox.showwarning("Warning", "EPSG code does not exist, please check and try again.")
        
        # Save settings to a pickle file with the project name
        with open(f'.\{project_name}.pkl', 'wb') as f:
            pickle.dump(settings, f)

        # Create project_data folder
        project_data_folder = f"{project_name}_data"
        os.makedirs(project_data_folder, exist_ok=True)

        # Save meta_data and model to the project_data folder
        # shutil.copy(self.model_selected, project_data_folder)
        shutil.copy(self.file_path, project_data_folder)
        
        if project_name:
            # Update the project settings in the main controller
            self.controller.load_project_settings(project_name)
            
            # Display the Dashboard
            self.controller.show_frame(Dashboard)

        # Close the ToplevelWindow
        self.destroy()

        print('Settings saved!')

class Dashboard(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)  

        self.controller = controller

        # configure grid layout (4x4)
        self.grid_columnconfigure((1,2,3,4,5), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)
        
        # create sidebar frame with widgets
        self.sidebar_frame = CTkFrame(self, width=140)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=(10,0), pady=10)
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.sidebar_button_1 = CTkButton(self.sidebar_frame, text="Dashboard", command=self.dashboard_button_event)
        self.sidebar_button_1.grid(row=0, column=0, padx=20, pady=10)
        self.sidebar_button_1.configure(state="disabled", text="Dashboard")
        self.sidebar_button_2 = CTkButton(self.sidebar_frame, text="Detect", command=self.detect_button_event)
        self.sidebar_button_2.grid(row=1, column=0, padx=20, pady= (0, 5))
        self.sidebar_button_3 = CTkButton(self.sidebar_frame, text="Validate", command=self.validate_button_event)
        self.sidebar_button_3.grid(row=2, column=0, padx=20, pady=5)
        self.sidebar_button_4 = CTkButton(self.sidebar_frame, text="Analyse", command=self.analyse_button_event)
        self.sidebar_button_4.grid(row=3, column=0, padx=20, pady=5)

        # change project
        self.project_label = CTkLabel(self.sidebar_frame, text="Change project:", anchor="w")
        self.project_label.grid(row=4, column=0, padx=20, pady=(5, 80))
        
        self.sidebar_button_5 = CTkButton(self.sidebar_frame, text="New Project", command=self.create_button)
        self.sidebar_button_5.grid(row=4, column=0, padx=20, pady= (0, 5))

        self.sidebar_button_6 = CTkButton(self.sidebar_frame, text="Load Project", command=self.load_button)
        self.sidebar_button_6.grid(row=4, column=0, padx=20, pady= (75, 5))

        self.toplevel_window = None

        self.appearance_mode_label = CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=7, column=0, padx=20, pady=(5, 0))
        self.appearance_mode_optionemenu = CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 10))

        # create dashboard frame
        self.dashboard_frame = CTkFrame(self)
        self.dashboard_frame.grid(row=0, column=1, rowspan=3, columnspan=3, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.dashboard_frame.grid_rowconfigure(3, weight=1)
        self.dashboard_frame_label = CTkLabel(self.dashboard_frame, text="Dashboard", anchor="w")
        self.dashboard_frame_label.grid(row=0, column=0, padx=20, pady=(5, 0))

        self.dashboard_frame.grid_rowconfigure(1, weight=1)
        self.dashboard_frame.grid_columnconfigure(0, weight=1)

        # Create recording summary frame
        self.recording_frame = CTkFrame(self.dashboard_frame)
        self.recording_frame.grid(row=1, column=0,  padx=(5, 5), pady=(5, 5), rowspan = 2, sticky="nsew")

        self.seg_button_dash = CTkSegmentedButton(self.recording_frame)
        self.seg_button_dash.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="ew")
        self.seg_button_dash.configure(values=["Dashboard", "Recordings", "Summary"])
        self.seg_button_dash.set("Recordings")
        self.seg_button_dash.configure(command=self.dash_change_subframe)
        
        # create scrollable frame
        self.dashboard_scrollable_frame = SiteRecordingsSubFrame(parent=self.recording_frame, controller=controller)
        self.dashboard_scrollable_frame.grid(row=1, column=0, padx=(5, 5), pady=(5, 5), sticky="nsew")

        # create a display points button widget
        self.display_button = CTkButton(self.recording_frame, text = "Plot sites", command= self.update_map_plot)
        self.display_button.grid(row=4, column=1,  padx=(5, 5), pady=(5, 5), sticky="nsew")

        # create text for dropdown menu
        self.text_label = CTkLabel(self.recording_frame, text="Display labels?", font=CTkFont(size=12), height = 1)
        self.text_label.grid(row=4, column=2,  padx=(5, 5), pady=(5, 5), sticky="nsew")
       
        # create option for displaying site labels
        self.text_var = StringVar(value="Select")  # set initial value
        self.text_dropdown = CTkOptionMenu(self.recording_frame, values=["Yes", "No"], variable=self.text_var)
        self.text_dropdown.grid(row=4, column=4,  padx=(5, 5), pady=(5, 5), sticky="nsew")
        
        # create map widget
        self.map_widget = TkinterMapView(self.dashboard_frame, corner_radius=10)
        self.map_widget.grid(row=3, column=0,  padx=(5, 5), pady=(5, 5), rowspan = 2, sticky="nsew")
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)  # google satellite

        # set default widget position and zoom
        self.map_widget.set_position(10.2, -83.8) # Costa Rica
        self.map_widget.set_zoom(6)

        # Create detect frame
        self.detect_frame = CTkFrame(self)
        self.detect_frame.grid(row=0, column=4, padx=(0, 5), pady=(10, 10), rowspan = 1, sticky="nsew")

        self.detect_frame.grid_rowconfigure(1, weight=1)
        self.detect_frame.grid_columnconfigure(0, weight=1)

        self.detect_frame.grid_propagate(False)  # Add this line

        self.seg_button_1 = CTkSegmentedButton(self.detect_frame)
        self.seg_button_1.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="ew")
        self.seg_button_1.configure(values=["Detect", "Totals", "Sites"])
        self.seg_button_1.set("Totals")
        self.seg_button_1.configure(command=self.detect_change_subframe)
        
        # create scrollable frame
        self.detect_scrollable_frame = Detect_ScrollableFrame(parent=self.detect_frame, controller=self)
        self.detect_scrollable_frame.grid(row=1, column=0, padx=(5, 5), pady=(5, 5), sticky="nsew")
       
        # create detect plot frame
        self.detect_plot_frame = CTkFrame(self)
        self.detect_plot_frame.grid(row=0, column=5, padx=(5, 10), pady=(10, 10), rowspan = 1, sticky="nsew")
        self.detect_plot_frame.grid_rowconfigure(1, weight=1)
        self.detect_plot_frame.grid_columnconfigure(0, weight=1) 

        # Store the original frame size for detect_plot_frame
        self.original_detect_plot_frame_width = self.detect_plot_frame.winfo_reqwidth()
        self.original_detect_plot_frame_height = self.detect_plot_frame.winfo_reqheight()
    
        # create validate frame
        self.validate_frame = CTkFrame(self)
        self.validate_frame.grid(row=1, column=4, padx=(0, 5), pady=(0, 5), rowspan = 1, sticky="nsew")
        
        # configure the frame
        self.validate_frame.grid_rowconfigure(1, weight=1)
        self.validate_frame.grid_columnconfigure(0, weight=1)

        # create a segmented button
        self.seg_button_2 = CTkSegmentedButton(self.validate_frame)
        self.seg_button_2.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="ew")
        self.seg_button_2.configure(values=["Validate", "Work", "Performance"])
        self.seg_button_2.set("Work")
        self.seg_button_2.configure(command=self.validate_change_subframe)

        # create display frame
        self.validate_subframe = ValidateSubFrame(parent=self.validate_frame, controller=self)
        self.validate_subframe.grid(row=1, column=0, padx=(5, 5), pady=(5, 5), sticky="nsew")

        # create validate plot frame
        self.validate_plot_frame = CTkFrame(self)
        self.validate_plot_frame.grid(row=1, column=5, padx=(5, 10), pady=(0, 5), rowspan = 1, sticky="nsew")
        
        # Store the original frame size for validate_plot_frame
        self.original_validate_plot_frame_width = self.validate_plot_frame.winfo_reqwidth()
        self.original_validate_plot_frame_height = self.validate_plot_frame.winfo_reqheight()
  
        # configure the frame
        self.validate_plot_frame.grid_rowconfigure(1, weight=1)
        self.validate_plot_frame.grid_columnconfigure(0, weight=1)       

        # create analyse frame
        self.analyse_frame = CTkFrame(self)
        self.analyse_frame.grid(row=2, column=4, padx=(0, 5), pady=(5, 10), rowspan = 1, sticky="nsew")

        self.analyse_frame.grid_rowconfigure(1, weight=1)
        self.analyse_frame.grid_columnconfigure(0, weight=1)

        self.seg_button_3 = CTkSegmentedButton(self.analyse_frame)
        self.seg_button_3.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="ew")
        self.seg_button_3.configure(values=["Analyse", "Totals", "Sites"])
        self.seg_button_3.set("Totals")
        self.seg_button_3.configure(command=self.analyse_change_subframe)

        # create scrollable frame
        self.analyse_scrollable_frame = Analyse_ScrollableFrame(parent=self.analyse_frame, controller=self)
        self.analyse_scrollable_frame.grid(row=1, column=0, padx=(5, 5), pady=(5, 5), sticky="nsew")
        
        # create analyse plot frame
        self.analyse_plot_frame = CTkFrame(self)
        self.analyse_plot_frame.grid(row=2, column=5, padx=(5, 10), pady=(5, 10), rowspan = 1, sticky="nsew")

        # Store the original frame size for analyse_plot_frame
        self.original_analyse_plot_frame_width = self.analyse_plot_frame.winfo_reqwidth()
        self.original_analyse_plot_frame_height = self.analyse_plot_frame.winfo_reqheight()

        self.analyse_plot_frame.grid_rowconfigure(1, weight=1)
        self.analyse_plot_frame.grid_columnconfigure(0, weight=1)  
    
    def convert_coordinates(self, long, lat):
        # get the EPSG code from the project settings
        current_proj = self.controller.EPSG_code

        # transform from current EPSG to 4326
        transformer = Transformer.from_crs(current_proj, "EPSG:4326")
        long_converted, lat_converted  = transformer.transform(long, lat)

        return lat_converted, long_converted
    
    def update_map_plot(self):
        print('Update_plot run')

        # Clear existing markers from the map
        if self.controller.markers:
            for element in self.controller.markers:
                element.delete()
        
        # Check if the text_var value is "Yes" or "No"
        if not (self.text_var.get() == "Yes" or self.text_var.get() == "No"):
            messagebox.showerror("Error", "Please set label display")
            return

        # load the point image:
        round_icon = ImageTk.PhotoImage(Image.open(os.path.join('.\\', "round_icon.png")).resize((10, 10)))

        # Create an empty DataFrame to store the converted coordinates
        converted_coordinates = pd.DataFrame(columns=['lat', 'long'])

        # extract the coordinates and store as markers
        for index, row in self.controller.meta_data.iterrows():
            # convert to 4326
            lat_converted, long_converted = self.convert_coordinates(row['long'], row['lat'])
 
            # Store the converted coordinates in the DataFrame
            converted_coordinates.loc[index] = [lat_converted, long_converted]
 
            if self.text_var.get() == "Yes":
                marker = self.map_widget.set_marker(long_converted, lat_converted, text=row['site'], icon = round_icon, text_color = "#FFFFFF")
                self.controller.markers.append(marker)
            else:
                marker = self.map_widget.set_marker(long_converted, lat_converted, icon = round_icon)
                self.controller.markers.append(marker) 
        
        # get a bounding box to reposition the map view to
        max_lat = converted_coordinates['lat'].max()  # Most northern point
        min_lat = converted_coordinates['lat'].min()  # Most southern point

        max_long = converted_coordinates['long'].max()  # Most eastern point
        min_long = converted_coordinates['long'].min()  # Most western point

        south_east_point = (min_long, max_lat)
        north_west_point = (max_long, min_lat)

        print(north_west_point, south_east_point)
        
        self.map_widget.fit_bounding_box(north_west_point, south_east_point)

    def dashboard_button_event(self):
            print("sidebar_button click")
            self.master.show_frame(Dashboard)

    def detect_button_event(self):
            print("detect_button click")
            self.master.show_frame(DetectPage)

    def validate_button_event(self):
            print("validate_button click")
            self.master.show_frame(ValidatePage)

    def analyse_button_event(self):
            print("analyse_button click")
            self.master.show_frame(AnalysePage)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        set_appearance_mode(new_appearance_mode)

    def dash_change_subframe(self, dash_subframe_name):
        if dash_subframe_name == 'Dashboard':
            self.master.show_frame(Dashboard)
        else:
            self.dashboard_scrollable_frame.show_subframe(dash_subframe_name + 'SubFrame')

    def validate_change_subframe(self, validate_subframe_name):
        if validate_subframe_name == 'Validate':
            self.master.show_frame(ValidatePage)
        else:
            self.validate_subframe.show_subframe(validate_subframe_name + 'Page')
            self.update_validate_plot(validate_subframe_name)  # Call update_plot directly
            
    def detect_change_subframe(self, detect_subframe_name):
        if detect_subframe_name == 'Detect':
            self.master.show_frame(DetectPage)
        else:
            self.detect_scrollable_frame.show_subframe('Detect_' + detect_subframe_name + 'Page')
            self.update_detect_plot(detect_subframe_name)  # Call update_plot directly

    def analyse_change_subframe(self, analyse_subframe_name):
        if analyse_subframe_name == 'Analyse':
            self.master.show_frame(AnalysePage)
        else:
            self.analyse_scrollable_frame.show_subframe('Analyse_' + analyse_subframe_name + 'Page')
            self.update_analyse_plot(analyse_subframe_name)  # Call update_plot directly

    def create_button(self):
            print("create_button click")
            if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
                self.toplevel_window = ToplevelWindow(self, controller=self.master)  # create window if its None or destroyed
            else:
                self.toplevel_window.focus()  # if window exists focus it

    def load_button(self):
            print("load_button click")
            file_path = filedialog.askopenfilename(filetypes=[("Pickle files", "*.pkl")])

            # Update the project settings in the main controller
            self.controller.load_project_settings(os.path.basename(file_path))
    
    def update_detect_plot(self, plot_type):
            # Clear the detect_plot_frame
            for widget in self.detect_plot_frame.winfo_children():
                widget.destroy()

            # Calculate the figure size based on the original frame size
            detect_fig_width = self.original_detect_plot_frame_width / 100
            detect_fig_height = self.original_detect_plot_frame_height / 100

            # Create a new plot
            detect_fig = Figure(figsize=(detect_fig_width, detect_fig_height), dpi=100)
            detect_axes = detect_fig.add_subplot()

            # Generate example data
            x = range(10)
            if plot_type == "Totals":
                y = [i**2 for i in x]
                detect_axes.set_xlabel("Species", fontsize=6)
                detect_axes.set_ylabel("Detections", fontsize=6)
            elif plot_type == "Sites":
                y = [i*2 for i in x]
                detect_axes.set_xlabel("Time", fontsize=6)
                detect_axes.set_ylabel("Detections", fontsize=6)

            # Plot the data
            detect_axes.tick_params(axis='both', which='major', labelsize=6)
            detect_axes.plot(x, y)

            # Adjust the plot margins
            detect_fig.subplots_adjust(top=0.95, right=0.95, left=0.15, bottom=0.25)

            # Add the plot to the detect_plot_frame
            self.detect_fig_canvas = FigureCanvasTkAgg(detect_fig, self.detect_plot_frame)
            self.detect_fig_canvas.get_tk_widget().grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    def update_validate_plot(self, plot_type):
            # Clear the detect_plot_frame
            for widget in self.validate_plot_frame.winfo_children():
                widget.destroy()

            # Calculate the figure size based on the original frame size
            validate_fig_width = self.original_validate_plot_frame_width / 100
            validate_fig_height = self.original_validate_plot_frame_height / 100

            # Create a new plot
            validate_fig = Figure(figsize=(validate_fig_width, validate_fig_height), dpi=100)
            validate_axes = validate_fig.add_subplot()

            # Generate example data
            x = range(10)
            if plot_type == "Work":
                y = [i**2 for i in x]
                validate_axes.set_ylabel("Count", fontsize=6)
                validate_axes.bar(x, y)
            elif plot_type == "Performance":
                y = [i*2 for i in x]
                validate_axes.set_xlabel("Metric", fontsize=6)
                validate_axes.set_ylabel("Value", fontsize=6)
                validate_axes.plot(x, y)

            # Plot the data
            validate_axes.tick_params(axis='both', which='major', labelsize=6)

            # Adjust the plot margins
            validate_fig.subplots_adjust(top=0.95, right=0.95, left=0.15, bottom=0.25)

            # Add the plot to the detect_plot_frame
            self.validate_fig_canvas = FigureCanvasTkAgg(validate_fig, self.validate_plot_frame)
            self.validate_fig_canvas.get_tk_widget().grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    def update_analyse_plot(self, plot_type):
            # Clear the detect_plot_frame
            for widget in self.analyse_plot_frame.winfo_children():
                widget.destroy()

            # Calculate the figure size based on the original frame size
            analyse_fig_width = self.original_analyse_plot_frame_width / 100
            analyse_fig_height = self.original_analyse_plot_frame_height / 100

            # Create a new plot
            analyse_fig = Figure(figsize=(analyse_fig_width, analyse_fig_height), dpi=100)
            analyse_axes = analyse_fig.add_subplot()

            # Generate example data
            x = range(10)
            if plot_type == "Totals":
                y = [i**2 for i in x]
                analyse_axes.set_xlabel("Species", fontsize=6)
                analyse_axes.set_ylabel("Detections", fontsize=6)
            elif plot_type == "Sites":
                y = [i*2 for i in x]
                analyse_axes.set_xlabel("Site", fontsize=6)
                analyse_axes.set_ylabel("Abundance", fontsize=6)

            # Plot the data
            analyse_axes.tick_params(axis='both', which='major', labelsize=6)
            analyse_axes.plot(x, y)

            # Adjust the plot margins
            analyse_fig.subplots_adjust(top=0.95, right=0.95, left=0.15, bottom=0.25)

            # Add the plot to the detect_plot_frame
            self.analyse_fig_canvas = FigureCanvasTkAgg(analyse_fig, self.analyse_plot_frame)
            self.analyse_fig_canvas.get_tk_widget().grid(row=1, column=0, padx=5, pady=5, sticky="nsew")           

class SiteRecordingsSubFrame(CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller  # Store the controller
        
        # Set the weight for the row and column configurations of the canvas
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.add_subframes([RecordingsSubFrame, SummarySubFrame])
        self.show_subframe("RecordingsSubFrame")
    
    def add_subframes(self, subframes):
        self.detect_subframes = {}
        for F in subframes:
            page_name = F.__name__
            frame = F(parent=self, controller=self.controller)  # Pass the controller here
            self.detect_subframes[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_remove()

    def show_subframe(self, page_name):
        for frame in self.detect_subframes.values():
            frame.grid_remove()

        frame = self.detect_subframes[page_name]
        frame.grid(row=0, column=0, sticky="nsew")

class RecordingsSubFrame(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller  # Store the controller       

        # get information on recordings
        site_data = self.controller.site_recording_data

        # Create the treeview widget
        self.recordings_tree = ttk.Treeview(self)
        
        # Configure the columns
        self.recordings_tree['columns'] = ('site', 'recording', 'date', 'start_time', 'end_time')
        self.recordings_tree.column('#0', width=0, stretch=tk.NO)  # Hide the first phantom column
        self.recordings_tree.heading('#0', text='')

        # Set column properties
        col_settings = [('site', 100, 'Site'), ('recording', 100, 'Recording'),
                        ('date', 100, 'Date'), ('start_time', 100, 'Start time'),
                        ('end_time', 100, 'End time')]

        for col, width, text in col_settings:
            self.recordings_tree.column(col, anchor=tk.CENTER, width=width)
            self.recordings_tree.heading(col, text=text, anchor=tk.CENTER)

        # Add the data to the treeview
        for i in range(len(site_data)):
            self.recordings_tree.insert('', 'end', values=(site_data.at[i, 'site'], 
                                                site_data.at[i, 'file_name'],
                                                site_data.at[i, 'date'].strftime('%Y-%m-%d'),
                                                site_data.at[i, 'start_time'].strftime('%H:%M:%S'),
                                                site_data.at[i, 'end_time'].strftime('%H:%M:%S')))


        self.recordings_tree.grid(row=0, column=0, sticky="nsew")

        self.recordings_tree.grid_rowconfigure(0, weight=1)
        self.recordings_tree.grid_columnconfigure(0, weight=1)
       
class SummarySubFrame(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller  # Store the controller    

        # get information on recordings
        site_data = self.controller.summary
              
        # Create the treeview widget
        self.summary_tree = ttk.Treeview(self)
        
        # Configure the columns
        self.summary_tree['columns'] = ('site', 'recordings', 'start_date', 'end_date', 'avg_per_day')
        self.summary_tree.column('#0', width=0, stretch=tk.NO)  # Hide the first phantom column
        self.summary_tree.heading('#0', text='')

        # Set column properties
        col_settings = [('site', 100, 'Site'), ('recordings', 100, 'Recordings'),
                        ('start_date', 100, 'Start Date'), ('end_date', 100, 'End Date'),
                        ('avg_per_day', 100, 'Avg/Day')]

        for col, width, text in col_settings:
            self.summary_tree.column(col, anchor=tk.CENTER, width=width)
            self.summary_tree.heading(col, text=text, anchor=tk.CENTER)

        # Add the data to the treeview
        for i in range(len(site_data)):
            self.summary_tree.insert('', 'end', values=(site_data.at[i, 'site'], 
                                                site_data.at[i, 'num_recordings'],
                                                site_data.at[i, 'start_date'].strftime('%Y-%m-%d'),
                                                site_data.at[i, 'end_date'].strftime('%H:%M:%S'),
                                                round(site_data.at[i, 'mean_per_day'].strftime('%H:%M:%S'), 2)))

        self.summary_tree.grid(row=0, column=0, sticky="nsew")

        self.summary_tree.grid_rowconfigure(0, weight=1)
        self.summary_tree.grid_columnconfigure(0, weight=1)
     
class ValidateSubFrame(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller  # Store the controller
        
        # Set the weight for the row and column configurations of the canvas
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.add_subframes([WorkPage, PerformancePage])
        self.show_subframe("WorkPage")

    def add_subframes(self, subframes):
        self.detect_subframes = {}
        for F in subframes:
            page_name = F.__name__
            frame = F(parent=self, controller=self.controller)  # Pass the controller here
            self.detect_subframes[page_name] = frame
            frame.grid(row=0, column=0, padx = (5, 15), pady = 5, sticky="nsew")
            frame.grid_remove()

    def show_subframe(self, page_name):
        for frame in self.detect_subframes.values():
            frame.grid_remove()

        frame = self.detect_subframes[page_name]
        frame.grid(row=0, column=0, sticky="nsew")

class WorkPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # Create table for SitesPage
        self.treeview = ttk.Treeview(self)

        self.treeview["columns"] = ("col1", "col2", "col3", "col4")
        self.treeview.column("#0", width=0, stretch=tk.NO)
        self.treeview.column("col1", width=60, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col2", width=60, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col3", width=60, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col4", width=60, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.heading("#0", text="")
        self.treeview.heading("col1", text="Type")
        self.treeview.heading("col2", text="Total")
        self.treeview.heading("col3", text="Checked")
        self.treeview.heading("col4", text="Remaining")
        self.treeview.grid(row=0, column=0, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

class PerformancePage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # Create table for TotalsPage
        self.treeview = ttk.Treeview(self)
        self.treeview["columns"] = ("col1", "col2", "col3")
        self.treeview.column("#0", width=0, stretch=tk.NO)
        self.treeview.column("col1", width=80, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col2", width=80, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col3", width=80, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.heading("#0", text="")
        self.treeview.heading("col1", text="Model")
        self.treeview.heading("col2", text="Recall")
        self.treeview.heading("col3", text="Precision")
        self.treeview.grid(row=0, column=0, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

class Detect_ScrollableFrame(CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller  # Store the controller
        
        # Set the weight for the row and column configurations of the canvas
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.add_subframes([Detect_TotalsPage, Detect_SitesPage])
        self.show_subframe("Detect_TotalsPage")
    
    def add_subframes(self, subframes):
        self.detect_subframes = {}
        for F in subframes:
            page_name = F.__name__
            frame = F(parent=self, controller=self.controller)  # Pass the controller here
            self.detect_subframes[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_remove()

    def show_subframe(self, page_name):
        for frame in self.detect_subframes.values():
            frame.grid_remove()

        frame = self.detect_subframes[page_name]
        frame.grid(row=0, column=0, sticky="nsew")

class Detect_SitesPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # Create table for SitesPage
        self.treeview = ttk.Treeview(self)

        self.treeview["columns"] = ("col1", "col2", "col3", "col4")
        self.treeview.column("#0", width=0, stretch=tk.NO)
        self.treeview.column("col1", width=40, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col2", width=70, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col3", width=70, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col4", width=70, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.heading("#0", text="")
        self.treeview.heading("col1", text="Site")
        self.treeview.heading("col2", text="Species 1")
        self.treeview.heading("col3", text="Species 2")
        self.treeview.heading("col4", text="Species 3")
        self.treeview.grid(row=0, column=0, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

class Detect_TotalsPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # Create table for TotalsPage
        self.treeview = ttk.Treeview(self)
        self.treeview["columns"] = ("col1", "col2", "col3")
        self.treeview.column("#0", width=0, stretch=tk.NO)
        self.treeview.column("col1", width=60, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col2", width=80, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col3", width=100, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.heading("#0", text="")
        self.treeview.heading("col1", text="Species")
        self.treeview.heading("col2", text="Detections")
        self.treeview.heading("col3", text="Mean per minute")
        self.treeview.grid(row=0, column=0, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

class Analyse_ScrollableFrame(CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller  # Store the controller
        
        # Set the weight for the row and column configurations of the canvas
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.add_subframes([Analyse_TotalsPage, Analyse_SitesPage])
        self.show_subframe("Analyse_TotalsPage")
    
    def add_subframes(self, subframes):
        self.detect_subframes = {}
        for F in subframes:
            page_name = F.__name__
            frame = F(parent=self, controller=self.controller)  # Pass the controller here
            self.detect_subframes[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_remove()

    def show_subframe(self, page_name):
        for frame in self.detect_subframes.values():
            frame.grid_remove()

        frame = self.detect_subframes[page_name]
        frame.grid(row=0, column=0, sticky="nsew")

class Analyse_SitesPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # Create table for SitesPage
        self.treeview = ttk.Treeview(self)

        self.treeview["columns"] = ("col1", "col2", "col3", "col4")
        self.treeview.column("#0", width=0, stretch=tk.NO)
        self.treeview.column("col1", width=30, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col2", width=70, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col3", width=70, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col4", width=70, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.heading("#0", text="")
        self.treeview.heading("col1", text="Site")
        self.treeview.heading("col2", text="Species 1")
        self.treeview.heading("col3", text="Species 2")
        self.treeview.heading("col4", text="Species 3")
        self.treeview.grid(row=0, column=0, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

class Analyse_TotalsPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # Create table for TotalsPage
        self.treeview = ttk.Treeview(self)
        self.treeview["columns"] = ("col1", "col2", "col3")
        self.treeview.column("#0", width=0, stretch=tk.NO)
        self.treeview.column("col1", width=60, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col2", width=100, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.column("col3", width=80, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview.heading("#0", text="")
        self.treeview.heading("col1", text="Species")
        self.treeview.heading("col2", text="Abundance")
        self.treeview.heading("col3", text="SE")
        self.treeview.grid(row=0, column=0, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

class DetectPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        
        # configure grid layout (4x4)
        self.grid_columnconfigure((1,2,3), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)
        
        # create sidebar frame with widgets
        self.sidebar_frame = CTkFrame(self, width=140)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=(10,0), pady=10)
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.sidebar_button_1 = CTkButton(self.sidebar_frame, text="Dashboard", command=self.dashboard_button_event)
        self.sidebar_button_1.grid(row=0, column=0, padx=20, pady=10)
        self.sidebar_button_2 = CTkButton(self.sidebar_frame, text="Detect", command=self.detect_button_event)
        self.sidebar_button_2.grid(row=1, column=0, padx=20, pady= (0, 5))
        self.sidebar_button_2.configure(state="disabled", text="Detect")        
        self.sidebar_button_3 = CTkButton(self.sidebar_frame, text="Validate", command=self.validate_button_event)
        self.sidebar_button_3.grid(row=2, column=0, padx=20, pady=5)
        self.sidebar_button_4 = CTkButton(self.sidebar_frame, text="Analyse", command=self.analyse_button_event)
        self.sidebar_button_4.grid(row=3, column=0, padx=20, pady=5)

        # create site frame
        self.site_frame = CTkScrollableFrame(self) 
        self.site_frame.grid(row=0, column=1, rowspan = 3, columnspan = 1, sticky="nsew", padx=(10,0), pady=(10,0))

        # create settings frame
        self.settings_frame = CTkFrame(self) 
        self.settings_frame.grid(row=3, column=1, columnspan = 1, sticky="nsew", padx=(10,0), pady=10)

        # create results frame
        self.results_frame = CTkScrollableFrame(self) 
        self.results_frame.grid(row=0, column=2, rowspan = 1, columnspan = 2, sticky="nsew", padx=(10,10), pady=(10,0))

        # create plot 
        self.plot_frame = CTkFrame(self) 
        self.plot_frame.grid(row=1, column=2, rowspan = 3, columnspan = 2, sticky="nsew", padx=(10,10), pady=(10,10))      

    def dashboard_button_event(self):
            print("sidebar_button click")
            self.master.show_frame(Dashboard)

    def detect_button_event(self):
            print("detect_button click")
            self.master.show_frame(DetectPage)

    def validate_button_event(self):
            print("validate_button click")
            self.master.show_frame(ValidatePage)

    def analyse_button_event(self):
            print("analyse_button click")
            self.master.show_frame(AnalysePage)

class ValidatePage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # configure grid layout (4x4)
        self.grid_columnconfigure((1,2,3), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)
        
        # create sidebar frame with widgets
        self.sidebar_frame = CTkFrame(self, width=140)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=(10,0), pady=10)
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.sidebar_button_1 = CTkButton(self.sidebar_frame, text="Dashboard", command=self.dashboard_button_event)
        self.sidebar_button_1.grid(row=0, column=0, padx=20, pady=10)
        self.sidebar_button_2 = CTkButton(self.sidebar_frame, text="Detect", command=self.detect_button_event)
        self.sidebar_button_2.grid(row=1, column=0, padx=20, pady= (0, 5))     
        self.sidebar_button_3 = CTkButton(self.sidebar_frame, text="Validate", command=self.validate_button_event)
        self.sidebar_button_3.grid(row=2, column=0, padx=20, pady=5)
        self.sidebar_button_3.configure(state="disabled", text="Validate")   
        self.sidebar_button_4 = CTkButton(self.sidebar_frame, text="Analyse", command=self.analyse_button_event)
        self.sidebar_button_4.grid(row=3, column=0, padx=20, pady=5)

    def dashboard_button_event(self):
            print("sidebar_button click")
            self.master.show_frame(Dashboard)

    def detect_button_event(self):
            print("detect_button click")
            self.master.show_frame(DetectPage)

    def validate_button_event(self):
            print("validate_button click")
            self.master.show_frame(ValidatePage)

    def analyse_button_event(self):
            print("analyse_button click")
            self.master.show_frame(AnalysePage)

class AnalysePage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        # configure grid layout (4x4)
        self.grid_columnconfigure((1,2,3), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = CTkFrame(self, width=140)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=(10,0), pady=10)
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.sidebar_button_1 = CTkButton(self.sidebar_frame, text="Dashboard", command=self.dashboard_button_event)
        self.sidebar_button_1.grid(row=0, column=0, padx=20, pady=10)
        self.sidebar_button_2 = CTkButton(self.sidebar_frame, text="Detect", command=self.detect_button_event)
        self.sidebar_button_2.grid(row=1, column=0, padx=20, pady= (0, 5))     
        self.sidebar_button_3 = CTkButton(self.sidebar_frame, text="Validate", command=self.validate_button_event)
        self.sidebar_button_3.grid(row=2, column=0, padx=20, pady=5)
        self.sidebar_button_4 = CTkButton(self.sidebar_frame, text="Analyse", command=self.analyse_button_event)
        self.sidebar_button_4.grid(row=3, column=0, padx=20, pady=5)
        self.sidebar_button_4.configure(state="disabled", text="Analyse")   

    def dashboard_button_event(self):
            print("sidebar_button click")
            self.master.show_frame(Dashboard)

    def detect_button_event(self):
            print("detect_button click")
            self.master.show_frame(DetectPage)

    def validate_button_event(self):
            print("validate_button click")
            self.master.show_frame(ValidatePage)

    def analyse_button_event(self):
            print("analyse_button click")
            self.master.show_frame(AnalysePage)

class MainApplication(CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("Parrot PAM Platform")
        self.geometry(f"{1100}x{580}")

        # configure grid layout (4x4)
        self.grid_columnconfigure((1, 2, 3), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # Initialize project_settings attribute
        self.project_settings = {}
        self.project_name = ""
        self.meta_data = None
        self.markers = [] # create a place to store the markers
        self.data_location = ""
        self.EPSG_code = []
        self.name_convention = ""
        self.date_convention = ""
        self.data_folder = ""
        self.site_recording_data = pd.DataFrame(columns=['site', 'file_name', 'date_time', 'date', 'start_time', 'end_time','duration'])
        self.summary = ""
 
        self.frames = {}
        for F in (LandingPage, Dashboard, DetectPage, ValidatePage, AnalysePage):
            page_name = F.__name__
            frame = F(parent=self, controller=self)
            self.frames[page_name] = frame

        self.current_frame_name = LandingPage.__name__  # set initial value
        self.show_frame(LandingPage)

        # Bind the keyboard commands to their respective functions
        self.bind('<Escape>', self.go_to_main_menu)
        self.bind('<BackSpace>', self.go_back)

    def show_frame(self, page_class):
        page_name = page_class.__name__
        current_frame = self.frames[self.current_frame_name]

        # Remove current frame from the grid
        current_frame.grid_remove()

        # Update current frame name and grid the new frame
        self.current_frame_name = page_name
        new_frame = self.frames[page_name]
        new_frame.grid(row=0, column=0, rowspan=4, columnspan=4, sticky="nsew")
        new_frame.lift()

        if page_name == 'DetectPage':
             display_name = 'Detect'
        elif page_name == 'ValidatePage':
             display_name = 'Validate'
        elif page_name == 'AnalysePage':
             display_name = 'Analyse'
        elif page_name == 'ProjectSettingsPage':
             display_name = 'Project Settings'       
        else:
             display_name = 'Dashboard'

        # Update the main window title
        self.title(f"Parrot PAM Platform - {display_name} - {self.project_name}")
        self.focus_set()  # Set the focus to the main application window
    
    def go_to_main_menu(self, event=None):
        self.show_frame(Dashboard)
        print("Going to the main menu...")

    def go_back(self, event=None):
        self.show_frame(Dashboard)
        print("Going back to the previous page...")

    def extract_datetime(self, date):
        if self.date_convention == "AudioMoth - legacy":
                # Convert the hexadecimal datetime to a standard datetime object
                print(date)
                hex_timestamp, ext = os.path.splitext(date)
                timestamp = int(hex_timestamp, 16)
                formatted_dt = datetime.fromtimestamp(timestamp)

        elif self.date_convention == "AudioMoth - standard":
                formatted_dt = datetime.utcfromtimestamp(date)
        
        return formatted_dt

    def get_wav_duration(self, file_path):
        # create the full file path of the audio
        audio_file = os.path.join(self.data_location, file_path)

        with audioread.audio_open(audio_file) as audio_file:
            duration = audio_file.duration
            return duration
        
    def read_extract_datetime(self):
        directory_path = self.data_location

        print('Looking for data in', directory_path)

        new_rows = []

        if self.name_convention == "(site)_(datetime)":
            files = [file for file in os.listdir(directory_path) if file.endswith('.WAV')]

            for file in files:
                print(file)
                # Split the filename into site name and hexadecimal datetime
                site_name, hex_datetime = file.split('_')

                # get the date
                date_time = self.extract_datetime(hex_datetime)

                # get file duration
                file_duration = self.get_wav_duration(file)

                # Append the information to the new_rows list
                end_time = date_time + timedelta(seconds=file_duration)

                new_rows.append({
                    'site': site_name,
                    'date_time': date_time,
                    'date': date_time.date(),
                    'start_time': date_time.time(),
                    'end_time': end_time,
                    'file_name': file,
                    'duration': file_duration,
                })

        elif self.name_convention == "(datetime)":
            items = os.listdir(directory_path)

            # Filter out only the folders
            folders = [item for item in items if os.path.isdir(os.path.join(directory_path, item))]

            # get the audio files from within each folder
            for site in folders:
                files = [file for file in os.listdir(site) if file.endswith('.WAV')]

                for file in files:
                    # remove the extention
                    timestamp = int(file.replace('.WAV', ''), 16)
                    # get the date
                    date_time = self.extract_datetime(timestamp)

                    # get site name
                    site_name = os.path.basename(file)

                    # get file duration
                    file_duration = self.get_wav_duration(file)

                    # Append the information to the new_rows list
                    end_time = date_time + timedelta(seconds=file_duration)

                    new_rows.append({
                        'site': site_name,
                        'date_time': date_time,
                        'date': date_time.date(),
                        'start_time': date_time.time(),
                        'end_time': end_time,
                        'file_name': file,
                        'duration': file_duration,
                    })

        new_data = pd.DataFrame(new_rows)
        self.site_recording_data = pd.concat([self.site_recording_data, new_data], ignore_index=True)

        return self.site_recording_data
    
    def summarise_recording_data(self):
        
        # First, convert the 'date_time' column to a datetime object
        self.site_recording_data['date_time'] = pd.to_datetime(self.site_recording_data['date_time'])

        # Group the DataFrame by 'site'
        grouped = self.site_recording_data.groupby('site')

        # Calculate summary statistics for each site
        self.summary = grouped.agg(
            num_recordings=('date_time', 'count'),
            start_date=('date_time', 'min'),
            end_date=('date_time', 'max'))

        # Calculate the mean recordings per day for each site
        self.summary['mean_per_day'] = self.summary['num_recordings'] / ((self.summary['end_date'] - self.summary['start_date']).dt.days + 1)

        # Reset the index to make 'site' a regular column
        self.summary.reset_index(inplace=True)

        return self.summary

    def load_project_settings(self, project_name):
        try:
            with open(f'.\{project_name}.pkl', 'rb') as f:
                self.project_settings = pickle.load(f)
        except FileNotFoundError as e:
            print(f"Error loading project file: {e}")
            return False

        self.project_name = project_name  # Update the project_name attribute
        self.EPSG_code = self.project_settings['EPSG_code']
        self.name_convention = self.project_settings['name_convention']
        self.date_convention = self.project_settings['date_convention']
        self.data_location = self.project_settings['data_location']

        # Load the meta_data DataFrame from the CSV file
        self.data_folder = f"{project_name}_data"
        meta_data_filepath = os.path.join('.\\', self.data_folder, self.project_settings['meta_data'])

        try:
            self.meta_data = pd.read_csv(meta_data_filepath)
        except FileNotFoundError as e:
            print(f"Error loading meta_data file: {e}")
            return False
        
        # Clear the existing markers
        self.markers.clear()

        # Read and extract the datetime information
        self.site_recording_data = self.read_extract_datetime()
       
        # Write the DataFrame to a CSV file
        self.csv_filepath = os.path.join('.\\', self.data_folder, '_recording_information.csv')

        self.site_recording_data.to_csv(self.csv_filepath , index=False) 

        print('Data saved') 

        # summarise the data
        self.summarise_recording_data()

        return True
  
if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()