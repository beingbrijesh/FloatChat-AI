import mysql.connector
import pandas as pd

# MySQL connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",      # e.g. root
    password="1234",  # your MySQL password
    database="argo_data"   # database you already created
)
cursor = conn.cursor()

# Load CSV
csv_file = "output.csv"
df = pd.read_csv(csv_file)

# Table name
table_name = "argo_data"
columns = df.columns

# Build CREATE TABLE query dynamically
create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("
for col in columns:
    col = col.replace(" ", "_").replace("-", "_")  # safe column names
    create_table_query += f"`{col}` TEXT,"
create_table_query = create_table_query.rstrip(",") + ");"

cursor.execute(create_table_query)

# Insert rows
for _, row in df.iterrows():
    values = [str(v) if pd.notna(v) else None for v in row.tolist()]
    placeholders = ','.join(['%s'] * len(values))
    insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"
    cursor.execute(insert_query, values)

# Commit changes
conn.commit()
cursor.close()
conn.close()

print(f"✅ Data from {csv_file} inserted into table '{table_name}' in MySQL")
