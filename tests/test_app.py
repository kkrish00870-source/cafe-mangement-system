import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import app


class CafeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        app.DB = Path(cls.temp.name) / 'test.db'
        app.initialize()
        cls.server = app.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def call(self, path, data=None):
        req = urllib.request.Request(self.base + path, data=None if data is None else json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_order_lifecycle_and_persistence(self):
        _, state = self.call('/api/state')
        item = state['menu'][0]
        status, order = self.call('/api/orders', {'customer': 'Table 4', 'items': [{'id': item['id'], 'quantity': 2}], 'total': 1})
        self.assertEqual(status, 201)
        self.assertEqual(order['total'], item['price'] * 2)
        path = f"/api/orders/{order['id']}/status"
        self.assertEqual(self.call(path, {'status': 'Completed'})[0], 400)
        for target in ('Ready', 'Completed'):
            self.assertEqual(self.call(path, {'status': target})[0], 200)
        self.assertEqual(self.call(path, {'status': 'Preparing'})[0], 400)
        app.initialize()
        _, state = self.call('/api/state')
        saved = next(row for row in state['orders'] if row['id'] == order['id'])
        self.assertEqual(saved['status'], 'Completed')
        self.assertEqual(saved['items'][0]['quantity'], 2)
        self.assertEqual(saved['customer'], 'Table 4')

    def test_invalid_orders_do_not_write(self):
        before = self.call('/api/state')[1]['orders']
        for payload in ({}, {'customer': 'A', 'items': []}, {'customer': 'A', 'items': [{'id': 999, 'quantity': 1}]}, {'customer': 'A', 'items': [{'id': 1, 'quantity': -1}]}, {'customer': 'A', 'items': [{'id': 1, 'quantity': True}]}):
            self.assertEqual(self.call('/api/orders', payload)[0], 400)
        self.assertEqual(self.call('/api/state')[1]['orders'], before)

    def test_static_page_and_not_found(self):
        with urllib.request.urlopen(self.base + '/') as response:
            self.assertIn(b'Daily Grind', response.read())
        self.assertEqual(self.call('/api/missing')[0], 404)
        self.assertEqual(self.call('/api/orders/999999/status', {'status': 'Ready'})[0], 404)


if __name__ == '__main__':
    unittest.main()
