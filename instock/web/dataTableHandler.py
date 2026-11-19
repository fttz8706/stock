#!/usr/local/bin/python3
# -*- coding: utf-8 -*-


import json
from abc import ABC
from tornado import gen
# import logging
import datetime
import tornado.web
from instock.lib.validation import trade_date
import instock.lib.trade_time as trd
import instock.core.singleton_stock_web_module_data as sswmd
import instock.web.base as webBase
from instock.web import quote_snapshot

__author__ = 'myh '
__date__ = '2023/3/10 '


class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, bytes):
            return "是" if ord(obj) == 1 else "否"
        elif isinstance(obj, datetime.date):
            delta = datetime.datetime.combine(obj, datetime.time.min) - datetime.datetime(1899, 12, 30)
            return f'/OADate({float(delta.days) + (float(delta.seconds) / 86400)})/'  # 86,400 seconds in day
            # return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)


# 获得页面数据。
class GetStockHtmlHandler(webBase.BaseHandler, ABC):
    @gen.coroutine
    def get(self):
        name = self.get_argument("table_name", default=None, strip=False)
        try:
            web_module_data = sswmd.stock_web_module_data().get_data(name)
        except KeyError:
            raise tornado.web.HTTPError(400, reason="未知的数据表")
        run_date, run_date_nph = trd.get_trade_date_last()
        if web_module_data.is_realtime:
            date_now_str = run_date_nph.strftime("%Y-%m-%d")
        else:
            date_now_str = run_date.strftime("%Y-%m-%d")
        snapshot_notice = ""
        if quote_snapshot.enabled(web_module_data.table_name):
            latest = self.db.query("SELECT MAX(`date`) AS latest FROM `cn_stock_selection`")[0]["latest"]
            if latest:
                date_now_str = latest.strftime("%Y-%m-%d")
            snapshot_notice = ("每日行情快照 · 来源：东方财富综合选股；非实时行情。"
                               "数据日期见日期栏，历史日期无记录时显示为空。缺失或口径未核实字段留空："
                               + quote_snapshot.projection()[1])
        self.render("stock_web.html", snapshot_notice=snapshot_notice, web_module_data=web_module_data, date_now=date_now_str,
                    leftMenu=webBase.GetLeftMenu(self.request.uri))


# 获得股票数据内容。
class GetStockDataHandler(webBase.BaseHandler, ABC):
    def get(self):
        name = self.get_argument("name", default=None, strip=False)
        date = self.get_argument("date", default=None, strip=False)
        try:
            web_module_data = sswmd.stock_web_module_data().get_data(name)
        except KeyError:
            raise tornado.web.HTTPError(400, reason="未知的数据表")
        self.set_header('Content-Type', 'application/json;charset=UTF-8')

        if date is None:
            where = ""
        else:
            # where = f" WHERE `date` = '{date}'"
            where = f" WHERE `date` = %s"

        order_by = ""
        if web_module_data.order_by is not None:
            order_by = f" ORDER BY {web_module_data.order_by}"

        order_columns = ""
        if web_module_data.order_columns is not None:
            order_columns = f",{web_module_data.order_columns}"

        sql = f" SELECT *{order_columns} FROM `{web_module_data.table_name}`{where}{order_by}"
        if quote_snapshot.enabled(web_module_data.table_name):
            columns, missing = quote_snapshot.projection()
            sql = f"SELECT {columns} FROM `cn_stock_selection`{where} ORDER BY `code`"
            self.set_header("X-InStock-Data-Source", "eastmoney-selection-snapshot")
        if date is not None:
            try:
                trade_date(date)
            except ValueError as exc:
                raise tornado.web.HTTPError(400, reason=str(exc))
        data = self.db.query(sql, date) if date is not None else self.db.query(sql)

        self.write(json.dumps(data, cls=MyEncoder))
