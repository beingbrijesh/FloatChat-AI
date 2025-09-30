from netCDF4 import Dataset
import os

file_path = r"E:\argo_db\processed\processed_rtraj_files\7902250_Rtraj.nc"

# Check if file exists
if not os.path.exists(file_path):
    print("❌ File does not exist!")
else:
    nc_file = Dataset(file_path, mode='r')

    print("\n--- Global Attributes ---")
    for attr in nc_file.ncattrs():
        print(f"{attr}: {getattr(nc_file, attr)}")

    print("\n--- Dimensions ---")
    for dim_name, dim in nc_file.dimensions.items():
        print(f"{dim_name}: size = {len(dim)}, is_unlimited = {dim.isunlimited()}")

    print("\n--- Variables ---")
    for var_name, var in nc_file.variables.items():
        print(f"\nVariable: {var_name}")
        print(f"  Dimensions: {var.dimensions}")
        print(f"  Shape: {var.shape}")
        print(f"  Data type: {var.dtype}")
        
        for attr_name in var.ncattrs():
            print(f"  {attr_name}: {getattr(var, attr_name)}")

        try:
            print(f"  Sample data: {var[:].flatten()[0:5]}")
        except Exception as e:
            print(f"  Could not preview data: {e}")

    nc_file.close()
