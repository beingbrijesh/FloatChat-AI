import webbrowser
import os
import pandas as pd
from sqlalchemy import create_engine, text
import time

# --- CONFIGURATION ---
DB_CONN = "postgresql+psycopg2://postgres:Ashish%40021@localhost:5432/argo_db"
OUTPUT_FILE = r"E:\argo_db\db_report.html"
ROW_LIMIT = 200 # Max number of rows to fetch from each table

# --- HTML TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Argo Database Report</title>
    <style>
        body {{ font-family: sans-serif; margin: 2em; background-color: #f8f9fa; color: #333; }}
        h1, h2, h3 {{ color: #0056b3; }}
        h1, h2 {{ border-bottom: 2px solid #ccc; padding-bottom: 5px;}}
        nav ul {{ list-style: none; padding: 0; }}
        nav li {{ display: inline-block; margin-right: 15px; }}
        nav a {{ text-decoration: none; color: #0056b3; font-weight: bold; }}
        nav a:hover {{ text-decoration: underline; }}
        .table-container {{ overflow-x: auto; margin-bottom: 2em; border: 1px solid #ddd; border-radius: 5px;}}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        thead th {{ background-color: #e9ecef; }}
        tbody tr:nth-child(even) {{ background-color: #f8f9fa; }}
        tbody tr:hover {{ background-color: #e2e6ea; }}
        .timestamp {{ font-size: 0.8em; color: #666; }}
        .explanation {{ background-color: #e2e6ea; border-left: 5px solid #0056b3; padding: 15px; margin-bottom: 2em; border-radius: 5px; }}
        code {{ background-color: #d1d5db; padding: 2px 5px; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>🌊 Argo Database Report</h1>
    <p class="timestamp">Generated on: {timestamp}</p>
    
    <div class="explanation">
        <h3>Understanding Your Database Structure</h3>
        <p>Your data is organized into two main types of tables:</p>
        <ul>
            <li><b>Metadata Tables</b> (e.g., <code>meta</code>, <code>profiles</code>): These contain summary information for each float or profile cycle. Complex fields have been transformed into new, simple columns like <code>calib_pa0</code>, <code>calibration_equation_type</code>, and <code>sampling_scheme_summary</code>.</li>
            <li><b>The <code>measurements</code> Table:</b> This table contains all the detailed scientific data. Each row represents a single measurement at a specific depth (<code>n_levels</code>), linked to the metadata by <code>platform_number</code> and <code>cycle_number</code>.</li>
        </ul>
    </div>
    
    <h2>Table of Contents</h2>
    <nav>
        <ul>
            {table_of_contents}
        </ul>
    </nav>
    
    <hr>
    
    {table_content}
</body>
</html>
"""

def get_table_names(engine):
    """Gets a list of all user tables from the public schema."""
    with engine.connect() as conn:
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        return [row[0] for row in conn.execute(query)]

def fetch_table_data_pandas(engine, table_name, limit):
    """Fetches data from a table into a Pandas DataFrame and converts to HTML."""
    query = f'SELECT * FROM "{table_name}" LIMIT {limit};'
    try:
        df = pd.read_sql(query, engine)
        if df.empty:
            return "<p>Table is empty.</p>"
        # Set option to prevent truncation of long text in cells
        pd.set_option('display.max_colwidth', None)
        return df.to_html(index=False, classes="db-table", border=0)
    except Exception as e:
        return f"<p>Error fetching data for table '{table_name}': {e}</p>"


if __name__ == "__main__":
    print("🚀 Starting HTML report generation...")
    
    try:
        engine = create_engine(DB_CONN)
        table_names = get_table_names(engine)
        
        if not table_names:
            print("❌ No tables found in the database.")
        else:
            toc_html_list = []
            content_html_list = []

            print(f"🔍 Found {len(table_names)} tables. Fetching data (up to {ROW_LIMIT} rows each)...")
            
            for table in table_names:
                print(f"   - Processing table: {table}")
                toc_html_list.append(f'<li><a href="#{table}">{table}</a></li>')
                
                table_html = fetch_table_data_pandas(engine, table, ROW_LIMIT)
                
                content_html_list.append(f'<h2 id="{table}">Table: {table}</h2>')
                content_html_list.append(f'<div class="table-container">{table_html}</div>')

            final_html = HTML_TEMPLATE.format(
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                table_of_contents="\n".join(toc_html_list),
                table_content="\n".join(content_html_list)
            )

            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(final_html)
            
            print(f"\n🎉 Successfully created report: {OUTPUT_FILE}")
            webbrowser.open_new_tab(f"file://{os.path.realpath(OUTPUT_FILE)}")

    except Exception as e:
        print(f"❌ An error occurred: {e}")