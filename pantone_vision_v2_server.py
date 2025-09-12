#!/usr/bin/env python3
"""
Pantone Vision 2.0 - Unified Server
Combines Pantone color identification with fashion sketch colorization
Preserves existing universal color identification logic
"""

import os
import json
import base64
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from io import BytesIO

import uvicorn
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import our services
from services.universal_color_system import UniversalColorMatcher
from services.sketch_colorization_service import SketchColorizationService

# Load environment configuration
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Pantone Vision 2.0",
    description="Universal Pantone Color Identification + Fashion Sketch Colorization",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
color_matcher = UniversalColorMatcher()
sketch_colorizer = SketchColorizationService()

# Global configuration
CONFIG = {
    'app_name': os.getenv('APP_NAME', 'Pantone Vision 2.0'),
    'app_version': os.getenv('APP_VERSION', '2.0.0'),
    'debug': os.getenv('DEBUG', 'true').lower() == 'true',
    'max_file_size_mb': int(os.getenv('MAX_FILE_SIZE_MB', '15')),
    'supported_formats': os.getenv('SUPPORTED_FORMATS', 'png,jpg,jpeg,webp').split(','),
    'upload_dir': os.getenv('UPLOAD_DIR', './uploads'),
    'results_dir': os.getenv('RESULTS_DIR', './results'),
}

# Ensure directories exist
for dir_path in [CONFIG['upload_dir'], CONFIG['results_dir'], 
                 os.path.join(CONFIG['upload_dir'], 'textiles'),
                 os.path.join(CONFIG['upload_dir'], 'sketches')]:
    os.makedirs(dir_path, exist_ok=True)

# Pydantic models
class ColorAnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str
    processing_time_ms: float

class ColorizationResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str
    processing_time_ms: float

# Utility functions
def validate_image_file(file: UploadFile) -> bool:
    """Validate uploaded image file"""
    if not file.filename:
        return False
        
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in CONFIG['supported_formats']:
        return False
        
    return True

def save_uploaded_file(file: UploadFile, subdir: str) -> str:
    """Save uploaded file and return path"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(CONFIG['upload_dir'], subdir, filename)
    
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    return file_path

def image_to_base64(image: Image.Image, format: str = 'PNG') -> str:
    """Convert PIL Image to base64 string"""
    buffered = BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode()

# Routes

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main interface"""
    try:
        with open("templates/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>Pantone Vision 2.0</h1>
                <p>Template not found. Please ensure templates/index.html exists.</p>
            </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": CONFIG['app_name'],
        "version": CONFIG['app_version'],
        "timestamp": datetime.now().isoformat(),
        "services": {
            "pantone_identification": "available",
            "sketch_colorization": "available",
            "claude_api": "configured" if color_matcher.api_key else "not_configured",
            "huggingface_api": "configured" if sketch_colorizer.hf_api_key != 'your_hf_token_here' else "not_configured"
        }
    }

