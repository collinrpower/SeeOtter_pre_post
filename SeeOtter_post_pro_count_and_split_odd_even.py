import tkinter as tk
from tkinter import filedialog
import pandas as pd
import tkinter.messagebox as messagebox
import os


def add_transect_column(final_df, input_filepath):
    # Normalize the path to ensure consistency regardless of the slashes used
    normalized_filepath = os.path.normpath(input_filepath)

    # Get the parent directory of the given file's directory
    parent_directory = os.path.dirname(os.path.dirname(os.path.dirname(normalized_filepath)))

    # Construct the path to the 'final_metadata_updated_filepath.csv'
    csv_path = os.path.join(parent_directory, 'final_metadata_updated_filepath.csv')

    # Read the CSV into a DataFrame
    df2 = pd.read_csv(csv_path)

    # Merge the DataFrames based on the matching columns
    final_df = final_df.merge(df2[['NewFilepath', 'Transect']], left_on='FilePath', right_on='NewFilepath', how='left')
    #final_df = final_df.merge(df2[['Filepath', 'Transect']], left_on='FilePath', right_on='Filepath', how='left')

    # Drop the redundant 'Filepath' column from the merged DataFrame
    #final_df.drop(columns='Filepath', inplace=True)
    final_df.drop(columns='NewFilepath', inplace=True)

    # Return the modified DataFrame
    return final_df


def process_data_final(df_predictions, df_otter_count, input_filepath):    # Step 1: Handle duplicates in df_otter_count
    # Sort such that if 'FilePath' is in df_predictions, it comes first
    df_otter_count['SortOrder'] = df_otter_count['FilePath'].isin(df_predictions['FilePath']).astype(int)
    df_otter_count = df_otter_count.sort_values(by=['FilePath', 'SortOrder'], ascending=[True, False]).drop_duplicates(subset='FilePath').drop(columns='SortOrder')

    # Filter rows where ValidationState is "CORRECT"
    correct_df = df_predictions[df_predictions['ValidationState'] == "CORRECT"]

    # Pivot the data to get counts of each PredictionCategoryName for every unique FilePath
    pivot_df = pd.pivot_table(correct_df, values='ImageID', index='FilePath', columns='PredictionCategoryName', aggfunc='count', fill_value=0)
    pivot_df['Total'] = pivot_df.sum(axis=1)
    if 'o' in pivot_df.columns and 'p' in pivot_df.columns:
        pivot_df['o+p'] = pivot_df['o'] + pivot_df['p']
    pivot_df.reset_index(inplace=True)

    merged_counts_df = pd.merge(df_otter_count[['FilePath']], pivot_df, on='FilePath', how='left').fillna(0)
    merged_df = pd.merge(merged_counts_df, df_otter_count, on='FilePath', how='left')
    necessary_columns = ['ImageID', 'Datetime', 'FilePath', 'CameraLatitude', 'CameraLongitude', 'CameraAltitude',
                         'ImageCorner1Lat', 'ImageCorner1Lon', 'ImageCorner2Lat', 'ImageCorner2Lon',
                         'ImageCorner3Lat', 'ImageCorner3Lon', 'ImageCorner4Lat', 'ImageCorner4Lon']
    final_df = merged_df[necessary_columns + list(pivot_df.columns.drop('FilePath'))]
    # Compute the new columns
    final_df['GSD'] = ((35.482 * final_df['CameraAltitude'] * 100) / (50 * 8563))
    #final_df['GSD'] = pd.to_numeric(final_df['GSD'], errors='coerce')  # Convert to numeric
    final_df['Width_m'] = (final_df['GSD'] * 8563 / 100)
    final_df['Height_m'] = (final_df['GSD'] * 5667 / 100)
    #final_df['Height_m'] = pd.to_numeric(final_df['Height_m'], errors='coerce')  # Convert to numeric
    #final_df['Width_m'] = pd.to_numeric(final_df['Width_m'], errors='coerce')  # Convert to numeric
    final_df['Coverage_sqkm'] = final_df['Width_m'] * final_df['Height_m'] / 1000000
    final_df = add_transect_column(final_df, input_filepath)
    return final_df



def process_file():
    input_filepath = results_all_predictions.get()
    if not input_filepath.endswith('.csv'):
        input_filepath += '.csv'
    distinct_filepath = filedialog.askopenfilename(
        title="Please select your 'results_distinct_otter_count_by_image.csv' file:",
        filetypes=[("CSV files", "*results_distinct_otter_count_by_image.csv")])
    df_predictions = pd.read_csv(input_filepath, low_memory=False)
    df_otter_count = pd.read_csv(distinct_filepath, low_memory=False)
    final_df = process_data_final(df_predictions, df_otter_count, input_filepath)
    # Save the full processed data to CSV
    output_filename = input_filepath.rsplit('.', 1)[0] + '_processed.csv'
    final_df = final_df.rename(columns={'Datetime': 'PHOTO_TIMESTAMP', 'CameraAltitude': 'ALTITUDE', 'CameraLatitude': 'LATITUDE_WGS84', 'CameraLongitude': 'LONGITUDE_WGS84', 'o': 'COUNT_ADULT', 'p':'COUNT_PUP', 'o+p': 'COUNT_ALL_OTTERS'})
    final_df['PHOTO_TIMESTAMP'] = final_df['PHOTO_TIMESTAMP'].str.replace(':', '-', 2)
    final_df.to_csv(output_filename, index=False)

    # Filter for odd ImageID and save to CSV
    odd_df = final_df[final_df['ImageID'] % 2 != 0]
    odd_output_filename = input_filepath.rsplit('.', 1)[0] + '_odd_processed.csv'
    odd_df.to_csv(odd_output_filename, index=False)

    # Filter for even ImageID and save to CSV
    even_df = final_df[final_df['ImageID'] % 2 == 0]
    even_output_filename = input_filepath.rsplit('.', 1)[0] + '_even_processed.csv'
    even_df.to_csv(even_output_filename, index=False)

    # Generate message for the messagebox
    message = f"Output Files:\n\nAll records:\n{output_filename}\nImages: {len(final_df)}\no+p count: {final_df['COUNT_ALL_OTTERS'].sum()}\n\n"
    message += f"Odd ImageIDs:\n{odd_output_filename}\nImages: {len(odd_df)}\no+p count: {odd_df['COUNT_ALL_OTTERS'].sum()}\n\n"
    message += f"Even ImageIDs:\n{even_output_filename}\nImages: {len(even_df)}\no+p count: {even_df['COUNT_ALL_OTTERS'].sum()}"
    root.update_idletasks()

    # Show the messagebox
    messagebox.showinfo("Processing Complete", message)
# Create the main window
root = tk.Tk()
root.title("Process CSV File")

results_all_predictions = tk.StringVar()

instruction_label = tk.Label(root, text="Please select your 'results_all_predictions.csv' file:")
instruction_label.pack(pady=10)

select_button = tk.Button(root, text="Select CSV File", command=lambda: results_all_predictions.set(filedialog.askopenfilename(filetypes=[("CSV files", "*results_all_predictions.csv")])))
select_button.pack(pady=20)

file_label = tk.Label(root, textvariable=results_all_predictions)
file_label.pack(pady=10)

process_button = tk.Button(root, text="Process File", command=process_file)
process_button.pack(pady=20)

root.mainloop()

