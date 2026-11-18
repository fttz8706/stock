"""Render untrusted stock labels as text, never executable markup."""
from html import escape
from instock.lib.validation import stock_code


def quote_link(code, name):
    stock_code(code)
    market_code = ('SH' if code.startswith('6') else 'SZ') + code
    return (f'<a href="https://quote.eastmoney.com/{market_code}.html" '
            f'target="_blank" rel="noopener noreferrer">{code}{escape(name or "", quote=True)}行情</a>')
