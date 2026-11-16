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

    def test_customer_email_is_normalized_and_reused(self):
        customer, created = storage.get_or_create_customer(
            "  SAMPLE@EXAMPLE.COM ", "Sample Customer"
        )
        repeated, created_again = storage.get_or_create_customer(
            "sample@example.com", "A different name"
        )

        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(customer["email"], "sample@example.com")
        self.assertEqual(repeated["name"], "Sample Customer")

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

    def test_csv_has_a_header_and_round_trips_values(self):
        storage.get_or_create_customer("sample@example.com", "Sample Customer")

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
