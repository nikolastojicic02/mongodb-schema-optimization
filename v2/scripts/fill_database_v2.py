# fill_database_v2.py

import pymongo
from data_importer_v2 import OptimizedDataImporter

# --- Connection and Data Parameters ---
MONGO_URL = "mongodb://localhost:27017/"
DB_NAME_V2 = "coffee_db_v2"  # Novi naziv baze za V2 šemu
DATA_PATH = "../../data"

if __name__ == '__main__':
    print("--- STARTING DATABASE POPULATION (OPTIMIZED SCHEMA v2) ---")

    try:
        # --- 1. Povezivanje na MongoDB ---
        client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        client.server_info()
        print("Connection to MongoDB server successful.")

        # --- 2. Brisanje postojeće V2 baze za čist uvoz ---
        print(f"Dropping existing database '{DB_NAME_V2}' if it exists...")
        client.drop_database(DB_NAME_V2)
        db = client[DB_NAME_V2]
        print(f"Database '{DB_NAME_V2}' created.")

        # --- 3. Uvoz podataka ---
        importer = OptimizedDataImporter(DATA_PATH)

        # Prvo, učitavamo sve potrebne podatke u memoriju
        importer._load_lookup_data()

        # Zatim, uvozimo transakcije sa novom, denormalizovanom šemom
        importer.import_optimized_transactions(db, period_suffix="202307")
        importer.import_optimized_transactions(db, period_suffix="202401")

        print("\n--- ALL DATA HAS BEEN SUCCESSFULLY IMPORTED ACCORDING TO THE OPTIMIZED SCHEMA! ---")

        # --- 4. Kreiranje Indeksa ---
        print("\n--- Creating strategic indexes for V2 schema... ---")

        transactions_collection = db["transactions"]

        transactions_collection.create_index(
            [("created_at", pymongo.ASCENDING), ("amounts.final", pymongo.DESCENDING)],
            name="idx_date_finalAmount"
        )
        print("  -> Created compound index for date range and sorting by final amount.")


        transactions_collection.create_index([("store.id", pymongo.ASCENDING)], name="idx_store_id")
        print("  -> Created index for grouping by store.")

        transactions_collection.create_index([("user.id", pymongo.ASCENDING)], sparse=True, name="idx_user_id_sparse")
        print("  -> Created sparse index for registered user analysis.")

        transactions_collection.create_index([("voucher.id", pymongo.ASCENDING)], sparse=True,
                                             name="idx_voucher_id_sparse")
        print("  -> Created sparse index for voucher analysis.")

        transactions_collection.create_index([("items.category", pymongo.ASCENDING)],
                                             name="idx_items_category_multikey")
        print("  -> Created multikey index for product category analysis.")

        transactions_collection.create_index([("createdAtDetails.dayOfWeek", pymongo.ASCENDING)], name="idx_dayOfWeek")
        print("  -> Created index for day-of-week analysis.")

        print("--- ALL INDEXES CREATED SUCCESSFULLY! ---")
        print(f"Database '{DB_NAME_V2}' is ready for optimized analysis.")

    except pymongo.errors.ServerSelectionTimeoutError as err:
        print(f"!!! ERROR: Could not connect to the MongoDB server. Is it running at {MONGO_URL}?")
    except Exception as e:
        print(f"!!! An unexpected error occurred: {e}")
    finally:
        if 'client' in locals():
            client.close()
            print("\nConnection to the MongoDB server has been closed.")