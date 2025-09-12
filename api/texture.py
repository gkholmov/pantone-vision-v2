#!/usr/bin/env python3
"""
Texture Application API Endpoint
Serverless function for applying fabric textures with AI enhancement
Preserves ALL 8 texture types: lace, embroidery, silk, satin, leather, velvet, mesh, sequin
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
    create_api_response, ProcessingTimer, image_to_base64
)
from _lib.database import store_processing_result, cleanup_connections

# Import texture service with lazy loading for performance
def get_texture_service():
    """Lazy load texture service to reduce cold start time"""
    try:
        from services.texture_application_service import TextureApplicationService
        return TextureApplicationService()
    except ImportError as e:
        print(f"Warning: Texture service import failed: {e}")
        return None

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Apply texture to uploaded image"""
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
                
                # Get required parameters
                if 'image' not in form:
                    self._send_error(400, "No image file provided")
                    return
                
                if 'texture_type' not in form:
                    self._send_error(400, "texture_type parameter required")
                    return
                
                # Read image content
                image_field = form['image']
                image_content = image_field.file.read()
                filename = getattr(image_field, 'filename', 'unknown.jpg')
                
                # Validate image
                validation = validate_image_file(image_content, filename)
                if not validation['success']:
                    self._send_error(400, validation['error'])
                    return
                
                image = validation['image']
                
                # Get texture parameters
                texture_type = form.get('texture_type')[0].value
                intensity = float(form.get('intensity', ['0.8'])[0].value)
                
                # Validate texture type (ALL 8 TYPES SUPPORTED)
                valid_textures = ['lace', 'embroidery', 'silk', 'satin', 'leather', 'velvet', 'mesh', 'sequin']
                if texture_type not in valid_textures:
                    self._send_error(400, f"Invalid texture_type. Supported: {', '.join(valid_textures)}")
                    return
                
                # Validate intensity
                if not 0.0 <= intensity <= 1.0:
                    self._send_error(400, "intensity must be between 0.0 and 1.0")
                    return
                
                # Get optional parameters
                pantone_colors = []
                if 'pantone_colors' in form:
                    try:
                        pantone_colors = json.loads(form.get('pantone_colors')[0].value)
                    except (json.JSONDecodeError, AttributeError):
                        print("Warning: Invalid pantone_colors JSON, ignoring")
                
                # Handle custom texture upload (optional)
                custom_texture_image = None
                if 'custom_texture' in form:
                    custom_texture_field = form['custom_texture']
                    if hasattr(custom_texture_field, 'file'):
                        custom_texture_content = custom_texture_field.file.read()
                        custom_texture_filename = getattr(custom_texture_field, 'filename', 'texture.jpg')
                        
                        custom_validation = validate_image_file(custom_texture_content, custom_texture_filename)
                        if custom_validation['success']:
                            custom_texture_image = custom_validation['image']
                        else:
                            print(f"Custom texture validation failed: {custom_validation['error']}")
                
                # Prepare image for processing
                processed_image = prepare_image_for_processing(image)
                
                # Initialize texture service
                texture_service = get_texture_service()
                if not texture_service:
                    self._send_error(500, "Texture service unavailable")
                    return
                
                # Apply texture based on type
                if custom_texture_image:
                    # Apply custom texture with AI pattern recognition
                    texture_result = texture_service.apply_custom_texture(
                        processed_image,
                        custom_texture_image,
                        pantone_colors,
                        intensity
                    )
                else:
                    # Apply predefined texture with full workflow
                    texture_result = texture_service.process_full_texture_workflow(
                        processed_image,
                        texture_type,
                        pantone_colors,
                        intensity=intensity
                    )
                
                if not texture_result.get('success'):
                    error_msg = texture_result.get('error', 'Texture application failed')
                    self._send_error(500, error_msg)
                    return
                
                # Convert result image to base64 for response
                textured_image = texture_result['textured_image']
                result_b64 = image_to_base64(textured_image, 'PNG')
                
                # Prepare response data
                response_data = {
                    'textured_image': f"data:image/png;base64,{result_b64}",
                    'texture_applied': {
                        'type': texture_type,
                        'intensity': intensity,
                        'method': texture_result.get('method', 'unknown'),
                        'ai_enhanced': texture_result.get('ai_method') is not None
                    },
                    'image_info': {
                        'original_size': validation['size'],
                        'processed_size': processed_image.size,
                        'output_size': textured_image.size,
                        'format': 'PNG'
                    },
                    'processing_info': {
                        'texture_type': texture_type,
                        'pantone_colors_used': len(pantone_colors) if pantone_colors else 0,
                        'custom_texture_used': custom_texture_image is not None,
                        'workflow_time': texture_result.get('workflow_time_seconds', 0),
                        'version': '2.0.0'
                    }
                }
                
                # Add detailed texture info if available
                if 'mask_info' in texture_result:
                    mask_info = texture_result['mask_info']
                    response_data['texture_analysis'] = {
                        'coverage_percentage': mask_info.get('coverage_percentage', 0),
                        'texture_areas': mask_info.get('texture_areas', 0),
                        'adaptive_threshold': mask_info.get('adaptive_threshold'),
                        'mean_brightness': mask_info.get('mean_brightness')
                    }
                
                # Add pattern analysis for custom textures
                if 'pattern_analysis' in texture_result:
                    pattern_info = texture_result['pattern_analysis']
                    response_data['pattern_analysis'] = {
                        'detected_type': pattern_info.get('detected_type'),
                        'confidence': pattern_info.get('confidence', 0),
                        'features': pattern_info.get('features', {})
                    }
                
                # Store result in database (non-blocking)
                try:
                    storage_result = store_processing_result(
                        {
                            'type': 'texture_application',
                            'texture_type': texture_type,
                            'intensity': intensity,
                            'processing_time_ms': timer.elapsed_ms,
                            'ai_enhanced': texture_result.get('ai_method') is not None
                        },
                        'texture_processing'
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
            print(f"Texture application error: {e}")
            import traceback
            traceback.print_exc()
            
            error_response = create_api_response(
                False, 
                error=f"Texture processing failed: {str(e)}",
                processing_time_ms=timer.elapsed_ms if timer.elapsed_ms else 0
            )
            self._send_json_response(500, error_response)
            
        finally:
            # Clean up resources
            cleanup_connections()
    
    def do_GET(self):
        """Get available texture types and information"""
        try:
            # Get texture service for available textures
            texture_service = get_texture_service()
            
            if texture_service:
                available_textures = texture_service.get_available_textures()
                
                response_data = {
                    'endpoint': 'texture',
                    'methods': ['POST'],
                    'description': 'Apply fabric textures to images with AI enhancement',
                    'available_textures': available_textures['textures'],
                    'total_textures': available_textures['total_available'],
                    'api_status': available_textures['api_status'],
                    'parameters': {
                        'image': 'Image file to apply texture to (required)',
                        'texture_type': f'Texture type: {", ".join(available_textures["textures"].keys())} (required)',
                        'intensity': 'Texture intensity 0.0-1.0 (default: 0.8)',
                        'pantone_colors': 'JSON array of Pantone colors for context (optional)',
                        'custom_texture': 'Custom texture image file (optional)'
                    },
                    'features': {
                        'ai_pattern_recognition': True,
                        'custom_texture_upload': True,
                        'pantone_color_context': True,
                        'intensity_control': True,
                        'fallback_processing': True
                    }
                }
            else:
                response_data = {
                    'endpoint': 'texture',
                    'status': 'service_unavailable',
                    'error': 'Texture service could not be loaded'
                }
            
            response = create_api_response(True, response_data)
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
        
        # Handle large responses (base64 images can be big)
        json_data = json.dumps(data, indent=2 if os.getenv('DEBUG') == 'true' else None)
        self.wfile.write(json_data.encode())
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        error_response = create_api_response(False, error=message)
        self._send_json_response(status_code, error_response)