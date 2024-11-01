import os
import shutil
import csv
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import json
import ast
from datetime import datetime


class ScrollableFrame(tk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        # Create canvas and scrollbars
        canvas = tk.Canvas(self)
        vscrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        hscrollbar = tk.Scrollbar(self, orient="horizontal", command=canvas.xview)

        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all"),
                width=e.width
            )
        )

        # Add window to canvas
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Configure scrollbars
        canvas.configure(yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)

        # Pack the canvas and scrollbars
        canvas.pack(side="left", fill="both", expand=True)
        vscrollbar.pack(side="right", fill="y")
        hscrollbar.pack(side="bottom", fill="x")


class SequentialApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SeeOtter Sequential Processing GUI")
        self.current_step = 0
        self.completed_steps = [False] * 9  # Initialize completed steps list

        self.source_folder = tk.StringVar()
        self.folder_0 = tk.StringVar()
        self.folder_1 = tk.StringVar()
        self.destination_folder = tk.StringVar()
        self.destination_folders = []

        # Initialize csv_data as an empty DataFrame
        self.csv_data = pd.DataFrame()

        self.steps = [
            "Backup Camera Files to hard drive",
            "Move image files into ‘0’ and ‘1’ camera folders",
            "Extract image metadata and verify data quality",
            "Assign images to transects",
            "Run Preprocessing",
            "Change Model Weights",
            "Edit Otter Checker Config",
            "Run SeeOtter Processing",
            "Final Processing"
        ]

        self.steps_functions = [
            self.backup_camera_files,
            self.move_image_files,
            self.extract_image_metadata,
            self.assign_images_to_transects,
            self.run_preprocessing,
            self.change_model_weights,
            self.edit_otter_checker_config,
            self.run_seeotter_processing,
            self.final_processing,
        ]

        self.create_widgets()
        self.update_step()

    def edit_otter_checker_config(self):
        self.instructions.config(text="Edit Otter Checker Config\n"
                                      "Modify the image tags and annotation categories.\n"
                                      "Save changes when done.")
        self.clear_widgets()
        self.load_config()

        # Create scrollable frame
        self.scrollable_frame = ScrollableFrame(self.root)
        self.scrollable_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Image Tags
        tk.Label(self.scrollable_frame.scrollable_frame, text="Image Tags:").grid(row=0, column=0, padx=10, pady=10,
                                                                                  sticky="w")
        self.image_tags_entries = []
        for i, tag in enumerate(self.config['IMAGE_TAGS']):
            entry = tk.Entry(self.scrollable_frame.scrollable_frame)
            entry.grid(row=1 + i, column=0, padx=10, pady=2, sticky="w")
            entry.insert(0, tag)
            self.image_tags_entries.append(entry)

        # Annotation Categories
        tk.Label(self.scrollable_frame.scrollable_frame, text="Annotation Categories:").grid(row=0, column=1, padx=10,
                                                                                             pady=10, sticky="w")
        self.annotation_categories_entries = []
        for i, (category, index) in enumerate(self.config['ANNOTATION_CATEGORIES']):
            entry_category = tk.Entry(self.scrollable_frame.scrollable_frame)
            entry_category.grid(row=1 + i, column=1, padx=10, pady=2, sticky="w")
            entry_category.insert(0, category)
            entry_index = tk.Entry(self.scrollable_frame.scrollable_frame)
            entry_index.grid(row=1 + i, column=2, padx=10, pady=2, sticky="w")
            entry_index.insert(0, index)
            self.annotation_categories_entries.append((entry_category, entry_index))

        # Add Add Category button inside scrollable frame
        tk.Button(self.scrollable_frame.scrollable_frame, text="Add Category", command=self.add_category).grid(
            row=1 + len(self.annotation_categories_entries), column=1, padx=10, pady=10, sticky="w")

        # Add Save Config button outside scrollable frame, but above navigation buttons
        self.save_button = tk.Button(self.root, text="Save Config", command=self.save_config)
        self.save_button.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="w")

        # Adjust position of navigation buttons
        self.next_button.grid(row=3, column=2, padx=10, pady=10)
        self.back_button.grid(row=3, column=0, padx=10, pady=10)
        self.skip_button.grid(row=3, column=1, padx=10, pady=10)

    def add_category(self):
        entry_category = tk.Entry(self.scrollable_frame.scrollable_frame)
        entry_category.grid(row=1 + len(self.annotation_categories_entries), column=1, padx=10, pady=2, sticky="w")
        entry_index = tk.Entry(self.scrollable_frame.scrollable_frame)
        entry_index.grid(row=1 + len(self.annotation_categories_entries), column=2, padx=10, pady=2, sticky="w")
        self.annotation_categories_entries.append((entry_category, entry_index))
        # Update Save Config button position
        self.update_save_button_position()

    def update_save_button_position(self):
        max_entries = max(len(self.image_tags_entries), len(self.annotation_categories_entries))
        self.save_button.grid(row=2 + max_entries, column=0, columnspan=3, padx=10, pady=10, sticky="w")

    def load_config(self):
        config_path = r"E:\SeeOtterUSGS\SeeOtter_pre_post-main\SeeOtter_pre_post-main\Config\otter_checker_config.py"
        self.config = {}

        with open(config_path, 'r') as f:
            content = f.read()

        # Extract IMAGE_TAGS
        image_tags_start = content.find("self.IMAGE_TAGS = [")
        image_tags_end = content.find("]", image_tags_start) + 1
        image_tags_data = content[image_tags_start:image_tags_end].split(" = ")[1]
        self.config['IMAGE_TAGS'] = ast.literal_eval(image_tags_data)

        # Extract ANNOTATION_CATEGORIES
        annotation_categories_start = content.find("self.ANNOTATION_CATEGORIES = [")
        annotation_categories_end = content.find("]", annotation_categories_start) + 1
        annotation_categories_data = content[annotation_categories_start:annotation_categories_end].split(" = ")[1]
        self.config['ANNOTATION_CATEGORIES'] = ast.literal_eval(annotation_categories_data)

    def add_tag(self):
        entry = tk.Entry(self.root)
        entry.grid(row=2 + len(self.image_tags_entries), column=0, padx=10, pady=2, sticky="w")
        self.image_tags_entries.append(entry)

    def add_category(self):
        entry_category = tk.Entry(self.root)
        entry_category.grid(row=2 + len(self.annotation_categories_entries), column=1, padx=10, pady=2, sticky="w")
        entry_index = tk.Entry(self.root)
        entry_index.grid(row=2 + len(self.annotation_categories_entries), column=2, padx=10, pady=2, sticky="w")
        self.annotation_categories_entries.append((entry_category, entry_index))

    def save_config(self):
        new_image_tags = [entry.get() for entry in self.image_tags_entries]
        new_annotation_categories = [(entry_category.get(), int(entry_index.get())) for entry_category, entry_index in
                                     self.annotation_categories_entries]

        config_path = r"E:\SeeOtterUSGS\SeeOtter_pre_post-main\SeeOtter_pre_post-main\Config\otter_checker_config.py"
        json_config_path = r"E:\SeeOtterUSGS\SeeOtter_pre_post-main\SeeOtter_pre_post-main\otter_checker_config.json"

        # Create a backup of the current config file
        backup_path = config_path + ".bak"
        shutil.copy2(config_path, backup_path)

        with open(config_path, 'r') as f:
            content = f.read()

        updated_content = content.split("self.IMAGE_TAGS = [")[0] + f"self.IMAGE_TAGS = {new_image_tags}\n"
        updated_content += \
        content.split("self.IMAGE_TAGS = [")[1].split("]")[1].split("self.ANNOTATION_CATEGORIES = [")[0]
        updated_content += f"self.ANNOTATION_CATEGORIES = {new_annotation_categories}\n" + \
                           content.split("self.ANNOTATION_CATEGORIES = [")[1].split("]")[1]

        with open(config_path, 'w') as f:
            f.write(updated_content)

        # Delete the .json config file if it exists
        if os.path.exists(json_config_path):
            os.remove(json_config_path)

        messagebox.showinfo("Success", f"Configuration updated successfully! Backup saved at {backup_path}")
        self.next_step()

    def create_widgets(self):
        self.instructions = tk.Label(self.root, text="", wraplength=500, justify="left")
        self.instructions.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        self.folder_0_label = tk.Label(self.root, text="Select Folder for '0' Images:")
        self.folder_0_entry = tk.Entry(self.root, textvariable=self.folder_0, width=50)
        self.folder_0_button = tk.Button(self.root, text="Browse", command=self.browse_folder_0)

        self.folder_1_label = tk.Label(self.root, text="Select Folder for '1' Images:")
        self.folder_1_entry = tk.Entry(self.root, textvariable=self.folder_1, width=50)
        self.folder_1_button = tk.Button(self.root, text="Browse", command=self.browse_folder_1)

        self.destination_folder_label = tk.Label(self.root, text="Select Destination Folder:")
        self.destination_folder_entry = tk.Entry(self.root, textvariable=self.destination_folder, width=50)
        self.destination_folder_button = tk.Button(self.root, text="Browse", command=self.browse_destination_folder)

        self.source_folder_label = tk.Label(self.root, text="Select Folder to Backup:")
        self.source_folder_entry = tk.Entry(self.root, textvariable=self.source_folder, width=50)
        self.source_folder_button = tk.Button(self.root, text="Browse", command=self.browse_source_folder)
        self.add_destination_button = tk.Button(self.root, text="Add Destination", command=self.add_destination_folder)
        self.destinations_frame = tk.Frame(self.root)
        self.num_backups_label = tk.Label(self.root, text="Number of Backups:")
        self.num_backups = tk.Spinbox(self.root, from_=1, to=10, width=5)

        self.next_button = tk.Button(self.root, text="Next", command=self.next_step)
        self.back_button = tk.Button(self.root, text="Back", command=self.prev_step)
        self.skip_button = tk.Button(self.root, text="Skip", command=self.skip_step)

        self.next_button.grid(row=5, column=2, padx=10, pady=10)
        self.back_button.grid(row=5, column=0, padx=10, pady=10)
        self.skip_button.grid(row=5, column=1, padx=10, pady=10)

        self.step_labels = [tk.Label(self.root, text=step) for step in self.steps]
        self.step_checkmarks = [tk.Label(self.root, text="✗") for _ in range(len(self.steps))]
        for i, (label, checkmark) in enumerate(zip(self.step_labels, self.step_checkmarks)):
            label.grid(row=6 + i, column=0, columnspan=2, sticky="w", padx=10, pady=2)
            checkmark.grid(row=6 + i, column=2, padx=10, pady=2)

    def update_step(self):
        self.clear_widgets()
        step_function = self.steps_functions[self.current_step]
        step_function()

        # Update checkmarks
        for i, checkmark in enumerate(self.step_checkmarks):
            if self.completed_steps[i]:
                checkmark.config(text="✓")
            else:
                checkmark.config(text="✗")

        # Ensure navigation buttons are always visible
        self.next_button.grid(row=5, column=2, padx=10, pady=10)
        self.back_button.grid(row=5, column=0, padx=10, pady=10)
        self.skip_button.grid(row=5, column=1, padx=10, pady=10)

    def clear_widgets(self):
        for widget in self.root.winfo_children():
            if widget not in {self.instructions, *self.step_labels, *self.step_checkmarks}:
                widget.grid_forget()

        self.destination_folders.clear()
        for widget in self.destinations_frame.winfo_children():
            widget.destroy()
        self.destination_folder.set("")

    def next_step(self):
        self.completed_steps[self.current_step] = True
        self.current_step += 1
        if self.current_step < len(self.steps_functions):
            self.update_step()
        else:
            messagebox.showinfo("Completed", "All steps are completed!")
            self.root.quit()

    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
        self.update_step()

    def skip_step(self):
        self.current_step += 1
        if self.current_step < len(self.steps_functions):
            self.update_step()
        else:
            messagebox.showinfo("Completed", "All steps are completed!")
            self.root.quit()

    def browse_folder_1(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_1.set(folder)

    def browse_folder_0(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_0.set(folder)

    def browse_destination_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.destination_folder.set(folder)

    def browse_source_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_folder.set(folder)

    def add_destination_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.destination_folders.append(folder)
            frame = tk.Frame(self.destinations_frame)
            label = tk.Label(frame, text=folder)
            label.pack(side="left")
            remove_button = tk.Button(frame, text="Remove", command=lambda: self.remove_destination_folder(frame, folder))
            remove_button.pack(side="right")
            frame.pack()
            self.destinations_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

    def remove_destination_folder(self, frame, folder):
        frame.destroy()
        self.destination_folders.remove(folder)

    def run_script(self, script_path, *args):
        try:
            subprocess.run(['python', script_path, *args], check=True)
            messagebox.showinfo("Success", f"{os.path.basename(script_path)} completed successfully!")
            self.completed_steps[self.current_step] = True
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to run {os.path.basename(script_path)}.\nError: {str(e)}\nReturn Code: {e.returncode}\nOutput: {e.output}"
            messagebox.showerror("Error", error_msg)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    def backup_camera_files(self):
        self.instructions.config(text="1. Backup Camera Files to hard drive\n"
                                      "a. Run Backup_Images.py to automate this process\n"
                                      "i. Select the number of backups you are going to make\n"
                                      "ii. Select the drive and folder where you want the backups placed\n"
                                      "iii. Run script\n"
                                      "b. Alternatively you can manually copy and paste the camera files onto each backup drive\n"
                                      "c. Backups should be made on at least 3 separate physical drives")
        self.source_folder_label.grid(row=1, column=0, padx=10, pady=10)
        self.source_folder_entry.grid(row=1, column=1, padx=10, pady=10)
        self.source_folder_button.grid(row=1, column=2, padx=10, pady=10)

        self.add_destination_button.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
        self.destinations_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

        tk.Button(self.root, text="Start Backup", command=self.start_backup).grid(row=4, column=2, padx=10, pady=10)

    def move_image_files(self):
        self.instructions.config(
            text="2. Move image files into ‘0’ and ‘1’ camera folders based on which camera the image was taken from\n"
                 "a. Create a folder structure and place the images inside\n"
                 "b. For non-Waldo cameras\n"
                 "c. For Waldo cameras")

        # Frame for Base Folder selection
        base_folder_frame = tk.Frame(self.root)
        base_folder_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        self.base_folder_label = tk.Label(base_folder_frame, text="Base Folder:")
        self.base_folder = tk.StringVar()
        self.base_folder_entry = tk.Entry(base_folder_frame, textvariable=self.base_folder, width=50)
        self.base_folder_button = tk.Button(base_folder_frame, text="Browse", command=self.browse_base_folder)

        self.base_folder_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.base_folder_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.base_folder_button.grid(row=0, column=2, padx=5, pady=5)

        # Frame for Location, Camera, Year, and MM_DD
        details_frame = tk.Frame(self.root)
        details_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        self.location_label = tk.Label(details_frame, text="Location:")
        self.location_entry = tk.Entry(details_frame, width=30)
        self.camera_label = tk.Label(details_frame, text="Camera:")
        self.camera_entry = tk.Entry(details_frame, width=30)
        self.year_label = tk.Label(details_frame, text="Year:")
        self.year_entry = tk.Entry(details_frame, width=30)
        self.mm_dd_label = tk.Label(details_frame, text="MM_DD:")
        self.mm_dd_entry = tk.Entry(details_frame, width=30)

        self.location_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.location_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.camera_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.camera_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.year_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.year_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.mm_dd_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.mm_dd_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Frame for Folder selection for '0' and '1' images
        folder_frame = tk.Frame(self.root)
        folder_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        self.folder_0_label = tk.Label(folder_frame, text="Select Folder for '0' Images:")
        self.folder_0_entry = tk.Entry(folder_frame, textvariable=self.folder_0, width=50)
        self.folder_0_button = tk.Button(folder_frame, text="Browse", command=self.browse_folder_0)

        self.folder_1_label = tk.Label(folder_frame, text="Select Folder for '1' Images:")
        self.folder_1_entry = tk.Entry(folder_frame, textvariable=self.folder_1, width=50)
        self.folder_1_button = tk.Button(folder_frame, text="Browse", command=self.browse_folder_1)

        self.folder_0_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.folder_0_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.folder_0_button.grid(row=0, column=2, padx=5, pady=5)

        self.folder_1_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.folder_1_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.folder_1_button.grid(row=1, column=2, padx=5, pady=5)

        # Frame for Move button
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        move_button = tk.Button(button_frame, text="Move Waldo Images", command=self.move_waldo_images)
        move_button.grid(row=0, column=0, padx=5, pady=10)

        # Navigation buttons
        self.back_button.grid(row=5, column=0, padx=5, pady=10, sticky="w")
        self.skip_button.grid(row=5, column=1, padx=5, pady=10, sticky="w")
        self.next_button.grid(row=5, column=2, padx=5, pady=10, sticky="e")

    def browse_base_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.base_folder.set(folder)

    def move_waldo_images(self):
        source_1 = self.folder_1.get()
        source_0 = self.folder_0.get()
        base_folder = self.base_folder.get().strip()
        location = self.location_entry.get().strip()
        camera = self.camera_entry.get().strip()
        year = self.year_entry.get().strip()
        mm_dd = self.mm_dd_entry.get().strip()

        if not (source_1 and source_0 and base_folder and location and camera and year and mm_dd):
            messagebox.showerror("Error", "Please fill out all fields and select all folders.")
            return

        # Construct the destination path based on user inputs
        destination_folder = os.path.join(base_folder, location, camera, year, mm_dd)

        # Create destination folder if it does not exist
        os.makedirs(destination_folder, exist_ok=True)

        # Store the created folder path
        self.created_folder_path = destination_folder

        try:
            # Move the contents of the '0' folder
            for item in os.listdir(source_0):
                source_path = os.path.join(source_0, item)
                dest_path = os.path.join(destination_folder, '0', item)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.move(source_path, dest_path)

            # Move the contents of the '1' folder
            for item in os.listdir(source_1):
                source_path = os.path.join(source_1, item)
                dest_path = os.path.join(destination_folder, '1', item)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.move(source_path, dest_path)

            messagebox.showinfo("Success", f"Images moved successfully to {destination_folder}!")
            self.next_step()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to move images: {e}")


    def move_generic_images(self):
        source_folders = []
        while True:
            folder = filedialog.askdirectory(title="Select Source Folder for a Camera")
            if folder:
                source_folders.append(folder)
                if not messagebox.askyesno("Add Another Folder", "Do you want to add another source folder?"):
                    break
            else:
                break

        if not source_folders:
            messagebox.showerror("Error", "Please select at least one source folder.")
            return

        destination_folder = filedialog.askdirectory(title="Select Destination Folder")
        if not destination_folder:
            messagebox.showerror("Error", "Please select a destination folder.")
            return

        csv_file = os.path.join(destination_folder, 'image_paths.csv')
        with open(csv_file, 'w', newline='') as csvfile:
            fieldnames = ['original_path', 'new_path']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for source_folder in source_folders:
                for foldername, subfolders, filenames in os.walk(source_folder):
                    for filename in filenames:
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                            original_path = os.path.join(foldername, filename)
                            new_path = os.path.join(destination_folder, filename)
                            shutil.move(original_path, new_path)
                            writer.writerow({'original_path': original_path, 'new_path': new_path})

        messagebox.showinfo("Success", "Generic camera images moved successfully!")
        self.next_step()

    def extract_image_metadata(self):
        self.instructions.config(text="3. Extract image metadata and verify data quality\n"
                                      "a. Run ‘Image_GPS_extract.py’\n"
                                      "i. Select Input Folder\n"
                                      "ii. Enter a name for your csv and select the folder you would like it to be saved\n"
                                      "b. Open the csv to view Image Filepaths, Timestamps, Latitudes, Longitudes, and Altitudes\n"
                                      "c. Upload a kml or shp of the proposed transects to be used as a reference")

        # Automatically set input and output paths if the folder was created in the previous step
        if hasattr(self, 'created_folder_path') and self.created_folder_path:
            self.folder_0.set(self.created_folder_path)
            output_csv_path = f"{self.created_folder_path}/original_gps_metadata.csv"
        else:
            output_csv_path = ""

        self.output_csv = tk.StringVar(value=output_csv_path)

        tk.Label(self.root, text="Input Folder:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        input_entry = tk.Entry(self.root, textvariable=self.folder_0, width=50)
        input_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        input_button = tk.Button(self.root, text="Browse", command=self.browse_folder_0)
        input_button.grid(row=1, column=2, padx=10, pady=5)

        tk.Label(self.root, text="Output CSV:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        output_entry = tk.Entry(self.root, textvariable=self.output_csv, width=50)
        output_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Update output_csv path when input folder is selected or changed
        def update_output_csv(*args):
            if self.folder_0.get():
                self.output_csv.set(f"{self.folder_0.get()}/original_gps_metadata.csv")

        self.folder_0.trace_add("write", update_output_csv)

        # Define the script path
        script_path = r"E:\SeeOtterUSGS\SeeOtter_pre_post-main\SeeOtter_pre_post-main\Image_GPS_extract.py"

        # Command to open the image metadata extractor GUI
        tk.Button(self.root, text="Extract Metadata",
                  command=lambda: self.run_script(script_path, self.folder_0.get(), self.output_csv.get())).grid(
            row=3, column=1, columnspan=2, padx=10, pady=10)

    import os
    import shutil
    import csv
    import subprocess
    import tkinter as tk
    from tkinter import filedialog, messagebox
    import pandas as pd
    import json
    import ast
    from datetime import datetime

    class ScrollableFrame(tk.Frame):
        def __init__(self, container, *args, **kwargs):
            super().__init__(container, *args, **kwargs)

            # Create canvas and scrollbars
            canvas = tk.Canvas(self)
            vscrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
            hscrollbar = tk.Scrollbar(self, orient="horizontal", command=canvas.xview)

            self.scrollable_frame = tk.Frame(canvas)

            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(
                    scrollregion=canvas.bbox("all"),
                    width=e.width
                )
            )

            # Add window to canvas
            canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

            # Configure scrollbars
            canvas.configure(yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)

            # Pack the canvas and scrollbars
            canvas.pack(side="left", fill="both", expand=True)
            vscrollbar.pack(side="right", fill="y")
            hscrollbar.pack(side="bottom", fill="x")

    class SequentialApp:
        def __init__(self, root):
            self.root = root
            self.root.title("SeeOtter Sequential Processing GUI")
            self.current_step = 0
            self.completed_steps = [False] * 9  # Initialize completed steps list

            self.source_folder = tk.StringVar()
            self.folder_0 = tk.StringVar()
            self.folder_1 = tk.StringVar()
            self.destination_folder = tk.StringVar()
            self.destination_folders = []

            self.steps = [
                "Backup Camera Files to hard drive",
                "Move image files into ‘0’ and ‘1’ camera folders",
                "Extract image metadata and verify data quality",
                "Assign images to transects",
                "Run Preprocessing",
                "Change Model Weights",
                "Edit Otter Checker Config",
                "Run SeeOtter Processing",
                "Final Processing"
            ]

            self.steps_functions = [
                self.backup_camera_files,
                self.move_image_files,
                self.extract_image_metadata,
                self.assign_images_to_transects,
                self.run_preprocessing,
                self.change_model_weights,
                self.edit_otter_checker_config,
                self.run_seeotter_processing,
                self.final_processing,
            ]

            self.create_widgets()
            self.update_step()

        def edit_otter_checker_config(self):
            self.instructions.config(text="Edit Otter Checker Config\n"
                                          "Modify the image tags and annotation categories.\n"
                                          "Save changes when done.")
            self.clear_widgets()
            self.load_config()

            # Create scrollable frame
            self.scrollable_frame = ScrollableFrame(self.root)
            self.scrollable_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

            # Image Tags
            tk.Label(self.scrollable_frame.scrollable_frame, text="Image Tags:").grid(row=0, column=0, padx=10, pady=10,
                                                                                      sticky="w")
            self.image_tags_entries = []
            for i, tag in enumerate(self.config['IMAGE_TAGS']):
                entry = tk.Entry(self.scrollable_frame.scrollable_frame)
                entry.grid(row=1 + i, column=0, padx=10, pady=2, sticky="w")
                entry.insert(0, tag)
                self.image_tags_entries.append(entry)

            # Annotation Categories
            tk.Label(self.scrollable_frame.scrollable_frame, text="Annotation Categories:").grid(row=0, column=1,
                                                                                                 padx=10,
                                                                                                 pady=10, sticky="w")
            self.annotation_categories_entries = []
            for i, (category, index) in enumerate(self.config['ANNOTATION_CATEGORIES']):
                entry_category = tk.Entry(self.scrollable_frame.scrollable_frame)
                entry_category.grid(row=1 + i, column=1, padx=10, pady=2, sticky="w")
                entry_category.insert(0, category)
                entry_index = tk.Entry(self.scrollable_frame.scrollable_frame)
                entry_index.grid(row=1 + i, column=2, padx=10, pady=2, sticky="w")
                entry_index.insert(0, index)
                self.annotation_categories_entries.append((entry_category, entry_index))

            # Add Add Category button inside scrollable frame
            tk.Button(self.scrollable_frame.scrollable_frame, text="Add Category", command=self.add_category).grid(
                row=1 + len(self.annotation_categories_entries), column=1, padx=10, pady=10, sticky="w")

            # Add Save Config button outside scrollable frame, but above navigation buttons
            self.save_button = tk.Button(self.root, text="Save Config", command=self.save_config)
            self.save_button.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="w")

            # Adjust position of navigation buttons
            self.next_button.grid(row=3, column=2, padx=10, pady=10)
            self.back_button.grid(row=3, column=0, padx=10, pady=10)
            self.skip_button.grid(row=3, column=1, padx=10, pady=10)

        def add_category(self):
            entry_category = tk.Entry(self.scrollable_frame.scrollable_frame)
            entry_category.grid(row=1 + len(self.annotation_categories_entries), column=1, padx=10, pady=2, sticky="w")
            entry_index = tk.Entry(self.scrollable_frame.scrollable_frame)
            entry_index.grid(row=1 + len(self.annotation_categories_entries), column=2, padx=10, pady=2, sticky="w")
            self.annotation_categories_entries.append((entry_category, entry_index))
            # Update Save Config button position
            self.update_save_button_position()

        def update_save_button_position(self):
            max_entries = max(len(self.image_tags_entries), len(self.annotation_categories_entries))
            self.save_button.grid(row=2 + max_entries, column=0, columnspan=3, padx=10, pady=10, sticky="w")

        def load_config(self):
            config_path = r"E:\SeeOtterUSGS\SeeOtter_pre_post-main\SeeOtter_pre_post-main\Config\otter_checker_config.py"
            self.config = {}

            with open(config_path, 'r') as f:
                content = f.read()

            # Extract IMAGE_TAGS
            image_tags_start = content.find("self.IMAGE_TAGS = [")
            image_tags_end = content.find("]", image_tags_start) + 1
            image_tags_data = content[image_tags_start:image_tags_end].split(" = ")[1]
            self.config['IMAGE_TAGS'] = ast.literal_eval(image_tags_data)

            # Extract ANNOTATION_CATEGORIES
            annotation_categories_start = content.find("self.ANNOTATION_CATEGORIES = [")
            annotation_categories_end = content.find("]", annotation_categories_start) + 1
            annotation_categories_data = content[annotation_categories_start:annotation_categories_end].split(" = ")[1]
            self.config['ANNOTATION_CATEGORIES'] = ast.literal_eval(annotation_categories_data)

        def add_tag(self):
            entry = tk.Entry(self.root)
            entry.grid(row=2 + len(self.image_tags_entries), column=0, padx=10, pady=2, sticky="w")
            self.image_tags_entries.append(entry)

        def add_category(self):
            entry_category = tk.Entry(self.root)
            entry_category.grid(row=2 + len(self.annotation_categories_entries), column=1, padx=10, pady=2, sticky="w")
            entry_index = tk.Entry(self.root)
            entry_index.grid(row=2 + len(self.annotation_categories_entries), column=2, padx=10, pady=2, sticky="w")
            self.annotation_categories_entries.append((entry_category, entry_index))

        def save_config(self):
            new_image_tags = [entry.get() for entry in self.image_tags_entries]
            new_annotation_categories = [(entry_category.get(), int(entry_index.get())) for entry_category, entry_index
                                         in
                                         self.annotation_categories_entries]

            config_path = r"E:\SeeOtterUSGS\SeeOtter_pre_post-main\SeeOtter_pre_post-main\Config\otter_checker_config.py"
            json_config_path = r"E:\SeeOtterUSGS\SeeOtter_pre_post-main\SeeOtter_pre_post-main\otter_checker_config.json"

            # Create a backup of the current config file
            backup_path = config_path + ".bak"
            shutil.copy2(config_path, backup_path)

            with open(config_path, 'r') as f:
                content = f.read()

            updated_content = content.split("self.IMAGE_TAGS = [")[0] + f"self.IMAGE_TAGS = {new_image_tags}\n"
            updated_content += \
                content.split("self.IMAGE_TAGS = [")[1].split("]")[1].split("self.ANNOTATION_CATEGORIES = [")[0]
            updated_content += f"self.ANNOTATION_CATEGORIES = {new_annotation_categories}\n" + \
                               content.split("self.ANNOTATION_CATEGORIES = [")[1].split("]")[1]

            with open(config_path, 'w') as f:
                f.write(updated_content)

            # Delete the .json config file if it exists
            if os.path.exists(json_config_path):
                os.remove(json_config_path)

            messagebox.showinfo("Success", f"Configuration updated successfully! Backup saved at {backup_path}")
            self.next_step()

        def create_widgets(self):
            self.instructions = tk.Label(self.root, text="", wraplength=500, justify="left")
            self.instructions.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

            self.folder_0_label = tk.Label(self.root, text="Select Folder for '0' Images:")
            self.folder_0_entry = tk.Entry(self.root, textvariable=self.folder_0, width=50)
            self.folder_0_button = tk.Button(self.root, text="Browse", command=self.browse_folder_0)

            self.folder_1_label = tk.Label(self.root, text="Select Folder for '1' Images:")
            self.folder_1_entry = tk.Entry(self.root, textvariable=self.folder_1, width=50)
            self.folder_1_button = tk.Button(self.root, text="Browse", command=self.browse_folder_1)

            self.destination_folder_label = tk.Label(self.root, text="Select Destination Folder:")
            self.destination_folder_entry = tk.Entry(self.root, textvariable=self.destination_folder, width=50)
            self.destination_folder_button = tk.Button(self.root, text="Browse", command=self.browse_destination_folder)

            self.source_folder_label = tk.Label(self.root, text="Select Folder to Backup:")
            self.source_folder_entry = tk.Entry(self.root, textvariable=self.source_folder, width=50)
            self.source_folder_button = tk.Button(self.root, text="Browse", command=self.browse_source_folder)
            self.add_destination_button = tk.Button(self.root, text="Add Destination",
                                                    command=self.add_destination_folder)
            self.destinations_frame = tk.Frame(self.root)
            self.num_backups_label = tk.Label(self.root, text="Number of Backups:")
            self.num_backups = tk.Spinbox(self.root, from_=1, to=10, width=5)

            self.next_button = tk.Button(self.root, text="Next", command=self.next_step)
            self.back_button = tk.Button(self.root, text="Back", command=self.prev_step)
            self.skip_button = tk.Button(self.root, text="Skip", command=self.skip_step)

            self.next_button.grid(row=5, column=2, padx=10, pady=10)
            self.back_button.grid(row=5, column=0, padx=10, pady=10)
            self.skip_button.grid(row=5, column=1, padx=10, pady=10)

            self.step_labels = [tk.Label(self.root, text=step) for step in self.steps]
            self.step_checkmarks = [tk.Label(self.root, text="✗") for _ in range(len(self.steps))]
            for i, (label, checkmark) in enumerate(zip(self.step_labels, self.step_checkmarks)):
                label.grid(row=6 + i, column=0, columnspan=2, sticky="w", padx=10, pady=2)
                checkmark.grid(row=6 + i, column=2, padx=10, pady=2)

        def update_step(self):
            self.clear_widgets()
            step_function = self.steps_functions[self.current_step]
            step_function()

            # Update checkmarks
            for i, checkmark in enumerate(self.step_checkmarks):
                if self.completed_steps[i]:
                    checkmark.config(text="✓")
                else:
                    checkmark.config(text="✗")

            # Ensure navigation buttons are always visible
            self.next_button.grid(row=5, column=2, padx=10, pady=10)
            self.back_button.grid(row=5, column=0, padx=10, pady=10)
            self.skip_button.grid(row=5, column=1, padx=10, pady=10)

        def clear_widgets(self):
            for widget in self.root.winfo_children():
                if widget not in {self.instructions, *self.step_labels, *self.step_checkmarks}:
                    widget.grid_forget()

            self.destination_folders.clear()
            for widget in self.destinations_frame.winfo_children():
                widget.destroy()
            self.destination_folder.set("")

        def next_step(self):
            self.completed_steps[self.current_step] = True
            self.current_step += 1
            if self.current_step < len(self.steps_functions):
                self.update_step()
            else:
                messagebox.showinfo("Completed", "All steps are completed!")
                self.root.quit()

        def prev_step(self):
            if self.current_step > 0:
                self.current_step -= 1
            self.update_step()

        def skip_step(self):
            self.current_step += 1
            if self.current_step < len(self.steps_functions):
                self.update_step()
            else:
                messagebox.showinfo("Completed", "All steps are completed!")
                self.root.quit()

        def browse_folder_1(self):
            folder = filedialog.askdirectory()
            if folder:
                self.folder_1.set(folder)

        def browse_folder_0(self):
            folder = filedialog.askdirectory()
            if folder:
                self.folder_0.set(folder)

        def browse_destination_folder(self):
            folder = filedialog.askdirectory()
            if folder:
                self.destination_folder.set(folder)

        def browse_source_folder(self):
            folder = filedialog.askdirectory()
            if folder:
                self.source_folder.set(folder)

        def add_destination_folder(self):
            folder = filedialog.askdirectory()
            if folder:
                self.destination_folders.append(folder)
                frame = tk.Frame(self.destinations_frame)
                label = tk.Label(frame, text=folder)
                label.pack(side="left")
                remove_button = tk.Button(frame, text="Remove",
                                          command=lambda: self.remove_destination_folder(frame, folder))
                remove_button.pack(side="right")
                frame.pack()
                self.destinations_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

        def remove_destination_folder(self, frame, folder):
            frame.destroy()
            self.destination_folders.remove(folder)

        def run_script(self, script_path, *args):
            try:
                subprocess.run(['python', script_path, *args], check=True)
                messagebox.showinfo("Success", f"{os.path.basename(script_path)} completed successfully!")
                self.completed_steps[self.current_step] = True
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to run {os.path.basename(script_path)}.\nError: {str(e)}\nReturn Code: {e.returncode}\nOutput: {e.output}"
                messagebox.showerror("Error", error_msg)
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

        def backup_camera_files(self):
            self.instructions.config(text="1. Backup Camera Files to hard drive\n"
                                          "a. Run Backup_Images.py to automate this process\n"
                                          "i. Select the number of backups you are going to make\n"
                                          "ii. Select the drive and folder where you want the backups placed\n"
                                          "iii. Run script\n"
                                          "b. Alternatively you can manually copy and paste the camera files onto each backup drive\n"
                                          "c. Backups should be made on at least 3 separate physical drives")
            self.source_folder_label.grid(row=1, column=0, padx=10, pady=10)
            self.source_folder_entry.grid(row=1, column=1, padx=10, pady=10)
            self.source_folder_button.grid(row=1, column=2, padx=10, pady=10)

            self.add_destination_button.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
            self.destinations_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

            tk.Button(self.root, text="Start Backup", command=self.start_backup).grid(row=4, column=2, padx=10, pady=10)

        def move_image_files(self):
            self.instructions.config(
                text="2. Move image files into ‘0’ and ‘1’ camera folders based on which camera the image was taken from\n"
                     "a. Create a folder structure and place the images inside\n"
                     "b. For non-Waldo cameras\n"
                     "c. For Waldo cameras")

            # Frame for Base Folder selection
            base_folder_frame = tk.Frame(self.root)
            base_folder_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

            self.base_folder_label = tk.Label(base_folder_frame, text="Base Folder:")
            self.base_folder = tk.StringVar()
            self.base_folder_entry = tk.Entry(base_folder_frame, textvariable=self.base_folder, width=50)
            self.base_folder_button = tk.Button(base_folder_frame, text="Browse", command=self.browse_base_folder)

            self.base_folder_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.base_folder_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            self.base_folder_button.grid(row=0, column=2, padx=5, pady=5)

            # Frame for Location, Camera, Year, and MM_DD
            details_frame = tk.Frame(self.root)
            details_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

            self.location_label = tk.Label(details_frame, text="Location:")
            self.location_entry = tk.Entry(details_frame, width=30)
            self.camera_label = tk.Label(details_frame, text="Camera:")
            self.camera_entry = tk.Entry(details_frame, width=30)
            self.year_label = tk.Label(details_frame, text="Year:")
            self.year_entry = tk.Entry(details_frame, width=30)
            self.mm_dd_label = tk.Label(details_frame, text="MM_DD:")
            self.mm_dd_entry = tk.Entry(details_frame, width=30)

            self.location_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.location_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            self.camera_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.camera_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
            self.year_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
            self.year_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
            self.mm_dd_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
            self.mm_dd_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

            # Frame for Folder selection for '0' and '1' images
            folder_frame = tk.Frame(self.root)
            folder_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

            self.folder_0_label = tk.Label(folder_frame, text="Select Folder for '0' Images:")
            self.folder_0_entry = tk.Entry(folder_frame, textvariable=self.folder_0, width=50)
            self.folder_0_button = tk.Button(folder_frame, text="Browse", command=self.browse_folder_0)

            self.folder_1_label = tk.Label(folder_frame, text="Select Folder for '1' Images:")
            self.folder_1_entry = tk.Entry(folder_frame, textvariable=self.folder_1, width=50)
            self.folder_1_button = tk.Button(folder_frame, text="Browse", command=self.browse_folder_1)

            self.folder_0_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.folder_0_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            self.folder_0_button.grid(row=0, column=2, padx=5, pady=5)

            self.folder_1_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.folder_1_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
            self.folder_1_button.grid(row=1, column=2, padx=5, pady=5)

            # Frame for Move button
            button_frame = tk.Frame(self.root)
            button_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

            move_button = tk.Button(button_frame, text="Move Waldo Images", command=self.move_waldo_images)
            move_button.grid(row=0, column=0, padx=5, pady=10)

            # Navigation buttons
            self.back_button.grid(row=5, column=0, padx=5, pady=10, sticky="w")
            self.skip_button.grid(row=5, column=1, padx=5, pady=10, sticky="w")
            self.next_button.grid(row=5, column=2, padx=5, pady=10, sticky="e")

        def browse_base_folder(self):
            folder = filedialog.askdirectory()
            if folder:
                self.base_folder.set(folder)

        def move_waldo_images(self):
            source_1 = self.folder_1.get()
            source_0 = self.folder_0.get()
            base_folder = self.base_folder.get().strip()
            location = self.location_entry.get().strip()
            camera = self.camera_entry.get().strip()
            year = self.year_entry.get().strip()
            mm_dd = self.mm_dd_entry.get().strip()

            if not (source_1 and source_0 and base_folder and location and camera and year and mm_dd):
                messagebox.showerror("Error", "Please fill out all fields and select all folders.")
                return

            # Construct the destination path based on user inputs
            destination_folder = os.path.join(base_folder, location, camera, year, mm_dd)

            # Create destination folder if it does not exist
            os.makedirs(destination_folder, exist_ok=True)

            # Store the created folder path
            self.created_folder_path = destination_folder

            try:
                # Move the contents of the '0' folder
                for item in os.listdir(source_0):
                    source_path = os.path.join(source_0, item)
                    dest_path = os.path.join(destination_folder, '0', item)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.move(source_path, dest_path)

                # Move the contents of the '1' folder
                for item in os.listdir(source_1):
                    source_path = os.path.join(source_1, item)
                    dest_path = os.path.join(destination_folder, '1', item)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.move(source_path, dest_path)

                messagebox.showinfo("Success", f"Images moved successfully to {destination_folder}!")
                self.next_step()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to move images: {e}")

        def move_generic_images(self):
            source_folders = []
            while True:
                folder = filedialog.askdirectory(title="Select Source Folder for a Camera")
                if folder:
                    source_folders.append(folder)
                    if not messagebox.askyesno("Add Another Folder", "Do you want to add another source folder?"):
                        break
                else:
                    break

            if not source_folders:
                messagebox.showerror("Error", "Please select at least one source folder.")
                return

            destination_folder = filedialog.askdirectory(title="Select Destination Folder")
            if not destination_folder:
                messagebox.showerror("Error", "Please select a destination folder.")
                return

            csv_file = os.path.join(destination_folder, 'image_paths.csv')
            with open(csv_file, 'w', newline='') as csvfile:
                fieldnames = ['original_path', 'new_path']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for source_folder in source_folders:
                    for foldername, subfolders, filenames in os.walk(source_folder):
                        for filename in filenames:
                            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                                original_path = os.path.join(foldername, filename)
                                new_path = os.path.join(destination_folder, filename)
                                shutil.move(original_path, new_path)
                                writer.writerow({'original_path': original_path, 'new_path': new_path})

            messagebox.showinfo("Success", "Generic camera images moved successfully!")
            self.next_step()

        def extract_image_metadata(self):
            self.instructions.config(text="3. Extract image metadata and verify data quality\n"
                                          "a. Run ‘Image_GPS_extract.py’\n"
                                          "i. Select Input Folder\n"
                                          "ii. Enter a name for your csv and select the folder you would like it to be saved\n"
                                          "b. Open the csv to view Image Filepaths, Timestamps, Latitudes, Longitudes, and Altitudes\n"
                                          "c. Upload a kml or shp of the proposed transects to be used as a reference")

            # Automatically set input and output paths if the folder was created in the previous step
            if hasattr(self, 'created_folder_path') and self.created_folder_path:
                self.folder_0.set(self.created_folder_path)
                output_csv_path = f"{self.created_folder_path}/original_gps_metadata.csv"
            else:
                output_csv_path = ""

            self.output_csv = tk.StringVar(value=output_csv_path)

            tk.Label(self.root, text="Input Folder:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
            input_entry = tk.Entry(self.root, textvariable=self.folder_0, width=50)
            input_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
            input_button = tk.Button(self.root, text="Browse", command=self.browse_folder_0)
            input_button.grid(row=1, column=2, padx=10, pady=5)

            tk.Label(self.root, text="Output CSV:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
            output_entry = tk.Entry(self.root, textvariable=self.output_csv, width=50)
            output_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

            # Update output_csv path when input folder is selected or changed
            def update_output_csv(*args):
                if self.folder_0.get():
                    self.output_csv.set(f"{self.folder_0.get()}/original_gps_metadata.csv")

            self.folder_0.trace_add("write", update_output_csv)

            # Define the script path
            script_path = r"E:\SeeOtterUSGS\SeeOtter_pre_post-main\SeeOtter_pre_post-main\Image_GPS_extract.py"

            # Command to open the image metadata extractor GUI
            tk.Button(self.root, text="Extract Metadata",
                      command=lambda: self.run_script(script_path, self.folder_0.get(), self.output_csv.get())).grid(
                row=3, column=1, columnspan=2, padx=10, pady=10)

        def assign_images_to_transects(self):
            self.instructions.config(text="4. Assign images to transects\n"
                                          "a. Use the tx_assignment_template.csv or create a csv with 5 columns\n"
                                          "b. Fill ‘transect_id’ with the names of your proposed transects\n"
                                          "c. For each transect set your start and end points\n"
                                          "i. Use file paths or times for start and end points")

            # Initialize the CSV container
            self.csv_container = ScrollableFrame(self.root)
            self.csv_container.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

            gps_metadata_csv_path = None
            if hasattr(self, 'created_folder_path') and self.created_folder_path:
                gps_metadata_csv_path = f"{self.created_folder_path}/original_gps_metadata.csv"
            elif hasattr(self, 'output_csv') and os.path.exists(self.output_csv.get()):
                gps_metadata_csv_path = self.output_csv.get()
            else:
                gps_metadata_csv_path = filedialog.askopenfilename(
                    title="Select the original_gps_metadata.csv",
                    filetypes=[("CSV Files", "*.csv")]
                )

            if gps_metadata_csv_path and os.path.exists(gps_metadata_csv_path):
                gps_metadata_df = pd.read_csv(gps_metadata_csv_path)
                self.filepaths = list(zip(gps_metadata_df['Filepath'], gps_metadata_df['DatetimeOriginal']))
            else:
                messagebox.showerror("Error", "The original_gps_metadata.csv file could not be found or opened.")
                self.filepaths = []

            if self.filepaths:
                self.select_filepaths_for_transects()

        def select_filepaths_for_transects(self):
            """Allow the user to select file paths to use for start_img and end_img columns."""
            # Create a new window for file path selection
            selection_window = tk.Toplevel(self.root)
            selection_window.title("Select File Paths for Transects")

            tk.Label(selection_window, text="Search by Filename:").pack(padx=10, pady=5)
            search_entry = tk.Entry(selection_window, width=50)
            search_entry.pack(padx=10, pady=5)

            tk.Label(selection_window, text="Select the file paths you want to use (Max 2):").pack(padx=10, pady=5)

            # Labels to show selected first and last images
            self.first_image_label = tk.Label(selection_window, text="First Image: None")
            self.first_image_label.pack(padx=10, pady=5)
            self.last_image_label = tk.Label(selection_window, text="Last Image: None")
            self.last_image_label.pack(padx=10, pady=5)

            # Initialize filtered_filepaths to the full list of filepaths
            self.filtered_filepaths = self.filepaths.copy()

            # Initialize selected file paths tracker
            self.selected_filepaths = []

            # Create a listbox for file path selection with DatetimeOriginal
            self.filepath_listbox = tk.Listbox(selection_window, selectmode=tk.MULTIPLE, width=100, height=20)
            self.update_file_listbox()
            self.filepath_listbox.pack(padx=10, pady=5)

            # Bind the search functionality
            search_entry.bind("<KeyRelease>", lambda event: self.filter_filepaths(search_entry.get()))

            # Bind the selection event to update the labels
            self.filepath_listbox.bind("<<ListboxSelect>>", self.update_image_labels)

            # Button to confirm selection
            tk.Button(selection_window, text="Confirm Selection",
                      command=lambda: self.confirm_filepaths(selection_window)).pack(padx=10, pady=10)

        def update_image_labels(self, event):
            """Update labels with the selected first and last images and preserve the selection."""
            selected_indices = self.filepath_listbox.curselection()
            selected_filepaths = [self.filtered_filepaths[i] for i in selected_indices]

            if len(selected_filepaths) > 0:
                # If it's the first selection, update the first image
                if len(self.selected_filepaths) == 0:
                    self.selected_filepaths.append(selected_filepaths[0])
                    self.first_image_label.config(text=f"First Image: {selected_filepaths[0][0]}")
                elif len(self.selected_filepaths) == 1 and selected_filepaths[0] != self.selected_filepaths[0]:
                    # If it's the second selection and not the same as the first, update the last image
                    self.selected_filepaths.append(selected_filepaths[0])
                    self.last_image_label.config(text=f"Last Image: {selected_filepaths[0][0]}")
                elif len(self.selected_filepaths) == 1:
                    # If the user changes the first selection, update it
                    self.selected_filepaths[0] = selected_filepaths[0]
                    self.first_image_label.config(text=f"First Image: {selected_filepaths[0][0]}")
                elif len(self.selected_filepaths) == 2:
                    # If the user changes the second selection, update it
                    self.selected_filepaths[1] = selected_filepaths[0]
                    self.last_image_label.config(text=f"Last Image: {selected_filepaths[0][0]}")

        def prompt_transect_name(self):
            """Prompt the user to enter a transect name."""
            transect_name = tk.simpledialog.askstring("Transect Name", "Enter the transect name:")
            return transect_name if transect_name else f"transect_{len(self.csv_data) + 1}"

        def confirm_filepaths(self, selection_window):
            """Confirm the selected file paths and their DatetimeOriginal values."""
            selected_indices = self.filepath_listbox.curselection()
            selected_filepaths = [self.filtered_filepaths[i] for i in selected_indices]

            if len(selected_filepaths) == 2:
                self.selected_filepaths = selected_filepaths

                # Prompt for transect name
                transect_name = self.prompt_transect_name()

                new_row = {
                    'start_img': self.selected_filepaths[0][0],
                    'end_img': self.selected_filepaths[1][0],
                    'transect_id': transect_name,
                    'start_time': self.selected_filepaths[0][1],
                    'end_time': self.selected_filepaths[1][1]
                }
                new_row_df = pd.DataFrame([new_row])

                # Ensure self.csv_data is initialized as a DataFrame
                if not hasattr(self, 'csv_data') or not isinstance(self.csv_data, pd.DataFrame):
                    self.csv_data = pd.DataFrame()

                # Concatenate the new row
                self.csv_data = pd.concat([self.csv_data, new_row_df], ignore_index=True)
                self.display_csv()
                selection_window.destroy()
            else:
                messagebox.showerror("Error", "Please select exactly two file paths.")

        def create_default_csv_with_selected_filepaths(self, selected_filepaths):
            """Create a default CSV structure pre-filled with the selected file paths."""
            default_columns = ['start_img', 'end_img', 'transect_id', 'start_time', 'end_time']
            # Initialize CSV with the first and last selected images
            data = {
                'start_img': [selected_filepaths[0][0]],
                'end_img': [selected_filepaths[-1][0]],
                'transect_id': ['transect_1'],
                'start_time': [selected_filepaths[0][1]],
                'end_time': [selected_filepaths[-1][1]]
            }

            self.csv_data = pd.DataFrame(data)
            self.display_csv()

        def load_csv(self):
            file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
            if not file_path:
                return

            self.csv_data = pd.read_csv(file_path)
            self.display_csv()

        def display_csv(self):
            # Ensure the CSV container is initialized
            if not hasattr(self, 'csv_container'):
                self.csv_container = ScrollableFrame(self.root)
                self.csv_container.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

            for widget in self.csv_container.scrollable_frame.winfo_children():
                widget.destroy()

            columns = list(self.csv_data.columns)
            for col_num, column in enumerate(columns):
                label = tk.Label(self.csv_container.scrollable_frame, text=column, borderwidth=1, relief="solid")
                label.grid(row=0, column=col_num, sticky="nsew")

            self.csv_widgets = []
            for i, row in self.csv_data.iterrows():
                row_widgets = []
                for j, value in enumerate(row):
                    entry = tk.Entry(self.csv_container.scrollable_frame)
                    entry.grid(row=i + 1, column=j, sticky="nsew")
                    entry.insert(0, value)
                    row_widgets.append(entry)
                self.csv_widgets.append(row_widgets)

            # Set column and row weights for resizing
            for i in range(len(columns)):
                self.csv_container.scrollable_frame.grid_columnconfigure(i, weight=1)
            for i in range(len(self.csv_data)):
                self.csv_container.scrollable_frame.grid_rowconfigure(i, weight=1)

        def save_csv(self):
            # If the folder_0 (input folder) has already been defined, use it to save the CSV
            if hasattr(self, 'created_folder_path') and self.created_folder_path:
                save_path = f"{self.created_folder_path}/transect_assignment.csv"
            elif hasattr(self, 'output_csv') and os.path.exists(self.output_csv.get()):
                save_path = os.path.join(os.path.dirname(self.output_csv.get()), "transect_assignment.csv")
            else:
                save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])

            if not save_path:
                return

            # Save the current data from the widgets into the DataFrame
            for i, row in self.csv_data.iterrows():
                for j, _ in enumerate(row):
                    self.csv_data.iat[i, j] = self.csv_widgets[i][j].get()

            # Sort by DatetimeOriginal before saving
            if 'start_img' in self.csv_data.columns:
                sorted_df = self.csv_data.sort_values(by='start_img')
            else:
                sorted_df = self.csv_data

            # Save the DataFrame to the specified CSV file
            sorted_df.to_csv(save_path, index=False)
            messagebox.showinfo("Success", f"CSV file saved successfully at {save_path}!")

        def display_csv(self):
            # Ensure the CSV container is initialized
            if not hasattr(self, 'csv_container'):
                self.csv_container = ScrollableFrame(self.root)
                self.csv_container.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

            for widget in self.csv_container.scrollable_frame.winfo_children():
                widget.destroy()

            columns = list(self.csv_data.columns)
            for col_num, column in enumerate(columns):
                label = tk.Label(self.csv_container.scrollable_frame, text=column, borderwidth=1, relief="solid")
                label.grid(row=0, column=col_num, sticky="nsew")

            self.csv_widgets = []
            for i, row in self.csv_data.iterrows():
                row_widgets = []
                for j, value in enumerate(row):
                    entry = tk.Entry(self.csv_container.scrollable_frame)
                    entry.grid(row=i + 1, column=j, sticky="nsew")
                    entry.insert(0, value)
                    row_widgets.append(entry)
                self.csv_widgets.append(row_widgets)

            # Set column and row weights for resizing
            for i in range(len(columns)):
                self.csv_container.scrollable_frame.grid_columnconfigure(i, weight=1)
            for i in range(len(self.csv_data)):
                self.csv_container.scrollable_frame.grid_rowconfigure(i + 1, weight=1)

            # Re-add the control buttons
            tk.Button(self.root, text="Load CSV", command=self.load_csv).grid(row=1, column=0, padx=10, pady=10)
            tk.Button(self.root, text="Save CSV", command=self.save_csv).grid(row=1, column=1, padx=10, pady=10)
            tk.Button(self.root, text="Create Default CSV", command=self.create_default_csv).grid(row=1, column=2,
                                                                                                  padx=10, pady=10)
            tk.Button(self.root, text="Add Row", command=self.add_row).grid(row=1, column=3, padx=10, pady=10)

        def create_default_csv(self):
            default_columns = ['start_img', 'end_img', 'transect_id', 'start_time', 'end_time']
            self.csv_data = pd.DataFrame(columns=default_columns)
            self.display_csv()

        def add_row(self):
            # Check if the CSV data is initialized
            if not hasattr(self, 'csv_data') or not isinstance(self.csv_data, pd.DataFrame):
                self.csv_data = pd.DataFrame()

            # Trigger the image selection process for the new row
            self.select_filepaths_for_new_row()

        def select_filepaths_for_new_row(self):
            """Allow the user to select file paths and corresponding DatetimeOriginal values for a new row."""
            # Create a new window for file path selection
            selection_window = tk.Toplevel(self.root)
            selection_window.title("Select File Paths for New Row")

            tk.Label(selection_window, text="Search by Filename:").pack(padx=10, pady=5)
            search_entry = tk.Entry(selection_window, width=50)
            search_entry.pack(padx=10, pady=5)

            tk.Label(selection_window, text="Select the file paths you want to use (Max 2):").pack(padx=10, pady=5)

            # Labels to show selected first and last images
            self.first_image_label = tk.Label(selection_window, text="First Image: None")
            self.first_image_label.pack(padx=10, pady=5)
            self.last_image_label = tk.Label(selection_window, text="Last Image: None")
            self.last_image_label.pack(padx=10, pady=5)

            # Initialize filtered_filepaths to the full list of filepaths
            self.filtered_filepaths = self.filepaths.copy()

            # Initialize selected file paths tracker
            self.selected_filepaths = []

            # Create a listbox for file path selection with DatetimeOriginal
            self.filepath_listbox = tk.Listbox(selection_window, selectmode=tk.MULTIPLE, width=100, height=20)
            self.update_file_listbox()
            self.filepath_listbox.pack(padx=10, pady=5)

            # Bind the search functionality
            search_entry.bind("<KeyRelease>", lambda event: self.filter_filepaths(search_entry.get()))

            # Bind the selection event to update the labels
            self.filepath_listbox.bind("<<ListboxSelect>>", self.update_image_labels)

            # Button to confirm selection
            tk.Button(selection_window, text="Confirm Selection",
                      command=lambda: self.confirm_new_row_filepaths(selection_window)).pack(padx=10, pady=10)

        def confirm_new_row_filepaths(self, selection_window):
            """Confirm the selected file paths and their DatetimeOriginal values for the new row."""
            selected_indices = self.filepath_listbox.curselection()
            selected_filepaths = [self.filtered_filepaths[i] for i in selected_indices]

            if len(selected_filepaths) == 2:
                start_filepath, start_time = selected_filepaths[0]
                end_filepath, end_time = selected_filepaths[1]

                # Prompt for the transect name
                transect_name = self.prompt_transect_name()

                new_row = {
                    'start_img': start_filepath,
                    'end_img': end_filepath,
                    'transect_id': transect_name,
                    'start_time': start_time,
                    'end_time': end_time
                }
                new_row_df = pd.DataFrame([new_row])

                # Add the new row to the CSV data
                self.csv_data = pd.concat([self.csv_data, new_row_df], ignore_index=True)

                # Update the CSV display
                self.display_csv()

                # Close the selection window
                selection_window.destroy()
            else:
                messagebox.showerror("Error", "Please select exactly two file paths.")

        def filter_filepaths(self, search_text):
            """Filter the file paths based on the search text, keeping selected paths at the top."""
            search_text = search_text.lower()

            # Filter the file paths based on the search text
            filtered_filepaths = [
                (fp, dt) for fp, dt in self.filepaths if search_text in os.path.basename(fp).lower()
            ]

            # Combine the selected paths with the filtered paths, ensuring no duplicates
            self.filtered_filepaths = self.selected_filepaths + [
                (fp, dt) for fp, dt in filtered_filepaths if (fp, dt) not in self.selected_filepaths
            ]

            # Update the listbox with the new filtered list
            self.update_file_listbox()

        def update_file_listbox(self):
            """Update the listbox to display the filtered file paths along with their DatetimeOriginal values."""
            self.filepath_listbox.delete(0, tk.END)  # Clear the current listbox content

            for filepath, datetime_original in self.filtered_filepaths:
                # Combine the file path and DatetimeOriginal for display
                display_text = f"{filepath} | {datetime_original}"
                self.filepath_listbox.insert(tk.END, display_text)

            # Restore previous selections
            for i, (fp, dt) in enumerate(self.filtered_filepaths):
                if (fp, dt) in self.selected_filepaths:
                    self.filepath_listbox.selection_set(i)

        def start_backup(self):
            source = self.source_folder.get()
            if not source:
                messagebox.showerror("Error", "Please select a folder to backup.")
                return

            if not self.destination_folders:
                messagebox.showerror("Error", "Please select at least one destination folder.")
                return

            for dest in self.destination_folders:
                backup_path = os.path.join(dest, f"{os.path.basename(source)}_backup")
                shutil.copytree(source, backup_path)

            messagebox.showinfo("Success", "Backup completed successfully!")
            self.next_step()

        def extract_gps_data(self):
            source_1 = self.folder_1.get()
            source_0 = self.folder_0.get()
            if not source_1 or not source_0:
                messagebox.showerror("Error", "Please select both source folders.")
                return
            self.run_script('SeeOtter_pre_post-main/Image_GPS_extract.py', source_1, source_0)
            self.next_step()

        def run_preprocessing(self):
            self.instructions.config(text="5. Run ‘SeeOtter_prepro_GUI_non_Waldo_with_GPS_fix.py’\n"
                                          "a. For input folder: select your Images folder inside your MM_DD folder\n"
                                          "b. For the transect csv: select the transect assignment csv created in step 4\n"
                                          "c. (Optional) Select KML for GPS correction\n"
                                          "d. Run ‘Extract & Assign Transects’")

            tk.Button(self.root, text="Run Preprocessing", command=self.run_preprocessing_script).grid(row=4, column=1,
                                                                                                       padx=10, pady=10)

        def run_preprocessing_script(self):
            self.run_script('SeeOtter_pre_post-main/SeeOtter_prepro_GUI_non_Waldo_with_GPS_fix.py')
            self.next_step()

        def run_seeotter_processing(self):
            self.instructions.config(text="6. Run ‘SeeOtter.exe’\n"
                                          "a. Create a new survey in SeeOtter\n"
                                          "b. Point to the newly generated ‘cropped_images_on_tx’ folder\n"
                                          "c. Start processing the survey\n"
                                          "d. Validate predictions in OtterChecker9000")

            tk.Button(self.root, text="Start SeeOtter", command=self.start_seeotter).grid(row=4, column=1, padx=10,
                                                                                          pady=10)

        def start_seeotter(self):
            self.run_script('SeeOtter_pre_post-main/start_see_otter_no_survey.py')
            self.next_step()

        def change_model_weights(self):
            self.instructions.config(text="7. Change Model Weights\n"
                                          "a. Select new model weights file (.pt)\n"
                                          "b. Replace the best.pt file in the ModelWeights folder\n"
                                          "c. Save a backup of the old best.pt file with a timestamp")

            tk.Button(self.root, text="Change Model Weights", command=self.change_model_weights_script).grid(row=4,
                                                                                                             column=1,
                                                                                                             padx=10,
                                                                                                             pady=10)

        def change_model_weights_script(self):
            new_weights = filedialog.askopenfilename(title="Select new model weights",
                                                     filetypes=(("PyTorch model files", "*.pt"), ("All files", "*.*")))
            if new_weights:
                model_weights_folder = os.path.join('SeeOtter_pre_post-main', 'ModelWeights')
                best_weights = os.path.join(model_weights_folder, 'best.pt')

                if os.path.exists(best_weights):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_weights = os.path.join(model_weights_folder, f"best_{timestamp}.pt")
                    shutil.copy2(best_weights, backup_weights)
                    messagebox.showinfo("Backup", f"Backup of current best.pt created: {backup_weights}")

                shutil.copy2(new_weights, best_weights)
                messagebox.showinfo("Success", "Model weights updated successfully!")
            self.next_step()

        def final_processing(self):
            self.instructions.config(text="8. Final Processing\n"
                                          "a. Run ‘SeeOtter_post_pro_count_and_split_odd_even.py’\n"
                                          "b. Verify final results in mapping software")

            tk.Button(self.root, text="Run Final Processing", command=self.final_processing_script).grid(row=4,
                                                                                                         column=1,
                                                                                                         padx=10,
                                                                                                         pady=10)

        def final_processing_script(self):
            self.run_script('SeeOtter_pre_post-main/SeeOtter_post_pro_count_and_split_odd_even.py')
            self.next_step()

    if __name__ == "__main__":
        os.chdir('E:\\SeeOtterUSGS\\SeeOtter_pre_post-main')

        root = tk.Tk()
        app = SequentialApp(root)
        root.mainloop()

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return

        self.csv_data = pd.read_csv(file_path)
        self.display_csv()


    def display_csv(self):
        for widget in self.csv_container.scrollable_frame.winfo_children():
            widget.destroy()

        columns = list(self.csv_data.columns)
        for col_num, column in enumerate(columns):
            label = tk.Label(self.csv_container.scrollable_frame, text=column, borderwidth=1, relief="solid")
            label.grid(row=0, column=col_num, sticky="nsew")

        self.csv_widgets = []
        for i, row in self.csv_data.iterrows():
            row_widgets = []
            for j, value in enumerate(row):
                entry = tk.Entry(self.csv_container.scrollable_frame)
                entry.grid(row=i + 1, column=j, sticky="nsew")
                entry.insert(0, value)
                row_widgets.append(entry)
            self.csv_widgets.append(row_widgets)

        # Set column and row weights for resizing
        for i in range(len(columns)):
            self.csv_container.scrollable_frame.grid_columnconfigure(i, weight=1)
        for i in range(len(self.csv_data)):
            self.csv_container.scrollable_frame.grid_rowconfigure(i, weight=1)

    def create_default_csv(self):
        default_columns = ['start_img', 'end_img', 'transect_id', 'start_time', 'end_time']
        self.csv_data = pd.DataFrame(columns=default_columns)
        self.display_csv()

    def add_row(self):
        if self.csv_data is None:
            messagebox.showerror("Error", "Please create or load a CSV file first.")
            return

        # Preserve current data
        for i, row in enumerate(self.csv_widgets):
            for j, entry in enumerate(row):
                self.csv_data.iat[i, j] = entry.get()

        # Create a DataFrame with a single new row
        new_row_df = pd.DataFrame([{col: "" for col in self.csv_data.columns}])

        # Concatenate the new row to the existing DataFrame
        self.csv_data = pd.concat([self.csv_data, new_row_df], ignore_index=True)

        # Re-display the CSV with the new row
        self.display_csv()

    def start_backup(self):
        source = self.source_folder.get()
        if not source:
            messagebox.showerror("Error", "Please select a folder to backup.")
            return

        if not self.destination_folders:
            messagebox.showerror("Error", "Please select at least one destination folder.")
            return

        for dest in self.destination_folders:
            backup_path = os.path.join(dest, f"{os.path.basename(source)}_backup")
            shutil.copytree(source, backup_path)

        messagebox.showinfo("Success", "Backup completed successfully!")
        self.next_step()

    def extract_gps_data(self):
        source_1 = self.folder_1.get()
        source_0 = self.folder_0.get()
        if not source_1 or not source_0:
            messagebox.showerror("Error", "Please select both source folders.")
            return
        self.run_script('SeeOtter_pre_post-main/Image_GPS_extract.py', source_1, source_0)
        self.next_step()

    def run_preprocessing(self):
        self.instructions.config(text="5. Run ‘SeeOtter_prepro_GUI_non_Waldo_with_GPS_fix.py’\n"
                                      "a. For input folder: select your Images folder inside your MM_DD folder\n"
                                      "b. For the transect csv: select the transect assignment csv created in step 4\n"
                                      "c. (Optional) Select KML for GPS correction\n"
                                      "d. Run ‘Extract & Assign Transects’")

        tk.Button(self.root, text="Run Preprocessing", command=self.run_preprocessing_script).grid(row=4, column=1, padx=10, pady=10)

    def run_preprocessing_script(self):
        self.run_script('SeeOtter_pre_post-main/SeeOtter_prepro_GUI_non_Waldo_with_GPS_fix.py')
        self.next_step()

    def run_seeotter_processing(self):
        self.instructions.config(text="6. Run ‘SeeOtter.exe’\n"
                                      "a. Create a new survey in SeeOtter\n"
                                      "b. Point to the newly generated ‘cropped_images_on_tx’ folder\n"
                                      "c. Start processing the survey\n"
                                      "d. Validate predictions in OtterChecker9000")

        tk.Button(self.root, text="Start SeeOtter", command=self.start_seeotter).grid(row=4, column=1, padx=10, pady=10)

    def start_seeotter(self):
        self.run_script('SeeOtter_pre_post-main/start_see_otter_no_survey.py')
        self.next_step()

    def change_model_weights(self):
        self.instructions.config(text="7. Change Model Weights\n"
                                      "a. Select new model weights file (.pt)\n"
                                      "b. Replace the best.pt file in the ModelWeights folder\n"
                                      "c. Save a backup of the old best.pt file with a timestamp")

        tk.Button(self.root, text="Change Model Weights", command=self.change_model_weights_script).grid(row=4, column=1, padx=10, pady=10)

    def change_model_weights_script(self):
        new_weights = filedialog.askopenfilename(title="Select new model weights", filetypes=(("PyTorch model files", "*.pt"), ("All files", "*.*")))
        if new_weights:
            model_weights_folder = os.path.join('SeeOtter_pre_post-main', 'ModelWeights')
            best_weights = os.path.join(model_weights_folder, 'best.pt')

            if os.path.exists(best_weights):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_weights = os.path.join(model_weights_folder, f"best_{timestamp}.pt")
                shutil.copy2(best_weights, backup_weights)
                messagebox.showinfo("Backup", f"Backup of current best.pt created: {backup_weights}")

            shutil.copy2(new_weights, best_weights)
            messagebox.showinfo("Success", "Model weights updated successfully!")
        self.next_step()

    def final_processing(self):
        self.instructions.config(text="8. Final Processing\n"
                                      "a. Run ‘SeeOtter_post_pro_count_and_split_odd_even.py’\n"
                                      "b. Verify final results in mapping software")

        tk.Button(self.root, text="Run Final Processing", command=self.final_processing_script).grid(row=4, column=1, padx=10, pady=10)

    def final_processing_script(self):
        self.run_script('SeeOtter_pre_post-main/SeeOtter_post_pro_count_and_split_odd_even.py')
        self.next_step()


if __name__ == "__main__":
    os.chdir('E:\\SeeOtterUSGS\\SeeOtter_pre_post-main')

    root = tk.Tk()
    app = SequentialApp(root)
    root.mainloop()
