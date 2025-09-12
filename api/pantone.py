#!/usr/bin/env python3
"""
Pantone Color Matching API Endpoint
Serverless function for color identification and Pantone matching
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from datetime import datetime
import base64
from io import BytesIO
import cgi

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from _lib.utils import (
    validate_image_file, prepare_image_for_processing, 
    create_api_response, ProcessingTimer, safe_json_serialize
)
from _lib.database import store_processing_result, cleanup_connections

# Import the original Pantone logic
try:
    from ORIGINAL_PANTONE_LOGIC import UniversalColorMatcher
except ImportError:
    # Fallback implementation if original not available
    print("Warning: ORIGINAL_PANTONE_LOGIC not found, using fallback")
    class UniversalColorMatcher:
        def identify_colors_from_image(self, image):
            return {"colors": [], "error": "Original Pantone logic not available"}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Process image for Pantone color matching"""
        timer = ProcessingTimer()
        
        try:
            with timer:
                # Parse multipart form data
                content_type = self.headers.get('Content-Type', '')
                
                if not content_type.startswith('multipart/form-data'):
                    self._send_error(400, "Content-Type must be multipart/form-data")
                    return
                
                # Read the request body
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                
                # Parse multipart data
                environ = {
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                    'CONTENT_LENGTH': str(content_length),
                }
                
                form = cgi.FieldStorage(
                    fp=BytesIO(body),
                    environ=environ,
                    keep_blank_values=True
                )
                
                # Get uploaded image
                if 'image' not in form:
                    self._send_error(400, "No image file provided")
                    return
                
                image_field = form['image']
                if not hasattr(image_field, 'file'):
                    self._send_error(400, "Invalid image field")
                    return
                
                # Read image content
                image_content = image_field.file.read()
                filename = getattr(image_field, 'filename', 'unknown.jpg')
                
                # Validate image
                validation = validate_image_file(image_content, filename)
                if not validation['success']:
                    self._send_error(400, validation['error'])
                    return
                
                image = validation['image']
                
                # Prepare image for processing
                processed_image = prepare_image_for_processing(image)
                
                # Perform Pantone color matching
                color_matcher = UniversalColorMatcher()
                color_results = color_matcher.identify_colors_from_image(processed_image)
                
                # Get additional parameters
                include_metadata = form.get('include_metadata', ['false'])[0].lower() == 'true'
                max_colors = int(form.get('max_colors', ['10'])[0])
                
                # Prepare response data
                response_data = {
                    'colors': color_results.get('colors', [])[:max_colors],
                    'image_info': {
                        'original_size': validation['size'],
                        'processed_size': processed_image.size,
                        'format': validation['format'],
                        'mode': validation['mode']
                    },
                    'processing_info': {
                        'colors_found': len(color_results.get('colors', [])),
                        'algorithm': 'UniversalColorMatcher',
                        'version': '2.0.0'
                    }
                }
                
                if include_metadata:
                    response_data['metadata'] = {
                        'file_size': validation['file_size'],
                        'filename': filename,
                        'confidence_scores': color_results.get('confidence', {}),
                        'color_spaces': color_results.get('color_spaces', {})
                    }
                
                # Store result in database (optional, non-blocking)
                try:
                    storage_result = store_processing_result(
                        {
                            'type': 'pantone_matching',
                            'colors_found': len(color_results.get('colors', [])),
                            'processing_time_ms': timer.elapsed_ms
                        },
                        'pantone_matching'
                    )
                    if storage_result['success']:
                        response_data['storage_id'] = storage_result['id']
                except Exception as e:
                    print(f"Storage warning: {e}")
                
                # Send success response
                response = create_api_response(
                    True, 
                    response_data, 
                    processing_time_ms=timer.elapsed_ms
                )
                
                self._send_json_response(200, response)
                
        except Exception as e:
            print(f"Pantone matching error: {e}")
            error_response = create_api_response(
                False, 
                error=f"Processing failed: {str(e)}",
                processing_time_ms=timer.elapsed_ms if timer.elapsed_ms else 0
            )
            self._send_json_response(500, error_response)
            
        finally:
            # Clean up resources
            cleanup_connections()
    
    def do_GET(self):
        """Get available Pantone colors or system info"""
        try:
            # Simple info endpoint
            info = {
                'endpoint': 'pantone',
                'methods': ['POST'],
                'description': 'Pantone color matching from images',
                'parameters': {
                    'image': 'Image file (required)',
                    'max_colors': 'Maximum colors to return (default: 10)',
                    'include_metadata': 'Include detailed metadata (default: false)'
                },
                'supported_formats': ['PNG', 'JPEG', 'GIF', 'WebP'],
                'max_file_size': '15MB'
            }
            
            response = create_api_response(True, info)
            self._send_json_response(200, response)
            
        except Exception as e:
            error_response = create_api_response(False, error=str(e))
            self._send_json_response(500, error_response)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def _send_json_response(self, status_code: int, data: dict):
        """Send JSON response with proper headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        
        # Safely serialize the response
        json_data = json.dumps(data, default=safe_json_serialize, indent=2 if os.getenv('DEBUG') == 'true' else None)
        self.wfile.write(json_data.encode())
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        error_response = create_api_response(False, error=message)
        self._send_json_response(status_code, error_response)