import os
import shutil
import csv
import tkinter as tk
from tkinter import filedialog

def select_folder():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder_selected = filedialog.askdirectory()  # Show the folder selection dialog
    return folder_selected

def move_and_rename_images(mainfolder):
    # Ensure the output folders exist
    zero_folder = os.path.join(mainfolder, 'Images', '0')
    one_folder = os.path.join(mainfolder, 'Images', '1')
    os.makedirs(zero_folder, exist_ok=True)
    os.makedirs(one_folder, exist_ok=True)

    # CSV file to store original and new paths
    csv_file = os.path.join(mainfolder, 'image_paths.csv')

    with open(csv_file, 'w', newline='') as csvfile:
        fieldnames = ['original_path', 'new_path']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Walk through main folder and subfolders
        for foldername, subfolders, filenames in os.walk(mainfolder):
            for filename in filenames:
                # Check if the file is an image based on its extension
                # (you might want to extend this list based on the image types you have)
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    original_path = os.path.join(foldername, filename)

                    # Construct the new name based on subfolder and original name
                    sub_folder_name = os.path.basename(foldername)
                    new_name = f"{sub_folder_name}_{filename}"

                    # Copy based on the starting character of the image name
                    if filename.startswith('0'):
                        new_path = os.path.join(zero_folder, new_name)
                        shutil.move(original_path, new_path)
                    elif filename.startswith('1'):
                        new_path = os.path.join(one_folder, new_name)
                        shutil.move(original_path, new_path)
                    else:
                        continue

                    # Write the paths to the CSV
                    writer.writerow({'original_path': original_path, 'new_path': new_path})


if __name__ == "__main__":
    mainfolder = select_folder()  # Use the GUI to select the folder
    if mainfolder:  # Check if a folder was selected
        move_and_rename_images(mainfolder)
    else:
        print("No folder selected. Exiting.")