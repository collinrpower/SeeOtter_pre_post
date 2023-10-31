import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import pandas as pd


def get_geotagging(exif):
    if not exif:
        return None

    geotagging = {}
    for (idx, tag) in TAGS.items():
        if tag == 'GPSInfo':
            if idx not in exif:
                return None

            for (key, val) in GPSTAGS.items():
                if key in exif[idx]:
                    geotagging[val] = exif[idx][key]

    return geotagging


def dms_to_decimal(degrees, minutes, seconds, ref):
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal


def extract_metadata_from_folder(folder_path):
    data = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(root, file)
                try:
                    img = Image.open(img_path)
                    exif_data = img._getexif()

                    if not exif_data:
                        data.append([img_path, 'NA', 'NA', 'NA', 'NA'])
                        continue

                    datetime_original = exif_data.get(36867, 'NA')
                    geotags = get_geotagging(exif_data)

                    if not geotags:
                        data.append([img_path, datetime_original, 'NA', 'NA', 'NA'])
                        continue

                    latitude = dms_to_decimal(*geotags.get('GPSLatitude', (0, 0, 0)),
                                              geotags.get('GPSLatitudeRef', 'N')) if 'GPSLatitude' in geotags else 'NA'
                    longitude = dms_to_decimal(*geotags.get('GPSLongitude', (0, 0, 0)),
                                               geotags.get('GPSLongitudeRef',
                                                           'E')) if 'GPSLongitude' in geotags else 'NA'
                    altitude = geotags.get('GPSAltitude', 'NA')

                    data.append([img_path, datetime_original, latitude, longitude, altitude])

                except Exception as e:
                    print(f"Error processing {img_path}: {e}")

    return pd.DataFrame(data, columns=['Filepath', 'DatetimeOriginal', 'Latitude', 'Longitude', 'Altitude'])


class MetadataExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Metadata Extractor")

        # Variables to hold file/folder paths
        self.folder_path = tk.StringVar()
        self.output_csv = tk.StringVar()

        # Create and place labels and buttons
        self.create_widgets()

    def run_extraction(self):
        metadata_df = extract_metadata_from_folder(self.folder_path.get())
        metadata_df.to_csv(self.output_csv.get(), index=False)
        messagebox.showinfo("Success", f"Metadata extracted and saved to {self.output_csv.get()}")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def browse_csv(self):
        csv_file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if csv_file:
            self.output_csv.set(csv_file)

    def create_widgets(self):
        tk.Label(self.root, text="Select Input Folder:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        tk.Entry(self.root, textvariable=self.folder_path, width=40).grid(row=0, column=1, padx=10, pady=10)
        tk.Button(self.root, text="Browse", command=self.browse_folder).grid(row=0, column=2, padx=10, pady=10)

        tk.Label(self.root, text="Select Output CSV:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        tk.Entry(self.root, textvariable=self.output_csv, width=40).grid(row=1, column=1, padx=10, pady=10)
        tk.Button(self.root, text="Browse", command=self.browse_csv).grid(row=1, column=2, padx=10, pady=10)

        tk.Button(self.root, text="Extract Metadata", command=self.run_extraction).grid(row=2, column=0, columnspan=3, padx=10, pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = MetadataExtractorGUI(root)
    root.mainloop()
