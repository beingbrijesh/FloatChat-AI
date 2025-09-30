import time
import pandas as pd
from sqlalchemy import create_engine, text, inspect

# --- CONFIGURATION ---
DB_CONN = "postgresql+psycopg2://postgres:Ashish%40021@localhost:5432/argo_db"
TABLES_TO_CLEAN = {
    "meta": {"id_cols": ["platform_number"], "timestamp_col": "date_update"},
    "profiles": {"id_cols": ["platform_number", "cycle_number"], "timestamp_col": "date_update"},
    "tech": {"id_cols": ["platform_number", "cycle_number"], "timestamp_col": "date_update"},
    "sprof": {"id_cols": ["platform_number", "cycle_number"], "timestamp_col": "date_update"},
    "measurements": {"id_cols": ['platform_number', 'cycle_number', 'n_levels'], "timestamp_col": None}
}
# Values to consider as 'empty' when checking columns
NULL_LIKE_VALUES = {'', '0', '0.0', 'n/a', 'N/A', 'none', 'None', 'NONE', 'nan', 'NaN', 'NAN', None}

def drop_empty_columns(conn, table_name):
    """Finds and drops columns where all values are NULL or null-like."""
    print(f"   🔍 Checking for uninformative empty columns in '{table_name}'...")
    
    try:
        # Fetch a sample of the data to check for emptiness
        df_sample = pd.read_sql(f'SELECT * FROM "{table_name}" LIMIT 1000;', conn)
        if df_sample.empty:
            print("   ✅ Table is empty. Nothing to drop.")
            return

        cols_to_drop = []
        for col_name in df_sample.columns:
            # Check if all unique non-null values in the column are in our null-like set
            unique_vals = df_sample[col_name].dropna().unique()
            if all(str(val).strip() in NULL_LIKE_VALUES for val in unique_vals):
                cols_to_drop.append(col_name)

        if not cols_to_drop:
            print("   ✅ No completely empty columns found.")
            return

        print(f"   ❗ Found {len(cols_to_drop)} uninformative columns to drop: {', '.join(cols_to_drop)}")
        confirm = input("      Proceed with dropping these columns? This is permanent. (y/n): ").strip().lower()

        if confirm == 'y':
            for col_name in cols_to_drop:
                print(f"      🗑️  Dropping column '{col_name}'...")
                drop_query = text(f'ALTER TABLE "{table_name}" DROP COLUMN "{col_name}";')
                conn.execute(drop_query)
            conn.commit()
            print(f"   ✅ Successfully dropped {len(cols_to_drop)} columns.")
        else:
            print("   🚫 Column drop cancelled by user.")
    except Exception as e:
        print(f"   ⚠️  Could not check for empty columns in '{table_name}': {e}")

def deduplicate_by_latest(conn, table_name, id_cols, timestamp_col):
    """Finds and removes older duplicate rows based on a timestamp."""
    if not timestamp_col:
        print(f"   ℹ️  Skipping 'keep latest' deduplication for '{table_name}' (no timestamp column defined).")
        return
        
    print(f"   🔍 Searching for older duplicate rows in '{table_name}'...")
    id_cols_str = ", ".join([f'"{c}"' for c in id_cols])
    
    find_dupes_query = f"""
        SELECT COUNT(*) FROM (
            SELECT ROW_NUMBER() OVER(PARTITION BY {id_cols_str} ORDER BY "{timestamp_col}" DESC NULLS LAST) as rn
            FROM "{table_name}"
        ) as sub WHERE rn > 1;
    """
    
    delete_dupes_query = f"""
        DELETE FROM "{table_name}" WHERE ctid IN (
            SELECT ctid FROM (
                SELECT ctid, ROW_NUMBER() OVER(PARTITION BY {id_cols_str} ORDER BY "{timestamp_col}" DESC NULLS LAST) as rn
                FROM "{table_name}"
            ) as sub WHERE rn > 1
        );
    """
    
    num_dupes = conn.execute(text(find_dupes_query)).scalar_one()

    if num_dupes == 0:
        print(f"   ✅ No older duplicates found in '{table_name}'.")
        return

    print(f"   ❗ Found {num_dupes} older duplicate rows that can be removed.")
    confirm = input(f"      Proceed with deleting these {num_dupes} rows? (y/n): ").strip().lower()

    if confirm == 'y':
        print("      🗑️  Deleting older rows...")
        start_time = time.time()
        result = conn.execute(text(delete_dupes_query))
        conn.commit()
        end_time = time.time()
        print(f"   ✅ Successfully removed {result.rowcount} rows in {end_time - start_time:.2f} seconds.")
    else:
        print("   🚫 Deletion cancelled by user.")

if __name__ == "__main__":
    print("🚀 Starting database optimization script.")
    engine = create_engine(DB_CONN)

    try:
        with engine.connect() as connection:
            for table_name, config in TABLES_TO_CLEAN.items():
                print(f"\n-`´-`´-`´-`´-`´-`´-`´-`´-`´-`´-`´-`´-`´-")
                print(f"⚙️  Optimizing table: '{table_name}'")
                
                # Step 1: Drop empty columns
                drop_empty_columns(connection, table_name)
                
                # Step 2: Remove older duplicates
                deduplicate_by_latest(connection, table_name, config["id_cols"], config["timestamp_col"])
                
        print("\n🎉 Optimization process finished.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")