# Parrot PAM app
The app for your local PAM processing needs

## Setup {#section-1}

### Create new project

1. After launching the app click on the ```Create``` button
2. A popup window “Create new project” will appear
3. Project requirements:
    - **Project name**: the name of your project
    - **EPSG code**: this is the European Petroleum Survey Group of the coordinate system or projection method of the coordinates
    - **Load meta data**: this is a csv file that contains the site names, lat, long
    - **Audio directory**: the location of the survey audio files. These files have to be in ```.WAV``` format. If you have sites in separate folders, use the parent folder to these and set the Naming Convention to (datetime).
    - **Custom model**: If you are using your own model select “Yes”, if not the default model is BirdNet. If you are using a Custom model, you will also have the option of using BirdNet.
    - **Model**: If you have set Custom Model to “Yes” you have to select your model
    - **Naming convention**: there are two options:
        - ```(site)_(datetime)```: this is where you have named each file with the site before the standard datetime stamp. Commonly used if all survey files are kept in the same location.
        - ```(datetime)```: this is the standard timestamp name used by most recording devices.
    - **Date convention**: currently supported are:
        - AudioMoth - legacy: a hexadecimal code for the date and time
        - AudioMoth - standard: a human readable format of ```YYYYMMDD_HHMMSS```
4. Once you have completed all of the requirements, click ```Save```. If you have chosen the default BirdNet model a popup will appear to confirm your selection. 
5. A popup will now appear to show the progress of setting up the project.
6. As well as creating a ```.pkl``` file for all the project settings to be save a ```(project)_data``` folder will be created. This folder will contain the metadata loaded earlier. It will also be where all model and validation outputs will be saved


### Load an existing project

1. After launching the app click on the ```Load``` button
2. Select your saved project, which will be a ```.pkl``` file

## Dasboard
### Sidebar

**Switch to validate page**: Click on the ```Validate``` button in the top left of the window
**Create of load new project**: See [Setup](#section-1) section above
**Change appearance**: Options are ```Dark``` or ```Light``` mode. Default is ```Light``` mode

### Classifier settings
1. If you have loaded a custom model, you still have the option to use BirdNet. 
2. There is an option to run a test, which is 10 randomly selected ```.WAV``` files from your survey. If the test is set to ```No``` then all files will be analysed.
3. **Minimum confidence** is the minimum level at which a segment will be positive for a certain species. This is slightly different for BirdNet or custom models. Custom models can only have one species per segment, whereas BirdNet can have multiple. Therefore, if two species are above the minimum confidence level the highest value will be selected when using Custom models. 
4. When the model has run it will save the results in a csv within the ```(project)_data folder```. The file will be called ```all_detections_[YYYY_MM_DD_HH_MM_SS]``` 

### Meta data
1. Click on the ```Show Meta data``` button
2. Summary data will then be shown, giving you an overview of key figures of your survey. 
3. You will have to scroll down, in the window, to get all the available figures.

### Performance
1. Performance can only be assessed if **Validation** has been carried out.
2. Because there could be multiple csvs containing results when models are run at different times, you will need to select the one you wish to see performance data for. 
3. Once you have loaded a results csv you can select a species you want to see the metrics for. 
4. If you want to save the metrics from these results then click ```Save Metrics``` and a csv will be saved in the data folder, it will be named:
    - ```all_detections_[YYYY_MM_DD_HH_MM_SS]_metrics```

### Plot
You can select ```Raw``` or ```Processed``` in the ```Data Type``` switch. Currently there is only capability to display the ```Raw``` data. This is the site locations, with or without site labels. When full functionality is available results from the classifier will be able to be viewed as well. 

## Validate
### Setup
1. Select data. A popup will appear, you need to select the results you want to validate
2. Once you have loaded the data the ```Species``` dropdown box will fill with the target species. Select one and then select the metric; precision or recall. 
    - Precision will load the positive detections for the target species
    - Recall will load a random select of non-target species segments
3. Click ```Load Audio```
4. A mel spectrogram will appear. The segment will be 5 seconds long, centred on the target window marked with dotted red lines. 
5. There are six buttons along the bottom of the spectrogram:
    - ```Play```: plays the segment with a blue line as a guide
    - ```Previous```: goes to previous segment, if it is the first segment it will not loop round to the last clip
    - ```Next```: goes to the next segment, if it is the last segment it will not loop round to the first clip
    - ```Correct```: will create a column called ManVal if there is not one already. Then will fill the row of the target segment with correct. Will automatically save the csv and move to the next segment
    - ```Incorrect```: will create a column called ManVal if there is not one already. Then will fill the row of the target segment with incorrect. Will automatically save the csv and move to the next segment
    - ```Save```: save the csv

