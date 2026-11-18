#!/usr/bin/env python3
# -*- coding: utf-8 -*-


__author__ = 'myh '
__date__ = '2023/4/10 '


class StrategyTemplate:
    name = 'DefaultStrategyTemplate'

    def __init__(self, user, log_handler, main_engine):
        self.user = user
        self.main_engine = main_engine
        self.clock_engine = StrategyClock(main_engine.clock_engine)
        # 优先使用自定义 log 句柄, 否则使用主引擎日志句柄
        self.log = self.log_handler() or log_handler
        try:
            self.init()
        except Exception:
            self.clock_engine.cleanup()
            raise

    def init(self):
        # 进行相关的初始化操作
        pass

    def strategy(self):
        pass

    def clock(self, event):
        pass

    def log_handler(self):
        """
        优先使用在此自定义 log 句柄, 否则返回None, 并使用主引擎日志句柄
        :return: log_handler or None
        """
        return None

    def shutdown(self):
        """
        关闭进程前调用该函数
        :return:
        """
        pass


class StrategyClock:
    """Keep ownership of moment handlers so hot reload can remove them."""
    def __init__(self, engine):
        self.engine = engine
        self.moments = []

    def __getattr__(self, name):
        return getattr(self.engine, name)

    def register_moment(self, *args, **kwargs):
        handler = self.engine.register_moment(*args, **kwargs)
        self.moments.append(handler)
        return handler

    def cleanup(self):
        for handler in self.moments:
            self.engine.unregister_moment(handler)
        self.moments.clear()
