#!/usr/bin/env python3
"""
Pantone Vision V2 - Full Web Interface
Serves both API and UI from a single endpoint
"""

from http.server import BaseHTTPRequestHandler
import json
import base64
from urllib.parse import parse_qs, urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve the full UI interface"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pantone Vision V2 - Professional Color & Texture System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', system-ui, sans-serif; }
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #fda085 100%);
        }
        .glass-morphism {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        .texture-card {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .texture-card:hover {
            transform: translateY(-4px) scale(1.02);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        .loading-spinner {
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .pantone-color {
            transition: all 0.2s;
        }
        .pantone-color:hover {
            transform: scale(1.1);
            z-index: 10;
        }
    </style>
</head>
<body class="min-h-screen gradient-bg">
    <div class="container mx-auto px-4 py-8 max-w-7xl">
        <!-- Header -->
        <div class="glass-morphism rounded-2xl p-8 mb-8 shadow-2xl">
            <h1 class="text-5xl font-bold text-gray-800 mb-4">Pantone Vision V2</h1>
            <p class="text-xl text-gray-600">Professional Color Matching & Textile Pattern Transfer System</p>
            <div class="flex gap-4 mt-6">
                <span class="px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-medium">✓ 8 Texture Types</span>
                <span class="px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">✓ Gemini AI</span>
                <span class="px-4 py-2 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">✓ Pantone Matching</span>
            </div>
        </div>

        <!-- Main Tabs -->
        <div class="glass-morphism rounded-2xl p-2 mb-8 shadow-xl">
            <div class="flex gap-2">
                <button onclick="switchTab('pantone')" id="tab-pantone" class="tab-btn flex-1 px-6 py-4 rounded-xl font-semibold transition-all bg-white shadow-md">
                    🎨 Pantone Colors
                </button>
                <button onclick="switchTab('texture')" id="tab-texture" class="tab-btn flex-1 px-6 py-4 rounded-xl font-semibold transition-all hover:bg-white hover:shadow-md">
                    🧵 Texture Application
                </button>
                <button onclick="switchTab('gemini')" id="tab-gemini" class="tab-btn flex-1 px-6 py-4 rounded-xl font-semibold transition-all hover:bg-white hover:shadow-md">
                    ✨ Pattern Transfer
                </button>
            </div>
        </div>

        <!-- Pantone Color Matching Section -->
        <div id="section-pantone" class="section">
            <div class="glass-morphism rounded-2xl p-8 shadow-2xl">
                <h2 class="text-3xl font-bold mb-6 text-gray-800">Pantone Color Identification</h2>
                
                <div class="grid md:grid-cols-2 gap-8">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Upload Image</label>
                        <div class="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-purple-500 transition-colors">
                            <input type="file" id="pantone-image" accept="image/*" class="hidden" onchange="previewImage('pantone')">
                            <label for="pantone-image" class="cursor-pointer">
                                <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                                </svg>
                                <p class="text-gray-600">Click to upload or drag and drop</p>
                                <p class="text-xs text-gray-500 mt-2">PNG, JPG, WEBP up to 15MB</p>
                            </label>
                        </div>
                        <img id="pantone-preview" class="mt-4 rounded-xl shadow-lg hidden max-h-64 mx-auto">
                        
                        <div class="mt-6 flex gap-4">
                            <button onclick="analyzePantone()" class="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold py-3 px-6 rounded-xl hover:shadow-lg transition-all">
                                Analyze Colors
                            </button>
                            <input type="number" id="max-colors" placeholder="Max colors" value="10" min="1" max="50" class="w-32 px-4 py-3 border rounded-xl">
                        </div>
                    </div>
                    
                    <div>
                        <h3 class="text-xl font-semibold mb-4 text-gray-700">Detected Pantone Colors</h3>
                        <div id="pantone-results" class="space-y-3 max-h-96 overflow-y-auto">
                            <p class="text-gray-500 text-center py-8">Upload an image to identify Pantone colors</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Texture Application Section -->
        <div id="section-texture" class="section hidden">
            <div class="glass-morphism rounded-2xl p-8 shadow-2xl">
                <h2 class="text-3xl font-bold mb-6 text-gray-800">AI Texture Application</h2>
                
                <div class="grid md:grid-cols-2 gap-8">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Upload Garment Image</label>
                        <div class="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-500 transition-colors">
                            <input type="file" id="texture-image" accept="image/*" class="hidden" onchange="previewImage('texture')">
                            <label for="texture-image" class="cursor-pointer">
                                <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                </svg>
                                <p class="text-gray-600">Upload garment image</p>
                            </label>
                        </div>
                        <img id="texture-preview" class="mt-4 rounded-xl shadow-lg hidden max-h-48 mx-auto">
                        
                        <div class="mt-6">
                            <label class="block text-sm font-medium text-gray-700 mb-3">Select Texture Type</label>
                            <div class="grid grid-cols-4 gap-2">
                                <button onclick="selectTexture('lace')" class="texture-card p-3 bg-white rounded-lg text-center hover:bg-purple-50 border-2 border-transparent">
                                    <span class="text-2xl">🕸️</span>
                                    <p class="text-xs mt-1">Lace</p>
                                </button>
                                <button onclick="selectTexture('embroidery')" class="texture-card p-3 bg-white rounded-lg text-center hover:bg-purple-50 border-2 border-transparent">
                                    <span class="text-2xl">🪡</span>
                                    <p class="text-xs mt-1">Embroidery</p>
                                </button>
                                <button onclick="selectTexture('silk')" class="texture-card p-3 bg-white rounded-lg text-center hover:bg-purple-50 border-2 border-transparent">
                                    <span class="text-2xl">✨</span>
                                    <p class="text-xs mt-1">Silk</p>
                                </button>
                                <button onclick="selectTexture('satin')" class="texture-card p-3 bg-white rounded-lg text-center hover:bg-purple-50 border-2 border-transparent">
                                    <span class="text-2xl">🌟</span>
                                    <p class="text-xs mt-1">Satin</p>
                                </button>
                                <button onclick="selectTexture('leather')" class="texture-card p-3 bg-white rounded-lg text-center hover:bg-purple-50 border-2 border-transparent">
                                    <span class="text-2xl">🎭</span>
                                    <p class="text-xs mt-1">Leather</p>
                                </button>
                                <button onclick="selectTexture('velvet')" class="texture-card p-3 bg-white rounded-lg text-center hover:bg-purple-50 border-2 border-transparent">
                                    <span class="text-2xl">🌹</span>
                                    <p class="text-xs mt-1">Velvet</p>
                                </button>
                                <button onclick="selectTexture('mesh')" class="texture-card p-3 bg-white rounded-lg text-center hover:bg-purple-50 border-2 border-transparent">
                                    <span class="text-2xl">🔲</span>
                                    <p class="text-xs mt-1">Mesh</p>
                                </button>
                                <button onclick="selectTexture('sequin')" class="texture-card p-3 bg-white rounded-lg text-center hover:bg-purple-50 border-2 border-transparent">
                                    <span class="text-2xl">💎</span>
                                    <p class="text-xs mt-1">Sequin</p>
                                </button>
                            </div>
                        </div>
                        
                        <div class="mt-6">
                            <label class="block text-sm font-medium text-gray-700 mb-2">Intensity</label>
                            <input type="range" id="texture-intensity" min="0" max="100" value="80" class="w-full">
                            <div class="flex justify-between text-xs text-gray-500 mt-1">
                                <span>Subtle</span>
                                <span id="intensity-value">80%</span>
                                <span>Strong</span>
                            </div>
                        </div>
                        
                        <button onclick="applyTexture()" class="w-full mt-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-3 px-6 rounded-xl hover:shadow-lg transition-all">
                            Apply Texture
                        </button>
                    </div>
                    
                    <div>
                        <h3 class="text-xl font-semibold mb-4 text-gray-700">Result</h3>
                        <div id="texture-result" class="bg-gray-50 rounded-xl p-8 min-h-[400px] flex items-center justify-center">
                            <p class="text-gray-500 text-center">Textured image will appear here</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Gemini Pattern Transfer Section -->
        <div id="section-gemini" class="section hidden">
            <div class="glass-morphism rounded-2xl p-8 shadow-2xl">
                <h2 class="text-3xl font-bold mb-6 text-gray-800">Gemini AI Pattern Transfer</h2>
                
                <div class="grid md:grid-cols-3 gap-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Textile Pattern</label>
                        <div class="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-green-500 transition-colors">
                            <input type="file" id="gemini-textile" accept="image/*" class="hidden" onchange="previewGemini('textile')">
                            <label for="gemini-textile" class="cursor-pointer">
                                <span class="text-3xl">🧵</span>
                                <p class="text-sm text-gray-600 mt-2">Upload textile</p>
                            </label>
                        </div>
                        <img id="gemini-textile-preview" class="mt-4 rounded-xl shadow-lg hidden">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Garment Sketch</label>
                        <div class="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-green-500 transition-colors">
                            <input type="file" id="gemini-sketch" accept="image/*" class="hidden" onchange="previewGemini('sketch')">
                            <label for="gemini-sketch" class="cursor-pointer">
                                <span class="text-3xl">👗</span>
                                <p class="text-sm text-gray-600 mt-2">Upload sketch</p>
                            </label>
                        </div>
                        <img id="gemini-sketch-preview" class="mt-4 rounded-xl shadow-lg hidden">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Optional Pantone</label>
                        <input type="text" id="pantone-color" placeholder="e.g., #FF6B6B" class="w-full px-4 py-3 border rounded-xl mb-3">
                        <input type="text" id="pantone-name" placeholder="e.g., Coral Pink" class="w-full px-4 py-3 border rounded-xl">
                        
                        <button onclick="transferPattern()" class="w-full mt-6 bg-gradient-to-r from-green-600 to-teal-600 text-white font-semibold py-3 px-6 rounded-xl hover:shadow-lg transition-all">
                            Transfer Pattern
                        </button>
                    </div>
                </div>
                
                <div class="mt-8">
                    <h3 class="text-xl font-semibold mb-4 text-gray-700">AI Generated Result</h3>
                    <div id="gemini-result" class="bg-gray-50 rounded-xl p-8 min-h-[300px] flex items-center justify-center">
                        <p class="text-gray-500 text-center">AI-generated pattern transfer will appear here</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Status Messages -->
        <div id="status" class="fixed bottom-8 right-8 max-w-sm"></div>
    </div>

    <script>
        let selectedTexture = null;
        let selectedImages = {};
        let selectedPantoneColor = null;
        
        // Tab switching
        function switchTab(tab) {
            document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(b => {
                b.classList.remove('bg-white', 'shadow-md');
                b.classList.add('hover:bg-white', 'hover:shadow-md');
            });
            
            document.getElementById('section-' + tab).classList.remove('hidden');
            document.getElementById('tab-' + tab).classList.remove('hover:bg-white', 'hover:shadow-md');
            document.getElementById('tab-' + tab).classList.add('bg-white', 'shadow-md');
        }
        
        // Image preview
        function previewImage(type) {
            const input = document.getElementById(type + '-image');
            const preview = document.getElementById(type + '-preview');
            
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.classList.remove('hidden');
                    selectedImages[type] = input.files[0];
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
        
        function previewGemini(type) {
            const input = document.getElementById('gemini-' + type);
            const preview = document.getElementById('gemini-' + type + '-preview');
            
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.classList.remove('hidden');
                    selectedImages['gemini-' + type] = input.files[0];
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
        
        // Texture selection
        function selectTexture(type) {
            selectedTexture = type;
            document.querySelectorAll('.texture-card').forEach(card => {
                card.classList.remove('border-purple-500', 'bg-purple-50');
                card.classList.add('border-transparent');
            });
            event.target.closest('.texture-card').classList.remove('border-transparent');
            event.target.closest('.texture-card').classList.add('border-purple-500', 'bg-purple-50');
        }
        
        // Intensity slider
        document.getElementById('texture-intensity')?.addEventListener('input', function(e) {
            document.getElementById('intensity-value').textContent = e.target.value + '%';
        });
        
        // Show status message
        function showStatus(message, type = 'info') {
            const colors = {
                'info': 'bg-blue-500',
                'success': 'bg-green-500',
                'error': 'bg-red-500',
                'loading': 'bg-yellow-500'
            };
            
            const status = document.getElementById('status');
            status.innerHTML = `
                <div class="glass-morphism p-4 rounded-xl shadow-lg mb-4 ${colors[type]} text-white">
                    ${type === 'loading' ? '<span class="loading-spinner inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"></span>' : ''}
                    ${message}
                </div>
            `;
            
            if (type !== 'loading') {
                setTimeout(() => status.innerHTML = '', 5000);
            }
        }
        
        // Pantone color analysis
        async function analyzePantone() {
            if (!selectedImages.pantone) {
                showStatus('Please upload an image first', 'error');
                return;
            }
            
            showStatus('Analyzing colors...', 'loading');
            
            const formData = new FormData();
            formData.append('image', selectedImages.pantone);
            formData.append('max_colors', document.getElementById('max-colors').value);
            
            try {
                const response = await fetch('/api/pantone', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    displayPantoneColors(result.data.colors);
                    showStatus('Colors identified successfully!', 'success');
                } else {
                    showStatus('Error: ' + result.error, 'error');
                }
            } catch (error) {
                showStatus('Failed to analyze colors: ' + error.message, 'error');
            }
        }
        
        function displayPantoneColors(colors) {
            const container = document.getElementById('pantone-results');
            container.innerHTML = colors.map((color, index) => `
                <div class="flex items-center gap-4 p-3 bg-white rounded-lg shadow pantone-color cursor-pointer hover:ring-2 hover:ring-purple-500 transition-all"
                     onclick="selectPantoneColor(${index}, '${color.pantone_code}', '${color.name || 'Color ' + (index + 1)}', '${color.hex || '#000000'}')">
                    <div class="w-16 h-16 rounded-lg shadow-inner" style="background-color: ${color.hex || color.rgb}"></div>
                    <div class="flex-1">
                        <p class="font-semibold">${color.name || 'Color ' + (index + 1)}</p>
                        <p class="text-sm text-gray-500">${color.pantone_code || color.hex || 'RGB: ' + color.rgb}</p>
                        ${color.confidence ? '<p class="text-xs text-gray-400">Confidence: ' + (color.confidence * 100).toFixed(1) + '%</p>' : ''}
                    </div>
                </div>
            `).join('');
            
            // Store colors globally for reference
            window.detectedPantoneColors = colors;
        }
        
        function selectPantoneColor(index, code, name, hex) {
            selectedPantoneColor = {
                code: code,
                name: name,
                hex: hex,
                index: index
            };
            
            // Update UI to show selection
            document.querySelectorAll('.pantone-color').forEach((el, i) => {
                if (i === index) {
                    el.classList.add('ring-2', 'ring-purple-500', 'bg-purple-50');
                } else {
                    el.classList.remove('ring-2', 'ring-purple-500', 'bg-purple-50');
                }
            });
            
            showStatus(`Selected: ${name} (${code})`, 'success');
        }
        
        // Texture application
        async function applyTexture() {
            if (!selectedImages.texture || !selectedTexture) {
                showStatus('Please upload an image and select a texture', 'error');
                return;
            }
            
            showStatus('Applying texture...', 'loading');
            
            const formData = new FormData();
            formData.append('image', selectedImages.texture);
            formData.append('texture_type', selectedTexture);
            formData.append('intensity', document.getElementById('texture-intensity').value / 100);
            
            // Add selected Pantone color if available
            if (selectedPantoneColor) {
                formData.append('pantone_color', selectedPantoneColor.code);
                formData.append('pantone_name', selectedPantoneColor.name);
                formData.append('pantone_hex', selectedPantoneColor.hex);
            }
            
            try {
                const response = await fetch('/api/texture', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    displayTextureResult(result.data.textured_image);
                    showStatus('Texture applied successfully!', 'success');
                } else {
                    showStatus('Error: ' + result.error, 'error');
                }
            } catch (error) {
                showStatus('Failed to apply texture: ' + error.message, 'error');
            }
        }
        
        function displayTextureResult(imageData) {
            const container = document.getElementById('texture-result');
            container.innerHTML = `<img src="${imageData}" class="max-w-full rounded-xl shadow-lg">`;
        }
        
        // Gemini pattern transfer
        async function transferPattern() {
            if (!selectedImages['gemini-textile'] || !selectedImages['gemini-sketch']) {
                showStatus('Please upload both textile and sketch images', 'error');
                return;
            }
            
            showStatus('Transferring pattern with AI...', 'loading');
            
            const formData = new FormData();
            formData.append('textile_image', selectedImages['gemini-textile']);
            formData.append('sketch_image', selectedImages['gemini-sketch']);
            
            const pantoneColor = document.getElementById('pantone-color').value;
            const pantoneName = document.getElementById('pantone-name').value;
            
            if (pantoneColor) formData.append('pantone_color', pantoneColor);
            if (pantoneName) formData.append('pantone_name', pantoneName);
            
            try {
                const response = await fetch('/api/gemini', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    displayGeminiResult(result.data.transferred_image);
                    showStatus('Pattern transferred successfully!', 'success');
                } else {
                    showStatus('Error: ' + result.error, 'error');
                }
            } catch (error) {
                showStatus('Failed to transfer pattern: ' + error.message, 'error');
            }
        }
        
        function displayGeminiResult(imageData) {
            const container = document.getElementById('gemini-result');
            container.innerHTML = `
                <div>
                    <img src="${imageData}" class="max-w-full rounded-xl shadow-lg mb-4">
                    <p class="text-sm text-gray-600 text-center">AI-generated pattern transfer using Gemini 2.5 Flash</p>
                </div>
            `;
        }
    </script>
</body>
</html>'''
        
        self.wfile.write(html.encode('utf-8'))