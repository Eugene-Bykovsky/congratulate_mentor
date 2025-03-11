import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


def load_data(file_name):
    with open(os.path.join('test_data', file_name), 'r',
              encoding='utf-8') as file:
        return json.load(file)


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/mentors':
            data = load_data('mentors.json')
        elif self.path == '/postcards':
            data = load_data('postcards.json')
        else:
            self.send_response(404)
            self.end_headers()
            return

        if data:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(
                json.dumps(data, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Запущен mock API сервер на порту {port}')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
