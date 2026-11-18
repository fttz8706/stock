"""Validation shared by HTTP handlers and local cache readers."""
import datetime
import re


def stock_code(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{6}", value):
        raise ValueError("股票代码必须是六位数字")
    return value


def trade_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("日期格式必须为 YYYY-MM-DD")
    datetime.date.fromisoformat(value)
    return value
