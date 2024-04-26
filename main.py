from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import socket
from datetime import  datetime
import json 
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import multiprocessing as mp
from dotenv import dotenv_values

config = dotenv_values(".env")
# client = MongoClient(f'mongodb+srv://kmoro:13091989morozova@cluster0.3k2urwx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0', server_api=ServerApi('1'))

client = MongoClient(f'mongodb+srv://{config.MONGO_DB_USER}:{config.MONGO_DB_PASSWORD}@cluster0.3k2urwx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0', server_api=ServerApi('1'))

db= client.users

def save_to_mongodb(data):
    db.users.insert_one(data)
    
class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)
                
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
        
        data_dict = {}
        for key, value in parsed_data.items():
            data_dict[key] = value[0] 
        data_dict['date'] = str(datetime.now())
        
        # Connect to server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 5000))

        # Send data 
        data_json = json.dumps(data_dict)
        client_socket.sendall(data_json.encode())

        response = client_socket.recv(1024)
        print("Response from socket server:", response.decode('utf-8'))

        client_socket.close()

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())
    
    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def start_http_server():
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, HttpHandler)
    print("Starting HTTP server on port 3000...")
    httpd.serve_forever()

def start_socket_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 5000))
    server_socket.listen(1)
    print("Socket server listening on port 5000...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection is from {addr}")

        data = client_socket.recv(1024)

        if data:
            try:
                data_dict = json.loads(data.decode('utf-8'))
                print("Received data:", data_dict)

                save_to_mongodb(data_dict)

                client_socket.send(b"Data received and processed successfully.")
                
            except json.JSONDecodeError:
                print("Error decoding data.")

        client_socket.close()

def main():
    http_process = mp.Process(target=start_http_server)
    http_process.start()

    # main process
    start_socket_server()
    
if __name__ == '__main__':
    main()
    

