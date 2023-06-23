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
import pygame
import requests
from GGM_recogniser import makePredictions
from pathlib import Path
import psutil

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

    def get_countries(self):
            print('Finding countries')

            ##df = pd.read_csv(self.file_path)

            #print(df.head(n = 10))

            # Create transformer
            #transformer = Transformer.from_crs(self.epsg_entry.get(), 'EPSG:4326')

            # Transform the coordinates
            #df['y'], df['x'] = transformer.transform(df['long'].values, df['lat'].values)
            #
            #print(df.head(n = 10))

            # Calculate bounding box
            #minx = df['x'].min()
            #miny = df['y'].min()
            #maxx = df['x'].max()
           # maxy = df['y'].max()

            # Overpass API expects bounding boxes in the form (miny, minx, maxy, maxx). 
            # This is because Overpass API uses a (latitude, longitude) ordering, which is (y, x).
            #overpass_bbox = (miny, minx, maxy, maxx) 
            #print(overpass_bbox)  

            # Use Overpass API to get country names that intersect the bounding box
            #overpass_url = "http://overpass-api.de/api/interpreter"
            #overpass_query = f"""
           # [out:json];
           # (
           # relation["boundary"="administrative"]["admin_level"="2"]({miny},{minx},{maxy},{maxx});
           # );
           # out body;
          #  >;
           # out skel qt;
           # """
          #  response = requests.get(overpass_url, params={'data': overpass_query})

          #  if response.status_code == 200:
          #          # Successful request
         #           data = response.json()
         #   elif response.status_code == 400:
         #           # Bad request
         #           print("Bad Request: ", response.text)
          #  else:
          #          # Other error
          #          print(f"HTTP {response.status_code}: ", response.text)
