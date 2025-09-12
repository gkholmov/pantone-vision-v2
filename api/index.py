#!/usr/bin/env python3
"""
Pantone Vision API - Main Index Endpoint
Simple health check endpoint for Vercel deployment
"""

from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    """Main API handler for Pantone Vision"""
    
    def do_GET(self):
        """Handle GET requests - API info endpoint"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        
        response = {
            "message": "Pantone Vision 2.0 API",
            "status": "healthy",
            "version": "2.0.0",
            "endpoints": {
                "/api/health": "System health check",
                "/api/pantone": "Pantone color matching",
                "/api/texture": "Texture application (8 types)",
                "/api/gemini": "Gemini pattern transfer"
            }
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()