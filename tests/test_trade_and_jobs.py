import datetime
import sys
import threading
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock
import pytest


def test_reloads_keep_one_callback_and_one_moment(monkeypatch,load_module):
    fake_time=ModuleType('instock.lib.trade_time')
    fake_time.is_trade_date=lambda date: True
    fake_time.is_tradetime=lambda value: True
    fake_time.get_next_trade_date=lambda date: date+datetime.timedelta(days=1)
    monkeypatch.setitem(sys.modules,'instock.lib.trade_time',fake_time)
    monkeypatch.setitem(sys.modules,'easytrader',ModuleType('easytrader'))
    clock_module=load_module('instock/trade/robot/engine/clock_engine.py','isolated_clock')
    monkeypatch.setitem(sys.modules,'instock.trade.robot.engine.clock_engine',clock_module)
    module=load_module('instock/trade/robot/engine/main_engine.py','isolated_main')
    template=load_module('instock/trade/robot/infrastructure/strategy_template.py','isolated_template')
    calls=[]
    class Strategy(template.StrategyTemplate):
        name='demo'
        def init(self):
            self.clock_engine.register_moment('demo',datetime.time(23,59,tzinfo=datetime.timezone.utc))
        def clock(self,event): calls.append(self)
    imported=SimpleNamespace(Strategy=Strategy)
    monkeypatch.setattr(module.importlib,'import_module',lambda *a:imported)
    monkeypatch.setattr(module.importlib,'reload',lambda m:m)
    mtime=[1]
    monkeypatch.setattr(module.os.path,'getmtime',lambda p:mtime[0])
    monkeypatch.setattr(module.signal, 'signal', lambda *args: None)
    engine=module.MainEngine(log_handler=Mock())
    baseline=len(engine.clock_engine.clock_moment_handlers)
    old_callback=None
    for version in range(1,5):
        mtime[0]=version
        engine.load(None,'demo.py')
        assert len(engine.strategy_list) == 1
        assert len(engine._listeners) == 1
        assert len(engine.clock_engine.clock_moment_handlers) == baseline+1
        callback=next(iter(engine._listeners.values()))
        callback(None)
        if old_callback is not None: old_callback(None)
        assert len(calls) == version
        old_callback=callback


def test_task_chain_and_failure(monkeypatch,load_module):
    names=['init_job','basic_data_daily_job','basic_data_other_daily_job',
           'basic_data_after_close_daily_job','indicators_data_daily_job','strategy_data_daily_job',
           'backtest_data_daily_job','klinepattern_data_daily_job','selection_data_daily_job']
    calls=[]
    for name in names:
        mod=ModuleType(name)
        mod.main=lambda name=name:calls.append(name)
        monkeypatch.setitem(sys.modules,name,mod)
    module=load_module('instock/job/execute_daily_job.py','isolated_job')
    module.main()
    assert sorted(calls)==sorted(names)
    assert calls.index('backtest_data_daily_job') > max(calls.index(name) for name in
        ['indicators_data_daily_job','strategy_data_daily_job','klinepattern_data_daily_job'])
    calls.clear()
    def fail():raise RuntimeError('worker failed')
    module.gdj.main=fail
    with pytest.raises(RuntimeError):module.main()
    assert 'backtest_data_daily_job' not in calls


def test_batch_errors_propagate(monkeypatch,load_module):
    fake=ModuleType('instock.lib.trade_time');fake.is_trade_date=lambda date:True
    monkeypatch.setitem(sys.modules,'instock.lib.trade_time',fake)
    module=load_module('instock/lib/run_template.py','isolated_batch')
    monkeypatch.setattr(module.time,'sleep',lambda seconds:None)
    monkeypatch.setattr(module.sys,'argv',['job.py','2026-11-16','2026-11-17'])
    calls=[]
    module.run_with_args(lambda date:calls.append(date))
    assert sorted(calls)==[datetime.date(2026,11,16),datetime.date(2026,11,17)]
    def fail(date):raise RuntimeError('failed')
    with pytest.raises(RuntimeError):module.run_with_args(fail)


def test_failed_strategy_initialization_cleans_clock(load_module):
    template=load_module('instock/trade/robot/infrastructure/strategy_template.py','failed_template')
    handle=object()
    clock=Mock();clock.register_moment.return_value=handle
    class Broken(template.StrategyTemplate):
        def init(self):
            self.clock_engine.register_moment('broken',None)
            raise RuntimeError('init failed')
    with pytest.raises(RuntimeError):Broken(None,Mock(),SimpleNamespace(clock_engine=clock))
    clock.unregister_moment.assert_called_once_with(handle)
