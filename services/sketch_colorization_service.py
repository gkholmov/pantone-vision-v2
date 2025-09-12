#!/usr/bin/env python3
"""
Sketch Colorization Service for Pantone Vision 2.0
Uses ControlNet + Stable Diffusion for intelligent sketch colorization
Preserves edges and form while applying realistic colors
"""

import os
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import requests
import base64
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO
from dotenv import load_dotenv

# Optional OpenCV import - graceful fallback if not available
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None

class SketchColorizationService:
    """
    Advanced sketch colorization using ControlNet + Stable Diffusion
    Respects fabric edges and form while applying Pantone colors
    """
    
    def __init__(self):
        load_dotenv()
        self.hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
        self.hf_model = os.getenv('HUGGINGFACE_MODEL', 'lllyasviel/control_v11p_sd15_lineart')
        self.controlnet_model = os.getenv('CONTROLNET_MODEL', 'lllyasviel/sd-controlnet-lineart')
        
        # Fallback APIs for production reliability
        self.replicate_key = os.getenv('REPLICATE_API_KEY')
        self.stability_key = os.getenv('STABILITY_API_KEY')
        
        # Processing settings
        self.max_resolution = int(os.getenv('MAX_IMAGE_RESOLUTION', '4096'))
        self.processing_timeout = int(os.getenv('PROCESSING_TIMEOUT', '30'))
        
    def preprocess_sketch(self, image: Image.Image) -> Dict[str, Any]:
        """
        Prepare sketch for colorization by enhancing edges and cleaning lines
        """
        # Convert to grayscale if needed
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image.copy()
            
        # Resize if too large
        if max(gray.size) > self.max_resolution:
            ratio = self.max_resolution / max(gray.size)
            new_size = tuple(int(dim * ratio) for dim in gray.size)
            gray = gray.resize(new_size, Image.Resampling.LANCZOS)
        
        # Enhance contrast and clean lines
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(1.5)
        
        # Apply slight blur to soften harsh edges
        smoothed = enhanced.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Convert to numpy for processing
        img_array = np.array(smoothed)
        
        if OPENCV_AVAILABLE and cv2 is not None:
            # Apply adaptive threshold for clean line art
            binary = cv2.adaptiveThreshold(
                img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Invert so lines are black on white background
            if np.mean(binary) < 127:
                binary = 255 - binary
                
            # Convert back to PIL
            processed_image = Image.fromarray(binary).convert('RGB')
        else:
            # Fallback without OpenCV - use PIL only
            # Simple threshold
            threshold = 128
            binary = np.where(img_array > threshold, 255, 0).astype(np.uint8)
            
            # Invert if needed
            if np.mean(binary) < 127:
                binary = 255 - binary
                
            processed_image = Image.fromarray(binary).convert('RGB')
        
        return {
            'processed_image': processed_image,
            'original_size': image.size,
            'processed_size': processed_image.size,
            'preprocessing_applied': ['contrast_enhancement', 'smoothing', 'adaptive_threshold']
        }
    
    def colorize_with_huggingface(self, sketch_image: Image.Image, 
                                  color_prompt: str, 
                                  pantone_colors: List[str] = None) -> Dict[str, Any]:
        """
        Colorize sketch using Hugging Face ControlNet API
        """
        if not self.hf_api_key or self.hf_api_key == 'your_hf_token_here':
            return self._fallback_colorization(sketch_image, color_prompt)
        
        try:
            # Convert image to base64
            buffered = BytesIO()
            sketch_image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Build color-aware prompt
            enhanced_prompt = self._build_color_prompt(color_prompt, pantone_colors)
            
            # API request to Hugging Face
            api_url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
            headers = {"Authorization": f"Bearer {self.hf_api_key}"}
            
            payload = {
                "inputs": enhanced_prompt,
                "parameters": {
                    "image": img_base64,
                    "num_inference_steps": 20,
                    "guidance_scale": 7.5,
                    "controlnet_conditioning_scale": 1.0,
                    "negative_prompt": "blurry, low quality, distorted, unrealistic colors"
                }
            }
            
            response = requests.post(
                api_url, 
                headers=headers, 
                json=payload, 
                timeout=self.processing_timeout
            )
            
            if response.status_code == 200:
                # Process successful response
                result_image_data = response.content
                colorized_image = Image.open(BytesIO(result_image_data))
                
                return {
                    'colorized_image': colorized_image,
                    'method': 'huggingface_controlnet',
                    'model_used': self.hf_model,
                    'prompt_used': enhanced_prompt,
                    'success': True,
                    'processing_time': response.elapsed.total_seconds()
                }
            else:
                # Try fallback method
                return self._try_replicate_fallback(sketch_image, enhanced_prompt)
                
        except Exception as e:
            return self._fallback_colorization(sketch_image, color_prompt, error=str(e))
    
    def _build_color_prompt(self, base_prompt: str, pantone_colors: List[str] = None) -> str:
        """
        Build enhanced prompt incorporating Pantone colors
        """
        prompt_parts = [
            "High-quality fashion illustration colorization,",
            base_prompt,
            "realistic fabric textures, professional fashion design,"
        ]
        
        if pantone_colors:
            color_descriptions = []
            for color in pantone_colors[:3]:  # Limit to top 3 colors
                if 'PANTONE' in color:
                    color_descriptions.append(f"using {color} color palette")
            
            if color_descriptions:
                prompt_parts.append(", ".join(color_descriptions))
        
        prompt_parts.extend([
            "clean lines, vibrant but realistic colors,",
            "professional fashion sketch style,",
            "high detail, sharp edges"
        ])
        
        return " ".join(prompt_parts)
    
    def _try_replicate_fallback(self, sketch_image: Image.Image, prompt: str) -> Dict[str, Any]:
        """
        Fallback to Replicate API if available
        """
        if not self.replicate_key or self.replicate_key == 'your_replicate_token_here':
            return self._fallback_colorization(sketch_image, prompt, error="No fallback API available")
        
        try:
            # Convert to base64 for Replicate
            buffered = BytesIO()
            sketch_image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Replicate ControlNet request
            api_url = "https://api.replicate.com/v1/predictions"
            headers = {
                "Authorization": f"Token {self.replicate_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "version": "control-net-1-1-lineart",
                "input": {
                    "image": f"data:image/png;base64,{img_base64}",
                    "prompt": prompt,
                    "num_inference_steps": 20,
                    "guidance_scale": 7.5
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 201:
                prediction_url = response.json()["urls"]["get"]
                
                # Poll for completion
                for _ in range(30):  # Wait up to 30 seconds
                    result_response = requests.get(prediction_url, headers=headers)
                    result = result_response.json()
                    
                    if result["status"] == "succeeded":
                        # Download colorized image
                        img_response = requests.get(result["output"][0])
                        colorized_image = Image.open(BytesIO(img_response.content))
                        
                        return {
                            'colorized_image': colorized_image,
                            'method': 'replicate_controlnet',
                            'success': True
                        }
                    elif result["status"] == "failed":
                        break
                    
                    import time
                    time.sleep(1)
            
            return self._fallback_colorization(sketch_image, prompt, error="Replicate API failed")
            
        except Exception as e:
            return self._fallback_colorization(sketch_image, prompt, error=f"Replicate error: {str(e)}")
    
    def _fallback_colorization(self, sketch_image: Image.Image, prompt: str, error: str = None) -> Dict[str, Any]:
        """
        Basic colorization using computer vision techniques
        When AI APIs are unavailable
        """
        try:
            # Convert to numpy array
            img_array = np.array(sketch_image)
            
            # Create basic color overlay
            colored = img_array.copy()
            
            # Apply subtle warm tone overlay
            if len(colored.shape) == 3:
                # Add warm tint
                colored[:, :, 0] = np.clip(colored[:, :, 0] * 1.1, 0, 255)  # Slight red boost
                colored[:, :, 1] = np.clip(colored[:, :, 1] * 1.05, 0, 255)  # Slight green boost
            
            if OPENCV_AVAILABLE and cv2 is not None:
                # Apply Gaussian blur for soft coloring effect
                blurred = cv2.GaussianBlur(colored.astype(np.uint8), (15, 15), 0)
                
                # Blend original sketch with colored version
                alpha = 0.7
                result = cv2.addWeighted(img_array.astype(np.uint8), alpha, blurred, 1-alpha, 0)
            else:
                # Fallback without OpenCV
                from PIL import ImageFilter
                pil_colored = Image.fromarray(colored.astype(np.uint8))
                blurred_pil = pil_colored.filter(ImageFilter.GaussianBlur(radius=5))
                blurred = np.array(blurred_pil)
                
                # Simple blending
                alpha = 0.7
                result = (img_array.astype(np.uint8) * alpha + blurred * (1-alpha)).astype(np.uint8)
            
            fallback_image = Image.fromarray(result)
            
            return {
                'colorized_image': fallback_image,
                'method': 'fallback_cv2',
                'success': True,
                'fallback_reason': error or 'AI services unavailable',
                'note': 'Basic colorization applied - configure API keys for AI-powered results'
            }
            
        except Exception as e:
            # Return original image if all else fails
            return {
                'colorized_image': sketch_image,
                'method': 'no_processing',
                'success': False,
                'error': f"All colorization methods failed: {str(e)}"
            }
    
    def apply_pantone_colors(self, colorized_image: Image.Image, 
                           pantone_colors: List[Dict], 
                           regions: List[Dict] = None) -> Dict[str, Any]:
        """
        Apply specific Pantone colors to regions of the colorized image
        """
        try:
            img_array = np.array(colorized_image)
            result = img_array.copy()
            
            # If specific regions provided, apply colors selectively
            if regions and len(regions) == len(pantone_colors):
                for region, color_info in zip(regions, pantone_colors):
                    if 'rgb' in color_info:
                        rgb = color_info['rgb']
                        # Apply color to specified region
                        # This is a simplified implementation
                        x, y, w, h = region.get('bbox', [0, 0, result.shape[1], result.shape[0]])
                        result[y:y+h, x:x+w] = self._blend_color(
                            result[y:y+h, x:x+w], rgb, alpha=0.3
                        )
            else:
                # Apply dominant color as overlay
                if pantone_colors and 'rgb' in pantone_colors[0]:
                    dominant_color = pantone_colors[0]['rgb']
                    color_overlay = np.full_like(img_array, dominant_color)
                    result = cv2.addWeighted(img_array, 0.8, color_overlay, 0.2, 0)
            
            enhanced_image = Image.fromarray(result.astype(np.uint8))
            
            return {
                'enhanced_image': enhanced_image,
                'pantone_colors_applied': [c.get('pantone_code', 'Unknown') for c in pantone_colors],
                'success': True
            }
            
        except Exception as e:
            return {
                'enhanced_image': colorized_image,
                'success': False,
                'error': f"Pantone color application failed: {str(e)}"
            }
    
    def _blend_color(self, region: np.ndarray, color: Tuple[int, int, int], alpha: float = 0.3) -> np.ndarray:
        """Helper function to blend color with region"""
        color_overlay = np.full_like(region, color)
        if OPENCV_AVAILABLE and cv2 is not None:
            return cv2.addWeighted(region, 1-alpha, color_overlay, alpha, 0)
        else:
            # Simple alpha blending without OpenCV
            return (region * (1-alpha) + color_overlay * alpha).astype(np.uint8)
    
    def process_full_workflow(self, sketch_image: Image.Image, 
                             pantone_colors: List[Dict] = None,
                             style_prompt: str = "fashion illustration") -> Dict[str, Any]:
        """
        Complete workflow: preprocess -> colorize -> apply Pantone colors
        """
        workflow_start = datetime.now()
        
        # Step 1: Preprocess sketch
        preprocess_result = self.preprocess_sketch(sketch_image)
        processed_sketch = preprocess_result['processed_image']
        
        # Step 2: Colorize using AI
        color_prompt = f"{style_prompt}, fashion design sketch, realistic fabric textures"
        colorization_result = self.colorize_with_huggingface(
            processed_sketch, 
            color_prompt,
            [c.get('pantone_code', '') for c in (pantone_colors or [])]
        )
        
        if not colorization_result.get('success'):
            return {
                'success': False,
                'error': colorization_result.get('error', 'Colorization failed'),
                'original_sketch': sketch_image,
                'processed_sketch': processed_sketch
            }
        
        colorized = colorization_result['colorized_image']
        
        # Step 3: Apply Pantone colors if provided
        final_result = colorized
        pantone_application = None
        
        if pantone_colors:
            pantone_result = self.apply_pantone_colors(colorized, pantone_colors)
            if pantone_result.get('success'):
                final_result = pantone_result['enhanced_image']
                pantone_application = pantone_result
        
        workflow_time = (datetime.now() - workflow_start).total_seconds()
        
        return {
            'success': True,
            'original_sketch': sketch_image,
            'processed_sketch': processed_sketch,
            'colorized_image': final_result,
            'preprocessing_info': preprocess_result,
            'colorization_info': colorization_result,
            'pantone_application': pantone_application,
            'pantone_colors_used': pantone_colors,
            'workflow_time_seconds': workflow_time,
            'timestamp': datetime.now().isoformat()
        }

# Example usage and testing
if __name__ == "__main__":
    service = SketchColorizationService()
    
    print("🎨 SKETCH COLORIZATION SERVICE")
    print("=" * 50)
    print(f"HuggingFace API: {'✅ Configured' if service.hf_api_key and service.hf_api_key != 'your_hf_token_here' else '❌ Not configured'}")
    print(f"Replicate API: {'✅ Configured' if service.replicate_key and service.replicate_key != 'your_replicate_token_here' else '❌ Not configured'}")
    print(f"Max Resolution: {service.max_resolution}px")
    print(f"Processing Timeout: {service.processing_timeout}s")