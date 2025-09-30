import pandas as pd
from sqlalchemy import create_engine, text, inspect
import time
import re
import sys
import os

# --- CONFIGURATION ---
DB_CONN = "postgresql+psycopg2://postgres:Ashish%40021@localhost:5432/argo_db"
OUTPUT_FILENAME = "model_training_data_final"
BASE_OUTPUT_DIR = r"E:\argo_db"

MIN_VALID_PERCENTAGE = 1.0
NULL_LIKE_VALUES = {'', '0', '0.0', 'n/a', 'N/A', 'none', 'None', 'NONE', 'nan', 'NaN', 'NAN', None, 'not specified'}

# --- HELPER FUNCTIONS ---
def get_existing_columns(engine, table_name, schema='public'):
    try:
        inspector = inspect(engine)
        return [col['name'] for col in inspector.get_columns(table_name, schema=schema)]
    except Exception:
        return []

def clean_value_final(value):
    if isinstance(value, bytes):
        value = value.decode('utf-8', 'ignore')
    if isinstance(value, str):
        try:
            if value.startswith('\\x'):
                value = bytes.fromhex(value.replace('\\x', '')).decode('utf-8', 'ignore')
        except (ValueError, TypeError):
            pass
        return value.strip().strip('\x00')
    return value

def make_unique_columns(df):
    seen = {}
    new_cols = []
    for col in df.columns:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    df.columns = new_cols
    return df

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("🚀 Starting final data extraction and preparation...")

    try:
        start_time = time.time()
        engine = create_engine(DB_CONN)

        print("⚙️  Checking database schema to build a custom query...")
        profiles_cols = get_existing_columns(engine, 'profiles')
        meta_cols = get_existing_columns(engine, 'meta')
        measurements_cols = get_existing_columns(engine, 'measurements')

        if not profiles_cols or not meta_cols:
            raise Exception("Required tables 'profiles' and/or 'meta' do not exist.")

        select_clauses = [f'p."{col}"' for col in profiles_cols]
        select_clauses.extend([f'm."{col}"' for col in meta_cols if col != 'platform_number'])
        if measurements_cols:
            select_clauses.extend([f'meas."{col}"' for col in measurements_cols if col not in ['platform_number', 'cycle_number']])

        from_clause = "profiles p LEFT JOIN meta m ON p.platform_number = m.platform_number"
        if measurements_cols:
            from_clause += " LEFT JOIN measurements meas ON p.platform_number = meas.platform_number AND p.cycle_number = meas.cycle_number"

        JOIN_QUERY = f"SELECT {', '.join(select_clauses)} FROM {from_clause};"

        print("⚙️  Connecting to database and executing dynamic JOIN query...")
        df = pd.read_sql(JOIN_QUERY, engine)

        if df.empty:
            print("❌ Query returned no data.")
            sys.exit(1)

        print(f"✅ Success! Fetched {len(df)} rows and {len(df.columns)} columns.")

        print("\n🔍 Performing final cleaning on retrieved data...")
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(clean_value_final)

        # --- IMPROVED LOGIC FOR REMOVING EMPTY COLUMNS ---
        print(f"🔍 Removing columns with less than {MIN_VALID_PERCENTAGE}% meaningful data (after trimming, lowercasing, etc.)...")
        cols_to_drop = []
        for col_name in df.columns:
            try:
                col = df[col_name]
                # If it's not an object or string dtype, skip it
                if not pd.api.types.is_object_dtype(col) and not pd.api.types.is_string_dtype(col):
                    continue
                # Ensure the column is treated as strings
                s = col.astype(str).apply(lambda x: str(x).strip().lower() if pd.notna(x) else x)
                nulls = {str(x).strip().lower() for x in NULL_LIKE_VALUES if x is not None}
                mask_null_like = s.isin(nulls)
                mask_orig_na = pd.isna(col)
                mask_total_null = mask_null_like | mask_orig_na
                valid_count = (~mask_total_null).sum()
                total = len(col)
                valid_percentage = (valid_count / total) * 100 if total > 0 else 0
                print(f"DEBUG: Column '{col_name}': valid count = {valid_count}, total = {total}, valid % = {valid_percentage:.2f}%")
                if valid_percentage < MIN_VALID_PERCENTAGE:
                    cols_to_drop.append(col_name)
            except Exception as e:
                print(f"⚠️ Error checking column '{col_name}': {e}")


        if cols_to_drop:
            df.drop(columns=cols_to_drop, inplace=True)
            print(f"✅ Dropped columns: {cols_to_drop}")
        else:
            print("   -> No uninformative columns found (even after stricter check).")

        # --- END OF IMPROVED LOGIC ---

        print("🔍 Deduplicating data, keeping latest profiles...")
        if {'juld', 'platform_number', 'cycle_number'}.issubset(df.columns):
            df = df.sort_values(by=['platform_number', 'cycle_number', 'juld'], ascending=[True, True, False])
            dedup_cols = ['platform_number', 'cycle_number']
            if 'n_levels' in df.columns:
                dedup_cols.append('n_levels')
            before = len(df)
            df = df.drop_duplicates(subset=dedup_cols, keep='first')
            print(f"   -> Removed {before - len(df)} older/duplicate rows.")

        print("\n🤖 Preparing data for model (One-Hot Encoding)...")
        cols_to_encode = [col for col in ['direction', 'data_mode', 'platform_type', 'calibration_equation_type', 'sampling_scheme_summary'] if col in df.columns]
        if cols_to_encode:
            before_cols = df.shape[1]
            df = pd.get_dummies(df, columns=cols_to_encode, dummy_na=True, dtype=int)
            after_cols = df.shape[1]
            print(f"   -> Transformed {len(cols_to_encode)} categorical columns into {after_cols - (before_cols - len(cols_to_encode))} new columns.")

        df = make_unique_columns(df)

        print("\n💾 Saving final model-ready dataset...")
        output_dir = os.path.join(BASE_OUTPUT_DIR, "output")
        parquet_path = os.path.join(output_dir, "parquet", f"{OUTPUT_FILENAME}.parquet")
        csv_path = os.path.join(output_dir, "csv", f"{OUTPUT_FILENAME}.csv")
        excel_path = os.path.join(output_dir, "excel", f"{OUTPUT_FILENAME}.xlsx")

        os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        os.makedirs(os.path.dirname(excel_path), exist_ok=True)

        df.to_parquet(parquet_path)
        df.to_csv(csv_path, index=False)
        df.to_excel(excel_path, index=False)

        end_time = time.time()
        print(f"\n🎉 Successfully saved dataset in {end_time - start_time:.2f} seconds.")
        print("📁 Output files:")
        print(f"   - Parquet: {parquet_path}")
        print(f"   - CSV    : {csv_path}")
        print(f"   - Excel  : {excel_path}")

    except Exception as e:
        print(f"❌ An error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
