import http.server
import socketserver
import socket
import threading
import json
import os
from datetime import datetime
from urllib.parse import parse_qs

HTTP_PORT = 3000
SOCKET_PORT = 5000
DATA_FILE = "storage/data.json"

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "/templates/index.html"
        elif self.path == "/message":
            self.path = "/templates/message.html"
        elif self.path.startswith("/static/"):
            self.path = self.path
        else:
            self.path = "/templates/error.html"
            self.send_response(404)
            self.end_headers()
            with open(self.path[1:], "rb") as file:
                self.wfile.write(file.read())
            return
        try:
            with open(self.path[1:], "rb") as file:
                self.send_response(200)
                if self.path.endswith(".css"):
                    self.send_header("Content-type", "text/css")
                elif self.path.endswith(".png"):
                    self.send_header("Content-type", "image/png")
                else:
                    self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(file.read())
        except:
            self.send_error(404, "File Not Found")


    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = parse_qs(post_data.decode("utf-8"))
            
            username = data.get("username", [""])[0]
            message = data.get("message", [""])[0]

            if username and message:
                send_to_socket_server(username, message)
                self.send_response(303)
                self.send_header("Location", "/")
            else:
                self.send_response(400)

            self.end_headers()

def start_http_server():
    with socketserver.TCPServer(("", HTTP_PORT), MyHandler) as httpd:
        print(f"Сервер запущено на порту {HTTP_PORT}")
        httpd.serve_forever()


def send_to_socket_server(username, message):
    data = {"username": username, "message": message}
    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_client.sendto(json.dumps(data).encode("utf-8"), ("localhost", SOCKET_PORT))
    udp_client.close()

def socket_server():
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server.bind(("localhost", SOCKET_PORT))
    
    if not os.path.exists("storage"):
        os.makedirs("storage")

    print(f"Сокет на порту {SOCKET_PORT}")

    while True:
        data, addr = udp_server.recvfrom(1024)
        message = json.loads(data.decode("utf-8"))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as file:
                messages = json.load(file)
        else:
            messages = {}

        messages[timestamp] = message

        with open(DATA_FILE, "w") as file:
            json.dump(messages, file, indent=2)

if __name__ == "__main__":
    socket_thread = threading.Thread(target=socket_server, daemon=True)
    socket_thread.start()
    start_http_server()