@app.post("/identify-color", response_model=ColorAnalysisResponse)
async def identify_color(
    file: Optional[UploadFile] = File(None),
    rgb: Optional[str] = Form(None)
):
    """
    Identify Pantone color from uploaded image or RGB values
    Preserves existing universal color identification logic
    """
    start_time = datetime.now()
    
    try:
        if file:
            # Validate file
            if not validate_image_file(file):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid file format. Supported: {', '.join(CONFIG['supported_formats'])}"
                )
            
            # Check file size
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            
            if file_size > CONFIG['max_file_size_mb'] * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds {CONFIG['max_file_size_mb']}MB limit"
                )
            
            # Save file
            file_path = save_uploaded_file(file, 'textiles')
            
            # Process image
            image = Image.open(file_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract dominant color
            image_array = np.array(image)
            dominant_rgb = color_matcher.analyze_image_color(image_array, method="dominant")
            
        elif rgb:
            # Parse RGB values
            try:
                rgb_values = json.loads(rgb)
                if len(rgb_values) != 3 or not all(0 <= v <= 255 for v in rgb_values):
                    raise ValueError("Invalid RGB values")
                dominant_rgb = tuple(rgb_values)
            except (json.JSONDecodeError, ValueError):
                raise HTTPException(status_code=400, detail="Invalid RGB format")
        else:
            raise HTTPException(status_code=400, detail="Either file or RGB values must be provided")
        
        # Identify color using preserved logic
        result = color_matcher.identify_color_with_ai(
            dominant_rgb, 
            image_description="textile color sample" if file else None
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ColorAnalysisResponse(
            success=True,
            data=result,
            timestamp=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ColorAnalysisResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )

@app.post("/colorize-sketch", response_model=ColorizationResponse)
async def colorize_sketch(
    sketch: UploadFile = File(...),
    style_prompt: str = Form("fashion illustration"),
    pantone_colors: Optional[str] = Form(None)
):
    """
    Colorize fashion sketch using AI with optional Pantone color guidance
    """
    start_time = datetime.now()
    
    try:
        # Validate sketch file
        if not validate_image_file(sketch):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file format. Supported: {', '.join(CONFIG['supported_formats'])}"
            )
        
        # Check file size
        sketch.file.seek(0, 2)
        file_size = sketch.file.tell()
        sketch.file.seek(0)
        
        if file_size > CONFIG['max_file_size_mb'] * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {CONFIG['max_file_size_mb']}MB limit"
            )
        
        # Save sketch file
        sketch_path = save_uploaded_file(sketch, 'sketches')
        
        # Load and process sketch
        sketch_image = Image.open(sketch_path)
        if sketch_image.mode not in ['RGB', 'L']:
            sketch_image = sketch_image.convert('RGB')
        
        # Parse Pantone colors if provided
        pantone_color_data = []
        if pantone_colors:
            try:
                pantone_color_data = json.loads(pantone_colors)
            except json.JSONDecodeError:
                # Ignore invalid JSON, proceed without Pantone colors
                pass
        
        # Perform full colorization workflow
        result = sketch_colorizer.process_full_workflow(
            sketch_image=sketch_image,
            pantone_colors=pantone_color_data,
            style_prompt=style_prompt
        )
        
        if not result.get('success'):
            raise Exception(result.get('error', 'Colorization failed'))
        
        # Convert result image to base64
        colorized_image = result['colorized_image']
        result['colorized_image_base64'] = image_to_base64(colorized_image)
        
        # Save result to disk
        result_filename = f"colorized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        result_path = os.path.join(CONFIG['results_dir'], result_filename)
        colorized_image.save(result_path)
        result['result_file_path'] = result_path
        
        # Remove the PIL Image from result (not JSON serializable)
        result.pop('colorized_image', None)
        result.pop('original_sketch', None)
        result.pop('processed_sketch', None)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ColorizationResponse(
            success=True,
            data=result,
            timestamp=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ColorizationResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download generated files"""
    file_path = os.path.join(CONFIG['results_dir'], filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type='application/octet-stream',
        filename=filename
    )

@app.get("/api/config")
async def get_config():
    """Get frontend configuration"""
    return {
        "app_name": CONFIG['app_name'],
        "app_version": CONFIG['app_version'],
        "max_file_size_mb": CONFIG['max_file_size_mb'],
        "supported_formats": CONFIG['supported_formats'],
        "features": {
            "pantone_identification": os.getenv('ENABLE_PANTONE_IDENTIFICATION', 'true').lower() == 'true',
            "sketch_colorization": os.getenv('ENABLE_SKETCH_COLORIZATION', 'true').lower() == 'true',
            "region_selection": os.getenv('ENABLE_REGION_SELECTION', 'true').lower() == 'true',
            "batch_processing": os.getenv('ENABLE_BATCH_PROCESSING', 'false').lower() == 'true'
        },
        "api_status": {
            "claude": color_matcher.api_key and color_matcher.api_key != 'your_anthropic_api_key_here',
            "huggingface": sketch_colorizer.hf_api_key != 'your_hf_token_here'
        }
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "detail": str(exc)}
    )

@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🎨 Pantone Vision 2.0 Starting...")
    print("=" * 60)
    print(f"App Name: {CONFIG['app_name']}")
    print(f"Version: {CONFIG['app_version']}")
    print(f"Debug Mode: {CONFIG['debug']}")
    print(f"Max File Size: {CONFIG['max_file_size_mb']}MB")
    print(f"Supported Formats: {', '.join(CONFIG['supported_formats'])}")
    print("\nService Status:")
    print(f"  ✅ Pantone Color Identification: Ready")
    print(f"  ✅ Sketch Colorization: Ready")
    print(f"  {'✅' if color_matcher.api_key != 'your_anthropic_api_key_here' else '❌'} Claude API: {'Configured' if color_matcher.api_key != 'your_anthropic_api_key_here' else 'Not configured'}")
    print(f"  {'✅' if sketch_colorizer.hf_api_key != 'your_hf_token_here' else '❌'} HuggingFace API: {'Configured' if sketch_colorizer.hf_api_key != 'your_hf_token_here' else 'Not configured'}")
    print("=" * 60)

# Main execution
if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '8000'))
    debug = CONFIG['debug']
    
    print(f"\n🚀 Starting Pantone Vision 2.0 Server")
    print(f"📍 Server will be available at: http://{host}:{port}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔧 Health Check: http://{host}:{port}/health")
    
    uvicorn.run(
        "pantone_vision_v2_server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning"
    )