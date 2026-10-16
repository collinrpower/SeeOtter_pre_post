# SeeOtter

## Windows downloads (64-bit)

| Version | Detection hardware | Download |
| --- | --- | --- |
| **CPU only — 3.5.3** | CPU | [Download Windows ZIP](https://github.com/collinrpower/SeeOtter_pre_post/releases/download/v3.5.3/SeeOtter-3.5.3-windows-x64.zip) |
| **GPU + CPU — 3.5.2** | Compatible NVIDIA GPU, with automatic CPU fallback | [Download release files](https://github.com/collinrpower/SeeOtter_pre_post/releases/tag/v3.5.2) |

For **CPU only**, download the ZIP and choose **Extract All**.

For images without EXIF metadata, use **CPU only 3.5.3**, which includes the
image-import hotfix. The existing GPU + CPU 3.5.2 download predates this fix;
the current source includes it for either build mode.

For **GPU + CPU**, download both `.zip.001` and `.zip.002` files plus
**Extract-SeeOtter.cmd** into one fresh folder. Double-click the helper to verify,
join, and extract the application. This download has two parts because GitHub
limits individual release files to 2 GiB. Allow about 11 GB of free disk space.

Open the extracted folder and double-click **SeeOtter.exe**. Both versions bundle
Python and application dependencies; the GPU + CPU version also bundles CUDA
libraries. Keep the whole extracted application folder together.

[Release notes, source archives, and checksums](https://github.com/collinrpower/SeeOtter_pre_post/releases/latest)

For rebuilding the application or developing from source, see the
[Windows distribution instructions](Deployment/WINDOWS_DISTRIBUTION.md).

SeeOtter is an AI-powered application designed to process and validate aerial wildlife photography, specifically tailored to detect sea otters using YOLOv5. The application supports survey creation, image validation, and automated prediction generation, providing a streamlined tool for conservationists and wildlife managers.

## Table of Contents
- [Features](#features)




- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Creating a New Survey](#creating-a-new-survey)
  - [Running Predictions](#running-predictions)
  - [Image Validation](#image-validation)
  - [Generating Results](#generating-results)
- [Configuration](#configuration)
- [Additional Settings](#additional-settings)
- [Troubleshooting](#troubleshooting)

## Features
- **AI-Driven Detection**: Uses YOLOv5 for precise otter detection in high-resolution images.
- **Multi-Step Processing Pipeline**: Pre-processing, prediction generation, and post-processing.
- **Flexible Survey Management**: Supports new surveys, Waldo data import, and customizable file structures.
- **Validation Tools**: Image validation with OtterChecker9000, annotation drawing, and filtering options.
- **Transect Management**: Supports .kml transect files and manual transect assignment for accurate survey analysis.
- **Ambiguous Validation Voting**: Enables multiple observers to resolve ambiguous predictions through majority voting.

## System Requirements
- **OS**: Windows
- **RAM**: 8GB+ recommended
- **GPU**: Nvidia GPU recommended

## Installation

1. Choose **CPU only** or **GPU + CPU** from the download table above.
2. For **CPU only**, extract the single ZIP using **Extract All**. For **GPU + CPU**, place both download parts and **Extract-SeeOtter.cmd** in one fresh, writable folder, then double-click the helper. Keep the part filenames unchanged.
3. Open the extracted folder and double-click **SeeOtter.exe** to open the launcher.
4. Choose the survey manager or one of the preprocessing/postprocessing tools.

The Windows release includes the model weights, libraries, and user guide. Keep
all extracted files together and save surveys outside the application folder.
The executable is unsigned, so Windows may display a publisher warning.
GitHub's **Code > Download ZIP** and the source archives contain development files;
use the Windows release ZIP for the ready-to-run application.

## Usage

### Creating a New Survey
1. Open the Survey Manager screen and click the blue plus button.
2. Fill in the survey details:
   - **Survey Name**
   - **Project Path** (an existing folder)
   - **Images Path** (optional, defaults to `[ProjectPath]/Images`)
3. To import Waldo data, select the "Create Survey from Waldo Data" option and provide the appropriate folder.

   

https://github.com/user-attachments/assets/ac662342-1a3e-4ca0-940f-aad12d530af5



### Running Predictions
1. Go to the Survey Overview section and check if the survey has been processed.
2. Click the green play button to start processing.
   - Progress and status updates will display during processing.

### Image Validation
1. Navigate to OtterChecker9000 to begin validation.
2. Use the top toolbar or arrow keys for navigation:
   - **Q**: Mark prediction as Correct
   - **W**: Mark prediction as Incorrect
   - **E**: Mark prediction as Ambiguous
3. Draw annotations by enabling draw mode (pencil icon or `D` key).

### Generating Results
- Click the "Generate Results" button. Results will be saved to the **Results** folder.

## Configuration
The application settings are in two JSON files:
- **see_otter_config.json**: Processing and runtime configurations.
- **otter_checker_config.json**: Visual and behavior settings.

Modify these files from the settings page or a text editor.

## Additional Settings
- **Transect Files**: Add .kml files to the Transects folder for automated assignments.
- **Inclinometer Data**: Place inclinometer data files in the **InclinometerData** folder for orientation correction.

## Troubleshooting
- **Images without EXIF**: Image dimensions are read from the raster header when EXIF dimensions are absent. Missing capture time and camera fields remain unknown and undated images use filename order. Set `FAIL_ON_MISSING_EXIF_FIELD` and `REQUIRE_GPS` to `false` in the application settings to allow images without that metadata. Georeferenced results still require appropriate GPS, altitude, and camera calibration data.
- **GPU Not Detected**: Enable discrete GPU in settings if not automatically selected.
- **Scaling Issues**: Adjust display scaling settings if portions of the screen are cut off.



# SeeOtter
Sea otter detection application for use in aerial photography surveys.

# Requirements for running from source (developers)

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

Follow the [Windows distribution instructions](Deployment/WINDOWS_DISTRIBUTION.md)
to create an isolated Python 3.9 environment with the pinned CUDA-enabled runtime,
then build from the repository root:

```powershell
.\Build-SeeOtter.ps1 -Python "$PWD\BuildEnvironment\Scripts\python.exe"
```

The current build supports both GPU and CPU detection. It rejects CPU-only Torch
at build time, bundles model weights and dependencies, and checks CPU fallback
and application startup before generating release files. No manual YOLOv5 copy
is required. The executable is `Deployment\dist\SeeOtter\SeeOtter.exe`.

Release ZIPs larger than GitHub's 2 GiB limit are split into download parts with
the Windows extraction helper. The complete local ZIP is also retained.

