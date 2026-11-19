import base64
import importlib
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch
from urllib.parse import urlencode
import tornado.web
from tornado.testing import AsyncHTTPTestCase


class TestProtectedWeb(AsyncHTTPTestCase):
    def get_app(self):
        modules = {}
        for name in ['instock.core.singleton_stock_web_module_data', 'instock.core.stockfetch',
                     'instock.core.kline.visualization', 'instock.core.tablestructure']:
            modules[name] = ModuleType(name)
        modules['instock.core.tablestructure'].TABLE_CN_STOCK_ATTENTION = {'name':'attention'}
        self.module_patch = patch.dict(sys.modules, modules)
        self.module_patch.start()
        from instock.web.base import BaseHandler
        from instock.web.dataIndicatorsHandler import SaveCollectHandler, GetDataIndicatorsHandler
        class Home(BaseHandler):
            def get(self): self.write('ok')
        self.db = Mock()
        self.db.execute_rowcount.return_value = 1
        app = tornado.web.Application([(r'/',Home),(r'/attention',SaveCollectHandler),
                                        (r'/indicators', GetDataIndicatorsHandler)],
            web_user='alice',web_password='test-password',xsrf_cookies=True,cookie_secret='test-only')
        app.db = self.db
        return app

    def tearDown(self):
        super().tearDown()
        self.module_patch.stop()
        for name in ['instock.web.base','instock.web.dataIndicatorsHandler']:
            sys.modules.pop(name,None)

    def headers(self):
        auth = base64.b64encode(b'alice:test-password').decode()
        headers = {'Authorization': 'Basic ' + auth}
        response = self.fetch('/',headers=headers)
        cookie = response.headers['Set-Cookie'].split(';')[0]
        headers.update({'Cookie':cookie,'X-XSRFToken':cookie.split('=',1)[1]})
        return headers

    def test_auth(self):
        response = self.fetch('/')
        assert response.code == 401
        assert response.headers['WWW-Authenticate'] == 'Basic realm="InStock", charset="UTF-8"'
        assert response.headers['Cache-Control'] == 'no-store'
        assert self.fetch('/',headers={'Authorization':'Basic invalid'}).code == 401
        assert self.fetch('/',headers=self.headers()).code == 200

    def test_writes_require_post_and_xsrf(self):
        headers = self.headers()
        assert self.fetch('/attention?code=600000&otype=0',headers=headers).code == 405
        headers.pop('X-XSRFToken')
        assert self.fetch('/attention',method='POST',headers=headers,body='code=600000&otype=0').code == 403
        self.db.execute_rowcount.assert_not_called()

    def test_write_and_validation(self):
        headers=self.headers()
        assert self.fetch('/attention',method='POST',headers=headers,body='code=600000&otype=0').code == 200
        sql,*args=self.db.execute_rowcount.call_args.args
        assert 'ON DUPLICATE KEY UPDATE' in sql
        assert args[-1] == '600000'
        for data in [{'code':'../bad','otype':'0'},{'code':'600000','otype':'7'}]:
            assert self.fetch('/attention',method='POST',headers=headers,body=urlencode(data)).code == 400
        self.db.execute_rowcount.side_effect=RuntimeError('secret-password')
        response=self.fetch('/attention',method='POST',headers=headers,body='code=600000&otype=1')
        assert response.code == 500
        assert b'secret-password' not in response.body

    def test_chart_validation(self):
        headers=self.headers()
        assert self.fetch('/indicators?code=../../bad&date=2026-11-18',headers=headers).code == 400
        assert self.fetch('/indicators?code=600000&date=2026-13-18',headers=headers).code == 400
