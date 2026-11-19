#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

from abc import ABC
import base64
import binascii
import hmac
import tornado.web
import instock.core.singleton_stock_web_module_data as sswmd

__author__ = 'myh '
__date__ = '2023/3/10 '


# 基础handler，主要负责检查mysql的数据库链接。
class BaseHandler(tornado.web.RequestHandler, ABC):
    def prepare(self):
        try:
            scheme, value = self.request.headers.get("Authorization", "").split(" ", 1)
            if scheme.lower() != "basic":
                raise ValueError()
            user, password = base64.b64decode(value, validate=True).decode("utf-8").split(":", 1)
            valid_user = hmac.compare_digest(user.encode(), self.settings["web_user"].encode())
            valid_password = hmac.compare_digest(password.encode(), self.settings["web_password"].encode())
            if not (valid_user and valid_password):
                raise ValueError()
        except (ValueError, UnicodeError, binascii.Error):
            self.set_header("WWW-Authenticate", 'Basic realm="InStock", charset="UTF-8"')
            raise tornado.web.HTTPError(401)
        # Materialize the cookie so the chart's POST request can send its XSRF token.
        self.xsrf_token
        self.set_header("Cache-Control", "no-store")
        self.set_header("X-Content-Type-Options", "nosniff")
        self.set_header("X-Frame-Options", "DENY")

    def write_error(self, status_code, **kwargs):
        # Tornado clears headers set in prepare() before rendering HTTP errors.
        if status_code == 401:
            self.set_header("WWW-Authenticate", 'Basic realm="InStock", charset="UTF-8"')
            self.set_header("Cache-Control", "no-store")
        super().write_error(status_code, **kwargs)

    @property
    def db(self):
        try:
            # check every time。
            self.application.db.query("SELECT 1 ")
        except Exception as e:
            print(e)
            self.application.db.reconnect()
        return self.application.db


class LeftMenu:
    def __init__(self, url):
        self.leftMenuList = sswmd.stock_web_module_data().get_data_list()
        self.current_url = url


# 获得左菜单。
def GetLeftMenu(url):
    return LeftMenu(url)
