import polars as pl

# The path to your output file
file_path = r"E:\argo_db\model_training_data_final.parquet"

print(f"📄 Loading data from {file_path}")

# Load the entire Parquet file into a DataFrame
df = pl.read_parquet(file_path)

# Print the full DataFrame to the console
print(df)

# Print a summary
print(f"\nSummary: {df.height} rows, {df.width} columns")