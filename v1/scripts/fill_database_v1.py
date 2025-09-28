# fill_database_v1.py

import pymongo
from data_importer_v1 import DataImporter

# --- Connection and Data Parameters ---
MONGO_URL = "mongodb://localhost:27017/"
DB_NAME_V1 = "coffee_db_v1"
DATA_PATH = "../../data"

if __name__ == '__main__':
    print("--- STARTING DATABASE POPULATION (INITIAL SCHEMA v1) ---")

    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        client.server_info()
        print("Connection to MongoDB server successful.")

        # Drop the existing database for a clean import
        print(f"Dropping existing database '{DB_NAME_V1}' if it exists...")
        client.drop_database(DB_NAME_V1)

        db = client[DB_NAME_V1]

        importer = DataImporter(DATA_PATH)

        # 1. Import static collections
        importer.import_static_collections(db)

        # 2. Import data for JULY 2023
        importer.import_dynamic_collections(db, period_suffix="202307")

        # 3. Import data for JANUARY 2024
        importer.import_dynamic_collections(db, period_suffix="202401")

        print("\n--- ALL DATA HAS BEEN SUCCESSFULLY IMPORTED ACCORDING TO THE INITIAL SCHEMA! ---")
        print(f"Database '{DB_NAME_V1}' is ready for analysis.")

    except pymongo.errors.ServerSelectionTimeoutError as err:
        print(f"!!! ERROR: Could not connect to the MongoDB server. Is it running at {MONGO_URL}?")
    except Exception as e:
        print(f"!!! An unexpected error occurred: {e}")
    finally:
        if 'client' in locals():
            client.close()
            print("Connection to the MongoDB server has been closed.")