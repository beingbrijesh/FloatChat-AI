import sys
import polars as pl
# --- FIX --- Import 'text' from sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# --- CONFIGURATION ---
DB_CONN = "postgresql+psycopg2://postgres:Ashish%40021@localhost:5432/argo_db"

def get_table_names(engine):
    """Gets a list of all user tables from the public schema."""
    try:
        with engine.connect() as conn:
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """
            # --- FIX --- Wrap the query string in text()
            result = conn.execute(text(query))
            tables = [row[0] for row in result]
            return tables
    except SQLAlchemyError as e:
        print(f"❌ Error fetching table list: {e}", file=sys.stderr)
        return None

def fetch_and_view_data(engine, query: str):
    """
    Connects to the PostgreSQL database, executes a given query,
    and displays the results.
    """
    print(f"\n⚙️  Executing query: {query}")
    try:
        df = pl.read_database(query=query, connection=engine)

        if df.is_empty():
            print("✅ Query executed successfully, but returned no results.")
            return

        print(f"✅ Success! Fetched {df.height} rows and {df.width} columns.")
        print("-" * 50)
        print(df)
        print("-" * 50)

    except SQLAlchemyError as e:
        print(f"❌ An error occurred while executing the query.", file=sys.stderr)
        print(f"Error Details: {e}", file=sys.stderr)
    except Exception as e:
        # Catch potential out-of-memory errors
        print(f"❌ An unexpected error occurred (e.g., out of memory): {e}", file=sys.stderr)

if __name__ == "__main__":
    try:
        engine = create_engine(DB_CONN)
        tables = get_table_names(engine)
        
        if not tables:
            print("Could not find any tables in the database.")
            sys.exit(1)

        while True:
            print("\n--- Argo Database Browser ---")
            for i, table_name in enumerate(tables):
                print(f"  {i + 1}: View table '{table_name}'")
            print("  0: Quit")
            print("-" * 29)

            try:
                choice_str = input("Enter the number of the table to view: ")
                choice = int(choice_str)
                
                if choice == 0:
                    print("Goodbye!")
                    break
                
                if 1 <= choice <= len(tables):
                    selected_table = tables[choice - 1]
                    
                    limit_str = input(f"How many rows from '{selected_table}' to see? (e.g., 20 or type 'ALL'): ").strip()
                    
                    query_limit = ""
                    proceed = True

                    if limit_str.upper() == 'ALL':
                        print("\n🚨 WARNING: Fetching all data from a large table can crash your application or make it unresponsive.")
                        confirm = input(f"Are you sure you want to view ALL rows from '{selected_table}'? (y/n): ").strip().lower()
                        if confirm != 'y':
                            print("Cancelled.")
                            proceed = False
                    elif not limit_str:
                        query_limit = "LIMIT 20"
                    else:
                        try:
                            limit = int(limit_str)
                            if limit <= 0:
                                print("❌ Number of rows must be positive.")
                                proceed = False
                            else:
                                query_limit = f"LIMIT {limit}"
                        except ValueError:
                            print("❌ Invalid input. Please enter a number or 'ALL'.")
                            proceed = False
                    
                    if proceed:
                        sql_query = f"SELECT * FROM \"{selected_table}\" {query_limit};"
                        fetch_and_view_data(engine, sql_query)
                    
                    input("\nPress Enter to return to the menu...")

                else:
                    print(f"❌ Invalid choice. Please enter a number between 0 and {len(tables)}.")

            except ValueError:
                print("❌ Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)