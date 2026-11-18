import os
import time
import pandas as pd
import pytest
from instock.lib.history_cache import history_cache


def test_cache_bypass_range_and_corruption(tmp_path):
    calls = []
    def fetch():
        calls.append(1)
        return pd.DataFrame({'date': ['2026-11-18'], 'close': [len(calls) + .123]})
    def get(enabled=True, end=None):
        return history_cache(tmp_path, '600000', '20231118', end, 'qfq', enabled, fetch)
    first = get()
    pd.testing.assert_frame_equal(get(), first)
    assert len(calls) == 1
    assert get(False).close.iloc[0] == 2.123
    assert get(end='20261117').close.iloc[0] == 3.123
    target = next(tmp_path.rglob('*latest.json.gz'))
    target.write_bytes(b'corrupt')
    assert get().close.iloc[0] == 4.123
    os.utime(target, (time.time() - 172800,) * 2)
    assert get().close.iloc[0] == 5.123


def test_legacy_pickle_ignored(tmp_path):
    directory = tmp_path / '202311' / '20231118'
    directory.mkdir(parents=True)
    (directory / '600000qfq.gzip.pickle').write_bytes(b'never deserialize')
    result = history_cache(tmp_path, '600000', '20231118', None, 'qfq', True,
                           lambda: pd.DataFrame({'close': [1]}))
    assert result.close.iloc[0] == 1


@pytest.mark.parametrize('code,start,end,adjust', [('../x','20231118',None,'qfq'),
    ('600000','../x',None,'qfq'), ('600000','20231118','20261301','qfq'),
    ('600000','20231118',None,'../x')])
def test_invalid_cache_paths(tmp_path,code,start,end,adjust):
    with pytest.raises(ValueError):
        history_cache(tmp_path,code,start,end,adjust,True,lambda: pytest.fail('fetch called'))


def test_symlink_escape(tmp_path):
    root = tmp_path/'cache'; root.mkdir()
    outside = tmp_path/'outside'; outside.mkdir()
    (root/'202311').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        history_cache(root,'600000','20231118',None,'qfq',True,lambda: None)
