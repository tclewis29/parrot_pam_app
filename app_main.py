import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkintermapview import TkinterMapView
from customtkinter import CTkFrame, CTk, set_appearance_mode, set_default_color_theme, CTkSwitch, CTkEntry, CTkButton, CTkTextbox, CTkOptionMenu, StringVar, CTkLabel, CTkOptionMenu, CTkSegmentedButton, CTkTabview, CTkFont, CTkToplevel, CTkScrollableFrame
import os.path
import shutil
import pickle
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from matplotlib.figure import Figure
import pandas as pd
from pyproj import Proj, Transformer
from PIL import Image, ImageTk
from datetime import datetime, timedelta
import audioread
import random
import numpy as np
import librosa
import tensorflow as tf
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
from timezonefinder import TimezoneFinder
import pytz
from scipy.signal import spectrogram
import pygame
import requests
import json
import rasterio
from rasterio import mask

matplotlib.use('TkAgg')

import sys
sys.stderr = open('err.txt', 'w')

set_appearance_mode("Light")  # Modes: "System" (standard), "Dark", "Light"
set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

class LandingPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)  

        self.controller = controller

        # configure grid layout (4x4)
        self.grid_columnconfigure((1,2), weight=1)
        self.grid_rowconfigure((0,1), weight=1)  

        # create sidebar frame with widgets
        self.sidebar_frame = CTkFrame(self, width=140)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(10,0), pady=10)
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
                self.controller.load_project_settings(project_name)
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
        self.data_location_button = CTkButton(self, text="Browse", command=self.find_data_location)
        self.data_location_button.grid(row=3, column=1, padx = (0,5), pady=(10, 0))
        self.data_location_textbox = CTkTextbox(self, wrap="word", height = 1)
        self.data_location_textbox.grid(row=3, column=2, columnspan=3, padx=(0, 10), pady=(10,0), sticky="ew")

        # type of model being used
        self.model_text = CTkLabel(self, text="Do you want to load a custom model?", font=CTkFont(size=12), height=1)
        self.model_text.grid(row=4, column=0, padx=(10, 5), columnspan = 2, pady=(10, 0))
        self.model_text_button = CTkSegmentedButton(self, values=["Yes", "No"], command=self.allow_model_load)
        self.model_text_button.grid(row=4, column=2, padx=(0, 5), columnspan = 3, pady=(10, 0), sticky="ew")
        self.model_text_button.set("Yes")       

        # setting the model location
        self.model_label = CTkLabel(self, text="Model", font=CTkFont(size=12), height=1)
        self.model_label.grid(row=5, column=0, padx=(10, 5), pady=(10, 0))
        self.model_location_button = CTkButton(self, text="Browse", command=self.find_model_location, state='disabled')
        self.model_location_button.grid(row=5, column=1, padx=(0, 5), pady=(10, 0))
        self.model_textbox = CTkTextbox(self, wrap="word", height=1)
        self.model_textbox.grid(row=5, column=2, padx=(0, 10), columnspan=3, pady=(10, 0), sticky="ew")

        # defining the naming convention
        self.naming_dropdown_label = CTkLabel(self, text="Naming convention", font=CTkFont(size=12), height = 1)
        self.naming_dropdown_label.grid(row=6, column=0, padx=(10,5), pady=(10, 0))

        naming_optionmenu_var = StringVar(value="Select")  # set initial value
        self.naming_combobox = CTkOptionMenu(self, values=["(site)_(datetime)", "(datetime)"],
                                        command=self.naming_optionmenu_callback, variable=naming_optionmenu_var)
        self.naming_combobox.grid(row=6, column=1, padx = (0,5), pady=(10, 0))
        self.naming_dropdown_textbox = CTkTextbox(self, wrap="word", height = 1)
        self.naming_dropdown_textbox.grid(row=6, column=2, columnspan=3, padx=(0, 10), pady=(10,0), sticky="ew")

        # defining the date convention
        self.date_dropdown_label = CTkLabel(self, text="Date convention", font=CTkFont(size=12), height = 1)
        self.date_dropdown_label.grid(row=7, column=0, padx=(10,5), pady=(10, 10))

        optionmenu_var = StringVar(value="Select")  # set initial value
        self.combobox = CTkOptionMenu(self, values=["AudioMoth - legacy", "AudioMoth - standard"],
                                        command=self.date_optionmenu_callback, variable=optionmenu_var)
        self.combobox.grid(row=7, column=1, padx = (0,5), pady=(10, 10))
        self.date_dropdown_textbox = CTkTextbox(self, wrap="word", height = 1)
        self.date_dropdown_textbox.grid(row=7, column=2, columnspan=3, padx=(0, 10), pady=(10,10), sticky="ew")

        # the save button
        self.save_button = CTkButton(self, text="Save", command=self.save_settings)
        self.save_button.grid(row=8, column=4, padx=10, pady=10, columnspan = 2)

    def allow_model_load(self, select_valued):
        if select_valued == "Yes":
            self.model_location_button.configure(state='normal')
        else:
            self.model_location_button.configure(state='disabled')
            self.model_textbox.delete("0.0", "end")
            self.model_textbox.insert("end", f"BirdNet")
            self.controller.model_selected = "BirdNet"

    def date_optionmenu_callback(self, choice):
        self.date_dropdown_textbox.delete("0.0", "end")
        print("optionmenu dropdown clicked:", choice)
        self.date_dropdown_textbox.insert("end", f"{choice}")

    def naming_optionmenu_callback(self, choice):
        self.naming_dropdown_textbox.delete("0.0", "end")
        print("optionmenu dropdown clicked:", choice)
        self.naming_dropdown_textbox.insert("end", f"{choice}")

    def load_csv_button(self):
        print("load_button click")
        self.attributes('-topmost', False)  # Disable topmost
        self.file_path = filedialog.askopenfilename(title = "Meta data file",filetypes=[("CSV Files", "*.csv")])
        self.attributes('-topmost', True)  # Re-enable topmost
        file_to_display = os.path.basename(self.file_path)

        if self.file_path:
                self.meta_data_textbox.delete("0.0", "end")
                # add text to display
                self.meta_data_textbox.insert("end", f"{file_to_display}") 

    def find_data_location(self):
        print('file location button')
        self.attributes('-topmost', False)  # Disable topmost
        self.controller.data_location = filedialog.askdirectory(title = "Audio directory")
        self.attributes('-topmost', True)  # Re-enable topmost
        if self.controller.data_location:
            self.data_location_textbox.delete("0.0", "end")
            self.data_location_textbox.insert("end", f"{self.controller.data_location}")

    def find_model_location(self):
        print('model location button')
        
        if self.model_text_button.get() == "No":
            self.model_textbox.delete("0.0", "end")
            self.controller.model_selected = "BirdNet"

        else:
            self.attributes('-topmost', False)  # Disable topmost 
            self.controller.model_selected = filedialog.askdirectory(title = "Custom model folder")
            self.attributes('-topmost', True)  # Re-enable topmost
        
        model_to_display = os.path.basename(self.controller.model_selected)
        
        if self.controller.model_selected:
            self.model_textbox.delete("0.0", "end")
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

        self.controller.EPSG_code = self.epsg_entry.get()
        
        # Gather all the settings
        settings = {
            'meta_data': self.meta_data_textbox.get("1.0", "end-1c"),
            'EPSG_code':  self.epsg_entry.get(),
            'data_location': self.controller.data_location,
            'model': self.controller.model_selected,
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
        
        # Check if the user hasn't selected a custom model
        if self.model_text_button.get() == "No":
            confirm_birdnet = messagebox.askyesno("Confirm BirdNet Model", "You have not selected a custom model, this means you will only be using BirdNet. Is this correct?")
            if not confirm_birdnet:
                return 
        
        # Create project_data folder
        project_data_folder = f"{project_name}_data"
        os.makedirs(project_data_folder, exist_ok=True)    
                 
        # Save settings to a pickle file with the project name
        with open(f'.\{project_name}.pkl', 'wb') as f:
            pickle.dump(settings, f)

        # Save meta_data and model to the project_data folder
        # shutil.copy(self.model_selected, project_data_folder)
        shutil.copy(self.file_path, project_data_folder)

        # Load the meta_data DataFrame from the CSV file
        data_folder = f"{project_name}_data"
        meta_data_filepath = os.path.join('.\\', data_folder, settings['meta_data'])
        self.controller.meta_data = pd.read_csv(meta_data_filepath)        
        if project_name:
            # Extract the audio file information and update the project settings
            self.controller.save_project_settings(project_name, project_data_folder, self.data_location_textbox.get("1.0", "end-1c"), self.naming_dropdown_textbox.get("1.0", "end-1c"), self.date_dropdown_textbox.get("1.0", "end-1c"))

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
        self.grid_columnconfigure((1,2,3), weight=1)
        self.grid_rowconfigure((0,1,2), weight=1)
        self.grid_rowconfigure(4, weight=0)
        
        # create sidebar frame with widgets
        self.sidebar_frame = CTkFrame(self, width=140)
        self.sidebar_frame.grid(row=0, column=0, rowspan=5, sticky="nsew", padx=(10,0), pady=10)
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.sidebar_button_1 = CTkButton(self.sidebar_frame, text="Dashboard", command=self.dashboard_button_event)
        self.sidebar_button_1.grid(row=0, column=0, padx=20, pady=(10,5))
        self.sidebar_button_1.configure(state="disabled", text="Dashboard")
        self.sidebar_button_3 = CTkButton(self.sidebar_frame, text="Validate", command=self.validate_button_event)
        self.sidebar_button_3.grid(row=1, column=0, padx=20, pady=5)

        # change project
        self.project_label = CTkLabel(self.sidebar_frame, text="Change project:", anchor="w")
        self.project_label.grid(row=4, column=0, padx=20, pady=(5, 5)) 
        self.sidebar_button_5 = CTkButton(self.sidebar_frame, text="New Project", command=self.create_button)
        self.sidebar_button_5.grid(row=4, column=0, padx=20, pady= (75, 5))
        self.sidebar_button_6 = CTkButton(self.sidebar_frame, text="Load Project", command=self.load_button)
        self.sidebar_button_6.grid(row=4, column=0, padx=20, pady= (150, 5))
        self.toplevel_window = None
        self.appearance_mode_label = CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(5, 0))
        self.appearance_mode_optionemenu = CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(5, 10))
        
        #### Classifier settings frame ####
        self.detect_frame = Detect_ModelPage(self, controller=controller)
        self.detect_frame.grid(row=0, column=1, padx=(10, 0), pady=(10, 0), sticky="nsew")
        self.detect_frame.grid_rowconfigure(0, weight=0)
        self.detect_frame.grid_columnconfigure(0, weight=1)
        
        #### Data display frame ####
        self.model_frame = CTkScrollableFrame(self)
        self.model_frame.grid(row=1, column=1, padx=(10, 0), pady=(10, 0), sticky="nsew")
        self.model_frame.grid_rowconfigure(0, weight=0) 
        self.model_frame.grid_columnconfigure(0, weight=1)

        self.model_title_frame = CTkFrame(self.model_frame)
        self.model_title_frame.grid(row =0, column = 0, padx = 5, columnspan=4, pady= 5, sticky = "ew")
        self.model_title = CTkLabel(self.model_title_frame, text = "Meta Data")
        self.model_title.grid(row = 0, column = 0, sticky = "ew", padx = (20, 0))

        self.summary_button = CTkButton(self.model_frame, text = "Show Meta data", command=self.load_summary_data)
        self.summary_button.grid(row = 1, column = 1, padx=10, pady=(5, 5), sticky = "ew")

        self.total_recordings = CTkLabel(self.model_frame, text="Total number of recordings")
        self.total_recordings.grid(row= 2, column = 0, padx=10, pady=(5, 5),sticky = "ew")
        self.total_recordings_text = CTkTextbox(self.model_frame, wrap = "word", height = 1)
        self.total_recordings_text.grid(row = 2, column = 1, padx=10, pady=(5, 5),sticky ="ew")

        self.total_sites = CTkLabel(self.model_frame, text = "Total sites")
        self.total_sites.grid(row = 3, column = 0, padx=10, pady=(5, 5),sticky = "ew")
        self.total_sites_text = CTkTextbox(self.model_frame, wrap = "word", height=1)
        self.total_sites_text.grid(row = 3, column = 1, padx=10, pady=(5, 5), sticky = "ew")

        self.total_days = CTkLabel(self.model_frame, text= "Total recording days")
        self.total_days.grid(row = 4, column = 0, padx = 10, pady = 5, sticky ="ew")
        self.total_days_text = CTkTextbox(self.model_frame, wrap = "word", height = 1)
        self.total_days_text.grid(row = 4, column = 1, padx = 10, pady = 5, sticky = "ew")

        self.mean_recordings = CTkLabel(self.model_frame, text = "Mean recordings per site")
        self.mean_recordings.grid(row = 5, column = 0, padx=10, pady=(5, 5),sticky = "ew")
        self.mean_recordings_text = CTkTextbox(self.model_frame, wrap = "word", height=1)
        self.mean_recordings_text.grid(row = 5, column = 1, padx=10, pady=(5, 5),sticky ="ew")

        self.start_date = CTkLabel(self.model_frame, text = "Start date")
        self.start_date.grid(row = 6, column = 0, padx=10, pady=(5, 5),sticky = "ew")
        self.start_date_text = CTkTextbox(self.model_frame, wrap = "word", height=1)
        self.start_date_text.grid(row = 6, column = 1, padx=10, pady=(5, 5),sticky = "ew")
        
        self.end_date = CTkLabel(self.model_frame, text = "End date")
        self.end_date.grid(row = 7, column = 0, padx=10, pady=(5, 5),sticky = "ew")
        self.end_date_text = CTkTextbox(self.model_frame, wrap = "word", height=1)
        self.end_date_text.grid(row = 7, column = 1, padx=10, pady=(5, 5),sticky = "ew")

        ### Metrics Frame ###
        self.metric_frame= CTkScrollableFrame(self)
        self.metric_frame.grid(row=2, column=1, padx=(10, 0), pady=(10, 0), sticky="nsew")
        self.metric_frame.grid_rowconfigure(0, weight=0) 
        self.metric_frame.grid_columnconfigure(0, weight=1)

        self.metric_title_frame = CTkFrame(self.metric_frame)
        self.metric_title_frame.grid(row =0, column = 0, padx = 5, columnspan=4, pady= 5, sticky = "ew")
        self.metric_title = CTkLabel(self.metric_title_frame, text = "Performance")
        self.metric_title.grid(row = 0, column = 0, sticky = "ew", padx = (20, 0))

        self.data_source = CTkLabel(self.metric_frame, text = "Select data")
        self.data_source.grid(row = 1, column = 0, padx=10, pady=(5, 5), sticky = "ew")
        self.load_data = CTkButton(self.metric_frame, text = "Load", command=self.load_data_source)
        self.load_data.grid(row = 1, column = 1, padx=10, pady=(5, 5), sticky = "ew")

        # select species
        self.species_source = CTkLabel(self.metric_frame, text = "Select species")
        self.species_source.grid(row = 2, column = 0, padx=10, pady=(5, 5), sticky = "ew")
        self.species_dropdown = CTkOptionMenu(self.metric_frame, values=["Select"])
        self.species_dropdown.grid(row=2, column=1,  padx=10, pady=(5, 5), sticky="nsew")

        self.precision = CTkLabel(self.metric_frame, text="Preicsion")
        self.precision.grid(row= 3, column = 0, padx=10, pady=(5, 5),sticky = "ew")
        self.precision_text = CTkTextbox(self.metric_frame, wrap = "word", height = 1)
        self.precision_text.grid(row = 3, column = 1, padx=10, pady=(5, 5),sticky ="ew")

        self.recall = CTkLabel(self.metric_frame, text = "Recall")
        self.recall.grid(row = 4, column = 0, padx=10, pady=(5, 5),sticky = "ew")
        self.recall_text = CTkTextbox(self.metric_frame, wrap = "word", height=1)
        self.recall_text.grid(row = 4, column = 1, padx=10, pady=(5, 5), sticky = "ew")
        
        self.save_metrics = CTkButton(self.metric_frame, text = "Save metrics", command=self.save_metric_data)
        self.save_metrics.grid(row = 5, column = 1, padx=10, pady=(5, 5), sticky = "ew")

        ### Plot instruction Frame ####
        self.plot_instructions = CTkScrollableFrame(self)
        self.plot_instructions.grid(row = 3, column = 1,  padx=(10, 0), pady=(10, 10), sticky = "ew")
        self.plot_instructions.grid_rowconfigure(0, weight=0) 
        self.plot_instructions.grid_columnconfigure(0, weight=1)

        self.plot_instructions_frame = CTkFrame(self.plot_instructions)
        self.plot_instructions_frame.grid(row = 0, column = 0, columnspan=4, padx = 5, pady= 5, sticky = "ew")
        self.plot_instructions_title = CTkLabel(self.plot_instructions_frame, text = "Plot")
        self.plot_instructions_title.grid(row = 0, column = 0, sticky = "ew", padx = (20, 0))

        self.swith_text = CTkLabel(self.plot_instructions, text = "Data Type")
        self.swith_text.grid(row = 1, column = 0, padx = 5, pady= 5, sticky = "ew")
        
        self.switch_var = StringVar(value="Raw")
        self.switch = CTkSwitch(self.plot_instructions, text = "", variable=self.switch_var, command = self.display_type, onvalue="Processed", offvalue="Raw")
        self.switch.grid(row = 1, column = 1, sticky = "ew", padx = (20, 0))
        self.switch_display = CTkTextbox(self.plot_instructions,  wrap = "word", height=1)
        self.switch_display.grid(row = 1, column = 2, sticky = "ew", padx=(5, 5), pady=(5, 5))
        self.switch_display.insert('1.0', self.switch_var.get())

        # create text for dropdown menu
        self.text_label = CTkLabel(self.plot_instructions, text="Display labels?", font=CTkFont(size=12), height = 1)
        self.text_label.grid(row=2, column=0,  padx=(5, 5), pady=(5, 5), sticky="nsew")
        self.text_var = StringVar(value="Select")  # set initial value
        self.text_dropdown = CTkOptionMenu(self.plot_instructions, values=["Yes", "No"], variable=self.text_var)
        self.text_dropdown.grid(row=2, column=2, padx=(5, 5), pady=(5, 5), sticky="nsew")
        
        self.species_label = CTkLabel(self.plot_instructions, text="Select species", font=CTkFont(size=12), height = 1)
        self.species_label.grid(row=3, column=0,  padx=(5, 5), pady=(5, 5), sticky="nsew")
        self.species_map_dropdown = CTkOptionMenu(self.plot_instructions, values=["Load data above"])
        self.species_map_dropdown.grid(row=3, column=2, padx=(5, 5), pady=(5, 5), sticky="nsew")
        self.species_map_dropdown.configure(state = "disabled")

        # create a display points button widget
        self.display_button = CTkButton(self.plot_instructions, text = "Plot", command= self.update_map_plot)
        self.display_button.grid(row=4, column=2, padx=(5, 5), pady=(5, 5), sticky="nsew")
        
        ### Create Map Frame ####
        self.map_frame = CTkFrame(self)
        self.map_frame.grid(row=0, column=2, rowspan = 4, columnspan = 2, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.map_frame.grid_rowconfigure(1, weight=1)
        self.map_frame.grid_columnconfigure(0, weight=1)

        # Configure the column and row weights in the map_frame
        self.map_frame.columnconfigure((1,2,3,4), weight=1)
        self.map_frame.columnconfigure(5, weight=0)
        self.map_frame.rowconfigure((1,2,3), weight=1)
        self.map_frame.rowconfigure(4, weight=0)
        
        self.map_widget = TkinterMapView(self.map_frame, corner_radius=10)
        self.map_widget.grid(row=1, column=0,  padx=(5, 5), pady=(5, 5), columnspan = 6, rowspan = 4, sticky="nsew")
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)  # google satellite

        # set default widget position and zoom
        self.map_widget.set_position(10.2, -83.8) # Costa Rica
        self.map_widget.set_zoom(6)      
    
    def display_type(self):
        self.switch_display.delete('1.0', 'end') 
        self.switch_display.insert('1.0', self.switch_var.get())
        if self.switch_var.get() == "Raw":
            self.species_map_dropdown.configure(state = "disabled")
            self.text_dropdown.configure(state = "normal")
        elif self.switch_var.get() == "Processed":
            self.species_map_dropdown.configure(state = "normal")
            self.text_dropdown.configure(state = "disabled")

    def save_metric_data(self):
        # Create a dataframe to store the results
        metric_data = pd.DataFrame(columns=['species', 'precision', 'recall'])
        print('Created dataframe', metric_data)
        # Loop over all the species in your data
        for species in self.data_source['common_name'].unique():
            print('Adding ', species, ' to dataframe')
            filtered_df = self.data_source[self.data_source['common_name'] == species]
            
            count_values = filtered_df['ManVal'].value_counts()
            TP = count_values.get('correct', 0)   # Returns count of 'correct' if it exists, 0 otherwise
            FP = count_values.get('incorrect', 0)   # Returns count of 'incorrect' if it exists, 0 otherwise

            if species in self.data_source.columns:
                recall_check = self.data_source[species].value_counts()
                FN = recall_check.get('incorrect', 0) # Returns count of 'incorrect' from target species column, 0 otherwise 
                recall = TP / (FN + TP) if (FN + TP) > 0 else 'NA'  # Check for ZeroDivisionError
            else:
                recall = 'NA'  # Not enough data for recall

            if TP + FP == 0:
                precision = 'NA'  # Not enough data for precision
            elif TP + FP < len(filtered_df):
                precision = 'NA'  # Not enough data for precision
            else:
                precision = TP / (TP + FP) if (TP + FP) > 0 else 'NA'  # Check for ZeroDivisionError
            
            # Append the results to the DataFrame
            try:
                metric_data = pd.concat([metric_data, pd.DataFrame({'species': [species], 'precision': [precision], 'recall': [recall]})], ignore_index=True)
                print('Appending: ', species)
            except Exception as e:
                print('Error while appending: ', e)
        
        # Generate the file name by adding '_metrics' before the file extension
        file_name, file_extension = os.path.splitext(self.file_path)
        metrics_file_path = f"{file_name}_metrics{file_extension}"
        
        # Save the DataFrame to a csv file
        metric_data.to_csv(metrics_file_path, index=False)

        print(f"Metrics data saved to: {metrics_file_path}")

    def load_data_source(self):
        print('Load data source')
        self.file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        self.data_source = pd.read_csv(f'{self.file_path}')
        
        self.unique_values = self.data_source['common_name'].unique().tolist()
        self.species_dropdown.destroy()
        self.species_map_dropdown.destroy()
        self.text_dropdown.configure(state = "disabled")

        self.species_var = StringVar(value=self.unique_values[0])
        self.species_dropdown = CTkOptionMenu(self.metric_frame, values=self.unique_values, variable=self.species_var, command=self.show_metrics, dynamic_resizing = False)
        self.species_dropdown.grid(row=2, column=1, padx=10, pady=(5, 5), sticky="nsew")
        
        self.species_plot_var = StringVar(value=self.unique_values[0])
        self.species_map_dropdown = CTkOptionMenu(self.plot_instructions, values=self.unique_values, variable=self.species_plot_var, dynamic_resizing = False)
        self.species_map_dropdown.grid(row=3, column=2, padx=(5, 5), pady=(5, 5), sticky="nsew")
        self.show_metrics(self.species_var.get())

    def show_metrics(self, value):
        print('Species:', value)
        self.precision_text.delete('1.0', 'end')
        self.recall_text.delete('1.0', 'end')

        filtered_df = self.data_source[self.data_source['common_name'] == value]
        
        count_values = filtered_df['ManVal'].value_counts()

        TP = count_values.get('correct', 0)   # Returns count of 'correct' if it exists, 0 otherwise
        FP = count_values.get('incorrect', 0)   # Returns count of 'incorrect' if it exists, 0 otherwise

        if value in self.data_source.columns:
            recall_check = self.data_source[value].value_counts()
            FN = recall_check.get('incorrect', 0) # Returns count of 'incorrect' from target species column, 0 otherwise 
            recall = TP / (FN + TP)   
        else:
            recall = "Please Validate negatives"

        if TP + FP == 0:
            precision = "Please Validate positives"
        elif TP + FP < len(filtered_df):
            precision = "Validation not complete" 
        else:
            precision = TP / (TP + FP) if (TP + FP) > 0 else 0 # Check for ZeroDivisionError

        print('Precision = ', precision,'\nRecall')

        self.precision_text.insert('1.0', precision)
        self.recall_text.insert('1.0', recall)

    def load_summary_data(self):
        self.controller.load_project_settings(self.controller.project_name)
       
        # get information on recordings
        self.site_data = self.controller.site_recording_data
        # get information on sites
        self.summary_data = self.controller.summary_data

        # First, convert the 'date_time' column to a datetime object
        self.site_data['date'] = pd.to_datetime(self.site_data['date'])

        self.dates = self.site_data.agg(
            start_date=('date', 'min'),
            end_date=('date', 'max'))
        
        # Get the start_date and end_date as individual variables and convert them to desired format
        start_date = self.dates.at['start_date', 'date'].strftime('%d-%m-%Y')
        end_date = self.dates.at['end_date','date'].strftime('%d-%m-%Y')
        
        # Calculate the total number of days between start_date and end_date
        start_date_datetime = self.dates.at['start_date', 'date']
        end_date_datetime = self.dates.at['end_date', 'date']
        total_days = (end_date_datetime - start_date_datetime).days
        
        # Insert the dates into the textboxes
        self.start_date_text.delete('1.0', 'end')
        self.start_date_text.insert('1.0', start_date)

        self.end_date_text.delete('1.0', 'end')
        self.end_date_text.insert('1.0', end_date)

        self.total_recordings_text.delete('1.0', 'end')
        self.total_recordings_text.insert('1.0', len(self.site_data['file_name']))

        self.mean_recordings_text.delete('1.0', 'end')
        self.mean_recordings_text.insert('1.0', round(len(self.site_data['file_name']) / len(self.summary_data['site'])),0)

        self.total_sites_text.delete('1.0', 'end')
        self.total_sites_text.insert('1.0', len(self.summary_data['site']))

        self.total_days_text.delete('1.0', 'end')
        self.total_days_text.insert('1.0', total_days)

    def convert_coordinates(self, long, lat):
        # get the EPSG code from the project settings
        current_proj = self.controller.EPSG_code

        # transform from current EPSG to 4326
        transformer = Transformer.from_crs(current_proj, "EPSG:4326")
        long_converted, lat_converted  = transformer.transform(long, lat)

        return lat_converted, long_converted
    
    def generate_coordinates(self):
        # Create an empty DataFrame to store the converted coordinates
        self.converted_coordinates = pd.DataFrame(columns=['site','lat', 'long'])

        # extract the coordinates and store as markers
        for index, row in self.controller.meta_data.iterrows():
            # convert to 4326
            lat_converted, long_converted = self.convert_coordinates(row['long'], row['lat'])
 
            # Store the converted coordinates in the DataFrame
            self.converted_coordinates.loc[index] = [row['site'], lat_converted, long_converted]

        # get a bounding box to reposition the map view to
        max_lat = self.converted_coordinates['lat'].max()  # Most northern point
        min_lat = self.converted_coordinates['lat'].min()  # Most southern point

        max_long = self.converted_coordinates['long'].max()  # Most eastern point
        min_long = self.converted_coordinates['long'].min()  # Most western point

        self.south_east_point = (min_long, max_lat)
        self.north_west_point = (max_long, min_lat)

    def update_map_plot(self):
        print('Update_plot run')
                          
        if hasattr(self, 'converted_coordinates'):
            print('Coordinates already exist:', self.north_west_point, self.south_east_point)
        else:    
            self.generate_coordinates()
            print('Generated coordindates:', self.north_west_point, self.south_east_point)
        
        print(self.switch_var.get())
                   
        if self.switch_var.get() == "Processed":
            if self.species_map_dropdown.get() == "Load data above":
                messagebox.showerror("Error", "Please load data in *Performance* section")
                return
            else:
                if self.map_widget:
                    self.map_widget.destroy()
                    print('Removing map_widget')
                
                # Construct bounding box
                minx, miny = self.south_east_point
                maxx, maxy = self.north_west_point
                bbox = (minx, maxy, maxx, miny)  # Overpass API uses (lat, lon) order
                print(bbox)

                # Use Overpass API to get country names that intersect the bounding box
                overpass_url = "http://overpass-api.de/api/interpreter"
                overpass_query = f"""
                [out:json];
                (
                relation["boundary"="administrative"]["admin_level"="2"]{bbox};
                );
                out body;
                >;
                out skel qt;
                """
                response = requests.get(overpass_url, params={'data': overpass_query})

                if response.status_code == 200:
                    # Successful request
                    data = response.json()
                elif response.status_code == 400:
                    # Bad request
                    print("Bad Request: ", response.text)
                else:
                    # Other error
                    print(f"HTTP {response.status_code}: ", response.text)


                countries = set()
                for element in data['elements']:
                    if element['type'] == 'relation':
                        for tag in element['tags']:
                            if tag == 'name:en':
                                countries.add(element['tags'][tag])

                print(countries)

                # Create the map figure and axis
                fig = Figure(figsize=(5, 5), dpi=100)  # Adjust figure size as needed
                ax = fig.add_subplot(111)
                ax.set_aspect('equal')

                with open('./country_codes.txt', 'r') as f:
                    COUNTRY_CODES = json.load(f)

                # Plot the base map
                tif_files = []
                for country in countries:
                    if country in COUNTRY_CODES:
                        tif_files.append(f'./country_geo/{COUNTRY_CODES[country]}_lc.tif')

                bbox_polygon = {
                    'type': 'Polygon',
                    'coordinates': [[
                        [minx, miny],
                        [minx, maxy],
                        [maxx, maxy],
                        [maxx, miny],
                        [minx, miny]
                    ]]
                }

                # Open and crop the raster data for each country
                for tif_file in tif_files:
                    # Open the raster file
                    with rasterio.open(tif_file) as src:
                        # Transform the bounding box to the same CRS as the raster
                        bbox_transformed = rasterio.warp.transform_bounds(src.crs, {'init': 'epsg:4326'}, *bbox)
                        # Check if the bounding box intersects the raster
                        if not rasterio.coords.disjoint_bounds(bbox_transformed, src.bounds):
                            # The bounding box intersects the raster
                            out_image, out_transform = rasterio.mask.mask(src, [bbox_polygon], crop=True)
                            out_meta = src.meta
                        else:
                            # The bounding box does not intersect the raster
                            print('The bounding box does not intersect the raster.')

                    out_meta.update({"driver": "GTiff",
                                    "height": out_image.shape[1],
                                    "width": out_image.shape[2],
                                    "transform": out_transform})

                    # Plot the cropped raster data
                    ax.imshow(out_image[0], cmap='viridis', aspect='auto')

                # Filter data by species and compute point sizes
                filtered_data = self.data_source[self.data_source['common_name'] == self.species_var.get()]
                sizes = filtered_data['ManVal'].apply(lambda x: 10 if x == 'correct' else 0)  # Adjust as needed

                # Plot points for each site
                for site, size in zip(self.converted_coordinates, sizes):
                    ax.plot(*site, 'o', color='black', markersize=size)

                # Set title and display the map
                ax.set_title(self.species_var.get())

                # Create canvas and draw the plot onto the canvas
                canvas = FigureCanvasTkAgg(fig, master=self.map_frame)  # Pass in the parent widget
                canvas.draw()

                # Get the widget from the canvas and grid it into the parent widget
                self.canvas_widget = canvas.get_tk_widget()
                self.canvas_widget.grid(row=1, column=0, padx=(5, 5), pady=(5, 5), columnspan=6, rowspan=4, sticky="nsew")   
            
        elif self.switch_var.get() == "Raw":
            
            # Clear existing markers from the map
            if self.controller.markers:
                for element in self.controller.markers:
                    element.delete()
            
            # Check if the text_var value is "Yes" or "No"
            if not (self.text_var.get() == "Yes" or self.text_var.get() == "No"):
                messagebox.showerror("Error", "Please set label display")
                return
            else:
                # load the point image:
                round_icon = ImageTk.PhotoImage(Image.open(os.path.join('.\\', "round_icon.png")).resize((10, 10)))
                
                if hasattr(self, 'canvas_widget'):
                    self.canvas_widget.destroy()
                if hasattr(self, 'map_widget'):
                    self.map_widget.destroy()

                print('Start of Map plot')
                self.map_widget = TkinterMapView(self.map_frame, corner_radius=10)
                self.map_widget.grid(row=1, column=0,  padx=(5, 5), pady=(5, 5), columnspan = 6, rowspan = 4, sticky="nsew")
                self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)  # google satellite
                print('Running raw sites')
                
                for index, row in self.converted_coordinates.iterrows():
                    long_converted, lat_converted = row['long'], row['lat']

                    if self.text_var.get() == "Yes":
                        marker = self.map_widget.set_marker(long_converted, lat_converted, text=row['site'], icon = round_icon, text_color = "#FFFFFF")
                        self.controller.markers.append(marker)
                    else:
                        marker = self.map_widget.set_marker(long_converted, lat_converted, icon = round_icon)
                        self.controller.markers.append(marker) 
                
                self.map_widget.fit_bounding_box(self.north_west_point, self.south_east_point)

    def dashboard_button_event(self):
            print("sidebar_button click")
            self.master.show_frame(Dashboard)

    def validate_button_event(self):
            print("validate_button click")
            self.master.show_frame(ValidatePage)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        set_appearance_mode(new_appearance_mode)

    def dash_change_subframe(self, dash_subframe_name):

        # load the site_data information
        self.controller.site_recording_data = self.controller.project_settings['site_recording_data']

        if dash_subframe_name == 'Dashboard':
            self.dashboard_scrollable_frame.show_subframe(dash_subframe_name + 'SubFrame')
        else:
            self.dashboard_scrollable_frame.show_subframe(dash_subframe_name + 'SubFrame')

    def validate_change_subframe(self, validate_subframe_name):
        if validate_subframe_name == 'Validate':
            self.master.show_frame(ValidatePage)
        else:
            self.validate_frame_table.show_subframe(validate_subframe_name + 'Page')
            
    def detect_change_subframe(self, detect_subframe_name):
        if detect_subframe_name == "Detect":
            self.detect_scrollable_frame.show_subframe('Detect_ModelPage')
        else:
            self.detect_scrollable_frame.show_subframe('Detect_' + detect_subframe_name + 'Page')

    def create_button(self):
            print("create_button click")
            if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
                self.toplevel_window = ToplevelWindow(self, controller=self.master)  # create window if its None or destroyed
            else:
                self.toplevel_window.focus()  # if window exists focus it

    def load_button(self):
            print("load_button click")
            file_path = filedialog.askopenfilename(filetypes=[("Pickle files", "*.pkl")])

            # Remove the extension from the file_path
            file_name_without_extension, ext = os.path.splitext(os.path.basename(file_path))

            # Update the project settings in the main controller
            self.controller.load_project_settings(os.path.basename(file_name_without_extension))         

