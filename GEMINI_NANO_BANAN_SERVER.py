#!/usr/bin/env python3
"""
PANTONE VISION 2.0 - GEMINI NANO BANAN INTEGRATION
Pantone color identification + Gemini 2.5 Flash Image for textile pattern transfer
"""

import os
import json
import base64
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from io import BytesIO

# FastAPI and web framework imports
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

# Image processing
from PIL import Image
import numpy as np

# Google GenAI SDK (2025 version)
from google import genai
from google.genai import types

# Original Pantone logic
from ORIGINAL_PANTONE_LOGIC import UniversalColorMatcher

# Configuration
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB

# Get API key from environment variables (SECURE)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

# Set API key as environment variable for Google GenAI SDK
os.environ['GOOGLE_API_KEY'] = GEMINI_API_KEY

app = FastAPI(title="Pantone Vision 2.0 - Gemini Nano Banan", version="4.0.0")

class GeminiTextileTransfer:
    """Gemini 2.5 Flash Image for textile pattern transfer"""
    
    def __init__(self):
        self.model_name = "gemini-2.5-flash-image-preview"  # Official model name from Google AI docs
        self.client = genai.Client()
    
    def transfer_textile_pattern(self, textile_image: Image.Image, sketch_image: Image.Image, 
                               pantone_color: str = None, pantone_name: str = None) -> Dict:
        """
        Transfer textile pattern from source image to garment sketch using Gemini
        """
        print(f"🎨 Starting Gemini textile pattern transfer...")
        print(f"   Pantone: {pantone_color} ({pantone_name})")
        
        try:
            # Convert images to base64
            textile_b64 = self._image_to_base64(textile_image)
            sketch_b64 = self._image_to_base64(sketch_image)
            
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
                generated_image = Image.open(BytesIO(image_data))
                
                # Convert to base64 for return
                generated_image_b64 = base64.b64encode(image_data).decode('utf-8')
                
                print(f"✅ Gemini textile transfer successful!")
                
                return {
                    'success': True,
                    'generated_image': generated_image,
                    'generated_image_base64': generated_image_b64,
                    'method': 'gemini-2.5-flash-image-preview',
                    'model_name': self.model_name,
                    'pantone_color': pantone_color,
                    'pantone_name': pantone_name
                }
            else:
                raise Exception("No image generated in response")
            
            # Check if response has candidates with content
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                generated_image_b64 = part.inline_data.data
                                
                                # Convert back to PIL Image
                                image_data = base64.b64decode(generated_image_b64)
                                generated_image = Image.open(BytesIO(image_data))
                                
                                print(f"✅ Gemini textile transfer successful!")
                                
                                return {
                                    'success': True,
                                    'generated_image': generated_image,
                                    'generated_image_base64': generated_image_b64,
                                    'method': 'gemini-2.5-flash-image',
                                    'model_name': self.model_name,
                                    'pantone_color': pantone_color,
                                    'pantone_name': pantone_name
                                }
            
            # Fallback: try direct access
            if hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    if hasattr(part, 'inline_data'):
                        generated_image_b64 = part.inline_data.data
                        
                        # Convert back to PIL Image
                        image_data = base64.b64decode(generated_image_b64)
                        generated_image = Image.open(BytesIO(image_data))
                        
                        print(f"✅ Gemini textile transfer successful!")
                        
                        return {
                            'success': True,
                            'generated_image': generated_image,
                            'generated_image_base64': generated_image_b64,
                            'method': 'gemini-2.0-flash-exp',
                            'model_name': self.model_name,
                            'pantone_color': pantone_color,
                            'pantone_name': pantone_name
                        }
            
            raise Exception("No image generated in response")
            
        except Exception as e:
            print(f"❌ Gemini textile transfer failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'generated_image': sketch_image  # Return original sketch as fallback
            }
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        # Resize if too large
        if max(image.size) > 2048:
            ratio = 2048 / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    def _create_textile_transfer_prompt(self, pantone_color: str = None, pantone_name: str = None) -> str:
        """Create detailed prompt for textile pattern transfer"""
        
        base_prompt = "Fill entire shape in image 2 with texture from image 1. Keep lines visible."
        
        if pantone_color and pantone_name:
            base_prompt += f" Use {pantone_color} color."

        return base_prompt

