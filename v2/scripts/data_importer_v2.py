# data_importer_v2.py

import csv
from datetime import datetime
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


class OptimizedDataImporter:
    def __init__(self, data_path):
        self._data_path = data_path
        # Memorije za lookup tabele radi brže transformacije
        self.stores = {}
        self.menu_items = {}
        self.payment_methods = {}
        self.vouchers = {}
        self.users = {}
        self.transaction_items_map = {}

    def _load_lookup_data(self):
        """Učitava sve statičke i dinamičke podatke u memoriju za brzi pristup."""
        print(" -> Loading lookup data into memory...")
        # Statički podaci
        self._load_csv_to_dict(f"{self._data_path}/stores.csv", self.stores, 'store_id', int)
        self._load_csv_to_dict(f"{self._data_path}/menu_items.csv", self.menu_items, 'item_id', int)
        self._load_csv_to_dict(f"{self._data_path}/payment_methods.csv", self.payment_methods, 'method_id', int)
        self._load_csv_to_dict(f"{self._data_path}/vouchers.csv", self.vouchers, 'voucher_id', int)

        # Dinamički podaci (korisnici i stavke transakcija)
        self._load_csv_to_dict(f"{self._data_path}/users_202307.csv", self.users, 'user_id', int)
        self._load_csv_to_dict(f"{self._data_path}/users_202401.csv", self.users, 'user_id', int, overwrite=False)
        self._load_transaction_items(f"{self._data_path}/transaction_items_202307.csv")
        self._load_transaction_items(f"{self._data_path}/transaction_items_202401.csv")
        print(" -> Lookup data loaded.")

    def _load_csv_to_dict(self, file_path, target_dict, key_field, key_type, overwrite=True):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = key_type(row[key_field])
                    if not overwrite and key in target_dict:
                        continue
                    target_dict[key] = row
        except FileNotFoundError:
            print(f"  !!! WARNING: Lookup file not found: {file_path}")
        except Exception as e:
            print(f"  !!! ERROR loading lookup file {file_path}: {e}")

    def _load_transaction_items(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    tx_id = row['transaction_id']
                    if tx_id not in self.transaction_items_map:
                        self.transaction_items_map[tx_id] = []
                    self.transaction_items_map[tx_id].append(row)
        except FileNotFoundError:
            print(f"  !!! WARNING: Transaction items file not found: {file_path}")
        except Exception as e:
            print(f"  !!! ERROR loading transaction items file {file_path}: {e}")

    def _get_age_group(self, birthdate_str):
        """Izračunava starosnu grupu na osnovu datuma rođenja."""
        if not birthdate_str:
            return "Nepoznato"
        birthdate = parser.parse(birthdate_str)
        age = 2024 - birthdate.year
        if age < 25: return "1) < 25"
        if 25 <= age < 35: return "2) 25-34"
        if 35 <= age < 45: return "3) 35-44"
        return "4) 45+"

    def _transform_transaction_v2(self, row):
        """Glavna funkcija transformacije koja primenjuje dizajn šablone."""
        # --- Osnovni podaci transakcije ---
        created_at_dt = parser.parse(row['created_at'])
        store_id = int(row['store_id'])
        payment_method_id = int(row['payment_method_id'])

        # --- Šablon proširene reference (Extended Reference) ---
        store_info = self.stores.get(store_id, {})
        payment_info = self.payment_methods.get(payment_method_id, {})

        user_doc = None
        user_id_raw = row.get('user_id')
        if user_id_raw and not pd.isna(pd.to_numeric(user_id_raw, errors='coerce')):
            user_id = int(float(user_id_raw))
            user_info = self.users.get(user_id)
            if user_info:
                user_doc = {
                    "id": user_id,
                    "gender": user_info.get('gender'),
                    "birthdate": parser.parse(user_info.get('birthdate')),
                    "age_group": self._get_age_group(user_info.get('birthdate'))
                }

        voucher_doc = None
        voucher_id_raw = row.get('voucher_id')
        if voucher_id_raw and not pd.isna(pd.to_numeric(voucher_id_raw, errors='coerce')):
            voucher_id = int(float(voucher_id_raw))
            voucher_info = self.vouchers.get(voucher_id)
            if voucher_info:
                voucher_doc = {
                    "id": voucher_id,
                    "discount_type": voucher_info.get('discount_type')
                }

        # --- Ugrađivanje stavki transakcije ---
        items_list = []
        transaction_items = self.transaction_items_map.get(row['transaction_id'], [])
        for item_row in transaction_items:
            menu_item_id = int(item_row['item_id'])
            menu_item_info = self.menu_items.get(menu_item_id, {})
            items_list.append({
                "menu_item_id": menu_item_id,
                "name": menu_item_info.get('item_name'),
                "category": menu_item_info.get('category'),
                "quantity": int(item_row['quantity']),
                "unit_price": to_decimal128(item_row['unit_price']),
                "subtotal": to_decimal128(item_row['subtotal'])
            })

        # --- Kreiranje finalnog dokumenta ---
        return {
            "_id": row['transaction_id'],
            "created_at": created_at_dt,
            "amounts": {
                "original": to_decimal128(row['original_amount']),
                "discount": to_decimal128(row['discount_applied']),
                "final": to_decimal128(row['final_amount'])
            },
            # Šablon proračunavanja (Computed Pattern)
            "createdAtDetails": {
                "year": created_at_dt.year,
                "month": created_at_dt.month,
                "dayOfWeek": created_at_dt.isoweekday(),  # 1=Ponedeljak, 7=Nedelja
                "hour": created_at_dt.hour
            },
            # Šablon proširene reference
            "store": {
                "id": store_id,
                "name": store_info.get('store_name'),
                "city": store_info.get('city')
            },
            "payment_method": {
                "id": payment_method_id,
                "name": payment_info.get('method_name')
            },
            "user": user_doc,
            "voucher": voucher_doc,
            # Ugrađene stavke
            "items": items_list,
            "item_count": len(items_list)
        }

    def import_optimized_transactions(self, db, period_suffix):
        """Uvozi transakcije koristeći V2 šemu."""
        collection_name = "transactions"
        file_name = f"transactions_{period_suffix}.csv"
        full_file_path = f"{self._data_path}/{file_name}"

        print(f"  -> Importing '{file_name}' into collection '{collection_name}' (Optimized V2 Schema)...")
        documents = []
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    documents.append(self._transform_transaction_v2(row))

            print(f"  -> Imported {len(documents)} documents into '{collection_name}'.")
        except FileNotFoundError:
            print(f"  !!! ERROR: File not found: {full_file_path}")
        except Exception as e:
            print(f"  !!! ERROR while processing file {file_name}: {e}")