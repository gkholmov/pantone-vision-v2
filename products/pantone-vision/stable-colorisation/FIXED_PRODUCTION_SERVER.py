#!/usr/bin/env python3
"""
PANTONE VISION 2.0 - PRODUCTION SERVER WITH ORIGINAL PANTONE LOGIC
*** ORIGINAL PANTONE IDENTIFICATION LOGIC PRESERVED EXACTLY ***
Enhanced with HuggingFace sketch colorization
"""

import os
import json
import math
import base64
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from io import BytesIO

# Core dependencies
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Pantone Vision 2.0", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Import texture service
from services.texture_application_service import TextureApplicationService

# Configuration
API_KEY = os.getenv('ANTHROPIC_API_KEY')
HF_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB

# Create directories
os.makedirs('uploads', exist_ok=True)
os.makedirs('results', exist_ok=True)

class UniversalColorMatcher:
    """
    *** ORIGINAL UNIVERSAL COLOR MATCHING LOGIC - PRESERVED EXACTLY ***
    Universal color matching system that can identify ANY color
    Uses AI + comprehensive color science instead of hardcoded database
    """
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        
    def rgb_to_lab(self, rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """Convert RGB to CIELAB color space"""
        r, g, b = [x / 255.0 for x in rgb]
        
        # Convert to linear RGB
        def to_linear(c):
            return c / 12.92 if c <= 0.04045 else pow((c + 0.055) / 1.055, 2.4)
        
        r_lin, g_lin, b_lin = map(to_linear, [r, g, b])
        
        # Convert to XYZ using sRGB matrix
        x = r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375
        y = r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750
        z = r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041
        
        # Normalize by D65 white point
        xn, yn, zn = 0.95047, 1.00000, 1.08883
        x, y, z = x/xn, y/yn, z/zn
        
        # Convert to LAB
        def f(t):
            return pow(t, 1/3) if t > 0.008856 else (7.787 * t + 16/116)
        
        fx, fy, fz = map(f, [x, y, z])
        
        L = 116 * fy - 16
        a = 500 * (fx - fy)
        b = 200 * (fy - fz)
        
        return (L, a, b)
    
    def identify_color_with_ai(self, rgb: Tuple[int, int, int], image_description: str = None) -> Dict:
        """
        Use Claude AI to intelligently identify ANY color
        This is the key innovation - AI can identify thousands of colors
        *** ORIGINAL LOGIC PRESERVED EXACTLY ***
        """
        try:
            import anthropic
            
            if not self.api_key or self.api_key == 'your_anthropic_api_key_here':
                return self._fallback_color_analysis(rgb)
                
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Convert to other color spaces for AI analysis
            lab = self.rgb_to_lab(rgb)
            hex_color = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
            
            # Create comprehensive prompt for ANY color identification
            prompt = f"""
You are an expert textile color analyst with access to the complete Pantone color system. 
Analyze this color and identify the closest Pantone match(es):

COLOR DATA:
- RGB: {rgb}
- HEX: {hex_color}
- CIELAB: L*={lab[0]:.1f}, a*={lab[1]:.1f}, b*={lab[2]:.1f}
{f"- Context: {image_description}" if image_description else ""}

TASK: Identify the closest Pantone color match(es) from the ENTIRE Pantone system including:
- PMS (Pantone Matching System)
- TPX/TCX (Textile colors)
- Fashion, Home + Interiors
- Process colors
- Metallic colors
- Fluorescent colors

Consider:
1. Exact color matches if available
2. Closest perceptual matches using Delta-E principles
3. Textile-specific considerations (metamerism, lighting)
4. Multiple potential matches with confidence levels

Respond with JSON:
{{
    "primary_match": {{
        "pantone_code": "PANTONE XXXX XXX",
        "name": "Color Name",
        "confidence": 0.95,
        "delta_e_estimated": 1.2,
        "category": "Red/Blue/Green/etc",
        "collection": "PMS/TPX/TCX/FHI"
    }},
    "alternative_matches": [
        {{
            "pantone_code": "PANTONE XXXX XXX",
            "name": "Alternative Name",
            "confidence": 0.87,
            "why": "reason for alternative"
        }}
    ],
    "color_analysis": {{
        "color_family": "Primary color family",
        "undertones": "Undertone description",
        "textile_suitability": "Assessment for textile use",
        "lighting_sensitivity": "Metamerism assessment"
    }},
    "confidence_factors": {{
        "rgb_precision": "Assessment of RGB accuracy",
        "lighting_conditions": "Assumed lighting conditions",
        "potential_variations": "Possible variations to consider"
    }}
}}
"""
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse AI response
            try:
                response_text = message.content[0].text
                # Extract JSON from response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    ai_analysis = json.loads(response_text[json_start:json_end])
                else:
                    ai_analysis = json.loads(response_text)
                
                # Add technical data
                ai_analysis['technical_data'] = {
                    'rgb': list(rgb),
                    'hex': hex_color,
                    'lab': [round(x, 2) for x in lab],
                    'analysis_method': 'AI_Enhanced',
                    'timestamp': datetime.now().isoformat()
                }
                
                return ai_analysis
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    'primary_match': {
                        'pantone_code': 'AI_ANALYSIS_AVAILABLE',
                        'name': 'See raw_ai_response for detailed analysis',
                        'confidence': 0.80,
                        'category': 'AI_Identified'
                    },
                    'raw_ai_response': response_text,
                    'technical_data': {
                        'rgb': list(rgb),
                        'hex': hex_color, 
                        'lab': [round(x, 2) for x in lab]
                    }
                }
                
        except Exception as e:
            return self._fallback_color_analysis(rgb, error=str(e))
    
    def _fallback_color_analysis(self, rgb: Tuple[int, int, int], error: str = None) -> Dict:
        """
        Fallback color analysis when AI is not available
        Uses color science to provide basic identification
        *** ORIGINAL LOGIC PRESERVED EXACTLY ***
        """
        lab = self.rgb_to_lab(rgb)
        hex_color = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
        
        # Basic color family identification
        r, g, b = rgb
        max_component = max(r, g, b)
        
        if r == max_component and r > g + 30 and r > b + 30:
            color_family = "Red"
            estimated_pantone = "PANTONE 18-XXXX (Red Family)"
        elif g == max_component and g > r + 30 and g > b + 30:
            color_family = "Green" 
            estimated_pantone = "PANTONE 15-XXXX (Green Family)"
        elif b == max_component and b > r + 30 and b > g + 30:
            color_family = "Blue"
            estimated_pantone = "PANTONE 19-XXXX (Blue Family)"
        elif abs(r - g) < 20 and abs(g - b) < 20:
            color_family = "Gray/Neutral"
            estimated_pantone = "PANTONE Cool Gray X"
        else:
            color_family = "Complex/Mixed"
            estimated_pantone = "PANTONE Mixed Color"
        
        return {
            'primary_match': {
                'pantone_code': estimated_pantone,
                'name': f'{color_family} Color',
                'confidence': 0.60,
                'category': color_family,
                'note': 'Basic analysis - AI enhancement recommended'
            },
            'fallback_reason': error or 'AI not available',
            'technical_data': {
                'rgb': list(rgb),
                'hex': hex_color,
                'lab': [round(x, 2) for x in lab],
                'analysis_method': 'Fallback_ColorScience'
            },
            'recommendation': 'Configure ANTHROPIC_API_KEY for full AI-powered color identification'
        }
    
    def analyze_image_color(self, image_array: np.ndarray, method: str = "dominant") -> Tuple[int, int, int]:
        """
        Extract representative color from image
        Supports multiple extraction methods
        *** ORIGINAL LOGIC PRESERVED EXACTLY ***
        """
        if method == "dominant":
            # Simple dominant color extraction
            pixels = image_array.reshape(-1, 3)
            
            # Remove very dark and very light pixels
            filtered_pixels = pixels[
                (pixels.sum(axis=1) > 50) & (pixels.sum(axis=1) < 700)
            ]
            
            if len(filtered_pixels) == 0:
                filtered_pixels = pixels
                
            # Calculate mean color
            mean_color = np.mean(filtered_pixels, axis=0)
            return tuple(int(x) for x in mean_color)
            
        elif method == "center":
            # Extract color from center region
            h, w = image_array.shape[:2]
            center_region = image_array[
                h//4:3*h//4, 
                w//4:3*w//4
            ]
            mean_color = np.mean(center_region.reshape(-1, 3), axis=0)
            return tuple(int(x) for x in mean_color)
            
        else:
            raise ValueError(f"Unknown extraction method: {method}")

