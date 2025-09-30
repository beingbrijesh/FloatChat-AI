import os
import pandas as pd
import xarray as xr
from tqdm import tqdm
import logging

# --- CONFIGURATION ---
# Point this to the folders containing the files with the actual measurements
SOURCE_FOLDERS = {
    'prof': r"E:\argo_db\nc_files\prof_files",
    'sprof': r"E:\argo_db\nc_files\sprof_files"
}
OUTPUT_FILE = r"E:\argo_db\scientific_measurements.csv"
LOG_FILE = r"E:\argo_db\measurement_extraction.log"

# --- LOGGING ---
logging.basicConfig(filename=LOG_FILE, filemode='w', format='%(asctime)s | %(levelname)s | %(message)s', level=logging.INFO)

def extract_measurements_from_file(file_path):
    """Opens a single NetCDF file and extracts a DataFrame of measurements."""
    try:
        with xr.open_dataset(file_path) as ds:
            # Convert the entire dataset to a pandas DataFrame
            # xarray cleverly expands the metadata to match the measurements
            df = ds.to_dataframe()
            
            # Reset index to turn levels like N_PROF and N_LEVELS into columns
            df = df.reset_index()
            
            # Define the core columns we want to keep
            # Use .lower() to match the case we used in the ETL script
            df.columns = [col.lower() for col in df.columns]
            
            core_columns = [
                'platform_number', 'cycle_number', 'direction', 'juld',
                'latitude', 'longitude', 'pres', 'temp', 'psal'
            ]
            
            # For Sprof files, adjusted values might be present
            sprof_columns = ['pres_adjusted', 'temp_adjusted', 'psal_adjusted']
            
            final_columns = []
            for col in core_columns + sprof_columns:
                if col in df.columns:
                    final_columns.append(col)
            
            if not final_columns:
                return None
                
            return df[final_columns]
            
    except Exception as e:
        logging.error(f"Failed to process file {file_path}: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Starting extraction of detailed scientific measurements...")
    
    all_files_to_process = []
    for folder_type, folder_path in SOURCE_FOLDERS.items():
        try:
            files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".nc")]
            all_files_to_process.extend(files)
            print(f"   -> Found {len(files)} files in '{folder_type}' folder.")
        except FileNotFoundError:
            print(f"   -> WARNING: Folder not found, skipping: {folder_path}")

    if not all_files_to_process:
        print("❌ No source files found in the configured folders. Exiting.")
    else:
        all_dfs = []
        print(f"\n⚙️  Processing {len(all_files_to_process)} files...")
        
        for f in tqdm(all_files_to_process):
            df = extract_measurements_from_file(f)
            if df is not None:
                all_dfs.append(df)
        
        if not all_dfs:
            print("❌ Could not extract any valid data from the source files.")
        else:
            print("\n consolidating all data into a single table...")
            # Concatenate all individual DataFrames into one large DataFrame
            final_df = pd.concat(all_dfs, ignore_index=True)
            
            # Drop rows where the core measurements are all missing
            final_df.dropna(subset=['pres', 'temp', 'psal'], how='all', inplace=True)
            
            print(f"✅ Success! Assembled a dataset with {len(final_df)} total measurements.")
            
            print(f"💾 Saving data to '{OUTPUT_FILE}'...")
            final_df.to_csv(OUTPUT_FILE, index=False)
            
            print(f"\n🎉 Successfully saved the full measurement dataset.")
            print("\nPreview of the first 5 rows:")
            print(final_df.head())