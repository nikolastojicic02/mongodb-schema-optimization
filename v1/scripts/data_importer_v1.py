# data_importer_v1.py

import csv
from dateutil import parser
from decimal import InvalidOperation
import pandas as pd
from bson.decimal128 import Decimal128


def to_decimal128(value):
    """Safely converts a string or number to a BSON Decimal128."""
    try:
        return Decimal128(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal128("0.0")


class DataImporter:
    def __init__(self, data_path):
        self._data_path = data_path

    def _import_generic(self, db, collection_name, file_name, transform_func):
        """Generic function to import data from a CSV file."""
        full_file_path = f"{self._data_path}/{file_name}"
        print(f"  -> Importing '{file_name}' into collection '{collection_name}'...")
        documents = []
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    documents.append(transform_func(row))

                db[collection_name].insert_many(documents, ordered=False)
            print(f"  -> Imported {len(documents)} documents.")
        except FileNotFoundError:
            print(f"  !!! ERROR: File not found: {full_file_path}")
        except Exception as e:
            print(f"  !!! ERROR while processing file {file_name}: {e}")

    def _transform_store(self, row):
        return {"_id": int(row['store_id']), "name": row['store_name'],
                "address": {"street": row['street'], "city": row['city'], "postal_code": row['postal_code'],
                            "state": row['state']},
                "location": {"type": "Point", "coordinates": [float(row['longitude']), float(row['latitude'])]}}

    def _transform_menu_item(self, row):
        return {"_id": int(row['item_id']), "name": row['item_name'], "category": row['category'],
                "price": to_decimal128(row['price'])}

    def _transform_payment_method(self, row):
        return {"_id": int(row['method_id']), "method_name": row['method_name'], "category": row['category']}

    def _transform_voucher(self, row):
        return {"_id": int(row['voucher_id']), "voucher_code": row['voucher_code'],
                "discount_type": row['discount_type'], "discount_value": to_decimal128(row['discount_value']),
                "valid_from": parser.parse(row['valid_from']), "valid_to": parser.parse(row['valid_to'])}

    def _transform_user(self, row):
        return {"_id": int(row['user_id']), "gender": row['gender'], "birthdate": parser.parse(row['birthdate']),
                "registered_at": parser.parse(row['registered_at'])}

    def _transform_transaction(self, row):
        user_id = int(float(row['user_id'])) if row.get('user_id') and not pd.isna(
            pd.to_numeric(row['user_id'], errors='coerce')) else None
        voucher_id = int(float(row['voucher_id'])) if row.get('voucher_id') and not pd.isna(
            pd.to_numeric(row['voucher_id'], errors='coerce')) else None
        return {"_id": row['transaction_id'], "store_id": int(row['store_id']), "user_id": user_id,
                "payment_method_id": int(row['payment_method_id']), "voucher_id": voucher_id,
                "amounts": {"original": to_decimal128(row['original_amount']),
                            "discount": to_decimal128(row['discount_applied']),
                            "final": to_decimal128(row['final_amount'])}, "created_at": parser.parse(row['created_at'])}

    def _transform_transaction_item(self, row):
        return {"transaction_id": row['transaction_id'], "menu_item_id": int(row['item_id']),
                "quantity": int(row['quantity']), "unit_price": to_decimal128(row['unit_price']),
                "subtotal": to_decimal128(row['subtotal'])}

    # --- Main methods ---

    def import_static_collections(self, db):
        print("\n--- Starting import of static collections (lookup tables) ---")
        self._import_generic(db, "stores", "stores.csv", self._transform_store)
        self._import_generic(db, "menu_items", "menu_items.csv", self._transform_menu_item)
        self._import_generic(db, "payment_methods", "payment_methods.csv", self._transform_payment_method)
        self._import_generic(db, "vouchers", "vouchers.csv", self._transform_voucher)

    def import_dynamic_collections(self, db, period_suffix):
        print(f"\n--- Starting import of data for period: {period_suffix} ---")
        self._import_generic(db, "users", f"users_{period_suffix}.csv", self._transform_user)
        self._import_generic(db, "transactions", f"transactions_{period_suffix}.csv", self._transform_transaction)
        self._import_generic(db, "transaction_items", f"transaction_items_{period_suffix}.csv",
                             self._transform_transaction_item)