# Initialize services
color_matcher = UniversalColorMatcher()
gemini_transfer = GeminiTextileTransfer()

# HTML Interface
HTML_INTERFACE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Pantone Vision 2.0 - Gemini Nano Banan</title>
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
        .gemini-badge { background: linear-gradient(45deg, #4285f4, #34a853, #fbbc04, #ea4335); }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="gradient-bg text-white py-6">
        <div class="max-w-6xl mx-auto px-4">
            <h1 class="text-3xl font-bold flex items-center">
                🎨 Pantone Vision 2.0 
                <span class="gemini-badge text-white px-3 py-1 rounded-full text-sm ml-4">✨ Powered by Gemini 2.5 Flash Image</span>
            </h1>
            <p class="text-white/80">Pantone Color Identification + AI Textile Pattern Transfer</p>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-6xl mx-auto px-4 py-8">
        
        <!-- Step 1: Pantone Color Identification -->
        <div class="bg-white rounded-lg shadow-lg mb-8 p-6">
            <h2 class="text-xl font-bold mb-4 flex items-center">
                <span class="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center mr-3 text-sm">1</span>
                🎯 Pantone Color Identification
            </h2>
            
            <div class="grid md:grid-cols-2 gap-6">
                <!-- Upload Textile -->
                <div>
                    <h3 class="font-medium mb-3">Upload Textile/Color Sample</h3>
                    <div id="color-upload" class="upload-area p-6 text-center rounded-lg cursor-pointer">
                        <i data-lucide="upload" class="w-8 h-8 mx-auto text-gray-400 mb-2"></i>
                        <p class="text-gray-600">Upload fabric/color sample</p>
                        <p class="text-sm text-gray-500">PNG, JPG up to 15MB</p>
                    </div>
                    <input type="file" id="color-file" class="hidden" accept="image/*">
                    
                    <!-- Camera Section -->
                    <div class="border-t pt-4 mt-4">
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
                    
                    <div id="textile-preview" class="mt-4 hidden">
                        <img id="textile-img" class="max-w-full h-32 object-contain mx-auto rounded-lg border">
                        <p id="textile-name" class="text-sm text-gray-600 text-center mt-2"></p>
                    </div>
                    <button onclick="identifyPantone()" id="identify-btn" class="w-full bg-blue-600 text-white py-3 mt-4 rounded-lg disabled:bg-gray-300" disabled>
                        🔍 Identify Pantone Color
                    </button>
                </div>

                <!-- Pantone Results -->
                <div>
                    <h3 class="font-medium mb-3">Identified Pantone Color</h3>
                    <div id="pantone-results" class="text-center text-gray-500">
                        Upload textile sample to identify Pantone color
                    </div>
                </div>
            </div>
        </div>

        <!-- Step 2: Gemini Textile Transfer -->
        <div class="bg-white rounded-lg shadow-lg p-6">
            <h2 class="text-xl font-bold mb-4 flex items-center">
                <span class="bg-green-500 text-white rounded-full w-8 h-8 flex items-center justify-center mr-3 text-sm">2</span>
                ✨ AI Textile Pattern Transfer
            </h2>
            
            <div class="grid md:grid-cols-2 gap-6">
                <!-- Upload Sketch -->
                <div>
                    <h3 class="font-medium mb-3">Upload Garment Sketch</h3>
                    <div id="sketch-upload" class="upload-area p-6 text-center rounded-lg cursor-pointer">
                        <i data-lucide="image" class="w-8 h-8 mx-auto text-gray-400 mb-2"></i>
                        <p class="text-gray-600">Upload fashion sketch</p>
                        <p class="text-sm text-gray-500">PNG, JPG up to 15MB</p>
                    </div>
                    <input type="file" id="sketch-file" class="hidden" accept="image/*">
                    <div id="sketch-preview" class="mt-4 hidden">
                        <img id="sketch-img" class="max-w-full h-32 object-contain mx-auto rounded-lg border">
                        <p id="sketch-name" class="text-sm text-gray-600 text-center mt-2"></p>
                    </div>
                    <button onclick="generateWithGemini()" id="generate-btn" class="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 mt-4 rounded-lg disabled:bg-gray-300" disabled>
                        ✨ Generate with Gemini AI
                    </button>
                </div>

                <!-- Generated Results -->
                <div>
                    <h3 class="font-medium mb-3">AI Generated Result</h3>
                    <div id="gemini-results" class="text-center text-gray-500">
                        Upload both textile and sketch to generate result
                    </div>
                    <div id="loading" class="hidden text-center py-4">
                        <i data-lucide="loader-2" class="w-6 h-6 animate-spin mx-auto mb-2"></i>
                        <p class="text-gray-600">AI processing with Gemini...</p>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let textileFile = null;
        let sketchFile = null;
        let currentPantoneData = null;
        let cameraStream = null;

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            lucide.createIcons();
            setupUploads();
            setupCamera();
        });

        function setupUploads() {
            // Textile upload
            document.getElementById('color-upload').onclick = () => document.getElementById('color-file').click();
            document.getElementById('color-file').onchange = function(e) {
                const file = e.target.files[0];
                if (file) {
                    textileFile = file;
                    showTextilePreview(file);
                    document.getElementById('identify-btn').disabled = false;
                }
            };

            // Sketch upload
            document.getElementById('sketch-upload').onclick = () => document.getElementById('sketch-file').click();
            document.getElementById('sketch-file').onchange = function(e) {
                const file = e.target.files[0];
                if (file) {
                    sketchFile = file;
                    showSketchPreview(file);
                    updateGenerateButton();
                }
            };
        }

        function showTextilePreview(file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('textile-img').src = e.target.result;
                document.getElementById('textile-name').textContent = file.name;
                document.getElementById('textile-preview').classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }

        function showSketchPreview(file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('sketch-img').src = e.target.result;
                document.getElementById('sketch-name').textContent = file.name;
                document.getElementById('sketch-preview').classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }

        function updateGenerateButton() {
            const btn = document.getElementById('generate-btn');
            btn.disabled = !(textileFile && sketchFile);
        }

        async function identifyPantone() {
            if (!textileFile) return;

            const formData = new FormData();
            formData.append('file', textileFile);

            try {
                document.getElementById('identify-btn').disabled = true;
                document.getElementById('identify-btn').textContent = '🔍 Analyzing...';

                const response = await fetch('/identify-color', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                
                if (result.success) {
                    currentPantoneData = result.data;
                    displayPantoneResults(result.data);
                } else {
                    alert('Pantone identification failed: ' + result.error);
                }
            } catch (error) {
                alert('Network error: ' + error.message);
            } finally {
                document.getElementById('identify-btn').disabled = false;
                document.getElementById('identify-btn').textContent = '🔍 Identify Pantone Color';
                updateGenerateButton();
            }
        }

        function displayPantoneResults(data) {
            const resultsDiv = document.getElementById('pantone-results');
            const match = data.primary_match || data;
            const hexColor = data.technical_data?.hex || match.technical_data?.hex || '#CCCCCC';
            
            resultsDiv.innerHTML = `
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="flex items-center justify-center space-x-4 mb-3">
                        <div class="w-16 h-16 rounded-lg border-2 border-gray-300" style="background-color: ${hexColor}"></div>
                        <div class="text-left">
                            <div class="font-bold text-lg">${match.pantone_code || 'Unknown'}</div>
                            <div class="text-gray-600">${match.name || 'Unknown'}</div>
                            <div class="text-sm text-gray-500">${hexColor}</div>
                        </div>
                    </div>
                    <div class="text-xs text-green-600 font-medium">✅ Ready for AI generation</div>
                    
                    ${data.alternative_matches && data.alternative_matches.length > 0 ? `
                        <div class="mt-4 border-t pt-3">
                            <h4 class="text-sm font-medium text-gray-700 mb-2">🎨 Related Colors</h4>
                            <div class="space-y-2">
                                ${data.alternative_matches.map(alt => `
                                    <div class="flex items-center space-x-3 p-2 bg-gray-50 rounded-lg">
                                        <div class="w-8 h-8 rounded border shadow" style="background-color: ${alt.technical_data?.hex || '#ccc'}"></div>
                                        <div class="flex-1">
                                            <div class="text-sm font-medium">${alt.pantone_code || 'Unknown'}</div>
                                            <div class="text-xs text-gray-600">${alt.name || 'Unknown'}</div>
                                            <div class="text-xs text-blue-600">${Math.round((alt.confidence || 0) * 100)}% confidence</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        async function generateWithGemini() {
            if (!textileFile || !sketchFile) return;

            const formData = new FormData();
            formData.append('textile_image', textileFile);
            formData.append('sketch_image', sketchFile);
            
            if (currentPantoneData) {
                formData.append('pantone_data', JSON.stringify(currentPantoneData));
            }

            try {
                document.getElementById('loading').classList.remove('hidden');
                document.getElementById('gemini-results').innerHTML = '';
                document.getElementById('generate-btn').disabled = true;

                const response = await fetch('/generate-textile-transfer', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                
                if (result.success) {
                    displayGeminiResults(result);
                } else {
                    alert('Generation failed: ' + result.error);
                }
            } catch (error) {
                alert('Network error: ' + error.message);
            } finally {
                document.getElementById('loading').classList.add('hidden');
                document.getElementById('generate-btn').disabled = false;
            }
        }

        function displayGeminiResults(result) {
            const resultsDiv = document.getElementById('gemini-results');
            
            resultsDiv.innerHTML = `
                <div class="space-y-4">
                    <img src="data:image/png;base64,${result.data.generated_image_base64}" 
                         class="max-w-full mx-auto rounded-lg shadow-sm border">
                    <div class="text-sm space-y-1">
                        <div class="flex justify-between">
                            <span class="text-gray-500">Model:</span>
                            <span class="font-medium">${result.data.model_name}</span>
                        </div>
                        ${result.data.pantone_color ? `
                            <div class="flex justify-between">
                                <span class="text-gray-500">Pantone:</span>
                                <span class="font-medium">${result.data.pantone_color} (${result.data.pantone_name || 'Unknown'})</span>
                            </div>
                        ` : ''}
                    </div>
                    <button onclick="downloadResult('${result.data.generated_image_base64}')" 
                            class="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700">
                        <i data-lucide="download" class="w-4 h-4 inline mr-2"></i>
                        Download Result
                    </button>
                </div>
            `;
            
            lucide.createIcons();
        }

        function downloadResult(base64Data) {
            const link = document.createElement('a');
            link.href = 'data:image/png;base64,' + base64Data;
            link.download = `gemini-textile-transfer-${Date.now()}.png`;
            link.click();
        }

        // Camera functionality
        function setupCamera() {
            document.getElementById('camera-btn').onclick = startCamera;
            document.getElementById('capture-btn').onclick = capturePhoto;
            document.getElementById('stop-camera-btn').onclick = stopCamera;
        }

        async function startCamera() {
            try {
                cameraStream = await navigator.mediaDevices.getUserMedia({
                    video: { 
                        facingMode: 'environment',  // Use back camera if available
                        width: { ideal: 1920 },
                        height: { ideal: 1080 }
                    }
                });
                
                const video = document.getElementById('camera-video');
                video.srcObject = cameraStream;
                
                document.getElementById('camera-section').classList.remove('hidden');
                document.getElementById('camera-btn').textContent = '📹 Camera Active';
                
            } catch (err) {
                console.error('Camera access denied:', err);
                alert('Camera access denied. Please allow camera access and try again.');
            }
        }

        function capturePhoto() {
            const video = document.getElementById('camera-video');
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0);
            
            canvas.toBlob(function(blob) {
                // Create a file from the captured image
                const capturedFile = new File([blob], `captured-${Date.now()}.png`, { type: 'image/png' });
                textileFile = capturedFile;
                
                // Show preview
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('textile-img').src = e.target.result;
                    document.getElementById('textile-name').textContent = capturedFile.name;
                    document.getElementById('textile-preview').classList.remove('hidden');
                };
                reader.readAsDataURL(capturedFile);
                
                // Enable identify button
                document.getElementById('identify-btn').disabled = false;
                
                // Stop camera after capture
                stopCamera();
            }, 'image/png');
        }

        function stopCamera() {
            if (cameraStream) {
                cameraStream.getTracks().forEach(track => track.stop());
                cameraStream = null;
                
                const video = document.getElementById('camera-video');
                video.srcObject = null;
                
                document.getElementById('camera-section').classList.add('hidden');
                document.getElementById('camera-btn').textContent = '📷 Use Device Camera';
            }
        }
    </script>
</body>
</html>
'''

# Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=HTML_INTERFACE)

@app.post("/identify-color")
async def identify_color(file: UploadFile = File(...)):
    """Identify Pantone color from uploaded image"""
    start_time = datetime.now()
    
    try:
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Process uploaded image
        image = Image.open(file.file)
        
        # Convert to numpy array and extract dominant color
        image_array = np.array(image)
        dominant_rgb = color_matcher.analyze_image_color(image_array, method="dominant")
        print(f"🎨 DOMINANT COLOR EXTRACTED: RGB{dominant_rgb}")
        
        # Identify color with AI
        result = color_matcher.identify_color_with_ai(
            dominant_rgb, 
            image_description="textile color sample"
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "success": True,
            "data": result,
            "processing_time_ms": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Color identification error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/generate-textile-transfer")
async def generate_textile_transfer(
    textile_image: UploadFile = File(...),
    sketch_image: UploadFile = File(...),
    pantone_data: str = Form("")
):
    """Generate textile pattern transfer using Gemini 2.5 Flash Image"""
    start_time = datetime.now()
    
    try:
        if textile_image.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Textile image too large")
        if sketch_image.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Sketch image too large")
        
        # Load images
        textile_img = Image.open(textile_image.file)
        sketch_img = Image.open(sketch_image.file)
        
        # Parse Pantone data
        pantone_color = None
        pantone_name = None
        if pantone_data:
            try:
                pantone_info = json.loads(pantone_data)
                primary_match = pantone_info.get('primary_match', pantone_info)
                pantone_color = primary_match.get('technical_data', {}).get('hex')
                pantone_name = primary_match.get('name')
            except:
                pass
        
        # Generate with Gemini
        result = gemini_transfer.transfer_textile_pattern(
            textile_img, sketch_img, pantone_color, pantone_name
        )
        
        if not result['success']:
            raise Exception(result.get('error', 'Gemini generation failed'))
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "success": True,
            "data": {
                "generated_image_base64": result['generated_image_base64'],
                "model_name": result['model_name'],
                "pantone_color": pantone_color,
                "pantone_name": pantone_name,
                "processing_time_ms": processing_time
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Gemini generation error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    print("🚀 Starting Pantone Vision 2.0 with Gemini Nano Banan...")
    print("   📍 Server: http://127.0.0.1:8000")
    print("   ✨ AI Model: Gemini 2.5 Flash Image (Nano Banan)")
    print("   🎨 Features: Pantone identification + AI textile transfer")
    
    uvicorn.run(app, host="127.0.0.1", port=8000)