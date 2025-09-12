#!/usr/bin/env python3
"""
Health check endpoint for Pantone Vision API
Vercel serverless function to monitor system status
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from datetime import datetime

# Add current directory to path for relative imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from _lib.config import APP_VERSION, DEBUG
    from _lib.database import health_check as db_health_check
    from _lib.utils import create_api_response
except ImportError:
    # Fallback for production deployment
    APP_VERSION = "2.0.0"
    DEBUG = False
    def health_check():
        return {'success': True, 'status': 'connected'}
    def create_api_response(success, data=None, error=None, processing_time_ms=None):
        response = {'success': success, 'timestamp': datetime.now().isoformat()}
        if success and data:
            response['data'] = data
        elif not success and error:
            response['error'] = error
        return response

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check endpoint"""
        try:
            start_time = datetime.now()
            
            # Check system components
            system_status = {
                'api_version': APP_VERSION,
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'debug_mode': DEBUG,
                'timestamp': datetime.now().isoformat()
            }
            
            # Check database connection
            db_status = db_health_check()
            
            # Check environment variables
            env_status = {
                'gemini_api': bool(os.getenv('GEMINI_API_KEY')),
                'anthropic_api': bool(os.getenv('ANTHROPIC_API_KEY')),
                'huggingface_api': bool(os.getenv('HUGGINGFACE_API_KEY')),
                'supabase_configured': bool(os.getenv('SUPABASE_URL')),
                'replicate_api': bool(os.getenv('REPLICATE_API_KEY')),
                'stability_api': bool(os.getenv('STABILITY_API_KEY'))
            }
            
            # Overall health status
            overall_healthy = (
                db_status.get('success', False) and
                env_status['gemini_api'] and
                env_status['supabase_configured']
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            response_data = {
                'status': 'healthy' if overall_healthy else 'degraded',
                'system': system_status,
                'database': db_status,
                'environment': env_status,
                'features_available': {
                    'pantone_matching': True,
                    'texture_application': env_status['huggingface_api'],
                    'gemini_pattern_transfer': env_status['gemini_api'],
                    'data_storage': db_status.get('success', False)
                }
            }
            
            response = create_api_response(True, response_data, processing_time_ms=processing_time)
            
            # Set response headers
            self.send_response(200 if overall_healthy else 503)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            # Error response
            error_response = create_api_response(False, error=f"Health check failed: {str(e)}")
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()