##
        #    self.controller.countries = set()
         #   for element in data['elements']:
        #            if element['type'] == 'relation':
         #               for tag in element['tags']:
         #                   if tag == 'name:en':
         #                       self.controller.countries.add(element['tags'][tag])
        #    
         #   print('The project is working in', self.controller.countries)

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

        # get the countries the project is working in
        # self.get_countries()

        # Read the EPSG codes from the .txt file and store them in a set
        with open("epsg_codes.txt", "r") as f:
            self.epsg_codes = {line.strip() for line in f}

        self.controller.EPSG_code = self.epsg_entry.get()
        print('Compiling settings')
        # Gather all the settings
        settings = {
            'meta_data': self.meta_data_textbox.get("1.0", "end-1c"),
            'EPSG_code':  self.epsg_entry.get(),
            'data_location': self.controller.data_location,
            'model': self.controller.model_selected,
            'date_convention': self.date_dropdown_textbox.get("1.0", "end-1c"),
            'name_convention': self.naming_dropdown_textbox.get("1.0", "end-1c"),
            'countries': self.controller.countries
        }
        print('Making new directory')
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

        ### Performance Frame ###
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
        for species in self.data_source[self.column_to_check].unique():
            print('Adding ', species, ' to dataframe')
            filtered_df = self.data_source[self.data_source[self.column_to_check] == species]
            
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

        self.column_to_check = 'common_name' if 'common_name' in self.data_source.columns else 'pred_class' if 'pred_class' in self.data_source.columns else None
        self.unique_values = self.data_source[self.column_to_check].unique().tolist()
        self.species_dropdown.destroy()
        self.species_map_dropdown.destroy()
        self.text_dropdown.configure(state = "disabled")

        self.species_var = StringVar(value="Select Species")
        self.species_dropdown = CTkOptionMenu(self.metric_frame, values=self.unique_values, variable=self.species_var, command=self.show_metrics, dynamic_resizing = False)
        self.species_dropdown.grid(row=2, column=1, padx=10, pady=(5, 5), sticky="nsew")
        
        self.species_plot_var = StringVar(value="Select Species")
        self.species_map_dropdown = CTkOptionMenu(self.plot_instructions, values=self.unique_values, variable=self.species_plot_var, dynamic_resizing = False)
        self.species_map_dropdown.grid(row=3, column=2, padx=(5, 5), pady=(5, 5), sticky="nsew")

    def show_metrics(self, value):
        print('Species:', value)
        
        self.precision_text.delete('1.0', 'end')
        self.recall_text.delete('1.0', 'end')

        if self.data_source is not None:
            print('Data is loaded')
            filtered_df = self.data_source[self.data_source[self.column_to_check] == value]
            print(filtered_df.head(n = 10))
            if not filtered_df.empty and 'ManVal' in filtered_df:
                count_values = filtered_df['ManVal'].value_counts()
                TP = count_values.get('correct', 0)   # Returns count of 'correct' if it exists, 0 otherwise
                FP = count_values.get('incorrect', 0)   # Returns count of 'incorrect' if it exists, 0 otherwise
                print('TP =', TP, 'FP =', FP)
            else:
                print('ManVal is not present or dataframe is empty')
                TP = 0
                FP = 0
        else:
            print("Cannot find data")     

        if value in self.data_source.columns:
            print(value, 'column exists')
            recall_check = self.data_source[value].value_counts()
            FN = recall_check.get('correct', 0) # Returns count of 'correct' from target species column, 0 otherwise 
            print('FN =', FN)
            if FN + TP == 0:
                recall = 0.0
            else:
                recall = TP / (FN + TP)   
        else:
            recall = "Please Validate negatives"

        if TP + FP == 0:
            precision = "Please Validate positives"
        elif TP + FP < len(filtered_df):
            precision = "Validation not complete" 
        else:
            precision = TP / (TP + FP) if (TP + FP) > 0 else 0 # Check for ZeroDivisionError

        print('Precision = ', precision,'\nRecall =', recall)

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
        
        if self.switch_var.get() == "Processed":
            if self.species_map_dropdown.get() == "Load data above":
                messagebox.showerror("Error", "Please load data in *Performance* section")
                return
            else:
                if self.map_widget:
                    self.map_widget.destroy()
                    print('Removing map_widget')

                # Create the map figure and axis
                fig = Figure(figsize=(5, 5), dpi=100)  # Adjust figure size as needed
                ax = fig.add_subplot(111)
                ax.set_aspect('equal')

                # Define the map
                min_lon, min_lat = self.south_east_point  # Lower left corner coordinates
                max_lon, max_lat = self.north_west_point  # Upper right corner coordinates

                m = Basemap(llcrnrlon=min_lon, llcrnrlat=min_lat, urcrnrlon=max_lon, urcrnrlat=max_lat, epsg=4326)
                m.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= True)

                # Filter data by species and compute point sizes
                filtered_data = self.data_source[self.data_source['common_name'] == self.species_var.get()]
                sizes = filtered_data['ManVal'].apply(lambda x: 10 if x == 'correct' else 0)  # Adjust as needed

                # Plot points for each site
                for site, size in zip(self.converted_coordinates, sizes):
                    x, y = m(*site)  # Convert lat/lon to map projection coords
                    m.plot(x, y, 'o', color='black', markersize=size)

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
                  
    def extract_site_name(self, file):
        file_base = os.path.basename(file)
        
        # split the file into two
        site_name, _ = file_base.split('_')

        return site_name

    def run_model(self):
        print('Run model')

        directory_path = self.controller.data_location
        
        if self.controller.name_convention == "(site)_(datetime)":
            data = [file for file in os.listdir(directory_path) if file.endswith('.WAV')]
            data_paths = [os.path.join(directory_path, file) for file in data]         
            if self.test_option.get() == "Yes":
                results = self.popup_model(random.sample(data_paths,10))
            else:
                results = self.popup_model(data_paths)
        
        elif self.controller.name_convention == "(datetime)":
            results_df = pd.DataFrame()
            items = os.listdir(directory_path)
            site_files = [item for item in items if os.path.isdir(os.path.join(directory_path, item))]
            for site in site_files:
                data = [file for file in os.listdir(site) if file.endswith('.WAV')]
                data_paths = [os.path.join(directory_path, site, file) for file in data]
                if self.test_option.get() == "Yes":
                    results_site = self.popup_model(data_paths[0:10])
                else:
                    results_site = self.popup_model(data_paths)
                
                results = pd.concat([results_df, results_site], axis=0, ignore_index=True)
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
    
    def popup_model(self, data_paths):
        popup = ModelProgressPopup(self, self, len(data_paths))

        custom_extractor = makePredictions(self.controller.model_selected, popup)

        result = custom_extractor.custom_extractor(data_paths) #this is where we put the new class from GGM_recogniser     
                       
        # Close the popup window
        popup.destroy()   
        
        return result
    
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
        
        # get the date requirements
        date = file_row['date_time'].values[0] # get the date 
        date_object = pd.to_datetime(date).to_pydatetime()
        print('Datetime:', date_object)
        
        week_number = int(date_object.strftime("%U")) + 1
        print('Week number:', week_number)  

        year = date_object.year
        month = date_object.month
        day = date_object.day
        time = date_object.time() 
        
        site = file_row['site'].values[0] # get the site

        meta_row = meta_data.loc[meta_data['site'] == site]

        if meta_row.empty:
            print("Site not found, defaulting to the first row.")
            meta_row = meta_data.iloc[0]
        else:
            print("Site found.")
            meta_row = meta_row.iloc[0]

        print(meta_row)
        if not meta_row.empty:
            lat =  meta_row['lat'] # get the lat
            long =  meta_row['long'] # get the long
        else:
            print("meta_row DataFrame is empty.")
        
        # transform from current EPSG to 4326
        transformer = Transformer.from_crs(self.controller.EPSG_code, "EPSG:4326")
        lat_converted, long_converted  = transformer.transform(long, lat)

        print('Lat:', lat_converted, 'Long:', long_converted)

        return site, lat_converted, long_converted, year, month, day, time
    
    def birdnet_analyse_file(self, popup, index, wav_file):
        popup.update_progress(index, wav_file)   
        site, lat, long, year, month, day, time = self.get_recording_info(wav_file)
        results = self.birdnet(site, wav_file, lat, long, year, month, day, time, float(self.min_confid_text.get()))

        return  results   
    
    def make_detections(self, data_paths):
        combined_results = pd.DataFrame()

        if self.test_option.get() == "Yes":
            popup = ModelProgressPopup(self, self, len(data_paths[0:10]))
            popup.update() 
            for index, wav_file in enumerate(data_paths[0:10]):
                results = self.birdnet_analyse_file(popup, index, wav_file)
                print(results)
                combined_results = pd.concat([combined_results, results], axis=0, ignore_index=True)             
        else: 
            popup = ModelProgressPopup(self, self, len(data_paths))
            popup.update() 
            for index, wav_file in enumerate(data_paths):
                results = self.birdnet_analyse_file(popup, index, wav_file)
                print(results)
                combined_results = pd.concat([combined_results, results], axis=0, ignore_index=True)  

        popup.destroy()
        return combined_results 


    def run_birdnet(self):
        directory_path = self.controller.data_location
        
        if self.controller.name_convention == "(site)_(datetime)":
            data = [file for file in os.listdir(directory_path) if file.endswith('.WAV')]
            data_paths = [os.path.join(directory_path, file).replace("\\", "/") for file in data]
            all_detections = self.make_detections(data_paths)

        elif self.controller.name_convention == "(datetime)":
            all_detections = pd.DataFrame()
            items = os.listdir(directory_path)
            folders = [item for item in items if os.path.isdir(os.path.join(directory_path, item))]
            for site in folders:
                print(os.path.join(directory_path, site))
                data = [file for file in os.listdir(os.path.join(directory_path, site)) if file.endswith('.WAV')]
                data_paths = [os.path.join(directory_path, site, file).replace("\\", "/") for file in data]
                detections = self.make_detections(data_paths)
                print(detections)
                all_detections = pd.concat([all_detections, detections], axis=0, ignore_index=True)
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
        
        message = f"Launching model..."
        self.message_label = CTkLabel(self)
        self.message_label.grid(row=0, column=0, columnspan = 3, padx = 5, pady = 5, sticky="nsew")
        self.message_label.configure(text=message)
        
        self.progress_bar = ttk.Progressbar(self, length=200)
        self.progress_bar.grid(row=0, column=3, padx = 5, pady = 5, sticky="nsew")
        self.progress_bar['maximum'] = self.total_files

        self.counter_label = CTkLabel(self)      
        self.counter_label.grid(row=0, column=4, padx = 5, pady = 5, sticky="nsew")
        
        counter = f"0/{self.total_files}"
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
        
        column_to_check = 'common_name' if 'common_name' in self.df.columns else 'pred_class' if 'pred_class' in self.df.columns else None
        
        self.unique_values = self.df[column_to_check].unique().tolist()
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
        # Check if the folder exists
        path = Path(self.controller.data_location)
        if not path.exists() or not path.is_dir():
            print(self.controller.data_location)
            messagebox.showerror("Error", f"The directory {self.controller.data_location} cannot be found")
            print('Cannot find audio location')
            return
        else:
            print(self.controller.data_location, 'has been located')
            if 'ManVal' not in self.df.columns:
                self.df['ManVal'] = ''

            column_to_check = 'common_name' if 'common_name' in self.df.columns else 'pred_class' if 'pred_class' in self.df.columns else None

            if column_to_check is None:
                print("Error: Neither 'common_name' nor 'pred_class' is available.")
                return

            if self.metric_var.get() == "Precision":
                # filter the dataframe for rows where 'common_name' or 'pred_class' matches the current species
                self.df_filtered = self.df[self.df[column_to_check] == self.species_var.get()]

            elif self.metric_var.get() == "Recall":
                # Select all rows where 'common_name' or 'pred_class' is not equal to species_var.get()
                self.df_filtered = self.df[self.df[column_to_check] != self.species_var.get()]

                # Group by 'soundfile' and remove duplicate rows based on 'start_time' and 'end_time'
                self.df_filtered = self.df_filtered.groupby('soundfile').apply(lambda x: x.drop_duplicates(subset=['start_time', 'end_time'])).reset_index(drop=True)

                # If df_filtered has less than 2000 rows, sample randomly up to 2000 rows with replacement. Otherwise, use all rows.
                if len(self.df_filtered) < 2000:
                    self.df_filtered = self.df_filtered.sample(n=2000, replace=True, random_state=1)
                # If the number of rows is already above 2000, leave the dataframe as it is
                else:
                    self.df_filtered = self.df_filtered

            if self.species_var.get() not in self.df.columns:
                self.df[self.species_var.get()] = ''
                print('Focal species:', self.species_var.get())

        # Find the first row that 'ManVal' is not 'correct' or 'incorrect' in df_filtered
        start_index = (~self.df_filtered['ManVal'].isin(['correct', 'incorrect'])).idxmax()

        # If the start_index is in df_filtered, use it as the starting point
        if start_index in self.df_filtered.index:
            # Find the position of start_index in df_filtered index
            start_pos = self.df_filtered.index.tolist().index(start_index)
            # Start from the row with start_index
            self.valid_rows = self.df_filtered.index[start_pos:].tolist()
        # If all 'ManVal' are 'correct' or 'incorrect' in df_filtered, start from the first row of df_filtered
        else:
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
        
        if 'common_name' in row and pd.notnull(row['common_name']):
            label = row['common_name']
        elif 'pred_class' in row and pd.notnull(row['pred_class']):
            label = row['pred_class']
        else:
            print("Error: Neither 'common_name' nor 'pred_class' is available.")
            label = None  # Or set to a default value, if you prefer
        
        self.status = row['ManVal']
        self.recall_status = row[self.species_var.get()]

        # ensure we are not loading a whole new sound file when we don't need to as we are loading full files to enable the playback
        try:
            if 'sound.files' in row:
                self.audio_file_name = row['sound.files']
                pygame.mixer.music.load(f'{self.audio_file_name}')
            elif 'sound.file' in row:
                self.audio_file_name = row['sound.file']
                pygame.mixer.music.load(f'{self.audio_file_name}')
            else:
                raise KeyError('Neither "sound.files" nor "sound.file" found in row.')
        except:
            self.audio_file_name = row['sound.file']
            pygame.mixer.music.load(f'{self.audio_file_name}')
            # Load audio file
            print('Loading new sound file')

        if length > 1:
            self.new_start = middle - 2.5
            self.audio, self.sr = librosa.load(f'{self.audio_file_name}', offset = self.new_start, duration = 5)
            self.visualize_audio(1, 4, label)
        else: 
            self.audio, self.sr = librosa.load(f'{self.audio_file_name}', offset = self.new_start, duration = 5)
            self.visualize_audio(2, 3, label)

    def mark_correct(self):
        print('Mark correct')
        if self.metric_var.get() == 'Precision':
            print('Adding correct to row', self.current_row_index)
            self.df.loc[self.current_row_index, "ManVal"] = "correct"
        elif self.metric_var.get() == 'Recall':
            self.df.loc[self.current_row_index, self.species_var.get()] = "correct"
            print('Adding correct to', self.species_var.get(),'row', self.current_row_index)

        self.save_df_to_csv()
        self.next_row()
        self.update_idletasks()  # force Tkinter to process any pending tasks

    def mark_incorrect(self):
        print('Mark incorrect')       
        if self.metric_var.get() == 'Precision':
            self.df.loc[self.current_row_index, "ManVal"] = "incorrect"
            print('Adding incorrect to row', self.current_row_index)
        elif self.metric_var.get() == 'Recall':
            self.df.loc[self.current_row_index, self.species_var.get()] = "incorrect"
        
        self.save_df_to_csv()
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
        print('Start Playing')
        if not self.is_playing:
            print('Playing')
            try:
                pygame.mixer.music.play(start = self.new_start)
                print('Pygame play method executed successfully')
            except Exception as e:
                print('An error occurred in pygame play method: ', e)

            self.is_playing = True

            try:
                self.start_animation()
                print('start_animation method executed successfully')
            except Exception as e:
                print('An error occurred in start_animation method: ', e)
            
            self.after(100, self.update_pos)  # schedule the first update

    def update_animation_line(self, i):
        pos = pygame.mixer.music.get_pos()
        if pos == -1:
            pos = 0
        pos /= 1000  # convert ms to seconds
        self.animation_line.set_data([pos, pos], [0, 8000])
        return [self.animation_line]

    def start_animation(self):
        print('Starting animation')
        # check if the animation is defined
        if self.anim is not None:
            self.anim.event_source.start()

    def visualize_audio(self, start, end, label):
        # Close all existing figures
        plt.close('all')

        # Check if the spectrogram_canvas exists and clear it
        if self.spectrogram_canvas is not None:
            plt.clf()
            self.spectrogram_canvas.get_tk_widget().destroy()

        # Get current system-wide memory usage
        mem_info = psutil.virtual_memory()

        # Convert bytes to MB
        available_memory_in_MB = mem_info.available / (1024 ** 2)

        # Check if available memory is less than 1 MB
        if available_memory_in_MB < 1:
            # If it is, show a popup message
            messagebox.showwarning("Warning", "Available memory is less than 1MB - Please restart the app")
        
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
        try:
            self.df.to_csv(self.file_path, index=False)
            print('File saved')
        except Exception as e:
            print(f"An error occurred: {e}")


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
        self.countries = ''
        self.standard_bbox = ''
 
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
                print('Hexstamp:', hex_timestamp)
                try:
                    timestamp = int(hex_timestamp, 16)
                    formatted_dt = datetime.fromtimestamp(timestamp)
                except ValueError:
                    print(f"Unable to convert hex timestamp: {hex_timestamp}")
                    # Handle the error appropriately, perhaps by setting a default datetime value, returning, or raising the exception

        elif date_convention == "AudioMoth - standard":
                # Convert the hexadecimal datetime to a standard datetime object
                date_object, ext = os.path.splitext(date)
                print('Hexstamp:', date_object)
                try:
                    formatted_dt = datetime.strptime(date_object, "%Y%m%d_%H%M%S")
                except ValueError:
                    print(f"Unable to convert hex timestamp: {date_object}")
                    # Handle the error appropriately
        else: 
            print('Naming convention not found')


        # Apply the timezone to the datetime object
        timezone = pytz.timezone(self.timezone)
        local_dt = formatted_dt.astimezone(timezone)
        
        return local_dt

    def get_wav_duration(self, file_path, data_location, name_convention):
        try:
            # create the full file path of the audio
            if name_convention == "(datetime)":
                audio_file = os.path.join(data_location, self.site, file_path)
            else:
                audio_file = os.path.join(data_location, file_path)
            print('Searching for', audio_file)

            with audioread.audio_open(audio_file) as audio_file:
                duration = audio_file.duration
                return duration
        except Exception as e:
            print(f"Cannot calculate length of '{file_path}': {e}")
            return 0  # Return 0 as the duration in case of an error
        
    def read_extract_datetime(self, data_location, name_convention, date_convention):
        directory_path = data_location

        print('Looking for data in', directory_path)

        new_rows = []
        total_files = 0

        if name_convention == "(site)_(datetime)":
            files = [file for file in os.listdir(directory_path) if file.endswith('.WAV')]
            print(len(files), 'files in', directory_path)
            total_files = len(files)
            print('Found', total_files, 'audio files')                              

        elif name_convention == "(datetime)":
            items = os.listdir(directory_path)
            print(len(items), 'sites folders', directory_path)
            folders = [item for item in items if os.path.isdir(os.path.join(directory_path, item))]
            for site in folders:
                print('Working on site:', site)
                total_files += len([file for file in os.listdir(os.path.join(directory_path, site)) if file.endswith('.WAV')])
                print('Found', total_files, 'in', site, 'folder')           
        
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
                print('Extracting datetime from:', hex_datetime) 
                date_time = self.extract_datetime(hex_datetime, date_convention)

                # get file duration
                print('Get file duration')
                file_duration = self.get_wav_duration(file, directory_path, name_convention)

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
                self.site = site
                print('Working on', site)
                files = [file for file in os.listdir(os.path.join(directory_path, site)) if file.endswith('.WAV')]

                for file in files:
                    # get the date
                    print('Extracting datetime from:', file)   

                    date_time = self.extract_datetime(file, date_convention)

                    # get file duration
                    print('Get file duration')
                    file_duration = self.get_wav_duration(file, directory_path, name_convention)

                    # Append the information to the new_rows list
                    end_time = date_time + timedelta(seconds=file_duration)

                    new_rows.append({
                        'site': self.site,
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
        self.project_settings['countries'] = self.countries

        print('Countries:', self.countries)

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
        self.countries = self.project_settings['countries']

        # Load the meta_data DataFrame from the CSV file
        self.data_folder = f"{project_name}_data"
        meta_data_filepath = os.path.join('.\\', self.data_folder, self.project_settings['meta_data'])
        print(meta_data_filepath)

        try:
            self.meta_data = pd.read_csv(meta_data_filepath)
            print(self.meta_data)
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