class SketchColorizer:
    """Enhanced sketch colorization with HuggingFace AI"""
    
    def __init__(self):
        self.hf_api_key = HF_API_KEY
    
    def colorize_sketch(self, sketch: Image.Image, style: str = "fashion", target_color: str = None, 
                       white_threshold: int = 245, color_variance: int = 30, skin_protection: float = 0.3) -> Dict:
        """AI-powered sketch colorization with HuggingFace"""
        print(f"🎨 SketchColorizer.colorize_sketch called with target_color: {target_color}")
        try:
            # Convert to RGB if needed
            if sketch.mode != 'RGB':
                sketch = sketch.convert('RGB')
            
            # Resize if too large
            if max(sketch.size) > 2048:
                ratio = 2048 / max(sketch.size)
                new_size = tuple(int(dim * ratio) for dim in sketch.size)
                sketch = sketch.resize(new_size, Image.Resampling.LANCZOS)
            
            # Try AI colorization if HF API available
            if self.hf_api_key and self.hf_api_key.startswith('hf_'):
                print(f"🤖 Using HF AI colorization with target_color: {target_color}")
                return self._ai_colorization(sketch, style, target_color)
            else:
                print(f"🎯 Using basic colorization with target_color: {target_color}")
                return self._basic_colorization(sketch, style, target_color, white_threshold, color_variance, skin_protection)
                
        except Exception as e:
            print(f"🚨 Exception in colorize_sketch, falling back to basic: {str(e)}")
            return self._basic_colorization(sketch, style, target_color, white_threshold, color_variance, skin_protection)
    
    def _ai_colorization(self, sketch: Image.Image, style: str, target_color: str = None) -> Dict:
        """HuggingFace AI-powered colorization"""
        try:
            import requests
            
            # Convert sketch to base64
            buffered = BytesIO()
            sketch.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Style-specific prompts
            style_prompts = {
                "fashion": "professional fashion illustration, elegant clothing design, haute couture, clean lines",
                "realistic": "realistic fabric textures, natural lighting, photorealistic clothing",
                "soft": "soft watercolor style, gentle colors, artistic fashion sketch"
            }
            
            base_prompt = style_prompts.get(style, style_prompts['fashion'])
            if target_color:
                prompt = f"{base_prompt}, dominant color {target_color}, matching color palette, high quality, detailed"
            else:
                prompt = f"{base_prompt}, high quality, detailed"
            
            # HuggingFace Inference API
            api_url = "https://api-inference.huggingface.co/models/lllyasviel/sd-controlnet-canny"
            headers = {"Authorization": f"Bearer {self.hf_api_key}"}
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "image": img_base64,
                    "num_inference_steps": 20,
                    "guidance_scale": 7.5,
                    "controlnet_conditioning_scale": 1.0
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                # Success - return AI colorized image
                colorized_data = response.content
                colorized_image = Image.open(BytesIO(colorized_data))
                
                return {
                    'success': True,
                    'colorized_image': colorized_image,
                    'method': 'huggingface_controlnet',
                    'style_applied': style,
                    'processing_time': 15.0
                }
            else:
                # Fallback to basic colorization
                print(f"🚨 HF API request failed, falling back to basic colorization with color: {target_color}")
                return self._basic_colorization(sketch, style, target_color, white_threshold, color_variance, skin_protection)
                
        except Exception as e:
            print(f"🚨 _ai_colorization exception, falling back to basic colorization: {str(e)}")
            return self._basic_colorization(sketch, style, target_color, white_threshold, color_variance, skin_protection)
    
    def _basic_colorization(self, sketch: Image.Image, style: str, target_color: str = None, 
                           white_threshold: int = 245, color_variance: int = 30, skin_protection: float = 0.3) -> Dict:
        """
        UNIVERSAL FASHION SKETCH COLORIZER - ANY GARMENT TYPE
        Uses line-enclosed region detection for precise garment boundary detection
        """
        print(f"🎯 UNIVERSAL COLORIZATION - Target Color: {target_color}, Style: {style}")
        
        # Import the universal colorizer function
        from universal_colorizer import universal_garment_colorizer
        
        # Use the universal approach with configurable parameters
        return universal_garment_colorizer(sketch, target_color, 
                                         white_threshold=white_threshold, 
                                         color_variance=color_variance, 
                                         skin_protection=skin_protection)

