from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "message": "Hello from Pantone Vision API",
            "status": "working",
            "path": self.path
        }
        
        self.wfile.write(json.dumps(response).encode())
        return

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "message": "POST request received",
            "status": "working"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return