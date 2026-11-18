import datetime
import sys
from types import ModuleType
from unittest.mock import Mock
import pandas as pd
import pytest
import requests


def test_each_date_gets_own_snapshot(monkeypatch,load_module):
    fake=ModuleType('instock.core.stockfetch')
    fake.fetch_stocks=lambda date: date
    monkeypatch.setitem(sys.modules,'instock.core.stockfetch',fake)
    monkeypatch.setitem(sys.modules,'instock.core.tablestructure',ModuleType('instock.core.tablestructure'))
    monkeypatch.setitem(sys.modules,'instock.lib.trade_time',ModuleType('instock.lib.trade_time'))
    module=load_module('instock/core/singleton_stock.py','isolated_stock')
    dates=[datetime.date(2026,11,16),datetime.date(2026,11,17)]
    assert [module.stock_data(date).get_data() for date in dates] == dates
    fake.fetch_stocks=lambda date: None
    assert module.stock_hist_data().get_data() is None
    assert module.stock_hist_data(stocks=[]).get_data() is None


def test_cookie_domain_and_https(monkeypatch,load_module):
    fake=ModuleType('instock.core.singleton_proxy');fake.proxys=lambda:None
    monkeypatch.setitem(sys.modules,'instock.core.singleton_proxy',fake)
    module=load_module('instock/core/eastmoney_fetcher.py','isolated_fetcher')
    session=requests.Session()
    module.eastmoney_fetcher._set_cookie(session,'a=one; b=two')
    def cookie(url): return session.prepare_request(requests.Request('GET',url)).headers.get('Cookie','')
    assert cookie('https://push2.eastmoney.com/x') == 'a=one; b=two'
    assert cookie('http://push2.eastmoney.com/x') == ''
    assert cookie('https://example.com/x') == ''
    for url in ['http://push2.eastmoney.com','https://eastmoney.com.evil.test']:
        with pytest.raises(ValueError): module.eastmoney_fetcher._validate_url(url)


def test_database_parameterizes_and_redacts(monkeypatch,load_module,caplog):
    monkeypatch.setenv('db_password','private@:/password')
    module=load_module('instock/lib/database.py','isolated_db')
    assert module.MYSQL_CONN_URL.password == 'private@:/password'
    cursor=Mock(); conn=Mock()
    from unittest.mock import MagicMock
    conn=MagicMock();conn.__enter__.return_value=conn
    conn.cursor.return_value.__enter__.return_value=cursor
    monkeypatch.setattr(module,'get_connection',lambda:conn)
    payload="x' OR '1'='1"
    module.update_db_from_df(pd.DataFrame([{'code':'600000','value':payload}]),'quotes',('code',))
    sql,params=cursor.execute.call_args.args
    assert payload not in sql and params == (payload,'600000')
    with pytest.raises(ValueError):module.update_db_from_df(pd.DataFrame([{'code':'1','value':2}]),'bad`table',('code',))


def test_quote_label_is_text():
    from instock.web.html_utils import quote_link
    from html.parser import HTMLParser
    class Elements(HTMLParser):
        def __init__(self): super().__init__(); self.tags=[]
        def handle_starttag(self, tag, attrs): self.tags.append(tag)
    result=quote_link('600000','<img src=x onerror=alert(1)>')
    parser=Elements();parser.feed(result)
    assert parser.tags == ['a']
    assert '&lt;img' in result
    with pytest.raises(ValueError):quote_link('600000\" onclick=bad','name')


def test_fetch_preserves_explicit_cache_bypass(monkeypatch,load_module):
    import os
    import numpy as np
    import instock.core.crawling
    names=['trade_date_hist','fund_etf_em','stock_selection','stock_lhb_em','stock_lhb_sina',
           'stock_dzjy_em','stock_hist_em','stock_fund_em','stock_fhps_em','stock_chip_race','stock_limitup_reason']
    for name in names:
        full='instock.core.crawling.'+name
        monkeypatch.setitem(sys.modules,full,ModuleType(full))
    fake_time=ModuleType('instock.lib.trade_time')
    fake_time.get_trade_hist_interval=lambda date:('20231118',True)
    monkeypatch.setitem(sys.modules,'instock.lib.trade_time',fake_time)
    monkeypatch.setitem(sys.modules,'instock.core.tablestructure',ModuleType('instock.core.tablestructure'))
    talib=ModuleType('talib');talib.ROC=lambda data,n:np.zeros(len(data))
    monkeypatch.setitem(sys.modules,'talib',talib)
    monkeypatch.setattr(os,'makedirs',lambda *args,**kwargs:None)
    module=load_module('instock/core/stockfetch.py','isolated_stockfetch')
    cache=Mock(return_value=pd.DataFrame({'close':[10.0],'volume':[1.0]}))
    monkeypatch.setattr(module,'stock_hist_cache',cache)
    module.fetch_stock_hist(('2026-11-18','600000'),is_cache=False)
    assert cache.call_args.args[3] is False
