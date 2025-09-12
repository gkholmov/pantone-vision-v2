#!/usr/bin/env python3
"""
Utility functions for Pantone Vision API
Shared helper functions for image processing and validation
"""

import base64
import io
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from PIL import Image
import numpy as np
from email.message import EmailMessage
from email import policy

from .config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS

def validate_image_file(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Validate uploaded image file
    Returns validation result with success status and details
    """
    try:
        # Check file size
        if len(file_content) > MAX_FILE_SIZE:
            return {
                'success': False,
                'error': f'File size ({len(file_content)} bytes) exceeds limit ({MAX_FILE_SIZE} bytes)'
            }
        
        # Check file extension
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if file_ext not in ALLOWED_EXTENSIONS:
            return {
                'success': False,
                'error': f'File extension .{file_ext} not allowed. Supported: {", ".join(ALLOWED_EXTENSIONS)}'
            }
        
        # Try to open and validate image
        try:
            image = Image.open(io.BytesIO(file_content))
            image.verify()  # Verify it's a valid image
            
            # Re-open for processing (verify closes the file)
            image = Image.open(io.BytesIO(file_content))
            
            return {
                'success': True,
                'image': image,
                'format': image.format,
                'size': image.size,
                'mode': image.mode,
                'file_size': len(file_content)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Invalid image file: {str(e)}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'File validation error: {str(e)}'
        }

def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Convert PIL Image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode()

def base64_to_image(base64_str: str) -> Image.Image:
    """Convert base64 string to PIL Image"""
    if base64_str.startswith('data:image/'):
        base64_str = base64_str.split(',')[1]
    return Image.open(io.BytesIO(base64.b64decode(base64_str)))

def prepare_image_for_processing(image: Image.Image, max_size: int = 2048) -> Image.Image:
    """
    Prepare image for AI processing - resize if needed, convert to RGB
    """
    # Convert to RGB if necessary
    if image.mode in ('RGBA', 'LA', 'P'):
        # Create white background for transparency
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize if too large
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    return image

def create_api_response(success: bool, data: Dict[str, Any] = None, 
                       error: str = None, processing_time_ms: float = None) -> Dict[str, Any]:
    """
    Create standardized API response
    """
    response = {
        'success': success,
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    }
    
    if success and data:
        response['data'] = data
    elif not success and error:
        response['error'] = error
    
    if processing_time_ms is not None:
        response['processing_time_ms'] = round(processing_time_ms, 2)
    
    return response

def extract_colors_from_image(image: Image.Image, num_colors: int = 10) -> List[Dict[str, Any]]:
    """
    Extract dominant colors from image using quantization
    """
    try:
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize for faster processing
        if max(image.size) > 256:
            ratio = 256 / max(image.size)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Get colors using PIL quantize
        quantized = image.quantize(colors=num_colors)
        palette = quantized.getpalette()
        
        colors = []
        for i in range(num_colors):
            rgb_start = i * 3
            if rgb_start + 2 < len(palette):
                r, g, b = palette[rgb_start:rgb_start + 3]
                colors.append({
                    'rgb': [r, g, b],
                    'hex': f'#{r:02x}{g:02x}{b:02x}',
                    'index': i
                })
        
        return colors
        
    except Exception as e:
        print(f"Color extraction error: {e}")
        return []

def safe_json_serialize(obj: Any) -> Any:
    """
    Safely serialize objects to JSON-compatible format
    """
    if isinstance(obj, (np.ndarray, np.generic)):
        return obj.tolist()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Image.Image):
        return f"PIL.Image({obj.size}, {obj.mode})"
    elif hasattr(obj, '__dict__'):
        return str(obj)
    else:
        return obj

class ProcessingTimer:
    """Context manager for timing operations"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
    
    @property
    def elapsed_ms(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

class MultipartField:
    """Represents a field in multipart form data"""
    def __init__(self, name: str, value: Any = None, filename: str = None):
        self.name = name
        self.value = value
        self.filename = filename
        self.file = None
        
        # For file fields, create a file-like object
        if isinstance(value, bytes):
            self.file = io.BytesIO(value)

class MultipartParser:
    """Python 3.13+ compatible multipart form data parser (replaces cgi.FieldStorage)"""
    
    def __init__(self, body: bytes, content_type: str):
        self.fields = {}
        self._parse(body, content_type)
    
    def _parse(self, body: bytes, content_type: str):
        """Parse multipart form data"""
        try:
            # Extract boundary from content type
            boundary_match = re.search(r'boundary=([^;]+)', content_type)
            if not boundary_match:
                return
            
            boundary = boundary_match.group(1).strip('"')
            boundary_bytes = ('--' + boundary).encode()
            
            # Split by boundary
            parts = body.split(boundary_bytes)
            
            for part in parts[1:-1]:  # Skip first empty part and last closing part
                if not part.strip():
                    continue
                
                # Split headers and body
                if b'\r\n\r\n' not in part:
                    continue
                    
                headers_data, body_data = part.split(b'\r\n\r\n', 1)
                
                # Parse headers
                headers_text = headers_data.decode('utf-8', errors='ignore')
                
                # Extract field name
                name_match = re.search(r'name="([^"]*)"', headers_text)
                if not name_match:
                    continue
                
                field_name = name_match.group(1)
                
                # Check if it's a file field
                filename_match = re.search(r'filename="([^"]*)"', headers_text)
                
                if filename_match:
                    # File field
                    filename = filename_match.group(1)
                    field = MultipartField(field_name, body_data, filename)
                else:
                    # Regular field
                    field = MultipartField(field_name, body_data.decode('utf-8', errors='ignore'))
                
                self.fields[field_name] = field
                
        except Exception as e:
            print(f"Multipart parsing error: {e}")
    
    def get(self, key: str, default=None):
        """Get field value(s) - returns list for compatibility with cgi.FieldStorage"""
        if key in self.fields:
            return [self.fields[key]]
        return default or []
    
    def __contains__(self, key: str) -> bool:
        return key in self.fields
    
    def __getitem__(self, key: str):
        return self.fields[key]