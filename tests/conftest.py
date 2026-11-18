import importlib.util
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import instock.core
import instock.lib
import instock.core.kline

@pytest.fixture
def load_module():
    def load(path, name):
        spec = importlib.util.spec_from_file_location(name, ROOT / path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return load
