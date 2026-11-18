"""Safe, atomic on-disk historical quote cache. Legacy pickle files are ignored."""
import datetime
import os
from pathlib import Path
import tempfile
import pandas as pd
from instock.lib.validation import stock_code


def history_cache(root, code, start, end, adjust, enabled, fetch):
    stock_code(code)
    if start is None:
        raise ValueError("Start date is required")
    for value in (start, end):
        if value is not None:
            if not isinstance(value, str) or len(value) != 8 or not value.isascii() or not value.isdigit():
                raise ValueError("Expected YYYYMMDD")
            datetime.datetime.strptime(value, "%Y%m%d")
    if adjust not in ("", "qfq", "hfq"):
        raise ValueError("Invalid adjustment")
    root = Path(root).resolve()
    directory = root / start[:6] / start
    target = directory / f"{code}_{adjust or 'none'}_{end or 'latest'}.json.gz"
    # Reject traversal via pre-existing symlinks as well as malformed input.
    if not target.resolve().is_relative_to(root):
        raise ValueError("Cache path outside configured directory")
    if enabled and target.is_file():
        modified = datetime.date.fromtimestamp(target.stat().st_mtime)
        if modified == datetime.date.today():
            try:
                return pd.read_json(target, orient="table", compression="gzip", convert_dates=False)
            except (ValueError, OSError, EOFError):
                pass  # Re-fetch corrupt or obsolete cache files.
    data = fetch()
    if data is None or data.empty or not enabled:
        return data
    directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, suffix=".json.gz", delete=False) as file:
            temporary = file.name
        data.to_json(temporary, orient="table", compression="gzip", double_precision=15)
        os.replace(temporary, target)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
    return data
