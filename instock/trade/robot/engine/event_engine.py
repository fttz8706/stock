#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from collections import defaultdict
from queue import Queue, Empty
from threading import Thread, RLock
import logging

__author__ = 'myh '
__date__ = '2023/4/10 '


class Event:
    def __init__(self, event_type, data=None):
        self.event_type = event_type
        self.data = data


class EventEngine:
    """事件驱动引擎"""

    def __init__(self):
        """初始化事件引擎"""
        # 事件队列
        self.__queue = Queue()

        # 事件引擎开关
        self.__active = False

        # 事件引擎处理线程
        self.__thread = Thread(target=self.__run, name="EventEngine.__thread")

        # 事件字典，key 为时间， value 为对应监听事件函数的列表
        self.__handlers = defaultdict(list)
        self.__lock = RLock()

    def __run(self):
        """启动引擎"""
        while self.__active:
            try:
                event = self.__queue.get(block=True, timeout=1)
                self.__process(event)
            except Empty:
                pass

    def __process(self, event):
        """事件处理"""
        with self.__lock:
            handlers = tuple(self.__handlers.get(event.event_type, ()))
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logging.exception("Strategy event handler failed")

    def start(self):
        """引擎启动"""
        self.__active = True
        self.__thread.start()

    def stop(self):
        """停止引擎"""
        self.__active = False
        self.__thread.join()

    def register(self, event_type, handler):
        """注册事件处理函数监听"""
        with self.__lock:
            if handler not in self.__handlers[event_type]:
                self.__handlers[event_type].append(handler)

    def unregister(self, event_type, handler):
        with self.__lock:
            handlers = self.__handlers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)
            if not handlers:
                self.__handlers.pop(event_type, None)

    def put(self, event):
        self.__queue.put(event)

    @property
    def queue_size(self):
        return self.__queue.qsize()
