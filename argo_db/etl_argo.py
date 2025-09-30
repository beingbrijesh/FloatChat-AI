import os
import shutil
import time
import logging
import re
from multiprocessing import Pool, cpu_count

import numpy as np
import xarray as xr
from sqlalchemy import create_engine, text, inspect
from tqdm import tqdm
from psycopg2.extras import execute_values
import pandas as pd
from pandas.io import sql as pd_sql

# ---------------- CONFIG ----------------
BASE_FOLDER = r"E:\argo_db\nc_files"
META_FOLDER = os.path.join(BASE_FOLDER, "meta_files")
PROF_FOLDER = os.path.join(BASE_FOLDER, "prof_files")
TECH_FOLDER = os.path.join(BASE_FOLDER, "tech_files")
SPROF_FOLDER = os.path.join(BASE_FOLDER, "sprof_files")
RTRAJ_FOLDER = os.path.join(BASE_FOLDER, "rtraj_files")

PROCESSED_FOLDER = r"E:\argo_db\processed"
PROCESSED_META_FOLDER = os.path.join(PROCESSED_FOLDER, "processed_meta_files")
PROCESSED_PROF_FOLDER = os.path.join(PROCESSED_FOLDER, "processed_prof_files")
PROCESSED_TECH_FOLDER = os.path.join(PROCESSED_FOLDER, "processed_tech_files")
PROCESSED_SPROF_FOLDER = os.path.join(PROCESSED_FOLDER, "processed_sprof_files")
PROCESSED_RTRAJ_FOLDER = os.path.join(PROCESSED_FOLDER, "processed_rtraj_files")

DB_CONN = "postgresql+psycopg2://postgres:Ashish%40021@localhost:5432/argo_db"
LOG_FILE = r"E:\argo_db\etl_argo.log"
BATCH_SIZE = 1000

