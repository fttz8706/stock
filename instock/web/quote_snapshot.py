"""Explicit, read-only display projection of the daily selection snapshot."""
import os
from instock.core import tablestructure as tbs


def enabled(table):
    return table == "cn_stock_spot" and os.environ.get("INSTOCK_DAILY_SNAPSHOT") == "1"


def projection():
    spot = tbs.TABLE_CN_STOCK_SPOT["columns"]
    selection = tbs.TABLE_CN_STOCK_SELECTION["columns"]
    # Volume units have not been verified across providers' endpoints.
    shared = set(spot) & set(selection) - {"volume"}
    columns = [f"`{key}`" if key in shared else f"NULL AS `{key}`" for key in spot]
    missing = [value["cn"] for key, value in spot.items() if key not in shared]
    return ",".join(columns), "、".join(missing)
