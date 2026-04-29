import os
import sys
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import urllib
from dotenv import load_dotenv

# ==========================================
# 1. Environment & DB Connection Setup
# ==========================================
load_dotenv()

DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME = os.getenv("DB_NAME", "HR_DW")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

try:
    if DB_USER and DB_PASS:
        # SQL Server Authentication
        encoded_password = urllib.parse.quote_plus(DB_PASS)
        connection_string = f"mssql+pyodbc://{DB_USER}:{encoded_password}@{DB_SERVER}/{DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server"
    else:
        # Windows Authentication (Trusted Connection)
        connection_string = f"mssql+pyodbc://@{DB_SERVER}/{DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
    
    # fast_executemany=True is crucial for fast bulk inserts into SQL Server
    engine = create_engine(connection_string, fast_executemany=True)
    print("✅ Database connection engine created successfully.")
except Exception as e:
    print(f"❌ Error creating database engine: {e}")
    sys.exit(1)

# ==========================================
# 2. ETL Functions
# ==========================================
def extract_and_clean_csv(uploaded_file):
    """Extracts data from CSV and applies HR-specific cleaning rules."""
    print("Reading and cleaning CSV data...")
    try:
        df = pd.read_csv(uploaded_file)
        
        # 1. Drop garbage columns & exact duplicates
        if 'Unnamed: 0' in df.columns:
            df = df.drop(columns=['Unnamed: 0'])
        df = df.drop_duplicates()
        
        # 2. Strip whitespace from text columns 
        # Added 'string' to silence pandas deprecation warning
        text_cols = df.select_dtypes(include=['object', 'string']).columns
        for col in text_cols:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({'nan': None, 'None': None, '': None, 'NaT': None})

        # 3. Convert Dates properly
        # Added format='mixed' and dayfirst=True to silence warnings and handle messy formats
        date_cols = ['StartDate', 'ExitDate', 'DOB', 'Survey Date', 'Training Date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='mixed', dayfirst=True, errors='coerce').dt.date

        # 4. Rename columns to match Staging_HR_Data exactly
        rename_mapping = {
            'Employee ID': 'Employee_ID',
            'Performance Score': 'Performance_Score',
            'Current Employee Rating': 'Current_Employee_Rating',
            'Survey Date': 'Survey_Date',
            'Engagement Score': 'Engagement_Score',
            'Satisfaction Score': 'Satisfaction_Score',
            'Work-Life Balance Score': 'Work_Life_Balance_Score',
            'Training Date': 'Training_Date',
            'Training Program Name': 'Training_Program_Name',
            'Training Type': 'Training_Type',
            'Training Outcome': 'Training_Outcome',
            'Training Duration(Days)': 'Training_Duration_Days',
            'Training Cost': 'Training_Cost'
        }
        df = df.rename(columns=rename_mapping)
        
        # 5. Convert Pandas NaN/NaT to actual Python None for SQL NULLs
        df = df.replace({np.nan: None})
        
        print(f"Data validation passed. {len(df)} rows ready for staging.")
        return df
    except Exception as e:
        print(f"Error during data extraction/cleaning: {e}")
        return None

def load_to_staging(df, db_engine):
    """Truncates staging and loads new dataframe."""
    print("Truncating Staging_HR_Data and loading new batch...")
    try:
        with db_engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE Staging_HR_Data;"))
            df.to_sql('Staging_HR_Data', con=conn, if_exists='append', index=False)
        print("Staging load completed successfully.")
    except Exception as e:
        print(f"Error loading to staging: {e}")
        raise

def run_data_warehouse_load(db_engine):
    """Executes the stored procedure to MERGE data into Star Schema."""
    print("Executing sp_LoadHRDataWarehouse to populate Dimensions and Fact...")
    try:
        with db_engine.begin() as conn:
            conn.execute(text("EXEC sp_LoadHRDataWarehouse;"))
        print("Star Schema Data Warehouse load procedure executed successfully.")
    except Exception as e:
        print(f"Error running stored procedure: {e}")
        raise

# ==========================================
# 3. Main Orchestrator
# ==========================================
def main_etl_process(uploaded_file, db_engine):
    """The main function to be called by the Streamlit App."""
    try:
        clean_df = extract_and_clean_csv(uploaded_file)
        if clean_df is not None and not clean_df.empty:
            load_to_staging(clean_df, db_engine)
            run_data_warehouse_load(db_engine)
            
            # Count Active vs Terminated for UI Metrics
            active_count = len(clean_df[clean_df['ExitDate'].isnull()])
            terminated_count = len(clean_df[clean_df['ExitDate'].notnull()])
            
            success_msg = f"Successfully Processed! Uploaded {len(clean_df)} records ({active_count} Active, {terminated_count} Terminated)."
            print(f"\nETL Process Completed: {success_msg}")
            return True, success_msg
        else:
            msg = "ETL process halted: No valid data to load."
            print(msg)
            return False, msg
    except Exception as e:
        error_msg = f"ETL process FAILED: {e}"
        print(f"\n{error_msg}")
        return False, error_msg

# ==========================================
# Standalone Testing Mode
# ==========================================
if __name__ == "__main__":
    csv_file_path = 'HR_Dataset.csv' # للاختبار المباشر بدون الواجهة
    print(f"Running ETL in standalone mode for: {csv_file_path}")
    
    try:
        with open(csv_file_path, 'rb') as f: 
            success, message = main_etl_process(f, engine)
        print(message)
    except FileNotFoundError:
        print(f"Error: Test file '{csv_file_path}' not found. Check the path.")