from http.server import BaseHTTPRequestHandler
import json
import sys
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "message": "Pantone Vision 2.0 API - Production Ready",
                "status": "healthy",
                "version": "2.0.0",
                "endpoints": {
                    "/api/health": "System health check",
                    "/api/pantone": "Pantone color matching",
                    "/api/texture": "Texture application (8 types)",
                    "/api/gemini": "Pattern transfer with Gemini AI"
                },
                "features": {
                    "texture_types": ["lace", "embroidery", "silk", "satin", "leather", "velvet", "mesh", "sequin"],
                    "ai_integration": "Gemini 2.5 Flash Image",
                    "database": "Supabase with connection pooling",
                    "serverless": "Vercel optimized"
                },
                "path": self.path
            }
            
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

    def do_POST(self):
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "message": "POST request received",
                "status": "working",
                "note": "Use specific endpoints: /api/pantone, /api/texture, /api/gemini"
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()