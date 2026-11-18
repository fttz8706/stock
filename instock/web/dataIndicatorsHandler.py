#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

from abc import ABC
from tornado import gen
import logging
import tornado.web
from instock.lib.validation import stock_code, trade_date
import instock.core.stockfetch as stf
import instock.core.kline.visualization as vis
import instock.web.base as webBase

__author__ = 'myh '
__date__ = '2023/3/10 '


# 获得页面数据。
class GetDataIndicatorsHandler(webBase.BaseHandler, ABC):
    @gen.coroutine
    def get(self):
        code = self.get_argument("code", default=None, strip=False)
        date = self.get_argument("date", default=None, strip=False)
        name = self.get_argument("name", default=None, strip=False)
        try:
            stock_code(code)
            trade_date(date)
        except ValueError as exc:
            raise tornado.web.HTTPError(400, reason=str(exc))
        comp_list = []
        try:
            if code.startswith(('1', '5')):
                stock = stf.fetch_etf_hist((date, code))
            else:
                stock = stf.fetch_stock_hist((date, code))
            if stock is None:
                return

            pk = vis.get_plot_kline(code, stock, date, name)
            if pk is None:
                return

            comp_list.append(pk)
        except Exception as e:
            logging.error(f"dataIndicatorsHandler.GetDataIndicatorsHandler处理异常：{e}")

        self.render("stock_indicators.html", comp_list=comp_list,
                    leftMenu=webBase.GetLeftMenu(self.request.uri))


# 关注股票。
class SaveCollectHandler(webBase.BaseHandler, ABC):
    def post(self):
        import datetime
        import instock.core.tablestructure as tbs
        code = self.get_argument("code", default="")
        otype = self.get_argument("otype", default="")
        try:
            stock_code(code)
            if otype not in ("0", "1"):
                raise ValueError("无效的关注操作")
        except ValueError as exc:
            raise tornado.web.HTTPError(400, reason=str(exc))
        table_name = tbs.TABLE_CN_STOCK_ATTENTION['name']
        try:
            if otype == '1':
                affected = self.db.execute_rowcount(f"DELETE FROM `{table_name}` WHERE `code` = %s", code)
            else:
                affected = self.db.execute_rowcount(
                    f"INSERT INTO `{table_name}` (`datetime`, `code`) VALUES (%s, %s) "
                    "ON DUPLICATE KEY UPDATE `datetime` = VALUES(`datetime`)",
                    datetime.datetime.now(), code)
        except Exception:
            logging.error("关注操作写入失败")
            raise tornado.web.HTTPError(500, reason="关注操作失败，请稍后重试")
        self.write({"data": [{"code": code, "collected": otype == "0", "affected": affected}]})
