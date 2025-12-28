import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pycelonis import get_celonis
from config import ERP_CONFIG
import logging

# Configure logging
logging.basicConfig(filename='main_debug.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

def connect_to_celonis():
    """Establishes connection to Celonis."""
    url = os.getenv("CELONIS_URL")
    api_token = os.getenv("CELONIS_API_TOKEN")
    
    if not url or not api_token:
        print("Error: CELONIS_URL or CELONIS_API_TOKEN not found in environment.")
        return None
    
    return get_celonis(base_url=url, api_token=api_token)

def select_erp_configuration():
    """Prompts user to select ERP and Process to auto-configure tables."""
    print("\n--- Enterprise Duplicate Checker Setup ---")
    print("Available ERP Systems:")
    erps = list(ERP_CONFIG.keys())
    for i, erp in enumerate(erps):
        print(f"{i + 1}. {erp}")
    print(f"{len(erps) + 1}. Custom (Manual Entry)")

    choice_idx = input("Select System (Number): ")
    try:
        if int(choice_idx) == len(erps) + 1:
            return None, None
        system = erps[int(choice_idx) - 1]
    except (ValueError, IndexError):
        print("Invalid selection. Defaulting to Custom.")
        return None, None

    print(f"\nAvailable Processes for {system}:")
    processes = list(ERP_CONFIG[system].keys())
    for i, proc in enumerate(processes):
        print(f"{i + 1}. {proc} - {ERP_CONFIG[system][proc]['description']}")
    
    proc_choice = input("Select Process (Number): ")
    try:
        process = processes[int(proc_choice) - 1]
        return system, process
    except (ValueError, IndexError):
        print("Invalid selection. Defaulting to Custom.")
        return None, None

def get_or_create_datamodel(pool, tables_to_add, data_model_id=None):
    """Gets or creates a temporary Data Model for extraction."""
    logging.info("Entering get_or_create_datamodel")
    
    dm = None
    if data_model_id:
        logging.info(f"Checking provided Data Model ID: {data_model_id}")
        try:
             # Validate with Data Pool
             dm = pool.get_data_models().find(data_model_id)
             if dm:
                 logging.info(f"Validated and found Data Model: {dm.name} ({dm.id})")
                 print(f"Using provided Data Model: {dm.name}")
        except Exception as e:
             logging.warning(f"Provided Data Model ID {data_model_id} not found or invalid: {e}")
             print(f"Warning: Data Model ID {data_model_id} invalid or not found. Searching for default...")
             dm = None

    if not dm:
        dm_name = "Enterprise_Dup_Check_Temp"
        try:
            logging.info("Listing Data Models...")
            dms = pool.get_data_models()
            for d in dms:
                if d.name == dm_name:
                    logging.info(f"Found temporary Data Model: {d.name}")
                    dm = d
                    break
            
            if not dm:
                logging.info(f"Creating extracted Data Model: {dm_name}")
                dm = pool.create_data_model(dm_name)
                logging.info(f"Created DM: {dm.id}")
        except Exception as e:
            logging.error(f"Error finding/creating default DM: {e}")

    if not dm:
        return None
            
    try:
        # Ensure tables are added
        for table_name in tables_to_add:
            try:
                # pycelonis 2.x add_table usually takes name or table object
                # Try adding by name (assuming same pool context)
                # It might require finding the table in the pool first?
                # But let's try simplest: add_table(name=..., alias=...)
                dm.add_table(name=table_name, alias=table_name)
                logging.info(f"Added {table_name} to DM.")
            except Exception as e:
                # If that fails, try finding table in pool and passing object
                try: 
                     t_obj = pool.get_tables().find(table_name)
                     dm.add_table(t_obj)
                     logging.info(f"Added {table_name} object to DM.")
                except Exception as ex:
                     logging.info(f"Skipping {table_name}: {e} // {ex}")
                
        logging.info("Reloading Data Model...")
        dm.reload()
        logging.info("Reload complete.")
        return dm
    except Exception as e:
        logging.error(f"Error managing Data Model: {e}")
        return None

def get_data_from_tables(pool, table_names):
    """Fetches data using a temporary Data Model and PQL."""
    logging.info(f"Fetching data from tables: {table_names}")
    
    # Check for DATA_MODEL_ID env var here to pass deeply
    data_model_id = os.getenv("DATA_MODEL_ID")
    if data_model_id and not data_model_id.strip():
        data_model_id = None
        
    dm = get_or_create_datamodel(pool, table_names, data_model_id)
    if not dm:

        logging.error("Failed to get Data Model.")
        return {}
        
from pycelonis.pql import PQL, PQLColumn, PQLFilter

# ... (Previous code) ...

def get_data_from_tables(pool, table_names):
    """Fetches data using a temporary Data Model and PQL."""
    logging.info(f"Fetching data from tables: {table_names}")
    dm = get_or_create_datamodel(pool, table_names)
    if not dm:
        logging.error("Failed to get Data Model.")
        return {}
        
    data_frames = {}
    for table_name in table_names:
        logging.info(f"Fetching data from table: {table_name}")
        try:
            # Find table in DM
            found_table = dm.get_tables().find(table_name)
            
            if found_table:
                logging.info(f"Found table {found_table.name}. Building PQL query...")
                
                # Get columns to select *
                cols = found_table.get_columns()
                query = PQL()
                for col in cols:
                    # Construct PQL: "TABLE"."COLUMN"
                    query += PQLColumn(name=col.name, query=f'"{found_table.name}"."{col.name}"')
                
                logging.info(f"Exporting DataFrame for {table_name} with {len(cols)} columns...")
                try:
                    df = dm.export_data_frame(query)
                    data_frames[table_name] = df
                    logging.info(f"Successfully fetched {len(df)} rows from {table_name}")
                except Exception as e:
                     logging.error(f"Export failed for {table_name}: {e}")

            else:
                logging.warning(f"Table '{table_name}' not found in Data Model.")
        except Exception as e:
            logging.error(f"Error fetching table {table_name}: {e}")
    return data_frames

def identify_common_keys(dfs):
    """Identifies common columns between DataFrames for joining."""
    if not dfs:
        return []
    common_cols = set(dfs[0].columns)
    for df in dfs[1:]:
        common_cols = common_cols.intersection(set(df.columns))
    return list(common_cols)

def join_tables(data_frames, config=None):
    """Joins multiple DataFrames based on configuration or common keys."""
    if not data_frames:
        return None
    
    tables_list = list(data_frames.values())
    if len(tables_list) == 1:
        return tables_list[0]
    
    join_keys = None
    if config and 'join_keys' in config:
        # Verify if configured keys exist in the fetched data
        valid_keys = True
        for df in tables_list:
            if not all(k in df.columns for k in config['join_keys']):
                valid_keys = False
                break
        if valid_keys:
            join_keys = config['join_keys']
            print(f"Using configured join keys: {join_keys}")

    if not join_keys:
        join_keys = identify_common_keys(tables_list)
        print(f"Using auto-detected join keys: {join_keys}")

    if not join_keys:
        print("Warning: No common keys found. Performing cross join (caution!).")
        merged_df = tables_list[0]
        for next_df in tables_list[1:]:
            merged_df = pd.merge(merged_df, next_df, how='inner')
    else:
        merged_df = tables_list[0]
        for next_df in tables_list[1:]:
            merged_df = pd.merge(merged_df, next_df, on=join_keys, how='inner')
            
    return merged_df

def check_duplicates(df, config=None):
    """Identifies duplicate records in the DataFrame."""
    subset = None
    if config and 'duplicate_keys' in config:
        # Verify keys exist
        if all(k in df.columns for k in config['duplicate_keys']):
            subset = config['duplicate_keys']
            print(f"Checking for duplicates on keys: {subset}")
        else:
             print(f"Warning: Configured duplicate keys {config['duplicate_keys']} not found in data. Checking all columns.")

    duplicate_mask = df.duplicated(subset=subset, keep=False)
    duplicates = df[duplicate_mask]
    return duplicates

def filter_by_frequency(df, frequency, date_column):
    """Filters duplicates based on the user's selected time frequency."""
    if date_column not in df.columns:
        print(f"Error: Date column '{date_column}' not found in data.")
        return df

    # Ensure date column is datetime
    try:
        df[date_column] = pd.to_datetime(df[date_column])
    except Exception as e:
        print(f"Error converting date column: {e}")
        return df
    
    now = datetime.now()
    cutoff = now 
    
    if frequency == 'hour':
        cutoff -= timedelta(hours=1)
    elif frequency == 'day':
        cutoff -= timedelta(days=1)
    elif frequency == 'week':
        cutoff -= timedelta(weeks=1)
    elif frequency == 'month':
        cutoff -= timedelta(days=30)
    else:
        print(f"Invalid frequency: {frequency}. Returning all duplicates.")
        return df
    
    return df[df[date_column] >= cutoff]

def main():
    celonis = connect_to_celonis()
    if not celonis:
        return

    pool_id = os.getenv("DATA_POOL_ID")
    if not pool_id:
        print("Error: DATA_POOL_ID not found in .env")
        try:
             pools = celonis.data_integration.get_data_pools()
             if pools:
                 print("\nAvailable Data Pools:")
                 for i, p in enumerate(pools):
                     print(f"{i+1}. {p.name} (ID: {p.id})")
                 sel = input("Select Pool (Number): ")
                 pool = pools[int(sel)-1]
             else:
                 print("No Data Pools found.")
                 return
        except:
             return
    else:
        try:
            pool = celonis.data_integration.get_data_pools().find(pool_id)
            print(f"Connected to Data Pool: {pool.name}")
        except Exception as e:
            print(f"Error finding pool {pool_id}: {e}")
            print("Falling back to listing pools...")
            try:
                 pools = celonis.data_integration.get_data_pools()
                 if pools:
                     print("\nAvailable Data Pools:")
                     for i, p in enumerate(pools):
                         print(f"{i+1}. {p.name} (ID: {p.id})")
                     sel = input("Select Pool (Number): ")
                     pool = pools[int(sel)-1]
                 else:
                     print("No Data Pools found.")
                     return
            except Exception as ex:
                 print(f"Error listing pools: {ex}")
                 return

    # Enterprise Selection
    system, process = select_erp_configuration()
    
    config = None
    if system and process:
        config = ERP_CONFIG[system][process]
        table_names = config['tables']
        print(f"Auto-selected tables for {system} {process}: {table_names}")
    else:
        table_names_input = input("Enter table names (comma separated): ")
        table_names = [name.strip() for name in table_names_input.split(",")]
    
    data_frames = get_data_from_tables(pool, table_names)
    
    if not data_frames:
        print("No data fetched. Exiting.")
        return
    
    merged_df = join_tables(data_frames, config)
    
    if merged_df is None or merged_df.empty:
        print("Merged data is empty.")
        return
    
    print(f"Total records after join: {len(merged_df)}")
    
    duplicates = check_duplicates(merged_df, config)
    print(f"Number of duplicate records identified: {len(duplicates)}")
    
    if duplicates.empty:
        print("No duplicates found.")
        return

    freq = input("Enter frequency to filter duplicates (month/week/day/hour/all): ").lower()
    
    if freq != 'all':
        date_col = None
        if config:
            for key in config['duplicate_keys']:
                if 'DAT' in key or 'DATE' in key: 
                    date_col = key
                    break
        
        if not date_col:
            date_col = input("Enter the timestamp column name for filtering: ")
            
        filtered_duplicates = filter_by_frequency(duplicates, freq, date_col)
        print(f"Number of duplicates after {freq} filter: {len(filtered_duplicates)}")
    else:
        filtered_duplicates = duplicates

    if filtered_duplicates.empty:
        print("No duplicates found after filtering.")
        return

    target_table_name = input("Enter the target Celonis table name to append data: ")
    
    try:
        # Use push_table on pool for appending result
        print(f"Appending {len(filtered_duplicates)} records to {target_table_name}...")
        filtered_duplicates = filtered_duplicates.reset_index(drop=True)
        # Check if table exists, if so append, else create
        try:
            # Check for existing table
            target_table = None
            try: 
                # Manual finding or use find() if trustworthy
                for t in pool.get_tables():
                    if t.name == target_table_name:
                        target_table = t
                        break
            except Exception: pass

            if target_table:
                print(f"Table {target_table_name} exists. Appending...")
                target_table.append(filtered_duplicates)
            else:
                print(f"Creating new table {target_table_name}...")
                pool.create_table(filtered_duplicates, target_table_name)
                
            print("Successfully appended data back to Celonis.")
        except Exception as e:
             logging.error(f"Push failed: {e}")
             print(f"Push failed: {e}")

    except Exception as e:
        print(f"Error appending data back to Celonis: {e}")

if __name__ == "__main__":
    main()