# Initialize services
color_matcher = UniversalColorMatcher()
sketch_colorizer = SketchColorizer()
texture_service = TextureApplicationService()

# HTML Interface (same as before)
HTML_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pantone Vision 2.0 - Production Ready</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
    <style>
        body { font-family: 'Inter', -apple-system, sans-serif; }
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .tab-active { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
        .upload-area { border: 2px dashed #e2e8f0; transition: all 0.3s ease; }
        .upload-area:hover { border-color: #667eea; background-color: #f8fafc; }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="gradient-bg text-white py-6">
        <div class="max-w-4xl mx-auto px-4">
            <h1 class="text-3xl font-bold">🎨 Pantone Vision 2.0</h1>
            <p class="text-white/80">Production Ready System - ORIGINAL Pantone Logic + AI Sketch Colorization</p>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-4xl mx-auto px-4 py-8">
        <!-- Tabs -->
        <div class="bg-white rounded-lg shadow-lg mb-8">
            <div class="flex border-b">
                <button onclick="switchTab('color')" id="tab-color" class="tab-active flex-1 py-4 px-6 font-medium">
                    🎯 Pantone Color ID
                </button>
                <button onclick="switchTab('sketch')" id="tab-sketch" class="flex-1 py-4 px-6 font-medium">
                    🎨 Sketch Colorization
                </button>
            </div>
        </div>

        <!-- Color ID Tab -->
        <div id="color-tab" class="tab-content">
            <div class="grid md:grid-cols-2 gap-8">
                <!-- Upload -->
                <div class="bg-white p-6 rounded-lg shadow-lg">
                    <h2 class="text-xl font-bold mb-4">📷 Upload Textile Image or Use Camera</h2>
                    <div class="space-y-4">
                        <div id="color-upload" class="upload-area p-8 text-center rounded-lg cursor-pointer">
                            <p class="text-gray-600 font-medium">Click or drag image here</p>
                            <p class="text-sm text-gray-500 mt-2">PNG, JPG up to 15MB</p>
                        </div>
                        <input type="file" id="color-file" class="hidden" accept="image/*">
                        
                        <!-- Camera Section -->
                        <div class="border-t pt-4">
                            <button id="camera-btn" class="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 px-4 rounded-lg font-medium hover:from-blue-600 hover:to-purple-700">
                                📷 Use Device Camera
                            </button>
                            <div id="camera-section" class="hidden mt-4">
                                <video id="camera-video" class="w-full rounded-lg mb-3" autoplay playsinline></video>
                                <div class="flex gap-2">
                                    <button id="capture-btn" class="flex-1 bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600">
                                        📸 Capture Color
                                    </button>
                                    <button id="stop-camera-btn" class="flex-1 bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600">
                                        ❌ Stop Camera
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="mt-4">
                        <button onclick="analyzeColor()" id="analyze-btn" class="w-full bg-blue-600 text-white py-3 rounded-lg font-medium disabled:bg-gray-300" disabled>
                            🔍 Identify Pantone Color
                        </button>
                    </div>
                </div>

                <!-- Results -->
                <div class="bg-white p-6 rounded-lg shadow-lg">
                    <h2 class="text-xl font-bold mb-4">📊 Color Analysis</h2>
                    <div id="color-results" class="hidden">
                        <div class="flex items-center mb-4">
                            <div id="color-swatch" class="w-16 h-16 rounded-lg border-4 border-white shadow-lg mr-4"></div>
                            <div>
                                <h3 id="color-name" class="font-bold text-lg"></h3>
                                <p id="color-code" class="text-blue-600 font-medium"></p>
                                <p id="color-confidence" class="text-sm text-gray-600"></p>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-4 text-sm">
                            <div><strong>RGB:</strong> <span id="color-rgb"></span></div>
                            <div><strong>HEX:</strong> <span id="color-hex"></span></div>
                        </div>
                        
                        <!-- Related Colors Section -->
                        <div id="related-colors" class="mt-4">
                            <h4 class="font-semibold text-gray-800 mb-2">🎨 Related Colors</h4>
                            <div id="alternative-matches" class="space-y-2">
                                <!-- Alternative matches will be populated here -->
                            </div>
                        </div>
                        
                        <button onclick="useForSketch()" class="w-full mt-4 bg-purple-600 text-white py-2 rounded-lg">
                            🎨 Use for Sketch Colorization
                        </button>
                    </div>
                    <div id="color-placeholder" class="text-center py-12 text-gray-400">
                        <p>Upload image to identify colors</p>
                    </div>
                    <div id="color-loading" class="hidden text-center py-8">
                        <div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                        <p>Analyzing with AI...</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Sketch Tab -->
        <div id="sketch-tab" class="tab-content hidden">
            <div class="grid md:grid-cols-2 gap-8">
                <!-- Upload -->
                <div class="bg-white p-6 rounded-lg shadow-lg">
                    <h2 class="text-xl font-bold mb-4">✏️ Upload Fashion Sketch</h2>
                    <div id="sketch-upload" class="upload-area p-8 text-center rounded-lg cursor-pointer">
                        <p class="text-gray-600 font-medium">Click or drag sketch here</p>
                        <p class="text-sm text-gray-500 mt-2">Line art, fashion designs</p>
                    </div>
                    <input type="file" id="sketch-file" class="hidden" accept="image/*">
                    
                    <div class="mt-4">
                        <label class="block text-sm font-medium mb-2">Style:</label>
                        <select id="sketch-style" class="w-full p-2 border rounded-lg">
                            <option value="fashion">Fashion Illustration</option>
                            <option value="realistic">Realistic Textures</option>
                            <option value="soft">Soft Watercolor</option>
                        </select>
                    </div>
                    
                    <!-- Advanced Colorization Controls -->
                    <div class="mt-4 border-t pt-4">
                        <details class="cursor-pointer">
                            <summary class="text-sm font-medium text-gray-700 hover:text-blue-600">
                                ⚙️ Advanced Settings
                            </summary>
                            <div class="mt-3 space-y-3">
                                <div>
                                    <label class="block text-xs font-medium mb-1 text-gray-600">White Threshold (245 recommended for bright garments):</label>
                                    <input type="range" id="white-threshold" min="200" max="255" value="245" class="w-full h-2 bg-gray-200 rounded-lg">
                                    <div class="flex justify-between text-xs text-gray-500">
                                        <span>200</span>
                                        <span id="white-threshold-value">245</span>
                                        <span>255</span>
                                    </div>
                                </div>
                                <div>
                                    <label class="block text-xs font-medium mb-1 text-gray-600">Color Variance (flexibility in RGB channels):</label>
                                    <input type="range" id="color-variance" min="10" max="50" value="30" class="w-full h-2 bg-gray-200 rounded-lg">
                                    <div class="flex justify-between text-xs text-gray-500">
                                        <span>10</span>
                                        <span id="color-variance-value">30</span>
                                        <span>50</span>
                                    </div>
                                </div>
                                <div>
                                    <label class="block text-xs font-medium mb-1 text-gray-600">Skin Protection (prevent color bleeding):</label>
                                    <input type="range" id="skin-protection" min="0" max="1" step="0.1" value="0.3" class="w-full h-2 bg-gray-200 rounded-lg">
                                    <div class="flex justify-between text-xs text-gray-500">
                                        <span>0.0</span>
                                        <span id="skin-protection-value">0.3</span>
                                        <span>1.0</span>
                                    </div>
                                </div>
                            </div>
                        </details>
                    </div>
                    
                    <!-- Product Information Fields -->
                    <div class="mt-4 space-y-3">
                        <div>
                            <label class="block text-sm font-medium mb-1">Collection Name:</label>
                            <input type="text" id="collection-name" class="w-full p-2 border rounded-lg" placeholder="e.g., Summer 2024">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1">Item Name:</label>
                            <input type="text" id="item-name" class="w-full p-2 border rounded-lg" placeholder="e.g., Structured Bodysuit">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1">SKU:</label>
                            <input type="text" id="item-sku" class="w-full p-2 border rounded-lg" placeholder="e.g., SB-001-WH">
                        </div>
                    </div>
                    
                    <button onclick="colorizeSketch()" id="colorize-btn" class="w-full mt-4 bg-green-600 text-white py-3 rounded-lg font-medium disabled:bg-gray-300" disabled>
                        🎨 Colorize Sketch
                    </button>
                </div>

                <!-- Results -->
                <div class="bg-white p-6 rounded-lg shadow-lg">
                    <h2 class="text-xl font-bold mb-4">🖼️ Colorized Result</h2>
                    <div id="sketch-results" class="hidden">
                        <img id="colorized-image" class="w-full rounded-lg border mb-4" alt="Colorized">
                        <button onclick="downloadResult()" class="w-full bg-green-600 text-white py-2 rounded-lg">
                            📥 Download PNG
                        </button>
                    </div>
                    <div id="sketch-placeholder" class="text-center py-12 text-gray-400">
                        <p>Upload sketch to colorize</p>
                    </div>
                    <div id="sketch-loading" class="hidden text-center py-8">
                        <div class="animate-spin w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                        <p>Colorizing sketch...</p>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let currentColorData = null;
        let currentSketch = null;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            lucide.createIcons();
            setupFileUploads();
            setupCamera();
            setupAdvancedControls();
        });
        
        function switchTab(tab) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('[id^="tab-"]').forEach(el => el.classList.remove('tab-active'));
            
            document.getElementById(tab + '-tab').classList.remove('hidden');
            document.getElementById('tab-' + tab).classList.add('tab-active');
        }
        
        function setupFileUploads() {
            // Color upload
            const colorUpload = document.getElementById('color-upload');
            const colorFile = document.getElementById('color-file');
            
            colorUpload.onclick = () => colorFile.click();
            colorFile.onchange = (e) => {
                if (e.target.files[0]) {
                    document.getElementById('analyze-btn').disabled = false;
                    colorUpload.innerHTML = '<p class="text-green-600">✅ Image selected: ' + e.target.files[0].name + '</p>';
                }
            };
            
            // Sketch upload
            const sketchUpload = document.getElementById('sketch-upload');
            const sketchFile = document.getElementById('sketch-file');
            
            sketchUpload.onclick = () => sketchFile.click();
            sketchFile.onchange = (e) => {
                if (e.target.files[0]) {
                    currentSketch = e.target.files[0];
                    document.getElementById('colorize-btn').disabled = false;
                    sketchUpload.innerHTML = '<p class="text-green-600">✅ Sketch selected: ' + e.target.files[0].name + '</p>';
                }
            };
        }
        
        // Camera functionality
        let cameraStream = null;
        let currentImage = null;
        
        function setupCamera() {
            const cameraBtn = document.getElementById('camera-btn');
            const captureBtn = document.getElementById('capture-btn');
            const stopCameraBtn = document.getElementById('stop-camera-btn');
            const cameraSection = document.getElementById('camera-section');
            const video = document.getElementById('camera-video');
            
            cameraBtn.addEventListener('click', async () => {
                try {
                    cameraStream = await navigator.mediaDevices.getUserMedia({ 
                        video: { 
                            facingMode: 'environment',
                            width: { ideal: 1280 },
                            height: { ideal: 720 }
                        } 
                    });
                    video.srcObject = cameraStream;
                    cameraSection.classList.remove('hidden');
                    cameraBtn.textContent = '📷 Camera Active';
                    cameraBtn.classList.add('bg-green-500');
                } catch (err) {
                    alert('Camera access denied or not available: ' + err.message);
                }
            });
            
            captureBtn.addEventListener('click', () => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);
                
                canvas.toBlob(blob => {
                    const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    
                    const fileInput = document.getElementById('color-file');
                    fileInput.files = dataTransfer.files;
                    
                    const uploadArea = document.getElementById('color-upload');
                    uploadArea.innerHTML = '<p class="text-green-600">✅ Camera capture ready for analysis</p>';
                    
                    document.getElementById('analyze-btn').disabled = false;
                    
                    stopCamera();
                }, 'image/jpeg', 0.9);
            });
            
            stopCameraBtn.addEventListener('click', stopCamera);
        }
        
        function stopCamera() {
            if (cameraStream) {
                cameraStream.getTracks().forEach(track => track.stop());
                cameraStream = null;
            }
            const cameraSection = document.getElementById('camera-section');
            const cameraBtn = document.getElementById('camera-btn');
            cameraSection.classList.add('hidden');
            cameraBtn.textContent = '📷 Use Device Camera';
            cameraBtn.classList.remove('bg-green-500');
        }
        
        function setupAdvancedControls() {
            // White Threshold slider
            const whiteThreshold = document.getElementById('white-threshold');
            const whiteThresholdValue = document.getElementById('white-threshold-value');
            whiteThreshold.addEventListener('input', (e) => {
                whiteThresholdValue.textContent = e.target.value;
            });
            
            // Color Variance slider
            const colorVariance = document.getElementById('color-variance');
            const colorVarianceValue = document.getElementById('color-variance-value');
            colorVariance.addEventListener('input', (e) => {
                colorVarianceValue.textContent = e.target.value;
            });
            
            // Skin Protection slider
            const skinProtection = document.getElementById('skin-protection');
            const skinProtectionValue = document.getElementById('skin-protection-value');
            skinProtection.addEventListener('input', (e) => {
                skinProtectionValue.textContent = e.target.value;
            });
        }
        
        async function analyzeColor() {
            const fileInput = document.getElementById('color-file');
            if (!fileInput.files[0]) return;
            
            document.getElementById('color-placeholder').classList.add('hidden');
            document.getElementById('color-results').classList.add('hidden');
            document.getElementById('color-loading').classList.remove('hidden');
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            try {
                const response = await fetch('/identify-color', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    displayColorResults(result.data);
                    currentColorData = result.data;
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Network error: ' + error.message);
            } finally {
                document.getElementById('color-loading').classList.add('hidden');
            }
        }
        
        function displayColorResults(data) {
            const match = data.primary_match;
            const tech = data.technical_data;
            
            document.getElementById('color-swatch').style.backgroundColor = tech.hex;
            document.getElementById('color-name').textContent = match.name;
            document.getElementById('color-code').textContent = match.pantone_code;
            document.getElementById('color-confidence').textContent = 'Confidence: ' + Math.round(match.confidence * 100) + '%';
            document.getElementById('color-rgb').textContent = tech.rgb.join(', ');
            document.getElementById('color-hex').textContent = tech.hex;
            
            // Display alternative/related colors
            const alternativesContainer = document.getElementById('alternative-matches');
            alternativesContainer.innerHTML = '';
            
            if (data.alternative_matches && data.alternative_matches.length > 0) {
                data.alternative_matches.forEach(alt => {
                    const altDiv = document.createElement('div');
                    altDiv.className = 'flex items-center space-x-3 p-2 bg-gray-50 rounded-lg';
                    altDiv.innerHTML = `
                        <div class="w-8 h-8 rounded border shadow" style="background-color: ${alt.hex || '#ccc'}"></div>
                        <div class="flex-1">
                            <div class="font-medium text-sm">${alt.pantone_code}</div>
                            <div class="text-xs text-gray-600">${alt.name}</div>
                            <div class="text-xs text-blue-600">${Math.round(alt.confidence * 100)}% confidence</div>
                        </div>
                    `;
                    alternativesContainer.appendChild(altDiv);
                });
            } else {
                alternativesContainer.innerHTML = '<p class="text-sm text-gray-500">No alternative matches available</p>';
            }
            
            document.getElementById('color-results').classList.remove('hidden');
        }
        
        function useForSketch() {
            switchTab('sketch');
        }
        
        async function colorizeSketch() {
            if (!currentSketch) return;
            
            document.getElementById('sketch-placeholder').classList.add('hidden');
            document.getElementById('sketch-results').classList.add('hidden');
            document.getElementById('sketch-loading').classList.remove('hidden');
            
            const formData = new FormData();
            formData.append('sketch', currentSketch);
            formData.append('style', document.getElementById('sketch-style').value);
            
            // Add product information
            formData.append('collection_name', document.getElementById('collection-name').value || '');
            formData.append('item_name', document.getElementById('item-name').value || '');
            formData.append('item_sku', document.getElementById('item-sku').value || '');
            
            // Add color data if available
            if (currentColorData) {
                console.log('🎨 Sending color data to colorization:', currentColorData.primary_match?.pantone_code);
                formData.append('color_data', JSON.stringify(currentColorData));
            } else {
                console.log('❌ NO COLOR DATA AVAILABLE - Please identify color first');
            }
            
            // Add advanced colorization parameters
            formData.append('white_threshold', document.getElementById('white-threshold').value);
            formData.append('color_variance', document.getElementById('color-variance').value);
            formData.append('skin_protection', document.getElementById('skin-protection').value);
            
            try {
                const response = await fetch('/colorize-sketch', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('colorized-image').src = 'data:image/png;base64,' + result.data.colorized_image_base64;
                    document.getElementById('sketch-results').classList.remove('hidden');
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Network error: ' + error.message);
            } finally {
                document.getElementById('sketch-loading').classList.add('hidden');
            }
        }
        
        function downloadResult() {
            const img = document.getElementById('colorized-image');
            const link = document.createElement('a');
            link.download = 'colorized-sketch-' + Date.now() + '.png';
            link.href = img.src;
            link.click();
        }
    </script>
</body>
</html>
"""

# Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=HTML_INTERFACE)

@app.get("/texture-ui")
async def texture_interface():
    """Serve the enhanced texture interface"""
    try:
        with open('templates/texture_interface.html', 'r') as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Texture interface not found</h1>", status_code=404)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "app": "Pantone Vision 2.0",
        "version": "2.0.0", 
        "timestamp": datetime.now().isoformat(),
        "features": {
            "pantone_identification": "available",
            "sketch_colorization": "available", 
            "texture_application": "available",
            "claude_api": "configured" if API_KEY else "not_configured",
            "huggingface_api": "configured" if HF_API_KEY and HF_API_KEY.startswith('hf_') else "not_configured"
        },
        "pantone_logic": "ORIGINAL - PRESERVED EXACTLY"
    }

@app.post("/identify-color")
async def identify_color(file: UploadFile = File(...)):
    """*** USES ORIGINAL PANTONE IDENTIFICATION LOGIC EXACTLY ***"""
    start_time = datetime.now()
    
    try:
        # Validate file
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File too large (max {MAX_FILE_SIZE//1024//1024}MB)")
        
        # Process image
        image = Image.open(file.file)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract dominant color using ORIGINAL method
        image_array = np.array(image)
        dominant_rgb = color_matcher.analyze_image_color(image_array, method="dominant")
        print(f"🎨 DOMINANT COLOR EXTRACTED: RGB{dominant_rgb}")
        
        # Identify color using ORIGINAL AI logic
        result = color_matcher.identify_color_with_ai(
            dominant_rgb, 
            image_description="textile color sample"
        )
        print(f"🤖 AI RESULT: {result}")
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": processing_time,
            "pantone_logic": "ORIGINAL - PRESERVED"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/colorize-sketch")
async def colorize_sketch(
    sketch: UploadFile = File(...),
    style: str = Form("fashion"),
    collection_name: str = Form(""),
    item_name: str = Form(""),
    item_sku: str = Form(""),
    color_data: str = Form(""),
    white_threshold: int = Form(245),
    color_variance: int = Form(30),
    skin_protection: float = Form(0.3)
):
    """Enhanced sketch colorization with HuggingFace"""
    start_time = datetime.now()
    
    try:
        if sketch.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Process sketch with color information
        sketch_image = Image.open(sketch.file)
        
        # Parse color data if available, otherwise AUTO-IDENTIFY from sketch
        target_color = None
        color_info = None
        if color_data:
            print(f"🎨 COLOR DATA RECEIVED: {color_data[:200]}...")  # Show first 200 chars
            try:
                color_info = json.loads(color_data)
                # Check multiple possible locations for hex color data
                target_color = None
                
                # Primary location: primary_match.technical_data.hex
                if ('primary_match' in color_info and 
                    'technical_data' in color_info['primary_match'] and 
                    'hex' in color_info['primary_match']['technical_data']):
                    target_color = color_info['primary_match']['technical_data']['hex']
                    print(f"✅ IDENTIFIED COLOR FROM PRIMARY_MATCH: {target_color}")
                
                # Fallback location: technical_data.hex at root level
                elif 'technical_data' in color_info and 'hex' in color_info['technical_data']:
                    target_color = color_info['technical_data']['hex']
                    print(f"✅ IDENTIFIED COLOR FROM ROOT TECHNICAL_DATA: {target_color}")
                
                # Debug fallback: show structure if no hex found
                else:
                    print(f"❌ NO HEX FOUND IN COLOR DATA")
                    print(f"   Available keys: {list(color_info.keys())}")
                    if 'primary_match' in color_info:
                        print(f"   Primary match keys: {list(color_info['primary_match'].keys())}")
                        
            except Exception as e:
                print(f"🚨 COLOR DATA PARSING FAILED: {str(e)}")
                print(f"🚨 Raw color_data: {color_data}")
                target_color = None
        else:
            print("ℹ️  NO COLOR DATA PROVIDED - Will use auto-identification")
        
        # AUTO-IDENTIFY PANTONE COLOR if no color provided
        # REMOVED COLOR-FIRST LOGIC - Now handled by garment-first approach in colorize_sketch()
        if not target_color:
            print("ℹ️  NO PANTONE COLOR PROVIDED - Will use garment-first AI identification in colorizer")
            # Let the colorizer handle both garment identification AND color selection
            target_color = None  # This will trigger garment-first logic in _basic_colorization
        
        print(f"🖌️  COLORIZING WITH COLOR: {target_color}")
        result = sketch_colorizer.colorize_sketch(sketch_image, style, target_color=target_color, 
                                                 white_threshold=white_threshold, color_variance=color_variance, skin_protection=skin_protection)
        
        if not result['success']:
            raise Exception(result.get('error', 'Colorization failed'))
        
        # Convert to base64
        buffered = BytesIO()
        result['colorized_image'].save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "success": True,
            "data": {
                "colorized_image_base64": img_base64,
                "method": result.get('method', 'enhanced'),
                "style_applied": result.get('style_applied', style),
                "processing_time_ms": processing_time,
                "auto_identified_color": target_color,
                "pantone_info": color_info.get('primary_match', {}) if color_info else None,
                "clothing_areas_detected": result.get('clothing_areas_detected', 0)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/textures/available")
async def get_available_textures():
    """Get list of available texture types and their descriptions"""
    try:
        textures_info = texture_service.get_available_textures()
        return {
            "success": True,
            "data": textures_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/apply-texture")
async def apply_texture(
    image: UploadFile = File(...),
    texture_image: UploadFile = File(...),
    intensity: float = Form(0.8),
    color_data: str = Form("")
):
    """Apply custom texture from uploaded image to a colorized sketch"""
    start_time = datetime.now()
    
    try:
        # Validate files
        if image.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"Image file too large (max {MAX_FILE_SIZE//1024//1024}MB)")
        if texture_image.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"Texture file too large (max {MAX_FILE_SIZE//1024//1024}MB)")
        
        # Load and process colorized image
        colorized_image = Image.open(image.file)
        if colorized_image.mode != 'RGB':
            colorized_image = colorized_image.convert('RGB')
            
        # Load and process texture image
        texture_img = Image.open(texture_image.file)
        if texture_img.mode != 'RGB':
            texture_img = texture_img.convert('RGB')
        
        # Parse color data if provided
        pantone_colors = None
        if color_data:
            try:
                color_info = json.loads(color_data)
                if 'primary_match' in color_info:
                    pantone_colors = [color_info['primary_match']]
            except Exception as e:
                print(f"Warning: Could not parse color data: {e}")
        
        # Apply custom texture
        result = texture_service.apply_custom_texture(
            colorized_image=colorized_image,
            texture_image=texture_img,
            pantone_colors=pantone_colors,
            intensity=intensity
        )
        
        if not result.get('success'):
            return {
                "success": False,
                "error": result.get('error', 'Texture application failed'),
                "timestamp": datetime.now().isoformat()
            }
        
        # Convert result image to base64
        textured_image = result['textured_image']
        buffered = BytesIO()
        textured_image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "success": True,
            "data": {
                "textured_image_base64": img_base64,
                "texture_type": "custom_upload",
                "intensity_applied": intensity,
                "method": result.get('texture_processing', {}).get('method', 'unknown'),
                "mask_coverage": result.get('mask_info', {}).get('coverage_percentage', 0),
                "pantone_colors": pantone_colors,
                "workflow_time_seconds": result.get('workflow_time_seconds', 0)
            },
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/colorize-and-texture")
async def colorize_and_texture(
    sketch: UploadFile = File(...),
    texture_image: UploadFile = File(...),
    style: str = Form("fashion"),
    intensity: float = Form(0.8),
    color_data: str = Form("")
):
    """Complete workflow: colorize sketch then apply custom texture"""
    start_time = datetime.now()
    
    try:
        if sketch.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Sketch file too large")
        if texture_image.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Texture file too large")
        
        # Step 1: Colorize sketch (using existing logic)
        sketch_image = Image.open(sketch.file)
        
        # Load texture image
        texture_img = Image.open(texture_image.file)
        if texture_img.mode != 'RGB':
            texture_img = texture_img.convert('RGB')
        
        # Parse color data
        target_color = None
        pantone_colors = None
        if color_data:
            try:
                color_info = json.loads(color_data)
                if 'technical_data' in color_info and 'hex' in color_info['technical_data']:
                    target_color = color_info['technical_data']['hex']
                if 'primary_match' in color_info:
                    pantone_colors = [color_info['primary_match']]
            except Exception as e:
                print(f"Color data parsing failed: {e}")
        
        # Colorize sketch
        colorization_result = sketch_colorizer.colorize_sketch(
            sketch_image, style, target_color=target_color,
            white_threshold=white_threshold, color_variance=color_variance, skin_protection=skin_protection
        )
        
        if not colorization_result.get('success'):
            return {
                "success": False,
                "error": colorization_result.get('error', 'Colorization failed'),
                "timestamp": datetime.now().isoformat()
            }
        
        # Step 2: Apply custom texture
        colorized_image = colorization_result['colorized_image']
        
        texture_result = texture_service.apply_custom_texture(
            colorized_image=colorized_image,
            texture_image=texture_img,
            pantone_colors=pantone_colors,
            intensity=intensity
        )
        
        if not texture_result.get('success'):
            return {
                "success": False,
                "error": texture_result.get('error', 'Texture application failed'),
                "timestamp": datetime.now().isoformat()
            }
        
        # Convert final image to base64
        final_image = texture_result['textured_image']
        buffered = BytesIO()
        final_image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "success": True,
            "data": {
                "final_image_base64": img_base64,
                "colorization_method": colorization_result.get('method', 'unknown'),
                "texture_type": "custom_upload",
                "intensity_applied": intensity,
                "texture_method": texture_result.get('texture_processing', {}).get('method', 'unknown'),
                "garment_analysis": colorization_result.get('garment_analysis', {}),
                "pantone_info": colorization_result.get('pantone_info', {}),
                "mask_coverage": texture_result.get('mask_info', {}).get('coverage_percentage', 0),
                "total_workflow_time": texture_result.get('workflow_time_seconds', 0)
            },
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Startup
if __name__ == "__main__":
    print("🎨 PANTONE VISION 2.0 - FIXED PRODUCTION SERVER")
    print("=" * 60)
    print(f"✅ Server starting at: http://127.0.0.1:8000")
    print(f"✅ Health check: http://127.0.0.1:8000/health")
    print(f"✅ Claude API: {'Configured' if API_KEY else 'Not configured'}")
    print(f"✅ HuggingFace API: {'Configured' if HF_API_KEY and HF_API_KEY.startswith('hf_') else 'Not configured'}")
    print("🔥 PANTONE LOGIC: ORIGINAL - PRESERVED EXACTLY")
    print("🚀 Enhanced with HuggingFace sketch colorization")
    print("=" * 60)
    
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)