Argo Float Data ETL and Reporting Pipeline
This project provides a complete ETL (Extract, Transform, Load) pipeline for processing oceanographic data from Argo float NetCDF (.nc) files. It extracts data from meta, prof, and tech files, loads it into a PostgreSQL database with a dynamic schema, and generates a standalone, interactive HTML report for data exploration.

Features
Automated ETL: A Python script (etl_argo.py) watches a directory for new .nc files and processes them automatically.

Dynamic Schema Creation: The ETL script intelligently analyzes .nc files and automatically adds new columns to the database tables as needed, preventing errors from schema mismatches.

Robust Data Loading: Handles different file types (meta, prof, tech) and maps them to separate, linked tables in a PostgreSQL database.

Interactive HTML Report: A second script (generate_report.py) queries the database and builds a single, self-contained argo_report.html file.

User-Friendly Interface: The HTML report allows for searching, filtering, and viewing detailed records in a clean, vertical layout without requiring a live server or backend.

Error Handling & Logging: Comprehensive logging tracks the entire process, and processed files are automatically moved to prevent re-processing.

Project Structure
E:\argo_db\
│
├── nc_files\                # -> Drop your .nc files here
│   ├── meta_files\
│   ├── prof_files\
│   └── tech_files\
│
├── processed\               # -> Successfully processed files are moved here
│
├── etl_argo.py              # -> The main ETL script to process files
├── generate_report.py       # -> The script to create the HTML report
├── argo_report.html         # -> The final, interactive report (output)
├── requirements.txt         # -> Python dependencies for the project
└── README.md                # -> This file

Setup and Installation
Prerequisites
Python 3.9+

PostgreSQL Server

Steps
Clone the Repository (or download the files)

# git clone <your-repo-url>
# cd argo_db

Create a Virtual Environment
It's highly recommended to use a virtual environment to manage project dependencies.

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

Install Dependencies
Install all the required Python libraries using the requirements.txt file.

pip install -r requirements.txt

Configure Database Connection
Open etl_argo.py and generate_report.py and update the DB_CONN string with your PostgreSQL credentials.

# Example from etl_argo.py
DB_CONN = "postgresql+psycopg2://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT/argo_db"

Set Up Database Schema
Connect to your PostgreSQL instance and run the provided SQL script to create the initial meta, profiles, and tech tables. This only needs to be done once.

How to Use
1. Run the ETL Pipeline
Place your .nc files into the appropriate subfolders within nc_files/. Then, run the ETL script from your terminal.

python etl_argo.py

The script will ask you to run in Manual or Automatic mode.

Manual Mode: Processes all current files and then exits.

Automatic Mode: Processes all current files and continues to watch the folders for new files.

2. Generate the Interactive Report
After your data has been loaded into the database, run the report generator script.

python generate_report.py

This will create (or overwrite) the argo_report.html file in your project directory.

3. View the Report
Simply double-click the argo_report.html file to open it in your default web browser. You can now search for floats and explore their detailed data.