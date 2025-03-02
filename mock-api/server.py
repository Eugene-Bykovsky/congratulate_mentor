import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


def load_data():
    with open(os.path.join(os.path.dirname(__file__), 'data.json'), 'r',
              encoding='utf-8') as file:
        return json.load(file)


data = load_data()


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/mentors', '/holidays', '/postcards']:
            key = self.path[1:]
            if key in data:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(
                    json.dumps(data[key], ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting mock API server on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
