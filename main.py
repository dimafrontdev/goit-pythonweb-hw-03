from http.server import HTTPServer, BaseHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import urllib.parse
import mimetypes
import pathlib
import json


class HttpHandler(BaseHTTPRequestHandler):
    env = Environment(loader=FileSystemLoader("."))

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {
            key: value for key, value in [el.split("=") for el in data_parse.split("&")]
        }

        self.save_to_json(data_dict)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message.html":
            self.send_html_file("message.html")
        elif pr_url.path == "/read.html":
            self.render_read_page()
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())

    def save_to_json(self, data):
        json_file = pathlib.Path("storage/data.json")
        json_file.parent.mkdir(exist_ok=True)

        messages = {}
        if json_file.exists():
            with json_file.open("r", encoding="utf-8") as f:
                messages = json.load(f)
        messages[datetime.now().isoformat()] = data

        with json_file.open("w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    def render_read_page(self):
        json_file = pathlib.Path("storage/data.json")
        messages = {}
        if json_file.exists():
            with json_file.open("r", encoding="utf-8") as f:
                messages = json.load(f)

        template = self.env.get_template("read.html")
        rendered_content = template.render(messages=messages)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(rendered_content.encode("utf-8"))


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
