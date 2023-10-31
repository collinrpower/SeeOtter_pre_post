import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os
import pandas as pd
import piexif
import xml.etree.ElementTree as ET
import numpy as np


class ImageMetadataGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Metadata Extractor and Cropper")

        # Variables to hold file/folder paths, crop pixel size, and KML file
        self.folder_path = tk.StringVar()
        self.transect_file = tk.StringVar()
        self.final_metadata_csv = tk.StringVar()
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.output_csv = tk.StringVar()
        self.crop_pixel_size = tk.StringVar()
        self.kml_file = tk.StringVar()

        # Set a default crop size
        self.crop_pixel_size.set("125")
        self.min_altitude = tk.StringVar(value="152")  # Default min altitude
        self.max_altitude = tk.StringVar(value="244")  # Default max altitude

        # Create and place labels and buttons
        self.create_widgets()

    def get_geotagging(self, exif):
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

    def dms_to_decimal(self, degrees, minutes, seconds, ref):
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        if ref in ['S', 'W']:
            decimal = -decimal
        return decimal

    def extract_metadata_from_folder(self, folder_path):
        data = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = root + '/' + file
                    img_path = img_path.replace('\\', '/')
                    img = Image.open(img_path)
                    exif_data = img._getexif()

                    if not exif_data:
                        data.append([img_path, 'NA', 'NA', 'NA', 'NA'])
                        continue

                    datetime_original = exif_data.get(36867, 'NA')
                    geotags = self.get_geotagging(exif_data)

                    if not geotags:
                        data.append([img_path, datetime_original, 'NA', 'NA', 'NA'])
                        continue

                    latitude = self.dms_to_decimal(*geotags.get('GPSLatitude', (0, 0, 0)),
                                                   geotags.get('GPSLatitudeRef', 'N')) if 'GPSLatitude' in geotags else 'NA'
                    longitude = self.dms_to_decimal(*geotags.get('GPSLongitude', (0, 0, 0)),
                                                    geotags.get('GPSLongitudeRef', 'E')) if 'GPSLongitude' in geotags else 'NA'
                    altitude = geotags.get('GPSAltitude', 'NA')

                    data.append([img_path, datetime_original, latitude, longitude, altitude])

        return pd.DataFrame(data, columns=['Filepath', 'DatetimeOriginal', 'Latitude', 'Longitude', 'Altitude'])

    def extract_and_assign_transects(self, folder_path, transect_file, output_csv):
        transect_assignment = pd.read_csv(transect_file)
        metadata = self.extract_metadata_from_folder(folder_path)
        metadata['Transect'] = 'NA'

        for index, row in transect_assignment.iterrows():
            if pd.notna(row['start_img']) and pd.notna(row['end_img']):
                start_time_entries = metadata.loc[metadata['Filepath'] == row['start_img'], 'DatetimeOriginal'].values
                end_time_entries = metadata.loc[metadata['Filepath'] == row['end_img'], 'DatetimeOriginal'].values
                if start_time_entries.size > 0 and end_time_entries.size > 0:
                    start_time = start_time_entries[0]
                    end_time = end_time_entries[0]
                else:
                    continue
            else:
                start_time = row['start_time']
                end_time = row['end_time']

            mask = (metadata['DatetimeOriginal'] >= start_time) & (metadata['DatetimeOriginal'] <= end_time)
            metadata.loc[mask, 'Transect'] = row['transect_id']
        metadata.to_csv(output_csv, index=False)
        return output_csv

    def crop_images_based_on_transect(self, final_metadata_csv, input_folder, output_folder, crop_amount=125):
        # Helper function to convert decimal coordinates to DMS format
        def decimal_to_dms(decimal):
            degrees = int(decimal)
            minutes = int((decimal - degrees) * 60)
            seconds = ((decimal - degrees - minutes / 60) * 3600)
            return ((degrees, 1), (minutes, 1), (int(seconds * 1000), 1000))
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        if os.path.exists(os.path.dirname(final_metadata_csv) + '/final_metadata_updated.csv'):
            metadata = pd.read_csv(os.path.dirname(final_metadata_csv) + '/final_metadata_updated.csv')
        else:
            metadata = pd.read_csv(os.path.dirname(
                final_metadata_csv)+ '/final_metadata.csv')  # Replace 'another_file.csv' with the desired filename if it doesn't exist

        valid_images = metadata[
            metadata['Transect'].notna() &
            (metadata['Transect'] != 'NA') &
            (metadata['Altitude'] >= float(self.min_altitude.get())) &
            (metadata['Altitude'] <= float(self.max_altitude.get()))
        ]

        print(f"Number of images to be cropped: {len(valid_images)}")

        count_0 = 0
        count_1 = 0

        for index, row in valid_images.iterrows():
            image_path = row['Filepath']

            if os.path.exists(image_path) and image_path.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                with Image.open(image_path) as img:
                    exif_data = piexif.load(img.info.get("exif", b""))
                    width, height = img.size
                    new_dimensions = (crop_amount, crop_amount, width - crop_amount, height - crop_amount)
                    cropped_img = img.crop(new_dimensions)

                    folder_name = os.path.basename(os.path.dirname(image_path))
                    if folder_name == '0':
                        count_0 += 1
                        prefix = '0'
                        count = count_0
                    elif folder_name == '1':
                        count_1 += 1
                        prefix = '1'
                        count = count_1
                    else:
                        continue

                    filename = f"{prefix}_000_00_{count:03d}.jpg"
                    output_file_path = os.path.join(output_folder, filename)
                    if os.path.exists(os.path.dirname(final_metadata_csv) + '/final_metadata_updated.csv'):
                        if not pd.isna(row['LatitudeNew']) and not pd.isna(row['LongitudeNew']) and not pd.isna(row['AltitudeNew']):
                            gps_ifd = {
                                piexif.GPSIFD.GPSLatitudeRef: 'S' if row['LatitudeNew'] < 0 else 'N',
                                piexif.GPSIFD.GPSLatitude: decimal_to_dms(abs(row['LatitudeNew'])),
                                piexif.GPSIFD.GPSLongitudeRef: 'W' if row['LongitudeNew'] < 0 else 'E',
                                piexif.GPSIFD.GPSLongitude: decimal_to_dms(abs(row['LongitudeNew'])),
                                piexif.GPSIFD.GPSAltitudeRef: 0,
                                piexif.GPSIFD.GPSAltitude: (int(abs(row['AltitudeNew']) * 1000), 1000),
                        }
                            exif_data['GPS'] = gps_ifd

                    cropped_img.save(output_file_path, quality=100, exif=piexif.dump(exif_data))
                    metadata.loc[index, 'NewFilepath'] = output_file_path

                    print(f"Cropped: {output_file_path}, Transect: {row['Transect']}")
        metadata.to_csv(self.final_metadata_csv.get(), index=False)
        metadata.to_csv(os.path.splitext(self.final_metadata_csv.get())[0] + '_updated_filepath.csv', index=False)

        print(f"Cropping completed. Cropped images are saved in '{output_folder}'.")


    def kml_to_csv(self, kml_filepath, csv_filepath):
        tree = ET.parse(kml_filepath)
        root = tree.getroot()

        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        ns_ext = {'gx': 'http://www.google.com/kml/ext/2.2'}

        coordinates = []
        timestamps = []

        for placemark in root.findall(".//kml:Placemark", ns):
            coords = placemark.findall(".//gx:coord", ns_ext)
            whens = placemark.findall(".//kml:when", ns)

            for coord, when_elem in zip(coords, whens):
                coordinate = coord.text.strip().split(' ')
                timestamp = when_elem.text

                coordinates.append(coordinate)
                timestamps.append(timestamp)

        df = pd.DataFrame(coordinates, columns=["Longitude", "Latitude", "Altitude"])
        df["Datetime"] = timestamps

        df.to_csv(csv_filepath, index=False)

    def integrate_csv_data(self):
        csv1 = pd.read_csv(self.final_metadata_csv.get())
        csv2 = pd.read_csv(os.path.splitext(self.kml_file.get())[0] + '.csv')

        csv1['Datetime'] = pd.to_datetime(csv1['DatetimeOriginal'], format='%Y:%m:%d %H:%M:%S')
        csv2['Datetime'] = pd.to_datetime(csv2['Datetime'], format='%Y-%m-%dT%H:%M:%S.%fZ')
        csv1['Timestamp'] = csv1['Datetime'].apply(lambda x: x.timestamp())

        csv2['Timestamp'] = csv2['Datetime'].apply(lambda x: x.timestamp())

        def find_closest(row):
            time_diff = (csv2['Timestamp'] - row['Timestamp']).abs()
            closest_idx = time_diff.idxmin()
            closest_time_diff = time_diff[closest_idx]

            # Check if a close enough match was found
            if closest_time_diff <= 3:
                return csv2.loc[closest_idx, ['Latitude', 'Longitude', 'Altitude']]
            else:
                # Return blank values as Pandas Series with NaN
                return pd.Series([np.nan, np.nan, np.nan],
                            index=['Latitude', 'Longitude', 'Altitude'])
        closest_values = csv1.apply(find_closest, axis=1)
        csv1[['LatitudeNew', 'LongitudeNew', 'AltitudeNew']] = closest_values

        csv1.to_csv(os.path.splitext(self.final_metadata_csv.get())[0] + '_updated.csv', index=False)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def browse_csv(self):
        csv_file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if csv_file:
            self.transect_file.set(csv_file)

    def browse_kml(self):
        kml_filepath = filedialog.askopenfilename(filetypes=[("KML Files", "*.kml"), ("All Files", "*.*")])
        if kml_filepath:
            self.kml_file.set(kml_filepath)

    def run_kml_to_csv_conversion(self):
        if not self.kml_file.get():
            messagebox.showerror("Error", "Please select a KML file.")
            return

        self.kml_to_csv(self.kml_file.get(), os.path.splitext(self.kml_file.get())[0] + '.csv')
        messagebox.showinfo("Success", "KML file converted to CSV successfully!")

    def run_extract_and_assign(self):
        if not self.folder_path.get() or not self.transect_file.get():
            messagebox.showerror("Error", "Please select both the input folder and the transect CSV.")
            return

        self.final_metadata_csv.set(os.path.join(os.path.dirname(self.folder_path.get()), 'final_metadata.csv'))
        self.output_folder.set(os.path.join(os.path.dirname(self.folder_path.get()), 'cropped_images_on_tx', 'Images'))
        self.output_csv.set(os.path.join(os.path.dirname(self.folder_path.get()), 'final_metadata.csv'))

        self.extract_and_assign_transects(self.folder_path.get(), self.transect_file.get(), self.final_metadata_csv.get())

        if os.path.exists(os.path.splitext(self.kml_file.get())[0] + '.csv'):
            self.integrate_csv_data()
            messagebox.showinfo("Success", "Transects extracted, assigned, and integrated successfully!")
        else:
            messagebox.showinfo("Success", "Transects extracted and assigned successfully!")

    def run_crop_images(self):
        if not self.final_metadata_csv.get() or not self.folder_path.get() or not self.output_folder.get():
            messagebox.showerror("Error", "Please run 'Extract & Assign Transects' first.")
            return
        self.input_folder.set(self.folder_path.get())

        self.crop_images_based_on_transect(self.final_metadata_csv.get(), self.input_folder.get(), self.output_folder.get())
        messagebox.showinfo("Success", "Images cropped successfully!")



    def create_widgets(self):
        tk.Label(self.root, text="Select Input Folder:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        tk.Entry(self.root, textvariable=self.folder_path, width=40).grid(row=0, column=1, padx=10, pady=10)
        tk.Button(self.root, text="Browse", command=self.browse_folder).grid(row=0, column=2, padx=10, pady=10)

        tk.Label(self.root, text="Select Transect CSV:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        tk.Entry(self.root, textvariable=self.transect_file, width=40).grid(row=1, column=1, padx=10, pady=10)
        tk.Button(self.root, text="Browse", command=self.browse_csv).grid(row=1, column=2, padx=10, pady=10)

        tk.Label(self.root, text="Select KML File:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        tk.Entry(self.root, textvariable=self.kml_file, width=40).grid(row=2, column=1, padx=10, pady=10)
        tk.Button(self.root, text="Browse", command=self.browse_kml).grid(row=2, column=2, padx=10, pady=10)

        tk.Label(self.root, text="Crop Pixel Size:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        tk.Entry(self.root, textvariable=self.crop_pixel_size, width=10).grid(row=3, column=1, padx=10, pady=10)

        # Altitude GUI elements
        tk.Label(self.root, text="Min Altitude (m):").grid(row=4, column=0, padx=10, pady=10, sticky="w")
        tk.Entry(self.root, textvariable=self.min_altitude, width=10).grid(row=4, column=1, padx=10, pady=10)

        tk.Label(self.root, text="Max Altitude (m):").grid(row=5, column=0, padx=10, pady=10, sticky="w")
        tk.Entry(self.root, textvariable=self.max_altitude, width=10).grid(row=5, column=1, padx=10, pady=10)

        # Adjusted row numbers for buttons
        tk.Button(self.root, text="Convert KML to CSV", command=self.run_kml_to_csv_conversion).grid(row=6, column=0,
                                                                                                     columnspan=3,
                                                                                                     padx=10, pady=10)
        tk.Button(self.root, text="Extract & Assign Transects", command=self.run_extract_and_assign).grid(row=7,
                                                                                                          column=0,
                                                                                                          columnspan=3,
                                                                                                          padx=10,
                                                                                                          pady=10)
        tk.Button(self.root, text="Crop Images", command=self.run_crop_images).grid(row=8, column=0, columnspan=3,
                                                                                    padx=10, pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageMetadataGUI(root)
    root.mainloop()
