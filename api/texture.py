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
from PIL import Image
# cgi module removed in Python 3.13+, using custom multipart parser

# Add current directory to path for relative imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from _lib.utils import (
        validate_image_file, prepare_image_for_processing, 
        create_api_response, ProcessingTimer, image_to_base64
    )
    from _lib.database import store_processing_result, cleanup_connections
except ImportError:
    # Fallback implementations for production deployment
    import base64
    from io import BytesIO
    from PIL import Image
    
    def validate_image_file(file_content, filename):
        try:
            image = Image.open(BytesIO(file_content))
            return {'success': True, 'image': image, 'size': image.size, 'format': image.format, 'mode': image.mode}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def prepare_image_for_processing(image):
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return image
    
    def create_api_response(success, data=None, error=None, processing_time_ms=None):
        return {'success': success, 'data': data, 'error': error, 'timestamp': datetime.now().isoformat()}
    
    class ProcessingTimer:
        def __init__(self):
            self.start_time = None
        def __enter__(self):
            self.start_time = datetime.now()
            return self
        def __exit__(self, *args):
            pass
        @property
        def elapsed_ms(self):
            return (datetime.now() - self.start_time).total_seconds() * 1000 if self.start_time else 0
    
    def image_to_base64(image, format="PNG"):
        buffer = BytesIO()
        image.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode()
    
    def store_processing_result(*args, **kwargs):
        return {'success': True}
    
    def cleanup_connections():
        pass
    
    # Simple multipart parser for Python 3.13+ compatibility
    import re
    
    class MultipartField:
        def __init__(self, name, value=None, filename=None):
            self.name = name
            self.value = value
            self.filename = filename
            self.file = None
            if isinstance(value, bytes):
                self.file = BytesIO(value)
    
    class MultipartParser:
        def __init__(self, body, content_type):
            self.fields = {}
            self._parse(body, content_type)
        
        def _parse(self, body, content_type):
            try:
                boundary_match = re.search(r'boundary=([^;]+)', content_type)
                if not boundary_match:
                    return
                boundary = boundary_match.group(1).strip('"')
                boundary_bytes = ('--' + boundary).encode()
                parts = body.split(boundary_bytes)
                
                for part in parts[1:-1]:
                    if not part.strip():
                        continue
                    if b'\r\n\r\n' not in part:
                        continue
                    headers_data, body_data = part.split(b'\r\n\r\n', 1)
                    headers_text = headers_data.decode('utf-8', errors='ignore')
                    name_match = re.search(r'name="([^"]*)"', headers_text)
                    if not name_match:
                        continue
                    field_name = name_match.group(1)
                    filename_match = re.search(r'filename="([^"]*)"', headers_text)
                    
                    if filename_match:
                        filename = filename_match.group(1)
                        field = MultipartField(field_name, body_data, filename)
                    else:
                        field = MultipartField(field_name, body_data.decode('utf-8', errors='ignore'))
                    self.fields[field_name] = field
            except Exception as e:
                print(f"Multipart parsing error: {e}")
        
        def get(self, key, default=None):
            if key in self.fields:
                return [self.fields[key]]
            return default or []
        
        def __contains__(self, key):
            return key in self.fields
        
        def __getitem__(self, key):
            return self.fields[key]

# Fallback texture service for when main service is unavailable
class FallbackTextureService:
    """Simple texture service that works without external dependencies"""
    
    def __init__(self):
        self.texture_patterns = {
            'lace': {'pattern': 'crosshatch', 'opacity': 0.3, 'blend': 'overlay'},
            'embroidery': {'pattern': 'dots', 'opacity': 0.4, 'blend': 'multiply'},
            'silk': {'pattern': 'gradient', 'opacity': 0.2, 'blend': 'screen'},
            'satin': {'pattern': 'shine', 'opacity': 0.25, 'blend': 'soft-light'},
            'leather': {'pattern': 'grain', 'opacity': 0.35, 'blend': 'multiply'},
            'velvet': {'pattern': 'soft', 'opacity': 0.3, 'blend': 'darken'},
            'mesh': {'pattern': 'grid', 'opacity': 0.4, 'blend': 'multiply'},
            'sequin': {'pattern': 'sparkle', 'opacity': 0.5, 'blend': 'screen'}
        }
    
    def process_full_texture_workflow(self, image, texture_type, pantone_colors=None, intensity=0.8):
        """Apply texture effect using PIL filters"""
        from PIL import ImageFilter, ImageEnhance, ImageOps
        import random
        
        # Apply texture-specific filters
        if texture_type == 'lace':
            # Add delicate pattern
            image = image.filter(ImageFilter.DETAIL)
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
        elif texture_type == 'embroidery':
            # Add raised texture effect
            image = image.filter(ImageFilter.EMBOSS)
            image = Image.blend(image, image.filter(ImageFilter.EDGE_ENHANCE), 0.3)
        elif texture_type == 'silk':
            # Add smooth, lustrous effect
            image = image.filter(ImageFilter.SMOOTH_MORE)
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
        elif texture_type == 'satin':
            # Add glossy effect
            image = image.filter(ImageFilter.GaussianBlur(radius=1))
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.3)
        elif texture_type == 'leather':
            # Add grain texture
            image = image.filter(ImageFilter.SHARPEN)
            image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
        elif texture_type == 'velvet':
            # Add soft, plush effect
            image = image.filter(ImageFilter.SMOOTH)
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.2)
        elif texture_type == 'mesh':
            # Add perforated pattern
            image = image.filter(ImageFilter.FIND_EDGES)
            image = ImageOps.autocontrast(image)
        elif texture_type == 'sequin':
            # Add sparkle effect
            image = image.filter(ImageFilter.MaxFilter(size=3))
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.2)
        
        # Apply intensity adjustment
        if intensity < 1.0:
            original = image.copy()
            image = Image.blend(original, image, intensity)
        
        # Apply Pantone color tinting if provided
        if pantone_colors and len(pantone_colors) > 0:
            # Apply subtle color overlay based on first Pantone color
            if 'hex' in pantone_colors[0]:
                hex_color = pantone_colors[0]['hex'].lstrip('#')
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                overlay = Image.new('RGB', image.size, rgb)
                image = Image.blend(image, overlay, 0.15)  # Subtle tint
        
        # Convert to base64 for response
        buffer = BytesIO()
        image.save(buffer, format='PNG', quality=95)
        textured_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'success': True,
            'textured_image': f"data:image/png;base64,{textured_base64}",
            'texture_applied': texture_type,
            'method': 'PIL_Fallback',
            'intensity': intensity
        }
    
    def apply_custom_texture(self, image, custom_texture, pantone_colors=None, intensity=0.8):
        """Apply custom texture using simple blending"""
        # Resize custom texture to match image size
        custom_texture = custom_texture.resize(image.size, Image.LANCZOS)
        
        # Blend the textures
        textured = Image.blend(image, custom_texture, intensity * 0.5)
        
        # Convert to base64
        buffer = BytesIO()
        textured.save(buffer, format='PNG', quality=95)
        textured_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'success': True,
            'textured_image': f"data:image/png;base64,{textured_base64}",
            'texture_applied': 'custom',
            'method': 'PIL_Fallback',
            'intensity': intensity
        }
    
    def get_available_textures(self):
        """Return list of available textures"""
        return {
            'textures': list(self.texture_patterns.keys()),
            'total_available': len(self.texture_patterns),
            'categories': {
                'delicate': ['lace', 'silk', 'mesh'],
                'luxury': ['velvet', 'satin', 'leather'],
                'decorative': ['embroidery', 'sequin']
            }
        }

