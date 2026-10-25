"""Small café management server. Run with Python 3.12 or newer."""
import json
import os
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parent
DB = Path(os.environ.get('CAFE_DB', ROOT / 'data' / 'cafe.db'))


def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    return db


def initialize():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS menu (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, price INTEGER NOT NULL CHECK(price > 0));
        CREATE TABLE IF NOT EXISTS orders (
          id INTEGER PRIMARY KEY, customer TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Preparing',
          total INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS order_items (
          order_id INTEGER REFERENCES orders(id), name TEXT NOT NULL,
          price INTEGER NOT NULL, quantity INTEGER NOT NULL);
        ''')
        if not db.execute('SELECT 1 FROM menu LIMIT 1').fetchone():
            db.executemany('INSERT INTO menu(name,price) VALUES (?,?)', [
                ('Espresso', 12000), ('Cappuccino', 18000), ('Iced Latte', 21000),
                ('Masala Chai', 9000), ('Butter Croissant', 15000), ('Chocolate Brownie', 16000)])


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'static'), **kwargs)

    def reply(self, value, status=200):
        payload = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/state':
            with connect() as db:
                menu = [dict(row) for row in db.execute('SELECT * FROM menu ORDER BY id')]
                orders = [dict(row) for row in db.execute('SELECT * FROM orders ORDER BY id DESC')]
                for order in orders:
                    order['items'] = [dict(row) for row in db.execute(
                        'SELECT name,price,quantity FROM order_items WHERE order_id=?', (order['id'],))]
            return self.reply({'menu': menu, 'orders': orders})
        if path.startswith('/api/'):
            return self.reply({'error': 'Not found'}, 404)
        super().do_GET()

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 65536:
                raise ValueError('Request body must be between 1 and 65536 bytes')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('Expected a JSON object')
            path = urlsplit(self.path).path
            with connect() as db:
                if path == '/api/orders':
                    customer = data.get('customer', '')
                    if not isinstance(customer, str) or not 1 <= len(customer.strip()) <= 80:
                        raise ValueError('Enter a customer or table name (1–80 characters)')
                    items = data.get('items')
                    if not isinstance(items, list) or not 1 <= len(items) <= 100:
                        raise ValueError('Choose between 1 and 100 menu items')
                    lines = []
                    for item in items:
                        if not isinstance(item, dict) or type(item.get('id')) is not int or type(item.get('quantity')) is not int or not 1 <= item['quantity'] <= 99:
                            raise ValueError('Each item needs a valid ID and quantity (1–99)')
                        product = db.execute('SELECT * FROM menu WHERE id=?', (item['id'],)).fetchone()
                        if product is None:
                            raise ValueError('Menu item does not exist')
                        lines.append((product['name'], product['price'], item['quantity']))
                    total = sum(price * quantity for _, price, quantity in lines)
                    order_id = db.execute('INSERT INTO orders(customer,total) VALUES (?,?)',
                                          (customer.strip(), total)).lastrowid
                    db.executemany('INSERT INTO order_items VALUES (?,?,?,?)',
                                   [(order_id, *line) for line in lines])
                    result = {'id': order_id, 'total': total}
                elif path.startswith('/api/orders/') and path.endswith('/status'):
                    try:
                        order_id = int(path.split('/')[3])
                    except (ValueError, IndexError):
                        raise ValueError('Invalid order ID')
                    status = data.get('status')
                    if status not in ('Preparing', 'Ready', 'Completed', 'Cancelled'):
                        raise ValueError('Invalid status')
                    current = db.execute('SELECT status FROM orders WHERE id=?', (order_id,)).fetchone()
                    if current is None:
                        return self.reply({'error': 'Order not found'}, 404)
                    allowed = {'Preparing': ('Ready', 'Cancelled'), 'Ready': ('Completed', 'Cancelled'),
                               'Completed': (), 'Cancelled': ()}
                    if status not in allowed[current['status']]:
                        raise ValueError('This status transition is not allowed')
                    db.execute('UPDATE orders SET status=? WHERE id=?', (status, order_id))
                    result = {'id': order_id, 'status': status}
                else:
                    return self.reply({'error': 'Not found'}, 404)
            self.reply(result, 201 if path == '/api/orders' else 200)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self.reply({'error': str(error)}, 400)


if __name__ == '__main__':
    initialize()
    server = ThreadingHTTPServer((os.environ.get('HOST', '127.0.0.1'), int(os.environ.get('PORT', '8000'))), Handler)
    print(f'Café server listening on port {server.server_port}', flush=True)
    server.serve_forever()
