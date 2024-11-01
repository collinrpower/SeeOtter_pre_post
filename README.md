# SeeOtter
Sea otter detection application for use in aerial photography surveys.

# Requirements

 - Windows
 - Conda
 - Python 3.9
 - PyTorch
   - https://pytorch.org/get-started/locally/
   - CUDA 11.3 Version Recommended if your computer has a supported Nvidia GPU
     - https://developer.nvidia.com/cuda-11.3.0-download-archive?target_os=Windows&target_arch=x86_64&target_version=10&target_type=exe_local
 - Kivy
   - https://kivy.org/doc/stable/gettingstarted/installation.html
   - https://anaconda.org/conda-forge/kivy

---

# Getting Started

Survey acts as the main project file that contains the images and data related to a survey.

## Create

```python
# Create survey with default images dir
survey = Survey.new("SurveyName")
```
```python
# Create survey with existing images dir
survey = Survey.new("SurveyName", images_dir="C:/Path/to/images")
```
```python
# Create survey in different directory
survey = Survey.new("SurveyName", survey_path="C:/Path/to/survey")
```
```python
# Overwrite existing survey
survey = Survey.new("SurveyName", images_dir="C:/Path/to/images", overwrite=True)
```

Creating a new survey will make a survey folder located at:
 
>./Surveys/{SurveyName}

If images_dir is not supplied, an images folder will be created at:

>./Surveys/{SurveyName}/Images

## Load

```python
survey.load("SurveyName")
```

```python
# Reloads images from disk and overwrites all associated data
survey.load("SurveyName", reload_images=True)
```
Load from different directory

```python
survey.load(survey_path="C:/Path/to/survey")
```

## Save

```python
survey.save()
```

---

# Processing

The easiest way to process a survey is to set the current survey in "select_survey.py" and run "main.py"

Add your survey name and image directory to the dict in "select_survey.py"

```python
## select_survey.py
surveys = [
    ("MySurvey1", None),
    ("MySurvey2", "C:/Path/to/images")
]
```

Select the survey you wish to use

```python
## select_survey.py
selected_survey_info = surveys[1]
```

Then run "main.py" to start processing of images.

---

# Waldo Survey

## File Structure

For a Waldo Survey to be imported, it must be stored with the correct naming conventions and folder organization as such:

> DriveLetter:/Location/CameraSystem/YYYY/MM_DD/Waldo Data

Example:

> D:\Cook_Inlet\Waldo\2022\04_11

## Importing/Converting Waldo Survey

>**Note: THE FOLLOWING WILL ALTER THE FILE STRUCTURE AND IMAGE NAMES. DO NOT DO THE FOLLOWING ON ORIGINAL DATA!!**

 - Open the script:

> HelperScripts/create_survey_from_waldo_images.py

 - Set the "image_day" variable to point towards the day of data you want to import (this should end in "MM_DD")
 - Run

This should create a new survey with the name (*Location_YYYY_MM_DD*)

The newly created survey should able to be processed as usual.

# OtterChecker9000

Start by running the script:

> start_otter_checker.py

It will load the survey given by "select_survey.py". Use the red/blue/green buttons to validate the predictions. Click 
the save icon in the top right before exiting to save your progress.

# Deploying Application

To build a deployable application, run the powershell script:

> SeeOtter/Deployment/build_application.ps1

Then copy the folder 'yolov5' to the output folder contining the executable. Failing to do so will give you the following error:

> AttributeError: 'NoneType' object has no attribute 'names'

The executable can be found at:

> SeeOtter\Deployment\dist\SeeOtter\SeeOtter.exe

This uses the python package PyInstaller, and relies on you having the SeeOtter Anaconda environment and Powershell. If 
you have issues running it. Make sure you have the SeeOtter Anaconda environment on your computer, and you're able to 
activate it through Powershell.

> (& "C:\ProgramData\Anaconda3\Scripts\conda.exe" "shell.powershell" "hook") | Out-String | Invoke-Expression

> conda activate SeeOtter


The build settings are defined in the 'SeeOtter.spec' file. Any files or 
directories that need to be included in the application should be listed in this file under the Analysis.datas section 
as such.

    datas=[('../View/Images/*.jpg', 'View/Images'),
           ('../View/Icons/*', 'View/Icons'),
           ('../Surveys', 'Surveys')]

Also, make sure your environment is using Pytorch-cpu when deploying. In theory, it should work with Pytorch-gpu, 
but I haven't had any luck with it. Pyinstaller really doesn't play nicely with cuda. If you have access to the 
SeeOtter(pytorch-cpu) conda environment, then the easiest way is to edit the "build_application.ps1" to point
torwards that environment. 

# SeqApp updates
# SeeOtter Sequential Processing GUI

A Tkinter-based GUI application designed to streamline and automate image processing tasks for the SeeOtter project. This application allows users to perform a sequence of steps essential for preparing, processing, and validating wildlife imagery data, specifically targeting the detection and counting of sea otters in aerial imagery.

## Features

- **Sequential Workflow**: Step-by-step guidance for each stage in the processing pipeline.
- **Backup and Organization**: Easily back up camera files and organize them into folders.
- **Metadata Extraction**: Extract GPS metadata from images to verify data quality.
- **Transect Assignment**: Assign images to specific transects based on their metadata.
- **Preprocessing**: Run preprocessing scripts to prepare images for analysis.
- **Model Weight Management**: Update model weights used for AI-based image detection.
- **Configuration Editing**: Modify image tags and annotation categories for the Otter Checker.
- **Final Processing and Validation**: Complete image processing and validate predictions in mapping software.

## Installation

### Prerequisites

- Python 3.8 or higher
- Required libraries (install via `pip`):
  ```bash
  pip install pandas tk