# Import texture service with lazy loading for performance
def get_texture_service():
    """Lazy load texture service to reduce cold start time"""
    try:
        from services.texture_application_service import TextureApplicationService
        return TextureApplicationService()
    except ImportError as e:
        print(f"Warning: Texture service import failed: {e}, using fallback")
        # Return a simple fallback texture service
        return FallbackTextureService()

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
                
                # Parse multipart data using custom parser (Python 3.13+ compatible)
                try:
                    from _lib.utils import MultipartParser as MP
                    form = MP(body, content_type)
                except ImportError:
                    # Define MultipartParser inline if not available
                    import re
                    
                    class MultipartField:
                        def __init__(self, name, value=None, filename=None):
                            self.name = name
                            self.value = value
                            self.filename = filename
                            self.file = None
                            if isinstance(value, bytes):
                                self.file = BytesIO(value)
                    
                    class MultipartParser:
                        def __init__(self, body, content_type):
                            self.fields = {}
                            self._parse(body, content_type)
                        
                        def _parse(self, body, content_type):
                            try:
                                boundary_match = re.search(r'boundary=([^;]+)', content_type)
                                if not boundary_match:
                                    return
                                boundary = boundary_match.group(1).strip('"')
                                boundary_bytes = ('--' + boundary).encode()
                                parts = body.split(boundary_bytes)
                                
                                for part in parts[1:-1]:
                                    if not part.strip():
                                        continue
                                    if b'\r\n\r\n' not in part:
                                        continue
                                    headers_data, body_data = part.split(b'\r\n\r\n', 1)
                                    headers_text = headers_data.decode('utf-8', errors='ignore')
                                    name_match = re.search(r'name="([^"]*)"', headers_text)
                                    if not name_match:
                                        continue
                                    field_name = name_match.group(1)
                                    filename_match = re.search(r'filename="([^"]*)"', headers_text)
                                    
                                    if filename_match:
                                        filename = filename_match.group(1)
                                        field = MultipartField(field_name, body_data, filename)
                                    else:
                                        field = MultipartField(field_name, body_data.decode('utf-8', errors='ignore'))
                                    self.fields[field_name] = field
                            except Exception as e:
                                print(f"Multipart parsing error: {e}")
                        
                        def get(self, key, default=None):
                            if key in self.fields:
                                return [self.fields[key]]
                            return default or []
                        
                        def __contains__(self, key):
                            return key in self.fields
                        
                        def __getitem__(self, key):
                            return self.fields[key]
                    
                    form = MultipartParser(body, content_type)
                
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
                texture_type_field = form.get('texture_type')
                if not texture_type_field:
                    self._send_error(400, "texture_type parameter required")
                    return
                texture_type = texture_type_field[0].value
                
                intensity_field = form.get('intensity', [])
                intensity = float(intensity_field[0].value) if intensity_field else 0.8
                
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
                pantone_colors_field = form.get('pantone_colors', [])
                if pantone_colors_field:
                    try:
                        pantone_colors = json.loads(pantone_colors_field[0].value)
                    except (json.JSONDecodeError, AttributeError):
                        print("Warning: Invalid pantone_colors JSON, ignoring")
                
                # Handle custom texture upload (optional)
                custom_texture_image = None
                if 'custom_texture' in form:
                    custom_texture_field = form['custom_texture']
                    if hasattr(custom_texture_field, 'file') and custom_texture_field.file:
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