class Detect_ModelPage(CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Get frame title
        self.title_frame = CTkFrame(self)
        self.title_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
        self.model_label = CTkLabel(self.title_frame, text='Classifier settings')
        self.model_label.grid(row=0, column=0, sticky="ew", padx=15, pady=(0,5))

        # Model name text
        self.model_label = CTkLabel(self, text='Are you using BirdNet?')
        self.model_label.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        self.birdnet_option = CTkOptionMenu(self, values=["Yes", "No"], command=self.get_model_name)
        self.birdnet_option.grid(row=1, column=1, padx=10, pady=5)
        self.birdnet_option.set("Yes")

        # Test labels / text
        self.model_label = CTkLabel(self, text='Is this a test?')
        self.model_label.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        self.test_option = CTkOptionMenu(self, values=["Yes", "No"],
                                        command=self.get_test_status)
        self.test_option.grid(row=2, column=1, padx=10, pady=5)
        self.test_option.set("Yes")

        # Confidence level text / label
        self.min_confid_label = CTkLabel(self, text = 'Minimum confidence:')
        self.min_confid_label.grid(row=3, column =0, sticky = "ew", padx = 10, pady = 5)

        self.min_confid_text = CTkEntry(self, placeholder_text= "0-0.99")
        self.min_confid_text.grid(row=3, column =1, sticky = "ew", padx=10, pady=5)

        self.settings_button_2 = CTkButton(self, text="Run", command=self.run)
        self.settings_button_2.grid(row=4, column=1, padx=10, pady=(5,10)) 
    
    def select_custom_model(self):
        print('Select custom model')
        
        model_to_display = 'to set'
        self.custom_model_text.delete("0.0", "end")
        self.custom_model_text.insert("end", f"{model_to_display}")

    def get_test_status(self, value):
        print("switch toggled, test status:", value)

    def get_model_name(self, value):
        print("Get model name:", value)
        if value == "No":
            self.min_confid_text.configure(state="disabled")
        else:
            self.min_confid_text.configure(state="normal")

            
    def preprocess_audio(self, audio_file):
        # Load the audio file using librosa
        audio, sr = librosa.load(audio_file, sr=22050)

        # Calculate the duration of the audio in samples
        duration_samples = len(audio)

        # Set the desired segment length (1 second)
        segment_length_samples = sr

        # Initialize an empty list to store the segments
        segments = []

        # Iterate over the audio and create 1-second segments
        for start_sample in range(0, duration_samples, segment_length_samples):
            end_sample = start_sample + segment_length_samples

            # Extract the segment from the audio
            segment = audio[start_sample:end_sample]

            # Convert the segment to a melspectrogram
            segment_melspectrogram = self.audio_to_melspectrogram(segment, sr)

            # Append the melspectrogram segment to the list
            segments.append(segment_melspectrogram)

        return np.array(segments)

    def audio_to_melspectrogram(self, audio, sr):

        # create spectrogram
        S = librosa.feature.melspectrogram(y=audio, sr=sr, n_fft=1024, hop_length=256,
                                        n_mels=128, fmin=500, fmax=9000)

        image = librosa.core.power_to_db(S)
        image_np = np.asmatrix(image)
        image_np_scaled_temp = (image_np - np.min(image_np))
        image_np_scaled = image_np_scaled_temp / np.max(image_np_scaled_temp)
        mean = image.flatten().mean()
        std = image.flatten().std()
        eps = 1e-8
        spec_norm = (image - mean) / (std + eps)
        spec_min, spec_max = spec_norm.min(), spec_norm.max()
        spec_scaled = (spec_norm - spec_min) / (spec_max - spec_min)
        S1 = spec_scaled

        # 3 different input
        return np.stack([S1, S1**3, S1**5], axis=2)

    def process_predictions(self, predictions, audio_file):
        # Get the class labels
        class_labels = ['No', 'GGM', 'SCM']
        
        # Get the class with the highest probability for each segment
        pred_classes = np.argmax(predictions, axis=1)

        # Convert the class indices to their corresponding labels
        pred_labels = [class_labels[i] for i in pred_classes]

        # Initialize the result DataFrame
        result = pd.DataFrame(columns=['sound.files','start_time', 'end_time', 'class'])

        # Loop through the segments and process the predictions
        i = 0
        while i < len(pred_labels):
            if pred_labels[i] != 'No':
                start_time = i
                end_time = i + 1
                current_class = pred_labels[i]

                # Combine adjacent segments of the same class
                while (i + 1 < len(pred_labels)) and (pred_labels[i + 1] == current_class):
                    end_time += 1
                    i += 1

                # Add the combined segments to the result DataFrame
                new_row = pd.DataFrame({'sound.files': [audio_file], 'start_time': [start_time], 'end_time': [end_time], 'class': [current_class]})
                result = pd.concat([result, new_row], ignore_index=True)
            i += 1

        return result

    
    def run_custom(self, audio_file, model):
        # Preprocess the audio file and run it through the model
        # This will depend on how your model is designed
        # Make sure to adapt this function to your specific use case

        # For example:
        processed_audio = self.preprocess_audio(audio_file)
        predictions = model.predict(processed_audio)
        
        # Process the model predictions and return the result
        result = self.process_predictions(predictions, audio_file)
        return result
    
    def load_model(self):
        # Load your TensorFlow model here
        print(self.controller.model_selected)
        model = tf.keras.models.load_model(self.controller.model_selected)
        return model
    
    def extract_site_name(self, file):
        file_base = os.path.basename(file)
        
        # split the file into two
        site_name, _ = file_base.split('_')

        return site_name

    def run_model(self):
        print('Run model')
        # Load your TensorFlow model here
        self.model = self.load_model()

        # Create an empty DataFrame to store the results
        combined_results = pd.DataFrame()

        directory_path = self.controller.data_location
        
        if self.controller.name_convention == "(site)_(datetime)":
            data = [file for file in os.listdir(directory_path) if file.endswith('.WAV')]
            data_paths = [os.path.join(directory_path, file) for file in data]         
            if self.test_option.get() == "Yes":
                results = self.popup_model(data_paths[0:10], combined_results)
            else:
                results = self.popup_model(data_paths, combined_results)
        
        elif self.controller.name_convention == "(datetime)":
            items = os.listdir(directory_path)
            site_files = [item for item in items if os.path.isdir(os.path.join(directory_path, item))]
            for site in site_files:
                data = [file for file in os.listdir(site) if file.endswith('.WAV')]
                data_paths = [os.path.join(directory_path, site, file) for file in data]
                if self.test_option.get() == "Yes":
                    results_site = self.popup_model(data_paths[0:10], combined_results)
                else:
                    results_site = self.popup_model(data_paths, combined_results)
                
                results = pd.concat([combined_results, results_site], axis=0, ignore_index=True)
        else:
            print('Error creating file paths')
        
        current_datetime = datetime.now()
        formatted_datetime_with_underscores = current_datetime.strftime("%Y-%m-%d %H:%M:%S").replace(" ", "_").replace(":", "_").replace("-", "_")

        results.to_csv(os.path.join('.\\', self.controller.data_folder, 'all_detections_'+ formatted_datetime_with_underscores + '.csv'))
        
        # save to the controller
        self.controller.detections = results

        try:
            with open(f'.\{self.controller.project_name}.pkl', 'rb') as f:
                self.project_settings = pickle.load(f)
        except FileNotFoundError as e:
            print(f"Error loading project file: {e}")
            return False
        
        # Save the DataFrame in the project_settings dictionary
        self.project_settings['detections_' + formatted_datetime_with_underscores] = results

        with open(f'.\{self.controller.project_name}.pkl', 'wb') as f:
            pickle.dump(self.project_settings, f)
        
        print('Data saved') 

        return results
    
    def popup_model(self, data_paths, df):
        popup = ModelProgressPopup(self, self, len(data_paths))
        for index, wav_file in enumerate(data_paths, start=1):
            result = self.custom_analyse_file(popup, index, wav_file, df)     
                
            # Append the result DataFrame to the combined_results DataFrame
            combined_results = pd.concat([df, result], axis=0, ignore_index=True)
        
        # Close the popup window
        popup.destroy()   
        
        return combined_results

    def custom_analyse_file(self, popup, index, wav_file, df):
        popup.update_progress(index, wav_file)
        results = self.run_custom(wav_file, self.model)
        combined_results = pd.concat([df, results], axis=0, ignore_index=True)
        
        return combined_results  
    
    def birdnet(self, site, audio_file, lat, long, year, month, day, time, min_conf):
        # Load and initialize the BirdNET-Analyzer models.
        analyzer = Analyzer()

        print("File:", audio_file, 
              "\nLat:", lat, 
              "\nLong:", long, 
              "\nDate:", datetime(year, month, day),
              "\nMin confidence:", min_conf)
        
        recording = Recording(
            analyzer,
            audio_file,
            lat=lat,
            lon=long,
            week_48=-1,
            date = datetime(year = year, month= month, day = day),
            min_conf=min_conf,
        )
        recording.analyze()
        print('Detections:' ,recording.detections)
        
        # Convert the list of dictionaries to a DataFrame
        df = pd.DataFrame(recording.detections)

        # Add a new column 'site' with a default value
        df["site"] = site
        df["date"] = datetime(year = year, month= month, day = day)
        df['time'] = time
        df['sound.file'] = audio_file

        return df
    
    def get_recording_info(self, wav_file):
        meta_data = self.controller.meta_data
        site_data = self.controller.site_recording_data 

        # get the row for the date / site
        file_row = site_data.loc[site_data['file_name'] == os.path.basename(wav_file)]
        print(file_row)
        
        # get the date requirements
        date = file_row['date_time'].values[0] # get the date 
        date_object = pd.to_datetime(date).to_pydatetime()
        print('Datetime:', date_object)
        
        week_number = int(date_object.strftime("%U")) + 1
        print('Week number:', week_number)  

        year = date_object.year
        month = date_object.month
        day = date_object.day
        time = date_object.time 
        
        site = file_row['site'].values[0] # get the site

        # get the row for the coordinates
        meta_row = meta_data.loc[meta_data['site'] == site]
        print(meta_row)
        
        lat =  meta_row['lat'].values[0] # get the lat
        long =  meta_row['long'].values[0] # get the long

        # transform from current EPSG to 4326
        transformer = Transformer.from_crs(self.controller.EPSG_code, "EPSG:4326")
        lat_converted, long_converted  = transformer.transform(long, lat)

        print('Lat:', lat_converted, 'Long:', long_converted)

        return site, lat_converted, long_converted, year, month, day, time
    
    def birdnet_analyse_file(self, popup, index, wav_file, df):
        popup.update_progress(index, wav_file)   
        site, lat, long, year, month, day, time = self.get_recording_info(wav_file)
        results = self.birdnet(site, wav_file, lat, long, year, month, day, time, float(self.min_confid_text.get()))
        combined_results = pd.concat([df, results], axis=0, ignore_index=True) 

        return  combined_results   
    
    def make_detections(self, data_paths):
        combined_results = pd.DataFrame()

        if self.test_option.get() == "Yes":
            popup = ModelProgressPopup(self, self, len(data_paths[0:10]))
            for index, wav_file in enumerate(data_paths[0:10], start=1):
                combined_results = self.birdnet_analyse_file(popup, index, wav_file, combined_results)             
        else: 
            popup = ModelProgressPopup(self, self, len(data_paths))
            for index, wav_file in enumerate(data_paths, start=1):
                combined_results = self.birdnet_analyse_file(popup, index, wav_file, combined_results)

        popup.destroy()
        return combined_results 

    def run_birdnet(self):
        directory_path = self.controller.data_location
        
        if self.controller.name_convention == "(site)_(datetime)":
            data = [file for file in os.listdir(directory_path) if file.endswith('.WAV')]
            data_paths = [os.path.join(directory_path, file).replace("\\", "/") for file in data]
            all_detections = self.make_detections(data_paths)

        elif self.controller.name_convention == "(datetime)":
            holding_df = pd.DataFrame()
            items = os.listdir(directory_path)
            folders = [item for item in items if os.path.isdir(os.path.join(directory_path, item))]
            for site in folders:
                data = [file for file in os.listdir(site) if file.endswith('.WAV')]
                data_paths = [os.path.join(directory_path, site, file).replace("\\", "/") for file in data]
                detections = self.make_detections(data_paths)
                all_detections = pd.concat([holding_df, detections], axis=0, ignore_index=True)
        else:
            print('Error creating file paths') 
        
        current_datetime = datetime.now()
        formatted_datetime_with_underscores = current_datetime.strftime("%Y-%m-%d %H:%M:%S").replace(" ", "_").replace(":", "_").replace("-", "_")

        all_detections.to_csv(os.path.join('.\\', self.controller.data_folder, 'all_detections_'+ formatted_datetime_with_underscores + '.csv'))
        
        # save to the controller
        self.controller.detections = all_detections

        try:
            with open(f'.\{self.controller.project_name}.pkl', 'rb') as f:
                self.project_settings = pickle.load(f)
        except FileNotFoundError as e:
            print(f"Error loading project file: {e}")
            return False
        
        # Save the DataFrame in the project_settings dictionary
        self.project_settings['detections_' + formatted_datetime_with_underscores] = all_detections

        with open(f'.\{self.controller.project_name}.pkl', 'wb') as f:
            pickle.dump(self.project_settings, f)
        
        print('Data saved')             
    
    def run(self):
        if not os.path.exists(self.controller.data_location):
            messagebox.showerror("Error", "Audio directory not found. Please check path exists")
            return

        if self.birdnet_option.get() == "Yes":
            if float(self.min_confid_text.get()) > 1:
                messagebox.showerror("Error", "The minimum confidence value should not be >1.")
                return
            elif float(self.min_confid_text.get()) == '':
                messagebox.showerror("Error", "Please enter a minimum confidence value (<1)")
                return
            elif float(self.min_confid_text.get()) < 0:
                messagebox.showerror("Error", "Don't be an idiot")
                return
            else:
                self.run_birdnet()
        elif self.birdnet_option.get() == "No":
            self.run_model()

class ModelProgressPopup(CTkToplevel):
    def __init__(self, parent, controller, total_files):
        super().__init__(parent)
        self.controller = controller
        self.total_files = total_files

        self.title("Processing Files")
        self.attributes('-topmost', True)

        self.message_label = CTkLabel(self)
        self.message_label.grid(row=0, column=0, columnspan = 3, padx = 5, pady = 5, sticky="nsew")
        
        self.progress_bar = ttk.Progressbar(self, length=200)
        self.progress_bar.grid(row=0, column=3, padx = 5, pady = 5, sticky="nsew")
        self.progress_bar['maximum'] = self.total_files

        self.counter_label = CTkLabel(self)      
        self.counter_label.grid(row=0, column=4, padx = 5, pady = 5, sticky="nsew")
       
        message = f"Launching model..."
        counter = f"0/{self.total_files}"
        self.message_label.configure(text=message)
        self.counter_label.configure(text=counter)
        self.update_idletasks()
        self.update()

    def update_progress(self, current_index, file_name):
        message = f"Analysing {os.path.basename(file_name)}"
        counter = f"{current_index}/{self.total_files}"

        self.message_label.configure(text=message)
        self.counter_label.configure(text=counter)
        self.progress_bar['value'] = current_index

        self.update_idletasks()
        self.update()
           
class ValidatePage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        pygame.mixer.init()  # initialize pygame mixer for audio playback
        self.is_playing = False
        self.time_format = '%Y-%m-%d %H:%M:%S'
        self.spectrogram_canvas = None
        self.animation_line = None

        # configure grid layout (4x4)
        self.grid_columnconfigure((1,2,3,4,5,6), weight=1)
        self.grid_rowconfigure((1,2,3,4,5,6,7), weight=1)
        self.grid_rowconfigure(8, weight=0)

        # create sidebar frame with widgets
        self.sidebar_frame = CTkFrame(self, width=140)
        self.sidebar_frame.grid(row=0, column=0, rowspan=9, sticky="nsew", padx=(10,0), pady=10)
        for row in range(10):
            self.sidebar_frame.grid_rowconfigure(row, weight=1 if row == 8 else 0)
        self.sidebar_button_1 = CTkButton(self.sidebar_frame, text="Dashboard", command=self.dashboard_button_event)
        self.sidebar_button_1.grid(row=0, column=0, padx=20, pady=(10,5))  
        self.sidebar_button_3 = CTkButton(self.sidebar_frame, text="Validate", command=self.validate_button_event)
        self.sidebar_button_3.grid(row=1, column=0, padx=20, pady=5)
        self.sidebar_button_3.configure(state="disabled", text="Validate")   
        self.filler = CTkLabel(self.sidebar_frame,  text = "")
        self.filler.grid(row=3, column=0, padx=20, pady=5)
        self.get_data_button = CTkButton(self.sidebar_frame, text = "Select data", command=self.get_data)
        self.get_data_button.grid(row=4, column=0, padx=20, pady=5)
        self.dropdown = CTkOptionMenu(self.sidebar_frame, values=["Species"])
        self.dropdown.grid(row=5, column=0,  padx=20, pady=5)
        self.metric_var = StringVar(value="Metric")
        self.metric = CTkOptionMenu(self.sidebar_frame, values=["Precision", "Recall"], command=self.specify_metric,
                                         variable=self.metric_var)
        self.metric.grid(row=6, column=0,  padx=20, pady=5)
        self.load_button = CTkButton(self.sidebar_frame, text="Load Audio", command=self.load_audio)
        self.load_button.grid(row=7, column=0,  padx=20, pady=(5,10))

        self.play_button = CTkButton(self, text="Play", command=self.play)
        self.play_button.grid(row=8, column=1, sticky="nsew", padx=(10,0), pady=10)
        self.play_button["state"] = "disabled"

        self.previous_button = CTkButton(self, text="Previous", command=self.previous_row)
        self.previous_button.grid(row=8, column=2, sticky="nsew", padx=(10,0), pady=10)

        self.next_button = CTkButton(self, text="Next", command=self.next_row)
        self.next_button.grid(row=8, column=3, sticky="nsew", padx=(10,0), pady=10)

        self.correct_button = CTkButton(self, text = "Correct", command= self.mark_correct)
        self.correct_button.grid(row=8, column=4, sticky="nsew", padx=(10,0), pady=10)

        self.incorrect_button = CTkButton(self, text = "Incorrect", command= self.mark_incorrect)
        self.incorrect_button.grid(row=8, column=5, sticky="nsew", padx=(10,0), pady=10)

        self.save_button = CTkButton(self, text = "Save", command= self.save_df_to_csv)
        self.save_button.grid(row=8, column=6, sticky="nsew", padx=(10,10), pady=10)

        self.spectrogram_frame = CTkFrame(self)
        self.spectrogram_frame.grid(row=1, column=1, columnspan = 6, rowspan = 7, sticky="nsew", padx=10, pady=(10,0))
     
    def get_data(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        self.df = pd.read_csv(f'{self.file_path}')

        self.unique_values = self.df['common_name'].unique().tolist()
        self.dropdown.destroy()

        self.species_var = StringVar(value=self.unique_values[0])
        self.dropdown = CTkOptionMenu(self.sidebar_frame, values=self.unique_values, variable=self.species_var, command=self.specify_species, dynamic_resizing = False)
        self.dropdown.grid(row=5, column=0, padx=20, pady=5)

    def specify_species(self, value):
        print('Focal species:', value)
        self.species_var.set(value)

    def specify_metric(self, value):
        print('Metric:', value)
        self.metric_var.set(value)

    def load_audio(self):
        if 'ManVal' not in self.df.columns:
            self.df['ManVal'] = ''

        if self.metric_var.get() == "Precision":
            # filter the dataframe for rows where 'common_name' matches the current species
            self.df_filtered = self.df[self.df['common_name'] == self.species_var.get()]
                
        elif self.metric_var.get() == "Recall":
            # get start times where 'common_name' is equal to species_var.get()
            same_species_start_times = self.df[self.df['common_name'] == self.species_var.get()]['start_time']
            
            # filter for rows where 'common_name' is not the current species and start_time is not in same_species_start_times
            self.df_filtered = self.df[(~self.df['start_time'].isin(same_species_start_times)) & (self.df['common_name'] != self.species_var.get())]
            
            # Remove any duplicate rows based on start_time and end_time
            self.df_filtered = self.df_filtered.drop_duplicates(subset=['start_time', 'end_time'])
            
            # If df_filtered has more than 2000 rows, sample 2000 rows. Otherwise, use all rows.
            if len(self.df_filtered) > 2000:
                self.df_filtered = self.df_filtered.sample(n=2000, random_state=1)

            if self.species_var.get() not in self.df.columns:
                self.df[self.species_var.get()] = ''
                print(self.species_var.get())

        # find the row index
        self.valid_rows = self.df_filtered.index.tolist()
        print(self.valid_rows)

        self.current_row_index = self.valid_rows[0]
        self.current_valid_row_pointer = 0

        self.play_button["state"] = "normal"
        self.load_audio_from_current_row()

 
    def load_audio_from_current_row(self):
        print('Load row ', self.current_row_index)
        row = self.df.loc[self.current_row_index]
        print(row)
        self.start = row['start_time']
        self.new_start = max(0, self.start - 2)
        self.new_end = self.new_start + 5
        self.end = row['end_time']
        length =  round(self.end - self.start, 0)
        middle = self.start + (length / 2)
        label = row['common_name']
        self.status = row['ManVal']
        self.recall_status = row[self.species_var.get()]
        
        # ensure we are not loading a whole new sound file when we don't need to as we are loading full files to enable the playback
        try:
            self.audio_file_name
        except:
            self.audio_file_name = os.path.basename(row['sound.file'])
            pygame.mixer.music.load(f'{self.controller.data_location}/{self.audio_file_name}')
            # Load audio file
            print('Loading new sound file')
        else:
            if os.path.basename(row['sound.file']) != self.audio_file_name:
                self.audio_file_name = os.path.basename(row['sound.file'])
                pygame.mixer.music.load(f'{self.controller.data_location}/{self.audio_file_name}')
                # Load audio file
                print('Loading new sound file')
            else:
                print('Using the existing sound files for playback')

        if length > 1:
            self.new_start = middle - 2.5
            self.audio, self.sr = librosa.load(f'{self.controller.data_location}/{self.audio_file_name}', offset = self.new_start, duration = 5)
            self.visualize_audio(1, 4, label)
        else: 
            self.audio, self.sr = librosa.load(f'{self.controller.data_location}/{self.audio_file_name}', offset = self.new_start, duration = 5)
            self.visualize_audio(2, 3, label)

    def mark_correct(self):
        print('Mark correct')
        if self.metric_var.get() == 'Precision':
            self.df.loc[self.current_row_index, "ManVal"] = "correct"
        elif self.metric_var.get() == 'Recall':
            self.df.loc[self.current_row_index, self.species_var.get()] = "correct"

        self.next_row()
        self.update_idletasks()  # force Tkinter to process any pending tasks

    def mark_incorrect(self):
        print('Mark incorrect')       
        if self.metric_var.get() == 'Precision':
            self.df.loc[self.current_row_index, "ManVal"] = "incorrect"
        elif self.metric_var.get() == 'Recall':
            self.df.loc[self.current_row_index, self.species_var.get()] = "incorrect"

        self.next_row()
        self.update_idletasks()  # force Tkinter to process any pending tasks

    def next_row(self):
        try:
            if self.anim is not None:
                print('Audio and Animation Stop')
                self.anim.event_source.stop()
                self.animation_line.set_xdata([0, 0])
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                self.is_playing = False

            # assuming self.current_valid_row_pointer is already defined somewhere else
            # and is updated every time next_row is called
            self.current_valid_row_pointer += 1  

            if self.current_valid_row_pointer >= len(self.valid_rows):
                self.current_valid_row_pointer = len(self.valid_rows) - 1  # Don't go past the end of the valid_rows list
            print('Current valid row pointer: ', self.current_valid_row_pointer)

            self.current_row_index = self.valid_rows[self.current_valid_row_pointer]  # update current row index using valid row pointer
            self.load_audio_from_current_row()
            print('Next')
        except Exception as e:
            print(f'Exception in next_row: {e}')

    def previous_row(self):
        try:
            if self.anim is not None:
                print('Audio and Animation Stop')
                self.anim.event_source.stop()
                self.animation_line.set_xdata([0, 0])
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                self.is_playing = False
            
            # this updated every time previous_row is called
            self.current_valid_row_pointer -= 1  

            if self.current_valid_row_pointer <=0:
                self.current_valid_row_pointer = 0  # Don't go past the end of the valid_rows list
            print('Current valid row pointer: ', self.current_valid_row_pointer)

            self.current_row_index = self.valid_rows[self.current_valid_row_pointer]  # update current row index using valid row pointer

            if self.current_row_index <= 0:
                self.current_row_index = 0  # Don't go past the end of the DataFrame

            self.load_audio_from_current_row()
            print('Next')
        except Exception as e:
            print(f'Exception in next_row: {e}')

    def update_pos(self):
        if self.is_playing:
            pos = int(pygame.mixer.music.get_pos())
            if pos >= 5000:
                pygame.mixer.music.stop()
                self.is_playing = False
                print('Stopped at 5 secs')
            else:
                self.after(100, self.update_pos)  # schedule another update after 100 ms

    def play(self):
        if not self.is_playing:
            pygame.mixer.music.play(start = self.new_start)
            self.is_playing = True
            self.start_animation()
            self.after(100, self.update_pos)  # schedule the first update

    def update_animation_line(self, i):
        pos = pygame.mixer.music.get_pos()
        if pos == -1:
            pos = 0
        pos /= 1000  # convert ms to seconds
        self.animation_line.set_data([pos, pos], [0, 8000])
        return [self.animation_line]

    def start_animation(self):
        # check if the animation is defined
        if self.anim is not None:
            self.anim.event_source.start()

    def visualize_audio(self, start, end, label):
        # Compute the melspectrogram of the audio
        melspectrogram = librosa.feature.melspectrogram(y=self.audio, sr = self.sr)

        # Convert the melspectrogram to a log scale
        log_melspectrogram = librosa.power_to_db(melspectrogram, ref=np.max)

        # Display the melspectrogram
        self.fig, ax = plt.subplots(figsize=(12, 4))
        img = librosa.display.specshow(log_melspectrogram, x_axis='time', y_axis='mel', sr=self.sr, fmax=8000)
        plt.colorbar(img, format='%+2.0f dB')

        # Add the title and the current row index
        if self.metric_var.get() == 'Precision':
            plt.title(f"Precision: \nThis is a {label} - {self.status} \n{self.audio_file_name} - {self.current_valid_row_pointer + 1} / {len(self.valid_rows)} - {self.start} to {self.end}", fontsize=10, loc='left')
        elif self.metric_var.get() == 'Recall':
            plt.title(f"Recall: \nThere is no {self.species_var.get()} in this clip : {self.recall_status}\n{self.audio_file_name} - {self.current_valid_row_pointer + 1} / {len(self.valid_rows)} - {self.start} to {self.end}", fontsize=10, loc='left')

        # Add vertical lines at 2 and 3 seconds
        ax.axvline(x=start, color='r', linestyle='--')  # Red dashed line at 2 seconds
        ax.axvline(x=end, color='r', linestyle='--')  # Red dashed line at 3 seconds

        self.animation_line = ax.plot([], [], 'b')[0]  # Add this line
        
        # Define the animation
        self.anim = FuncAnimation(self.fig, self.update_animation_line, frames=np.arange(0, 5, 0.1), interval=100, blit = True)           

        # Destroy the existing canvas if it exists
        if self.spectrogram_canvas is not None:
            self.spectrogram_canvas.get_tk_widget().destroy()

        # Embedding the figure into the spectrogram_frame
        self.spectrogram_canvas = FigureCanvasTkAgg(self.fig, master=self.spectrogram_frame)
        self.spectrogram_canvas.draw()
        self.spectrogram_canvas.get_tk_widget().pack(side='top', fill='both', expand=True)

    def save_df_to_csv(self):
        self.df.update(self.df_filtered)
        self.df.to_csv(self.file_path, index=False)
        print('File saved')

    def dashboard_button_event(self):
            print("sidebar_button click")
            self.master.show_frame(Dashboard)

    def validate_button_event(self):
            print("validate_button click")
            self.master.show_frame(ValidatePage)

class ProcessProgressPopup(tk.Toplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.title("Processing Files")

        # Set the window to be always on top
        self.attributes('-topmost', True)

        self.progress_bar = ttk.Progressbar(self, length=300)
        self.progress_bar.pack(pady=10, padx=10)

    def update_progress(self, value):
        self.progress_bar['value'] = value
        self.update_idletasks()

class MainApplication(CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("Parrot PAM Platform")
        self.attributes('-fullscreen', True)
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)

        # configure grid layout (4x4)
        self.grid_columnconfigure((1, 2), weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

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
        self.site_recording_data = ""
        self.summary_data = ""
        self.model_selected = ""
        self.timezone = ""
        self.detections = None
        self.combined_results = None
 
        self.frames = {}
        for F in (LandingPage, Dashboard, ValidatePage):
            page_name = F.__name__
            frame = F(parent=self, controller=self)
            self.frames[page_name] = frame

        self.current_frame_name = LandingPage.__name__  # set initial value
        self.show_frame(LandingPage)

        # Bind the keyboard commands to their respective functions
        self.bind('<BackSpace>', self.go_back)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.attributes("-fullscreen", False)
        return "break"
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

        if page_name == 'ValidatePage':
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

    def extract_datetime(self, date, date_convention):
        if date_convention == "AudioMoth - legacy":
                # Convert the hexadecimal datetime to a standard datetime object
                hex_timestamp, ext = os.path.splitext(date)
                timestamp = int(hex_timestamp, 16)
                formatted_dt = datetime.fromtimestamp(timestamp)

        elif date_convention == "AudioMoth - standard":
                formatted_dt = datetime.utcfromtimestamp(date)
        
        else: 
            print('Naming convention not found')

        # Apply the timezone to the datetime object
        timezone = pytz.timezone(self.timezone)
        local_dt = formatted_dt.astimezone(timezone)
        
        return local_dt

    def get_wav_duration(self, file_path, data_location):
        try:
            # create the full file path of the audio
            audio_file = os.path.join(data_location, file_path)

            with audioread.audio_open(audio_file) as audio_file:
                duration = audio_file.duration
                return duration
        except Exception as e:
            print(f"Error processing file '{file_path}': {e}")
            return 0  # Return 0 as the duration in case of an error
        
    def read_extract_datetime(self, data_location, name_convention, date_convention):
        directory_path = data_location

        print('Looking for data in', directory_path)

        new_rows = []
        total_files = 0

        all_files = [file for file in os.listdir(directory_path)]
        print(len(all_files), 'files in', directory_path)

        if name_convention == "(site)_(datetime)":
            files = [file for file in os.listdir(directory_path) if file.endswith('.WAV')]
            total_files = len(files)
            print('Found', total_files, 'audio files')                              

        elif name_convention == "(datetime)":
            items = os.listdir(directory_path)
            folders = [item for item in items if os.path.isdir(os.path.join(directory_path, item))]
            for site in folders:
                total_files += len([file for file in os.listdir(site) if file.endswith('.WAV')])
                print('Found', total_files, 'audio files')           
        
        else:
            print('Naming convention not found')

        # Create and display the popup window
        popup = ProcessProgressPopup(self, self)
        popup.update_idletasks()  # Add this line

        progress_bar = popup.progress_bar
        progress_bar['maximum'] = total_files
        progress_bar['value'] = 0
        processed_files = 0

        if name_convention == "(site)_(datetime)":
            for file in files:
                # Split the filename into site name and hexadecimal datetime
                site_name, hex_datetime = file.split('_')

                # get the date
                date_time = self.extract_datetime(hex_datetime, date_convention)

                # get file duration
                file_duration = self.get_wav_duration(file, data_location)

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

                processed_files += 1
                progress_bar['value'] = processed_files
                popup.update()  # Change this line

        elif name_convention == "(datetime)":
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
                    file_duration = self.get_wav_duration(file, data_location)

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

                    processed_files += 1
                    progress_bar['value'] = processed_files
                    popup.update()
        else:
            print('Name convention not found')

        # create a csv
        df = pd.DataFrame(columns=['site', 'date_time', 'date', 'start_time', 'end_time', 'file_name', 'duration'])
        new_data = pd.DataFrame(new_rows)
        self.site_recording_data = pd.concat([df, new_data], ignore_index=True)

        # Enable the close button in the popup window when the processing is done
        popup.destroy()

        return self.site_recording_data
 
    def summarise_recording_data(self):
        
        # First, convert the 'date_time' column to a datetime object
        self.site_recording_data['date'] = pd.to_datetime(self.site_recording_data['date'])

        # Group the DataFrame by 'site'
        grouped = self.site_recording_data.groupby('site')

        # Calculate summary statistics for each site
        self.summary = grouped.agg(
            num_recordings=('date_time', 'count'),
            start_date=('date', 'min'),
            end_date=('date', 'max'))

        # Calculate the mean recordings per day for each site
        self.summary['mean_per_day'] = self.summary['num_recordings'] / ((self.summary['end_date'] - self.summary['start_date']).dt.days + 1)

        # Reset the index to make 'site' a regular column
        self.summary.reset_index(inplace=True)

        return self.summary
    
    def save_project_settings(self, project_name, project_folder, data_location, name_convention, date_convention):
        # set the timezone from the meta_data
        self.get_timezone()

        # Read and extract the datetime information
        self.site_recording_data = self.read_extract_datetime(data_location, name_convention, date_convention)
       
        # Write the DataFrame to a CSV file
        self.csv_filepath = os.path.join('.\\', project_folder, 'recording_information.csv')

        self.site_recording_data.to_csv(self.csv_filepath , index=False) 

        # summarise the data
        self.summarise_recording_data()

        try:
            with open(f'.\{project_name}.pkl', 'rb') as f:
                self.project_settings = pickle.load(f)
        except FileNotFoundError as e:
            print(f"Error loading project file: {e}")
            return False
        
        # Save the DataFrame in the project_settings dictionary
        self.project_settings['site_recording_data'] = self.site_recording_data

        with open(f'.\{project_name}.pkl', 'wb') as f:
            pickle.dump(self.project_settings, f)
        
        print('Data saved') 
    
    def get_timezone(self):
        # Calculate the average latitude and longitude from the meta_data DataFrame
        avg_latitude = self.meta_data['lat'].mean()
        avg_longitude = self.meta_data['long'].mean()

        # transform from current EPSG to 4326
        transformer = Transformer.from_crs(self.EPSG_code, "EPSG:4326")
        long_converted, lat_converted  = transformer.transform(avg_longitude, avg_latitude)
        
        # Find the timezone for the average coordinates
        timefinder = TimezoneFinder()
        self.timezone = timefinder.timezone_at(lng=long_converted, lat=lat_converted)

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
        self.site_recording_data = self.project_settings['site_recording_data']  
        self.model_selected = self.project_settings['model']
    
        # Load the meta_data DataFrame from the CSV file
        self.data_folder = f"{project_name}_data"
        meta_data_filepath = os.path.join('.\\', self.data_folder, self.project_settings['meta_data'])

        try:
            self.meta_data = pd.read_csv(meta_data_filepath)
        except FileNotFoundError as e:
            print(f"Error loading meta_data file: {e}")
            return False
        
        # summarise the data
        self.summary_data = self.summarise_recording_data() 

        self.get_timezone
        
        # Clear the existing markers
        self.markers.clear()

        return True
    
    def get_detections_list(self):
        # Assuming project_settings is a dictionary containing all the project settings
        detections_keys = [key for key in self.project_settings.keys() if "detections_" in key]
        return detections_keys

    def load_detections(self, selected_item):
        # Load the selected detections into the controller's detections attribute
        self.detections = self.project_settings[selected_item]
        # Update the DataFrameTable to show the loaded detections
        self.frames["DataFrameTable"].dataframe = self.detections
        self.frames["DataFrameTable"].refresh_table()


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()