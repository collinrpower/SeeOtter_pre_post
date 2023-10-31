import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os
os.environ['USE_PYGEOS'] = '0'
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point
import zipfile

def process_data(even_odd, polygon_csv_path):
    points_csv_path = polygon_csv_path
    polygon_shp_path = os.path.dirname(polygon_csv_path) + '/camera_outlines_WGS84' + even_odd
    points_shp_path = os.path.dirname(polygon_csv_path) + '/camera_points_WGS84' + even_odd
    root_dir = os.path.dirname(polygon_csv_path)

    df = pd.read_csv(polygon_csv_path)
    polygons = []

    for index, row in df.iterrows():
        polygon = Polygon([(row['ImageCorner1Lon'], row['ImageCorner1Lat']),
                           (row['ImageCorner2Lon'], row['ImageCorner2Lat']),
                           (row['ImageCorner3Lon'], row['ImageCorner3Lat']),
                           (row['ImageCorner4Lon'], row['ImageCorner4Lat'])])
        polygons.append(polygon)

    df['geometry'] = polygons
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    gdf = gdf.set_crs(epsg=4326)
    gdf.to_file(f"{polygon_shp_path}.shp")

    data = pd.read_csv(points_csv_path)
    filtered_data = data
    geometry = [Point(xy) for xy in zip(filtered_data['LONGITUDE_WGS84'], filtered_data['LATITUDE_WGS84'])]
    geo_df = gpd.GeoDataFrame(filtered_data, geometry=geometry)
    geo_df.set_crs(epsg=4326, inplace=True)
    geo_df.to_file(f"{points_shp_path}.shp")

    show_completed_message(polygon_shp_path, points_shp_path)

def zip_shp_files(base_name, root_dir):
    with zipfile.ZipFile(f"{root_dir}/{base_name}.zip", 'w') as zipf:
        for extension in ['.shp', '.shx', '.dbf', '.prj']:
            file = f"{root_dir}/{base_name}{extension}"
            zipf.write(file, arcname=f"{base_name}{extension}")

def browse_file():
    filename = filedialog.askopenfilename(initialdir="/", title="Select A File",
                                          filetype=(("csv files", "*.csv"), ("all files", "*.*")))
    polygon_csv_path.set(filename)

def on_select(event):
    even_odd.set(event.widget.get())

def show_completed_message(polygon_shp_path, points_shp_path):
    message = f"Processing completed.\nPolygon Shapefile Path: {polygon_shp_path}.shp\nPoints Shapefile Path: {points_shp_path}.shp\n\nNote: These projections are only representations and not accurate. They should only be used for data cleaning purposes and general observations."
    messagebox.showinfo("Processing Completed", message)

root = tk.Tk()
root.title("Polygon Processing")

even_odd = tk.StringVar(value='all')
polygon_csv_path = tk.StringVar()

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Label(frame, text="Select Even/Odd/All:").grid(column=0, row=0, sticky=tk.W)
combo = ttk.Combobox(frame, textvariable=even_odd, values=['even', 'odd', 'all'])
combo.grid(column=1, row=0)
combo.bind('<<ComboboxSelected>>', on_select)

ttk.Label(frame, text="Polygon CSV Path:").grid(column=0, row=1, sticky=tk.W)
ttk.Entry(frame, textvariable=polygon_csv_path, width=40).grid(column=1, row=1)
ttk.Button(frame, text="Browse", command=browse_file).grid(column=2, row=1)

ttk.Button(frame, text="Process Data", command=lambda: process_data(even_odd.get(), polygon_csv_path.get())).grid(columnspan=3, row=2, pady=10)

root.mainloop()