# ---------------- LOGGING ----------------
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(filename=LOG_FILE, filemode='a', format='%(asctime)s | %(levelname)s | %(message)s', level=logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# ---------------- UTILS ----------------
engine = create_engine(DB_CONN)

def parse_calib_coefficients(text_block):
    if not isinstance(text_block, str): return {}
    pattern = re.compile(r'([A-Z0-9]+)\s*=\s*(-?\d+\.?\d*(?:e-?\d+)?)')
    matches = pattern.findall(text_block)
    coeffs = {}
    for key, value in matches:
        try:
            if value: coeffs[f"calib_{key.lower()}"] = float(value)
        except (ValueError, TypeError): continue
    return coeffs

def simplify_sampling_scheme(text_block):
    if not isinstance(text_block, str) or "Primary sampling:" not in text_block: return "not specified"
    summary = text_block.replace("Primary sampling:", "").strip()
    return re.sub(r'\s+', ' ', summary)

def simplify_equation(text_block):
    if not isinstance(text_block, str): return "not specified"
    if "y=thermistor output" in text_block and "pressure (psia)" in text_block: return "Standard Pressure/Temperature Formula"
    return "Custom or Unknown Formula"

def clean_and_decode_value(value):
    if isinstance(value, (bytes, np.bytes_)): return value.decode('utf-8', 'ignore').strip().strip('\x00')
    if isinstance(value, str): return value.strip().strip('\x00')
    if isinstance(value, np.ndarray): return str(value.tolist())
    return value

def get_sql_type(dtype):
    if pd.api.types.is_float_dtype(dtype): return 'DOUBLE PRECISION'
    if pd.api.types.is_integer_dtype(dtype): return 'BIGINT'
    return 'TEXT'

def sync_schema(engine, table_name, df):
    # (This function is unchanged from the last correct version)
    if df.empty: return
    with engine.connect() as conn:
        inspector = inspect(engine)
        table_exists = inspector.has_table(table_name, schema='public')
        if not table_exists:
            logging.info(f"Table '{table_name}' does not exist. Creating it.")
            create_statement = pd.io.sql.get_schema(df, table_name, con=engine)
            for p_type, s_type in {'TEXT':'TEXT', 'INTEGER':'BIGINT', 'REAL':'DOUBLE PRECISION'}.items():
                create_statement = create_statement.replace(p_type, s_type)
            conn.execute(text(create_statement))
            pk_cols = []
            if table_name in ['profiles', 'tech', 'sprof']: pk_cols = ['platform_number', 'cycle_number']
            elif table_name == 'meta': pk_cols = ['platform_number']
            elif table_name == 'measurements': pk_cols = ['platform_number', 'cycle_number', 'n_levels']
            if pk_cols and all(col in df.columns for col in pk_cols):
                pk_cols_str = ", ".join([f'"{c}"' for c in pk_cols])
                pk_query = f'ALTER TABLE "{table_name}" ADD PRIMARY KEY ({pk_cols_str});'
                conn.execute(text(pk_query))
                logging.info(f"Primary key set for table '{table_name}'.")
            conn.commit()
        df_cols = set(df.columns)
        query = text(f"SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '{table_name}'")
        result = conn.execute(query)
        db_cols = set(row[0] for row in result)
        missing_cols = df_cols - db_cols
        if missing_cols:
            add_clauses = [f'ADD COLUMN "{col_name}" {get_sql_type(df[col_name].dtype)}' for col_name in sorted(list(missing_cols))]
            full_alter_query = f'ALTER TABLE "{table_name}" {", ".join(add_clauses)}'
            print(f"🔧 Applying batch schema update to table '{table_name}'.")
            conn.execute(text(full_alter_query))
            conn.commit()

def upsert_bulk(df, table, conflict_cols):
    # (This function is unchanged from the last correct version)
    if df.empty: return 0
    cols = [f'"{c}"' for c in df.columns]
    if conflict_cols and all(col in df.columns for col in conflict_cols):
        conflict_cols_quoted = [f'"{c}"' for c in conflict_cols]
        insert_cols = ", ".join(cols)
        update_cols = [c for c in df.columns if c not in conflict_cols]
        if update_cols:
            update_stmt = ", ".join([f'"{c}"=EXCLUDED."{c}"' for c in update_cols])
            sql = f"INSERT INTO \"{table}\" ({insert_cols}) VALUES %s ON CONFLICT ({', '.join(conflict_cols_quoted)}) DO UPDATE SET {update_stmt};"
        else:
            sql = f"INSERT INTO \"{table}\" ({insert_cols}) VALUES %s ON CONFLICT ({', '.join(conflict_cols_quoted)}) DO NOTHING;"
    else: 
        insert_cols = ", ".join(cols)
        sql = f"INSERT INTO \"{table}\" ({insert_cols}) VALUES %s;"
    temp_engine = create_engine(DB_CONN)
    conn = temp_engine.raw_connection()
    try:
        with conn.cursor() as cur:
            rows = df.to_records(index=False).tolist()
            execute_values(cur, sql, rows)
            conn.commit()
    finally:
        conn.close()
    return len(df)

# --- FIX --- Re-introducing the function to check the database log
def is_file_processed(filename):
    """Checks the processedfiles table to see if a file has been ingested."""
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS processedfiles (filename TEXT PRIMARY KEY);"))
        conn.commit()
        result = conn.execute(text("SELECT 1 FROM processedfiles WHERE filename=:filename"), {"filename": filename})
        return result.first() is not None

def process_nc_file(ds):
    # (This function is unchanged from the last correct version)
    primary_dims = {'N_PROF', 'N_CYCLE', 'N_MEASUREMENT'}
    primary_dim = next((dim for dim in primary_dims if dim in ds.sizes), None)
    num_profiles = ds.sizes.get(primary_dim, 1) if primary_dim else 1
    level_dim_name = 'N_LEVELS' if 'N_LEVELS' in ds.dims else None
    metadata_rows = [{} for _ in range(num_profiles)]
    measurement_vars_by_profile = [{} for _ in range(num_profiles)]
    for var_name, variable in ds.variables.items():
        var_name_lower = var_name.lower()
        if level_dim_name and level_dim_name in variable.dims:
            if primary_dim and num_profiles > 1 and variable.ndim == 2:
                for i in range(num_profiles):
                    measurement_vars_by_profile[i][var_name_lower] = variable.values[i]
            else:
                measurement_vars_by_profile[0][var_name_lower] = variable.values.flatten()
        elif primary_dim and primary_dim in variable.dims and variable.ndim == 1:
            for i in range(num_profiles):
                metadata_rows[i][var_name_lower] = clean_and_decode_value(variable.values[i])
        elif variable.ndim <= 1:
            value = clean_and_decode_value(variable.values.item(0) if variable.values.size > 0 else None)
            for i in range(num_profiles):
                metadata_rows[i][var_name_lower] = value
    metadata_df = pd.DataFrame(metadata_rows)
    for coord in ['LATITUDE', 'LONGITUDE', 'JULD']:
        if coord in ds.coords and coord.lower() not in metadata_df.columns:
            if ds.coords[coord].values.size > 0:
                 metadata_df[coord.lower()] = ds.coords[coord].values[0]
    all_measurements_dfs = []
    if level_dim_name and any(measurement_vars_by_profile):
        for i in range(num_profiles):
            if measurement_vars_by_profile[i]:
                measurements_df = pd.DataFrame(measurement_vars_by_profile[i])
                if 'platform_number' in metadata_df.columns: measurements_df['platform_number'] = metadata_df.at[i, 'platform_number']
                if 'cycle_number' in metadata_df.columns: measurements_df['cycle_number'] = metadata_df.at[i, 'cycle_number']
                measurements_df['n_levels'] = np.arange(len(measurements_df))
                all_measurements_dfs.append(measurements_df)
    measurements_df = pd.concat(all_measurements_dfs, ignore_index=True) if all_measurements_dfs else pd.DataFrame()
    if "predeployment_calib_coefficient" in metadata_df.columns:
        coeffs_df = pd.json_normalize(metadata_df["predeployment_calib_coefficient"].apply(parse_calib_coefficients))
        if not coeffs_df.empty: metadata_df = metadata_df.join(coeffs_df)
        metadata_df = metadata_df.drop(columns=["predeployment_calib_coefficient"])
    if "predeployment_calib_equation" in metadata_df.columns:
        metadata_df["calibration_equation_type"] = metadata_df["predeployment_calib_equation"].apply(simplify_equation)
        metadata_df = metadata_df.drop(columns=["predeployment_calib_equation"])
    if "vertical_sampling_scheme" in metadata_df.columns:
        metadata_df["sampling_scheme_summary"] = metadata_df["vertical_sampling_scheme"].apply(simplify_sampling_scheme)
        metadata_df = metadata_df.drop(columns=["vertical_sampling_scheme"])
    return metadata_df, measurements_df

# --- ETL PROCESSORS (Unchanged) ---
def process_file_with_measurements(ds, table_name, conflict_cols):
    metadata_df, measurements_df = process_nc_file(ds)
    total_rows = 0
    if not metadata_df.empty:
        if conflict_cols: metadata_df.drop_duplicates(subset=conflict_cols, keep='last', inplace=True)
        sync_schema(engine, table_name, metadata_df)
        total_rows += upsert_bulk(metadata_df, table_name, conflict_cols)
    if not measurements_df.empty:
        measurement_conflict_cols = ['platform_number', 'cycle_number', 'n_levels']
        sync_schema(engine, 'measurements', measurements_df)
        total_rows += upsert_bulk(measurements_df, 'measurements', measurement_conflict_cols)
    return total_rows
def process_file_simple(ds, table_name, conflict_cols):
    metadata_df, _ = process_nc_file(ds)
    if metadata_df.empty: return 0
    if conflict_cols: metadata_df.drop_duplicates(subset=conflict_cols, keep='last', inplace=True)
    sync_schema(engine, table_name, metadata_df)
    return upsert_bulk(metadata_df, table_name, conflict_cols)
def process_meta_file(ds): return process_file_simple(ds, "meta", ["platform_number"])
def process_prof_file(ds): return process_file_with_measurements(ds, 'profiles', ["platform_number", "cycle_number"])
def process_tech_file(ds): return process_file_simple(ds, 'tech', ["platform_number", "cycle_number"])
def process_sprof_file(ds): return process_file_with_measurements(ds, 'sprof', ["platform_number", "cycle_number"])
def process_rtraj_file(ds): return process_file_simple(ds, 'rtraj', [])

# --- GENERIC FILE PROCESSOR ---
# --- FIX --- Updated to check the DB and log processed files.
def process_file_wrapper(args):
    nc_path, dest_folder, processor_func = args
    filename = os.path.basename(nc_path)
    try:
        # Check the database to see if this file has been processed before.
        if is_file_processed(filename):
            logging.info(f"Skipping already processed file: {filename}")
            dest_path = os.path.join(dest_folder, filename)
            os.makedirs(dest_folder, exist_ok=True)
            shutil.move(nc_path, dest_path)
            return {} # Return empty dict as no rows were processed

        # If not processed, proceed with ingestion.
        with xr.open_dataset(nc_path, decode_times=False) as ds:
            rows_processed = processor_func(ds)
        
        # Log the filename to the database after successful processing.
        upsert_bulk(pd.DataFrame([{"filename": filename}]), "processedfiles", ["filename"])
        
        dest_path = os.path.join(dest_folder, filename)
        os.makedirs(dest_folder, exist_ok=True)
        shutil.move(nc_path, dest_path)
        logging.info(f"Processed and moved {filename} to {dest_folder}")
        
        return {processor_func.__name__: rows_processed}
    except Exception as e:
        logging.error(f"Error in worker processing {nc_path}: {e}", exc_info=True)
        return {}
        
# ---------------- MAIN ----------------
if __name__ == "__main__":
    all_folders = [
        META_FOLDER, PROF_FOLDER, TECH_FOLDER, SPROF_FOLDER, RTRAJ_FOLDER,
        PROCESSED_META_FOLDER, PROCESSED_PROF_FOLDER, PROCESSED_TECH_FOLDER,
        PROCESSED_SPROF_FOLDER, PROCESSED_RTRAJ_FOLDER
    ]
    for folder in all_folders:
        os.makedirs(folder, exist_ok=True)
    
    mode = input("Select mode: 1 = Automatic (Continuous), 2 = Manual Run Once: ").strip()
    if mode not in ["1", "2"]:
        print("Invalid mode. Exiting.")
        exit(1)

    folders_to_process = [
        ("Meta Files", META_FOLDER, PROCESSED_META_FOLDER, process_meta_file),
        ("Profile Files", PROF_FOLDER, PROCESSED_PROF_FOLDER, process_prof_file),
        ("Tech Files", TECH_FOLDER, PROCESSED_TECH_FOLDER, process_tech_file),
        ("Sprof Files", SPROF_FOLDER, PROCESSED_SPROF_FOLDER, process_sprof_file),
        ("Rtraj Files", RTRAJ_FOLDER, PROCESSED_RTRAJ_FOLDER, process_rtraj_file),
    ]
    num_processes = 1
    
    while True:
        all_files = []
        for name, folder_path, dest_path, processor in folders_to_process:
            try:
                files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".nc")]
                for file_path in files:
                    all_files.append((file_path, dest_path, processor))
            except FileNotFoundError:
                logging.warning(f"Source folder not found: {folder_path}. Skipping.")
        
        if not all_files:
            if mode == '1':
                print("No new files found. Waiting for 30 seconds...")
                time.sleep(30)
                continue
            else:
                print("No files to process. Manual run complete.")
                break
        
        for i in range(0, len(all_files), BATCH_SIZE):
            batch_tasks = all_files[i:i + BATCH_SIZE]
            print(f"\nProcessing batch {i//BATCH_SIZE + 1} with {len(batch_tasks)} files...")
            with Pool(processes=num_processes, maxtasksperchild=100) as pool:
                results = list(tqdm(pool.imap_unordered(process_file_wrapper, batch_tasks), total=len(batch_tasks)))
            
            total_summary = {}
            processed_count = 0
            for res in results:
                if res:
                    processed_count += 1
                    for k, v in res.items():
                        total_summary[k] = total_summary.get(k, 0) + (v or 0)

            print("\n--- Batch Summary ---")
            skipped_count = len(batch_tasks) - processed_count
            if skipped_count > 0:
                print(f"   -> Skipped {skipped_count} files that were already in the database.")

            if not total_summary:
                 print("   -> No new rows were added from the remaining files.")
            else:
                for name, count in total_summary.items():
                    table_name = name.replace('process_', '').replace('_file', '')
                    print(f"   -> Processed {count} total rows for '{table_name}' files (metadata + measurements)")
        
        if mode == '2':
            break

    print("\n✅ Script finished.")