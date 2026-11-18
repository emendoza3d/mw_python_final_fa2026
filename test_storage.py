import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import storage
from readmenu import read_menu


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.customers_file = Path(self.temp_dir.name) / "customers.csv"
        self.orders_file = Path(self.temp_dir.name) / "orders.csv"
        self.customer_files = patch.object(storage, "CUSTOMERS_FILE", self.customers_file)
        self.order_files = patch.object(storage, "ORDERS_FILE", self.orders_file)
        self.customer_files.start()
        self.order_files.start()
        self.addCleanup(self.customer_files.stop)
        self.addCleanup(self.order_files.stop)

    def test_customer_password_is_hashed_and_email_is_normalized(self):
        customer = storage.register_customer(
            "  SAMPLE@EXAMPLE.COM ", "Sample Customer", "secure-passphrase"
        )

        self.assertEqual(customer["email"], "sample@example.com")
        self.assertNotEqual(customer["password_hash"], "secure-passphrase")
        self.assertTrue(
            customer["password_hash"].startswith("pbkdf2_sha256$")
        )
        self.assertEqual(
            storage.authenticate_customer("SAMPLE@example.com", "secure-passphrase")[
                "name"
            ],
            "Sample Customer",
        )
        self.assertIsNone(
            storage.authenticate_customer("sample@example.com", "wrong-password")
        )

    def test_registration_rejects_existing_legacy_profile_and_short_password(self):
        self.customers_file.write_text(
            "email,name,created_at\n"
            "legacy@example.com,Legacy User,2025-01-01T00:00:00+00:00\n",
            encoding="utf-8",
        )

        with self.assertRaises(ValueError):
            storage.register_customer(
                "legacy@example.com", "Legacy User", "secure-passphrase"
            )
        with self.assertRaises(ValueError):
            storage.register_customer("new@example.com", "New User", "short")
        self.assertIsNone(
            storage.authenticate_customer("legacy@example.com", "any-password")
        )

    def test_registration_preserves_legacy_profiles_when_migrating_csv(self):
        self.customers_file.write_text(
            "email,name,created_at\n"
            "legacy@example.com,Legacy User,2025-01-01T00:00:00+00:00\n",
            encoding="utf-8",
        )
        storage.register_customer(
            "new@example.com", "New User", "secure-passphrase"
        )

        with self.customers_file.open("r", newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["email"], "legacy@example.com")
        self.assertEqual(rows[0]["password_hash"], "")
        self.assertTrue(rows[1]["password_hash"])

    def test_orders_are_saved_and_filtered_by_customer(self):
        sample_order = storage.create_order(
            "SAMPLE@example.com",
            {
                "shape": "oval",
                "style": "halo",
                "metal": "gold",
                "diamond": "lab",
            },
        )
        storage.create_order(
            "other@example.com",
            {
                "shape": "round",
                "style": "solitaire",
                "metal": "platinum",
                "diamond": "natural",
            },
        )

        orders = storage.get_customer_orders("sample@example.com")
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["order_id"], sample_order["order_id"])
        self.assertEqual(orders[0]["shape"], "oval")

    def test_order_can_be_updated_only_by_its_owner(self):
        sample_order = storage.create_order(
            "sample@example.com",
            {
                "shape": "oval",
                "style": "halo",
                "metal": "gold",
                "diamond": "lab",
            },
        )
        changes = {
            "shape": "round",
            "style": "solitaire",
            "metal": "platinum",
            "diamond": "natural",
        }

        self.assertFalse(
            storage.update_order(sample_order["order_id"], "other@example.com", changes)
        )
        self.assertTrue(
            storage.update_order(sample_order["order_id"], "sample@example.com", changes)
        )
        updated = storage.get_customer_orders("sample@example.com")[0]
        self.assertEqual(updated["shape"], "round")
        self.assertEqual(updated["style"], "solitaire")

    def test_order_can_be_finalized_only_by_its_owner_and_then_locked(self):
        order = storage.create_order(
            "sample@example.com",
            {
                "shape": "oval",
                "style": "halo",
                "metal": "gold",
                "diamond": "lab",
            },
        )
        selections = {
            "shape": "round",
            "style": "solitaire",
            "metal": "platinum",
            "diamond": "natural",
        }

        self.assertFalse(
            storage.finalize_order(order["order_id"], "other@example.com")
        )
        self.assertTrue(storage.finalize_order(order["order_id"], "sample@example.com"))
        self.assertFalse(storage.finalize_order(order["order_id"], "sample@example.com"))
        self.assertFalse(
            storage.update_order(order["order_id"], "sample@example.com", selections)
        )
        finalized = storage.get_customer_orders("sample@example.com")[0]
        self.assertEqual(finalized["status"], "finalized")
        self.assertEqual(finalized["shape"], "oval")

    def test_legacy_orders_default_to_editable_concepts(self):
        self.orders_file.write_text(
            "order_id,customer_email,created_at,shape,style,metal,diamond\n"
            "LEGACY1234,sample@example.com,2025-01-01T00:00:00+00:00,"
            "oval,halo,gold,lab\n",
            encoding="utf-8",
        )

        orders = storage.get_customer_orders("sample@example.com")

        self.assertEqual(orders[0]["status"], "concept")
        self.assertTrue(
            storage.update_order(
                "LEGACY1234",
                "sample@example.com",
                {
                    "shape": "round",
                    "style": "solitaire",
                    "metal": "platinum",
                    "diamond": "natural",
                },
            )
        )

    def test_csv_has_a_header_and_round_trips_values(self):
        storage.register_customer(
            "sample@example.com", "Sample Customer", "secure-passphrase"
        )

        with self.customers_file.open("r", newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Sample Customer")

    def test_menu_parser_handles_colons_and_blank_lines(self):
        menu_file = self.customers_file.parent / "test-menu.txt"
        menu_file.write_text(
            " SHAPE : round, oval\n\nSTYLE : three:stone, halo\n",
            encoding="utf-8",
        )

        self.assertEqual(
            read_menu(menu_file),
            {"SHAPE": "round, oval", "STYLE": "three:stone, halo"},
        )


if __name__ == "__main__":
    unittest.main()
