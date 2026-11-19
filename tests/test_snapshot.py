import os
import sqlite3
import unittest
from unittest.mock import patch
from instock.web import quote_snapshot
from instock.core import tablestructure as tbs


class SnapshotTest(unittest.TestCase):
    def test_opt_in_only_for_daily_page(self):
        with patch.dict(os.environ, {"INSTOCK_DAILY_SNAPSHOT": "1"}):
            self.assertTrue(quote_snapshot.enabled("cn_stock_spot"))
            self.assertFalse(quote_snapshot.enabled("cn_stock_selection"))
        with patch.dict(os.environ, {"INSTOCK_DAILY_SNAPSHOT": "0"}):
            self.assertFalse(quote_snapshot.enabled("cn_stock_spot"))

    def test_projection_preserves_source_values_and_missing_fields(self):
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        cols = tbs.TABLE_CN_STOCK_SELECTION["columns"]
        db.execute("CREATE TABLE source (" + ",".join(f"`{k}`" for k in cols) + ")")
        db.execute("INSERT INTO source (date,code,new_price,volume) VALUES (?,?,?,?)",
                   ("2026-11-19", "000001", 12.04, 123456))
        projection, missing = quote_snapshot.projection()
        row = dict(db.execute("SELECT " + projection + " FROM source").fetchone())
        self.assertEqual(row["date"], "2026-11-19")
        self.assertEqual(row["code"], "000001")
        self.assertEqual(row["new_price"], 12.04)
        self.assertIsNone(row["volume"])
        self.assertIsNone(row["open_price"])
        self.assertIn("成交量", missing)
        self.assertEqual(set(row), set(tbs.TABLE_CN_STOCK_SPOT["columns"]))
        db.close()


if __name__ == "__main__":
    unittest.main()
