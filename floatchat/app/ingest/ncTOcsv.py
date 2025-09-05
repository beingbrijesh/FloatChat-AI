import xarray as xr
import pandas as pd

def nc_to_csv(nc_file, csv_file):
    # Open the NetCDF file
    ds = xr.open_dataset(nc_file)

    # Convert the dataset into a DataFrame
    df = ds.to_dataframe().reset_index()

    # Save as CSV
    df.to_csv(csv_file, index=False)

    print(f"✅ Converted {nc_file} to {csv_file}")

# Example usage
nc_to_csv("1900121_tech.nc", "output.csv")
