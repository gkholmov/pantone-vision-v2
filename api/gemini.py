#!/usr/bin/env python3
"""
Gemini Pattern Transfer API Endpoint
Serverless function for textile pattern transfer using Gemini 2.5 Flash Image
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from datetime import datetime
import base64
from io import BytesIO
# cgi module removed in Python 3.13+, using custom multipart parser
import time
from PIL import Image

# Add current directory to path for relative imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from _lib.utils import (
        validate_image_file, prepare_image_for_processing, 
        create_api_response, ProcessingTimer, image_to_base64
    )
    from _lib.database import store_processing_result, cleanup_connections
    from _lib.config import GEMINI_API_KEY
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
    
    # Get Gemini API key from environment
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
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

# Lazy load Gemini components
def get_gemini_client():
    """Lazy load Gemini client to reduce cold start time"""
    try:
        from google import genai
        # Set API key
        os.environ['GOOGLE_API_KEY'] = GEMINI_API_KEY
        return genai.Client()
    except ImportError as e:
        print(f"Warning: Gemini import failed: {e}")
        # Return a simple HTTP-based client instead
        return SimpleGeminiClient(GEMINI_API_KEY)

class SimpleGeminiClient:
    """Simple Gemini client using HTTP requests instead of SDK"""
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        # Add models attribute to match the expected interface
        self.models = self
    
    def is_available(self):
        """Check if API key is configured"""
        return bool(self.api_key and self.api_key != 'your_gemini_api_key_here')
    
    def generate_content(self, model, contents):
        """Generate content using Gemini API via HTTP"""
        import requests
        
        if not self.is_available():
            raise Exception("Gemini API key not configured")
        
        # For now, return an error to use fallback
        raise Exception("SimpleGeminiClient HTTP implementation not complete - using fallback")

class GeminiTextileTransfer:
    """Gemini 2.5 Flash Image for textile pattern transfer - serverless optimized"""
    
    def __init__(self):
        self.model_name = "gemini-2.5-flash-image-preview"  # Official model name from Google AI docs
        self.client = get_gemini_client()
    
    def transfer_textile_pattern(self, textile_image, sketch_image, 
                               pantone_color=None, pantone_name=None):
        """Transfer textile pattern from source to garment sketch using Gemini"""
        if not self.client:
            # Use fallback pattern transfer without Gemini
            return self._fallback_pattern_transfer(
                textile_image, sketch_image, pantone_color, pantone_name
            )
        
        try:
            print(f"🎨 Starting Gemini textile pattern transfer...")
            print(f"   Pantone: {pantone_color} ({pantone_name})")
            
            # Craft detailed prompt for textile transfer
            prompt = self._create_textile_transfer_prompt(pantone_color, pantone_name)
            
            print(f"🚀 Sending request to Gemini 2.5 Flash Image...")
            
            # Add retry logic for 500 errors
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Generate with Gemini using official 2025 API format (pass PIL Images directly)
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=[prompt, textile_image, sketch_image],
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    if "500" in str(e) and attempt < max_retries - 1:
                        print(f"🔄 Retry {attempt + 1}/{max_retries} - Gemini server error, waiting 2s...")
                        time.sleep(2)
                        continue
                    else:
                        raise e  # Re-raise if not 500 error or max retries reached
            
            # Process response from Gemini 2.5 Flash Image API
            print(f"Debug: Response type: {type(response)}")
            print(f"Debug: Response candidates: {len(response.candidates) if response.candidates else 'None'}")
            
            # Check if response has valid structure
            if not response.candidates:
                raise Exception("No candidates in response")
            
            candidate = response.candidates[0]
            print(f"Debug: Candidate content: {candidate.content}")
            print(f"Debug: Candidate attributes: {dir(candidate)}")
            
            if not candidate.content:
                # Check if there's finish_reason or other info
                if hasattr(candidate, 'finish_reason'):
                    print(f"Debug: Finish reason: {candidate.finish_reason}")
                raise Exception("No content in response candidate - check if prompt triggers safety filters")
            
            if not candidate.content.parts:
                raise Exception("No parts in response content")
            
            # Extract generated image using 2025 API format
            image_parts = [
                part.inline_data.data
                for part in candidate.content.parts
                if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.data
            ]
            
            if image_parts:
                # The data is already binary, no need to base64 decode
                image_data = image_parts[0]
                result_image = Image.open(BytesIO(image_data))
                
                print(f"✅ Gemini textile transfer successful!")
                
                return {
                    'success': True,
                    'result_image': result_image,
                    'method': 'gemini-2.5-flash-image-preview',
                    'model_used': self.model_name,
                    'pantone_context': {
                        'color': pantone_color,
                        'name': pantone_name
                    }
                }
            else:
                raise Exception("No image generated in response")
            
        except Exception as e:
            print(f"Gemini pattern transfer error: {e}")
            return {
                'success': False,
                'error': f'Gemini processing failed: {str(e)}',
                'exception_type': type(e).__name__
            }
    
    def _fallback_pattern_transfer(self, textile_image, sketch_image, 
                                   pantone_color=None, pantone_name=None):
        """Fallback pattern transfer using PIL when Gemini is unavailable"""
        from PIL import ImageFilter, ImageEnhance, ImageOps, ImageChops
        
        try:
            print("Using fallback pattern transfer method...")
            
            # Ensure images are same size
            target_size = sketch_image.size
            textile_image = textile_image.resize(target_size, Image.LANCZOS)
            
            # Extract pattern from textile
            textile_gray = textile_image.convert('L')
            textile_pattern = textile_gray.filter(ImageFilter.FIND_EDGES)
            
            # Extract sketch structure
            sketch_gray = sketch_image.convert('L')
            sketch_edges = sketch_gray.filter(ImageFilter.FIND_EDGES)
            sketch_inverted = ImageOps.invert(sketch_edges)
            
            # Create mask from sketch
            sketch_mask = sketch_inverted.point(lambda x: 255 if x > 128 else 0)
            
            # Apply textile pattern to sketch areas
            # 1. Create base with textile texture
            result = textile_image.copy()
            
            # 2. Blend with sketch structure
            result = Image.blend(result, sketch_image, 0.3)
            
            # 3. Apply pattern overlay
            pattern_overlay = ImageChops.multiply(textile_pattern, sketch_mask)
            pattern_colored = ImageOps.colorize(pattern_overlay, 'black', 'white')
            result = Image.blend(result, pattern_colored.convert('RGB'), 0.4)
            
            # 4. Apply Pantone color if provided
            if pantone_color and pantone_name:
                # Parse hex color
                hex_color = pantone_color.replace('#', '')
                if len(hex_color) == 6:
                    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                else:
                    # Try to extract from name or use a default
                    rgb = (128, 128, 128)
                
                # Create color overlay
                color_overlay = Image.new('RGB', target_size, rgb)
                result = Image.blend(result, color_overlay, 0.2)
                
                # Enhance color
                enhancer = ImageEnhance.Color(result)
                result = enhancer.enhance(1.3)
            
            # 5. Final adjustments
            enhancer = ImageEnhance.Contrast(result)
            result = enhancer.enhance(1.1)
            
            enhancer = ImageEnhance.Sharpness(result)
            result = enhancer.enhance(1.2)
            
            # Convert to base64
            buffer = BytesIO()
            result.save(buffer, format='PNG', quality=95)
            result_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'success': True,
                'result_image': result,
                'description': f'Pattern transferred using PIL fallback method. {"Pantone " + pantone_name + " applied." if pantone_name else ""}',
                'method': 'PIL_Fallback',
                'model_used': 'None (Fallback)',
                'pantone_context': {
                    'color': pantone_color,
                    'name': pantone_name
                } if pantone_color else {}
            }
            
        except Exception as e:
            print(f"Fallback pattern transfer error: {e}")
            return {
                'success': False,
                'error': f'Fallback pattern transfer failed: {str(e)}',
                'exception_type': type(e).__name__
            }
    
    def _create_textile_transfer_prompt(self, pantone_color=None, pantone_name=None):
        """Create detailed prompt for textile pattern transfer"""
        
        base_prompt = "Fill entire shape in image 2 with texture from image 1. Keep lines visible."
        
        if pantone_color and pantone_name:
            base_prompt += f" Use {pantone_color} color."
        
        return base_prompt

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Process textile pattern transfer using Gemini"""
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
                
                # Get required images
                if 'textile_image' not in form:
                    self._send_error(400, "textile_image file required")
                    return
                
                if 'sketch_image' not in form:
                    self._send_error(400, "sketch_image file required")
                    return
                
                # Validate textile image
                textile_field = form['textile_image']
                textile_content = textile_field.file.read()
                textile_filename = getattr(textile_field, 'filename', 'textile.jpg')
                
                textile_validation = validate_image_file(textile_content, textile_filename)
                if not textile_validation['success']:
                    self._send_error(400, f"Textile image error: {textile_validation['error']}")
                    return
                
                # Validate sketch image
                sketch_field = form['sketch_image']
                sketch_content = sketch_field.file.read()
                sketch_filename = getattr(sketch_field, 'filename', 'sketch.jpg')
                
                sketch_validation = validate_image_file(sketch_content, sketch_filename)
                if not sketch_validation['success']:
                    self._send_error(400, f"Sketch image error: {sketch_validation['error']}")
                    return
                
                # Get optional parameters
                pantone_color_field = form.get('pantone_color', [])
                pantone_color = pantone_color_field[0].value if pantone_color_field else None
                
                pantone_name_field = form.get('pantone_name', [])
                pantone_name = pantone_name_field[0].value if pantone_name_field else None
                
                # Prepare images for processing
                textile_image = prepare_image_for_processing(textile_validation['image'])
                sketch_image = prepare_image_for_processing(sketch_validation['image'])
                
                # Initialize Gemini transfer service
                gemini_service = GeminiTextileTransfer()
                
                # Perform pattern transfer
                transfer_result = gemini_service.transfer_textile_pattern(
                    textile_image,
                    sketch_image,
                    pantone_color,
                    pantone_name
                )
                
                if not transfer_result.get('success'):
                    error_msg = transfer_result.get('error', 'Pattern transfer failed')
                    
                    # Include additional context for debugging
                    debug_info = {
                        'finish_reason': transfer_result.get('finish_reason'),
                        'exception_type': transfer_result.get('exception_type'),
                        'response_format': transfer_result.get('response_format'),
                        'retry_suggested': transfer_result.get('retry_suggested', False)
                    }
                    
                    self._send_error(500, error_msg, debug_info)
                    return
                
                # Convert result image to base64
                result_image = transfer_result['result_image']
                result_b64 = image_to_base64(result_image, 'PNG')
                
                # Prepare response data
                response_data = {
                    'transferred_image': f"data:image/png;base64,{result_b64}",
                    'transfer_info': {
                        'method': transfer_result.get('method'),
                        'model_used': transfer_result.get('model_used'),
                        'description': transfer_result.get('description', ''),
                        'pantone_context': transfer_result.get('pantone_context', {})
                    },
                    'image_info': {
                        'textile_size': textile_validation['size'],
                        'sketch_size': sketch_validation['size'],
                        'output_size': result_image.size,
                        'output_format': 'PNG'
                    },
                    'processing_info': {
                        'gemini_model': gemini_service.model_name,
                        'pantone_color_applied': pantone_color is not None,
                        'version': '2.0.0'
                    }
                }
                
                # Store result in database (non-blocking)
                try:
                    storage_result = store_processing_result(
                        {
                            'type': 'gemini_pattern_transfer',
                            'model_used': transfer_result.get('model_used'),
                            'processing_time_ms': timer.elapsed_ms,
                            'pantone_applied': bool(pantone_color)
                        },
                        'gemini_processing'
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
            print(f"Gemini endpoint error: {e}")
            import traceback
            traceback.print_exc()
            
            error_response = create_api_response(
                False, 
                error=f"Gemini processing failed: {str(e)}",
                processing_time_ms=timer.elapsed_ms if timer.elapsed_ms else 0
            )
            self._send_json_response(500, error_response)
            
        finally:
            # Clean up resources
            cleanup_connections()
    
    def do_GET(self):
        """Get Gemini service information"""
        try:
            # Check if Gemini is available
            gemini_client = get_gemini_client()
            gemini_available = gemini_client is not None and (
                hasattr(gemini_client, 'is_available') and gemini_client.is_available() 
                if isinstance(gemini_client, SimpleGeminiClient) 
                else True
            )
            
            response_data = {
                'endpoint': 'gemini',
                'methods': ['POST'],
                'description': 'Textile pattern transfer using Gemini 2.5 Flash Image',
                'model': 'gemini-2.5-flash-image-preview',
                'status': 'available' if gemini_available else 'unavailable',
                'parameters': {
                    'textile_image': 'Source textile/pattern image (required)',
                    'sketch_image': 'Target garment sketch image (required)',
                    'pantone_color': 'Pantone color code (optional)',
                    'pantone_name': 'Pantone color name (optional)'
                },
                'features': {
                    'pattern_transfer': True,
                    'texture_application': True,
                    'pantone_color_integration': True,
                    'photorealistic_output': True,
                    'retry_logic': True
                },
                'capabilities': [
                    'Fabric pattern recognition and transfer',
                    'Garment shape preservation',
                    'Realistic draping simulation',
                    'Color palette integration',
                    'High-resolution output'
                ]
            }
            
            if not gemini_available:
                response_data['error'] = 'Gemini service not available - check API configuration'
            
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
        
        json_data = json.dumps(data, indent=2 if os.getenv('DEBUG') == 'true' else None)
        self.wfile.write(json_data.encode())
    
    def _send_error(self, status_code: int, message: str, debug_info: dict = None):
        """Send error response with optional debug info"""
        error_response = create_api_response(False, error=message)
        if debug_info:
            error_response['debug'] = debug_info
        self._send_json_response(status_code, error_response)