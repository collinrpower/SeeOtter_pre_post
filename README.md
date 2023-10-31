This README provides detailed instructions for the process of backing up camera files, organizing and processing them, and generating results. These steps are intended to be followed in sequence.

## 1. Backup Camera Files to Hard Drive

### a. Run Backup_Images.py to Automate This Process

1. Select the number of backups you are going to make.
2. Select the drive and folder where you want the backups placed.
3. Run the script.

### b. Alternatively, You Can Manually Copy and Paste the Camera Files

### c. Backups Should Be Made on at Least 3 Separate Physical Drives

#### i. 2 (or More) of These Drives Will Serve as Archives and Will Not Be Processed

##### 1. Large External Hard Drives (HHD) Work Well for This Purpose

- Make sure not to move HHDs when reading or writing data.

#### ii. 1 of These Drives Will Serve as the Working Drive Where the Data Will Be Processed

##### 1. A 1-2 TB External Solid State Drive (SSD) Is Best for the Working Drive

- HHDs will also work but you will see a decrease in performance.

## 2. Move Image Files into ‘0’ and ‘1’ Camera Folders Based on Which Camera the Image Was Taken From

### a. You Should Create a Folder Structure That Looks Like This and Place the Images Inside Here:

`*Location*/*Camera*/*YYYY*/*MM_DD*/Images`

- Example: `G:\GBLAtest\Waldo\2022\08_03\Images`

### b. For Non-Waldo Cameras

#### i. Create an "Images" Folder in Your "MM_DD" Folder

#### ii. Create Two New Folders in This Images Folder Named '0' and '1'

#### iii. Copy All the Images from the Specific Cameras into Their Respective Folders

### c. For Waldo Cameras

#### i. Run Move_Waldo_Images_Into_1_0_folders.py

1. Select your MM_DD folder.
2. This will automatically move the images into the proper folders.

## 3. Extract Image Metadata and Verify Data Quality

### a. Run 'Image_GPS_extract.py'

1. For 'Select Input Folder,' choose the "Images folder you created in step two.
   - Folder structure: `X:\*Location*\*Camera*\*YYYY*\*MM_DD*\Images`
   - Example: `G:\GBLAtest\Waldo\2022\08_03\Images`
2. Enter a name for your CSV and select the folder you would like it to be saved.

### b. Open the CSV You Just Created to View Image Filepaths, Timestamps, Latitudes, Longitudes, and Altitudes in a Mapping Software (ArcMap, QGIS, Google Earth, etc.)

- Verify that there are no large gaps with missing data and images appear to be where they are supposed to be.

### c. Upload a KML or SHP of the Proposed Transects to Be Used as a Reference

## 4. Assign Images to Transects

### a. Use the tx_assignment_template.csv or Create a CSV with 5 Columns:

- 'start_img', 'end_img', 'transect_id', 'start_time', 'end_time'

### b. Fill 'transect_id' with the Names of Your Proposed Transects

### c. For Each Transect, Set Your Start and End Points

- You can do this with either filepaths of images or times.

## 5. Run 'SeeOtter_prepro_GUI_non_Waldo_with_GPS_fix.py'

- Follow the instructions in your documentation.

## 6. Open 'SeeOtter.exe'

- Create a new survey and start processing.

## 7. Run 'SeeOtter_PostPro_Odd_Even.py' to Sum the Number of Individuals per Image and Remove Image Forelap

## 8. Final Results are a CSV with These Columns
