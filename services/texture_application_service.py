#!/usr/bin/env python3
"""
Texture Application Service for Pantone Vision 2.0
Applies realistic fabric textures (lace, embroidery, silk, etc.) to colorized sketches
Uses Stable Diffusion + ControlNet for high-quality texture synthesis
"""

import os
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import requests
import base64
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from io import BytesIO
from dotenv import load_dotenv
import time

class TextureApplicationService:
    """
    Advanced texture application using Stable Diffusion + ControlNet
    Applies realistic fabric textures while preserving garment structure
    """
    
    def __init__(self):
        load_dotenv()
        
        # API Configuration
        self.hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
        self.stability_key = os.getenv('STABILITY_API_KEY')
        self.replicate_key = os.getenv('REPLICATE_API_KEY')
        
        # Model Configuration - Using FLUX.1-dev for highest quality
        self.flux_model = "black-forest-labs/FLUX.1-dev"  # Primary high-quality model
        self.texture_model = "runwayml/stable-diffusion-v1-5"  # Fallback model
        self.controlnet_model = "lllyasviel/sd-controlnet-canny"  # For edge preservation
        
        # Processing Settings
        self.max_resolution = int(os.getenv('MAX_IMAGE_RESOLUTION', '4096'))
        self.processing_timeout = int(os.getenv('PROCESSING_TIMEOUT', '60'))  # Longer for texture processing
        
        # Texture Definitions
        self.texture_prompts = {
            'lace': {
                'prompt': 'intricate floral lace pattern, delicate mesh texture, detailed lacework, high-end lingerie fabric',
                'negative': 'solid fabric, opaque material, simple texture, low quality',
                'strength': 0.8,
                'guidance_scale': 7.5,
                'steps': 25
            },
            'embroidery': {
                'prompt': 'detailed embroidery pattern, raised thread texture, luxury fashion detailing, intricate stitchwork',
                'negative': 'plain fabric, flat texture, simple surface, no decoration',
                'strength': 0.7,
                'guidance_scale': 8.0,
                'steps': 30
            },
            'silk': {
                'prompt': 'smooth silk fabric texture, lustrous sheen, elegant draping, premium textile',
                'negative': 'rough texture, matte surface, cheap fabric, synthetic look',
                'strength': 0.6,
                'guidance_scale': 7.0,
                'steps': 20
            },
            'satin': {
                'prompt': 'glossy satin finish, reflective surface, smooth fabric texture, luxury material',
                'negative': 'matte finish, rough texture, dull surface, cotton texture',
                'strength': 0.65,
                'guidance_scale': 7.2,
                'steps': 22
            },
            'leather': {
                'prompt': 'realistic leather texture, fine grain pattern, luxury material, smooth finish',
                'negative': 'fabric texture, cloth material, soft surface, textile look',
                'strength': 0.75,
                'guidance_scale': 7.8,
                'steps': 28
            },
            'velvet': {
                'prompt': 'soft velvet texture, plush pile surface, luxury fabric, rich texture',
                'negative': 'smooth surface, flat texture, synthetic look, cheap material',
                'strength': 0.7,
                'guidance_scale': 7.3,
                'steps': 24
            },
            'mesh': {
                'prompt': 'fine mesh texture, breathable fabric, athletic material, perforated surface',
                'negative': 'solid fabric, non-breathable, dense material, opaque texture',
                'strength': 0.8,
                'guidance_scale': 7.6,
                'steps': 26
            },
            'sequin': {
                'prompt': 'sparkling sequin texture, reflective discs, glamorous surface, party wear finish',
                'negative': 'matte surface, plain fabric, no shine, simple texture',
                'strength': 0.85,
                'guidance_scale': 8.2,
                'steps': 32
            }
        }
    
    def prepare_texture_mask(self, colorized_image: Image.Image, 
                           texture_areas: List[Dict] = None) -> Dict[str, Any]:
        """
        Prepare mask for selective texture application with lace pattern support
        """
        width, height = colorized_image.size
        
        # Convert to numpy for processing
        img_array = np.array(colorized_image)
        
        # Create texture mask (default: apply to garment areas)
        mask = np.ones((height, width), dtype=np.uint8) * 255
        
        # Improved background detection for lace textures
        gray = np.dot(img_array[...,:3], [0.2989, 0.5870, 0.1140])
        
        # Use adaptive threshold based on image statistics
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        # Lower threshold for lace patterns (was 240, now adaptive)
        if mean_brightness > 200:  # Bright image with lots of white/lace
            white_threshold = max(200, mean_brightness - 0.5 * std_brightness)
        else:
            white_threshold = 240  # Original threshold for normal images
        
        # Create base mask excluding pure background
        mask[gray > white_threshold] = 0
        
        # Edge detection to preserve lace boundaries
        try:
            from PIL import ImageFilter
            gray_image = Image.fromarray(gray.astype(np.uint8))
            edges = gray_image.filter(ImageFilter.FIND_EDGES)
            edge_array = np.array(edges)
            
            # Include edge areas in mask (lace has many edges)
            edge_threshold = 30
            edge_mask = edge_array > edge_threshold
            mask[edge_mask] = 255
            
            # Fill small holes in mask (common in lace patterns)
            try:
                from scipy import ndimage
                mask = ndimage.binary_fill_holes(mask > 0).astype(np.uint8) * 255
            except ImportError:
                # Fallback: simple morphological operations with numpy
                # Basic hole filling using dilation + erosion
                kernel = np.ones((3, 3), dtype=np.uint8)
                mask_binary = (mask > 0).astype(np.uint8)
                
                # Simple dilation and erosion
                for _ in range(2):  # 2 iterations of dilation
                    dilated = np.zeros_like(mask_binary)
                    for i in range(1, mask_binary.shape[0]-1):
                        for j in range(1, mask_binary.shape[1]-1):
                            if np.any(mask_binary[i-1:i+2, j-1:j+2] * kernel):
                                dilated[i, j] = 1
                    mask_binary = dilated
                
                mask = mask_binary * 255
            
        except ImportError:
            print("Warning: scipy not available, using basic edge detection")
            # Fallback: simple edge detection using numpy
            grad_x = np.abs(np.diff(gray, axis=1))
            grad_y = np.abs(np.diff(gray, axis=0))
            
            # Pad to maintain shape
            grad_x = np.pad(grad_x, ((0, 0), (0, 1)), mode='edge')
            grad_y = np.pad(grad_y, ((0, 1), (0, 0)), mode='edge')
            
            edges = grad_x + grad_y
            edge_mask = edges > 20  # Lower threshold for lace
            mask[edge_mask] = 255
        
        # Apply custom texture areas if provided
        if texture_areas:
            custom_mask = np.zeros((height, width), dtype=np.uint8)
            for area in texture_areas:
                x, y, w, h = area.get('bbox', [0, 0, width, height])
                x, y, w, h = int(x), int(y), int(w), int(h)
                custom_mask[y:y+h, x:x+w] = 255
            mask = custom_mask
        
        # Smooth mask edges for better blending
        try:
            from PIL import ImageFilter
            mask_image = Image.fromarray(mask)
            mask_image = mask_image.filter(ImageFilter.GaussianBlur(radius=0.5))
            mask = np.array(mask_image)
        except:
            pass  # Use unsmoothed mask if filtering fails
        
        mask_image = Image.fromarray(mask)
        
        return {
            'mask_image': mask_image,
            'texture_areas': len(np.where(mask > 0)[0]),
            'total_pixels': width * height,
            'coverage_percentage': (len(np.where(mask > 0)[0]) / (width * height)) * 100,
            'adaptive_threshold': white_threshold,
            'mean_brightness': mean_brightness
        }
    
    def apply_texture_with_stable_diffusion(self, colorized_image: Image.Image,
                                          texture_type: str,
                                          pantone_colors: List[Dict] = None,
                                          mask: Image.Image = None) -> Dict[str, Any]:
        """
        Apply texture using Stable Diffusion + ControlNet
        """
        if not self.hf_api_key or self.hf_api_key == 'your_hf_token_here':
            return self._fallback_texture_application(colorized_image, texture_type)
        
        try:
            # Get texture configuration
            texture_config = self.texture_prompts.get(texture_type, self.texture_prompts['silk'])
            
            # Prepare images
            base64_image = self._image_to_base64(colorized_image)
            base64_mask = self._image_to_base64(mask) if mask else None
            
            # Build enhanced prompt with color information
            enhanced_prompt = self._build_texture_prompt(
                texture_config['prompt'], texture_type, pantone_colors
            )
            
            # Try FLUX.1-dev via HuggingFace first (highest quality)
            result = self._try_huggingface_texture(
                base64_image, enhanced_prompt, texture_config, base64_mask
            )
            
            if result.get('success'):
                return result
            
            # Fallback to basic image processing if HuggingFace fails
            return self._fallback_texture_application(colorized_image, texture_type, "HuggingFace API failed, using fallback")
            
        except Exception as e:
            return self._fallback_texture_application(
                colorized_image, texture_type, error=str(e)
            )
    
    def _try_huggingface_texture(self, base64_image: str, prompt: str, 
                               config: Dict, mask: str = None) -> Dict[str, Any]:
        """
        Apply texture using HuggingFace FLUX.1-dev API for highest quality
        """
        try:
            # Try FLUX.1-dev first for highest quality
            api_url = f"https://api-inference.huggingface.co/models/{self.flux_model}"
            headers = {"Authorization": f"Bearer {self.hf_api_key}"}
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "image": base64_image,
                    "mask_image": mask,
                    "num_inference_steps": config['steps'],
                    "guidance_scale": config['guidance_scale'],
                    "strength": config['strength'],
                    "negative_prompt": config['negative']
                }
            }
            
            response = requests.post(
                api_url, headers=headers, json=payload, 
                timeout=self.processing_timeout
            )
            
            if response.status_code == 200:
                # Handle different response types
                content_type = response.headers.get('content-type', '')
                
                if 'image' in content_type:
                    # Direct image response
                    textured_image = Image.open(BytesIO(response.content))
                else:
                    # JSON response with base64 image
                    result_data = response.json()
                    if isinstance(result_data, list) and len(result_data) > 0:
                        img_data = base64.b64decode(result_data[0])
                        textured_image = Image.open(BytesIO(img_data))
                    else:
                        return {'success': False, 'error': 'Invalid API response format'}
                
                return {
                    'textured_image': textured_image,
                    'method': 'huggingface_flux_dev',
                    'model_used': self.flux_model,
                    'prompt_used': prompt,
                    'config_applied': config,
                    'success': True,
                    'processing_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'success': False, 
                    'error': f"HuggingFace API error: {response.status_code}"
                }
                
        except Exception as e:
            return {'success': False, 'error': f"HuggingFace texture error: {str(e)}"}
    
    def _try_replicate_texture(self, base64_image: str, prompt: str, 
                             config: Dict, mask: str = None) -> Dict[str, Any]:
        """
        Fallback texture application using Replicate API
        """
        if not self.replicate_key or self.replicate_key == 'your_replicate_token_here':
            return {'success': False, 'error': 'No Replicate API key available'}
        
        try:
            api_url = "https://api.replicate.com/v1/predictions"
            headers = {
                "Authorization": f"Token {self.replicate_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "version": "stability-ai/stable-diffusion:27b93a2413e7f36cd83da926f3656280b2931564ff050bf9575f1fdf9bcd7478",
                "input": {
                    "image": f"data:image/png;base64,{base64_image}",
                    "mask": f"data:image/png;base64,{mask}" if mask else None,
                    "prompt": prompt,
                    "negative_prompt": config['negative'],
                    "num_inference_steps": config['steps'],
                    "guidance_scale": config['guidance_scale'],
                    "strength": config['strength']
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 201:
                prediction_url = response.json()["urls"]["get"]
                
                # Poll for completion
                for attempt in range(60):  # Wait up to 60 seconds
                    time.sleep(1)
                    result_response = requests.get(prediction_url, headers=headers)
                    result = result_response.json()
                    
                    if result["status"] == "succeeded":
                        # Download textured image
                        img_response = requests.get(result["output"][0])
                        textured_image = Image.open(BytesIO(img_response.content))
                        
                        return {
                            'textured_image': textured_image,
                            'method': 'replicate_stable_diffusion',
                            'success': True
                        }
                    elif result["status"] == "failed":
                        return {'success': False, 'error': 'Replicate processing failed'}
            
            return {'success': False, 'error': 'Replicate API request failed'}
            
        except Exception as e:
            return {'success': False, 'error': f"Replicate texture error: {str(e)}"}
    
    def _fallback_texture_application(self, image: Image.Image, texture_type: str, 
                                    error: str = None) -> Dict[str, Any]:
        """
        Basic texture simulation using image filters
        """
        try:
            img_array = np.array(image)
            
            # Apply texture-specific processing
            if texture_type == 'lace':
                # Create lace-like pattern using noise
                noise = np.random.random(img_array.shape[:2]) * 50
                pattern = (noise > 25).astype(np.uint8) * 255
                
                # Apply transparency effect for lace areas
                for i in range(3):  # RGB channels
                    img_array[:, :, i] = np.where(
                        pattern > 0, 
                        np.clip(img_array[:, :, i] * 0.7 + pattern * 0.3, 0, 255),
                        img_array[:, :, i]
                    )
            
            elif texture_type == 'silk':
                # Apply smooth gradient effect for silk sheen
                from PIL import ImageEnhance
                pil_image = Image.fromarray(img_array.astype(np.uint8))
                enhancer = ImageEnhance.Brightness(pil_image)
                brightened = enhancer.enhance(1.1)
                enhancer = ImageEnhance.Contrast(brightened)
                contrasted = enhancer.enhance(1.05)
                img_array = np.array(contrasted)
            
            elif texture_type == 'embroidery':
                # Add slight texture overlay
                texture_overlay = np.random.normal(0, 5, img_array.shape)
                img_array = np.clip(img_array + texture_overlay, 0, 255)
            
            # Default: slight enhancement for any texture
            textured_image = Image.fromarray(img_array.astype(np.uint8))
            
            return {
                'textured_image': textured_image,
                'method': 'fallback_filter_texture',
                'success': True,
                'fallback_reason': error or 'AI texture services unavailable',
                'note': f'Basic {texture_type} texture applied - configure API keys for AI-powered results'
            }
            
        except Exception as e:
            # Return original if all fails
            return {
                'textured_image': image,
                'method': 'no_texture_processing',
                'success': False,
                'error': f"All texture methods failed: {str(e)}"
            }
    
    def _build_texture_prompt(self, base_prompt: str, texture_type: str, 
                            pantone_colors: List[Dict] = None) -> str:
        """
        Build enhanced prompt with color and garment context
        """
        prompt_parts = [
            f"High-quality {texture_type} texture application,",
            base_prompt,
            "realistic fabric surface, professional fashion photography,",
        ]
        
        # Add color context if available
        if pantone_colors:
            for color in pantone_colors[:2]:  # Top 2 colors
                if 'name' in color:
                    color_name = color['name'].lower()
                    prompt_parts.append(f"in {color_name} color,")
        
        # Add texture-specific quality terms
        quality_terms = {
            'lace': "intricate details, delicate transparency, fine craftsmanship",
            'embroidery': "raised threads, detailed stitching, luxury finish",
            'silk': "lustrous sheen, smooth surface, elegant draping",
            'satin': "glossy finish, reflective surface, premium quality",
            'leather': "fine grain, natural texture, luxury material",
            'velvet': "soft pile, rich texture, plush surface",
            'mesh': "breathable texture, athletic quality, technical fabric",
            'sequin': "sparkling surface, reflective elements, glamorous finish"
        }
        
        if texture_type in quality_terms:
            prompt_parts.append(quality_terms[texture_type])
        
        prompt_parts.extend([
            "high resolution, sharp details, professional quality,",
            "realistic lighting, fabric authenticity"
        ])
        
        return " ".join(prompt_parts)
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string"""
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    def process_full_texture_workflow(self, colorized_image: Image.Image,
                                    texture_type: str,
                                    pantone_colors: List[Dict] = None,
                                    texture_areas: List[Dict] = None,
                                    intensity: float = 0.8) -> Dict[str, Any]:
        """
        Complete texture application workflow
        """
        workflow_start = datetime.now()
        
        # Step 1: Prepare texture mask
        mask_result = self.prepare_texture_mask(colorized_image, texture_areas)
        texture_mask = mask_result['mask_image']
        
        # Step 2: Apply texture
        texture_result = self.apply_texture_with_stable_diffusion(
            colorized_image, texture_type, pantone_colors, texture_mask
        )
        
        if not texture_result.get('success'):
            return {
                'success': False,
                'error': texture_result.get('error', 'Texture application failed'),
                'original_image': colorized_image,
                'mask_info': mask_result
            }
        
        textured_image = texture_result['textured_image']
        
        # Step 3: Blend with original based on intensity
        if intensity < 1.0:
            # Blend textured and original
            original_array = np.array(colorized_image)
            textured_array = np.array(textured_image)
            
            blended_array = (
                original_array * (1 - intensity) + 
                textured_array * intensity
            ).astype(np.uint8)
            
            final_image = Image.fromarray(blended_array)
        else:
            final_image = textured_image
        
        workflow_time = (datetime.now() - workflow_start).total_seconds()
        
        return {
            'success': True,
            'original_image': colorized_image,
            'textured_image': final_image,
            'texture_type': texture_type,
            'intensity_applied': intensity,
            'mask_info': mask_result,
            'texture_processing': texture_result,
            'pantone_colors_used': pantone_colors,
            'workflow_time_seconds': workflow_time,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_available_textures(self) -> Dict[str, Any]:
        """
        Return available texture types with descriptions
        """
        return {
            'textures': {
                name: {
                    'name': name.title(),
                    'description': config['prompt'],
                    'recommended_for': self._get_texture_recommendations(name),
                    'processing_time': f"{config['steps']}s estimated"
                }
                for name, config in self.texture_prompts.items()
            },
            'total_available': len(self.texture_prompts),
            'api_status': {
                'huggingface': 'configured' if self.hf_api_key and self.hf_api_key != 'your_hf_token_here' else 'not_configured',
                'replicate': 'configured' if self.replicate_key and self.replicate_key != 'your_replicate_token_here' else 'not_configured',
                'stability': 'configured' if self.stability_key and self.stability_key != 'your_stability_token_here' else 'not_configured'
            }
        }
    
    def _get_texture_recommendations(self, texture_type: str) -> List[str]:
        """
        Get garment type recommendations for each texture
        """
        recommendations = {
            'lace': ['lingerie', 'bodysuits', 'evening wear', 'bridal'],
            'embroidery': ['formal wear', 'cultural garments', 'luxury items'],
            'silk': ['evening wear', 'blouses', 'luxury garments', 'scarves'],
            'satin': ['evening wear', 'lingerie', 'formal wear', 'bridal'],
            'leather': ['jackets', 'pants', 'accessories', 'edgy fashion'],
            'velvet': ['evening wear', 'luxury items', 'winter clothing'],
            'mesh': ['athletic wear', 'lingerie', 'modern fashion', 'casual'],
            'sequin': ['party wear', 'evening gowns', 'performance costumes']
        }
        return recommendations.get(texture_type, ['general garments'])

    def _detect_texture_pattern(self, texture_image: Image.Image) -> Dict[str, Any]:
        """
        Analyze uploaded texture to identify pattern type using AI
        """
        try:
            # Convert to grayscale for analysis
            gray = texture_image.convert('L')
            img_array = np.array(gray)
            
            # Calculate texture features
            mean_val = np.mean(img_array)
            std_val = np.std(img_array)
            
            # Edge density (for lace detection)
            from PIL import ImageFilter
            edges = gray.filter(ImageFilter.FIND_EDGES)
            edge_density = np.mean(np.array(edges)) / 255.0
            
            # Pattern regularity (using gradient analysis)
            grad_x = np.abs(np.diff(img_array, axis=1))
            grad_y = np.abs(np.diff(img_array, axis=0))
            gradient_variance = np.var(grad_x) + np.var(grad_y)
            
            # Texture classification based on features
            texture_type = 'generic'
            confidence = 0.5
            
            # Improved lace detection - look for white/light areas with intricate patterns
            if (mean_val > 150 and std_val > 40 and edge_density > 0.05) or \
               (edge_density > 0.3 and std_val > 50):
                # Light with patterns OR high edge density = likely lace
                texture_type = 'lace'
                confidence = min(0.9, (mean_val / 255.0) * 0.5 + edge_density * 0.5)
            elif mean_val > 200 and std_val < 30:
                # High brightness, low variation = silk/satin
                texture_type = 'silk'
                confidence = 0.7
            elif gradient_variance > 25000 and std_val > 40 and edge_density < 0.1:
                # High texture variation but low edges = embroidery/complex pattern
                texture_type = 'embroidery'
                confidence = 0.8
            elif std_val < 20:
                # Very smooth = satin/leather
                texture_type = 'satin'
                confidence = 0.6
            
            return {
                'detected_type': texture_type,
                'confidence': confidence,
                'features': {
                    'edge_density': edge_density,
                    'mean_brightness': mean_val,
                    'std_deviation': std_val,
                    'gradient_variance': gradient_variance
                }
            }
            
        except Exception as e:
            print(f"Warning: Pattern detection failed: {e}")
            return {
                'detected_type': 'generic',
                'confidence': 0.3,
                'features': {},
                'error': str(e)
            }

    def apply_custom_texture(self, colorized_image: Image.Image,
                           texture_image: Image.Image,
                           pantone_colors: Optional[List[Dict]] = None,
                           intensity: float = 0.8) -> Dict[str, Any]:
        """
        Apply custom texture from uploaded image to colorized sketch with AI pattern recognition
        
        Args:
            colorized_image: The colorized garment sketch
            texture_image: Custom texture image from user upload
            pantone_colors: Pantone color information for context
            intensity: Texture application intensity (0.0-1.0)
            
        Returns:
            Dict with success status and processed image
        """
        start_time = datetime.now()
        
        try:
            print(f"🎨 APPLYING CUSTOM TEXTURE WITH AI ANALYSIS")
            print(f"   • Colorized Image: {colorized_image.size}")
            print(f"   • Texture Image: {texture_image.size}")
            print(f"   • Intensity: {intensity}")
            
            # Step 1: Analyze texture pattern using AI
            pattern_analysis = self._detect_texture_pattern(texture_image)
            detected_type = pattern_analysis['detected_type']
            confidence = pattern_analysis['confidence']
            
            print(f"🔍 TEXTURE ANALYSIS:")
            print(f"   • Detected Pattern: {detected_type}")
            print(f"   • Confidence: {confidence:.2f}")
            print(f"   • Features: {pattern_analysis['features']}")
            
            # Step 2: Try AI-powered texture synthesis if confidence is high
            ai_result = None
            if confidence > 0.7 and self.hf_api_key and self.hf_api_key != 'your_hf_token_here':
                print(f"🤖 Attempting AI synthesis for {detected_type} texture...")
                
                # Use the AI pipeline for detected texture type
                texture_config = self.texture_prompts.get(detected_type, self.texture_prompts['silk'])
                
                # Prepare mask for AI processing
                mask_info = self.prepare_texture_mask(colorized_image)
                
                # Try AI texture application
                ai_result = self.apply_texture_with_stable_diffusion(
                    colorized_image, 
                    detected_type, 
                    pantone_colors, 
                    mask_info['mask_image']
                )
                
                if ai_result.get('success'):
                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    print(f"✅ AI TEXTURE SYNTHESIS SUCCESSFUL in {processing_time:.1f}ms")
                    
                    return {
                        'success': True,
                        'textured_image': ai_result['textured_image'],
                        'processing_time_ms': processing_time,
                        'texture_type': f'ai_{detected_type}',
                        'intensity_applied': intensity,
                        'pattern_analysis': pattern_analysis,
                        'ai_method': ai_result.get('method', 'unknown'),
                        'message': f'AI-powered {detected_type} texture applied successfully'
                    }
            
            # Step 3: Fallback to enhanced custom blending
            print(f"🎭 Using enhanced blending for custom texture...")
            
            # Resize texture to match colorized image dimensions
            target_size = colorized_image.size
            texture_resized = texture_image.resize(target_size, Image.Resampling.LANCZOS)
            
            # Convert images to RGB if needed
            if colorized_image.mode != 'RGB':
                colorized_image = colorized_image.convert('RGB')
            if texture_resized.mode != 'RGB':
                texture_resized = texture_resized.convert('RGB')
            
            # Create garment mask with pattern-specific adjustments
            mask_info = self.prepare_texture_mask(colorized_image)
            garment_mask = mask_info['mask_image']
            
            print(f"🎭 Mask Coverage: {mask_info['coverage_percentage']:.1f}% of image")
            print(f"   • Adaptive Threshold: {mask_info.get('adaptive_threshold', 'N/A')}")
            
            # Adjust intensity based on detected pattern
            if detected_type == 'lace' and confidence > 0.5:
                # Lace needs higher intensity for visibility
                adjusted_intensity = min(1.0, intensity * 1.2)
            elif detected_type in ['silk', 'satin'] and confidence > 0.5:
                # Silk/satin needs subtle application
                adjusted_intensity = intensity * 0.8
            else:
                adjusted_intensity = intensity
            
            # Apply texture using enhanced blend modes
            textured_result = self._blend_custom_texture(
                colorized_image, 
                texture_resized, 
                garment_mask, 
                adjusted_intensity
            )
            
            # Apply pattern-specific enhancements
            if detected_type == 'lace' and confidence > 0.5:
                # Additional enhancement for lace patterns
                textured_result = self._enhance_lace_texture(textured_result)
            else:
                # Standard enhancement
                textured_result = self._enhance_textured_result(textured_result)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            print(f"✅ ENHANCED CUSTOM TEXTURE APPLIED in {processing_time:.1f}ms")
            
            return {
                'success': True,
                'textured_image': textured_result,
                'processing_time_ms': processing_time,
                'texture_type': f'custom_{detected_type}',
                'intensity_applied': adjusted_intensity,
                'pattern_analysis': pattern_analysis,
                'mask_info': mask_info,
                'message': f'Enhanced {detected_type} texture applied successfully'
            }
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Custom texture application failed: {str(e)}"
            print(f"❌ ERROR: {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'processing_time_ms': processing_time,
                'timestamp': datetime.now().isoformat()
            }
    
    def _blend_custom_texture(self, base_image: Image.Image, 
                            texture_image: Image.Image,
                            mask: Image.Image,
                            intensity: float) -> Image.Image:
        """
        Blend custom texture with base image using corrected mathematical operations
        """
        try:
            # Convert to numpy arrays for processing (use float64 to prevent overflow)
            base_array = np.array(base_image, dtype=np.float64)
            texture_array = np.array(texture_image, dtype=np.float64)
            
            # Convert mask to numpy array
            mask_array = np.array(mask, dtype=np.float64)
            if mask_array.ndim == 3:
                mask_array = mask_array[:, :, 0]  # Use first channel if RGB
            mask_array = np.clip(mask_array / 255.0, 0.0, 1.0)
            
            # Normalize arrays to 0-1 range for calculations
            base_norm = base_array / 255.0
            texture_norm = texture_array / 255.0
            
            # Apply safe blending modes with proper bounds checking
            # 1. Multiply blend for shadows and depth
            multiply_blend = np.clip(base_norm * texture_norm, 0.0, 1.0)
            
            # 2. Overlay blend for highlights (fixed math)
            overlay_condition = base_norm < 0.5
            overlay_blend = np.where(
                overlay_condition,
                np.clip(2.0 * base_norm * texture_norm, 0.0, 1.0),
                np.clip(1.0 - 2.0 * (1.0 - base_norm) * (1.0 - texture_norm), 0.0, 1.0)
            )
            
            # 3. Soft light for subtle texture (simplified and safe)
            soft_light_condition = texture_norm < 0.5
            soft_light = np.where(
                soft_light_condition,
                np.clip(base_norm * (2.0 * texture_norm + base_norm * (1.0 - 2.0 * texture_norm)), 0.0, 1.0),
                np.clip(base_norm + (2.0 * texture_norm - 1.0) * (np.sqrt(np.clip(base_norm, 0.001, 1.0)) - base_norm), 0.0, 1.0)
            )
            
            # Combine blend modes with safe weights
            combined = np.clip(
                multiply_blend * 0.3 +
                overlay_blend * 0.4 + 
                soft_light * 0.3,
                0.0, 1.0
            )
            
            # Apply intensity and mask with proper broadcasting
            result = base_norm.copy()
            
            # Handle both grayscale and RGB textures
            if len(combined.shape) == 2:  # Grayscale texture
                combined = np.stack([combined] * 3, axis=2)
            
            # Apply mask to each channel
            mask_3d = np.stack([mask_array] * 3, axis=2)
            blended_intensity = np.clip(intensity, 0.0, 1.0)
            
            result = (
                result * (1.0 - blended_intensity * mask_3d) + 
                combined * blended_intensity * mask_3d
            )
            
            # Convert back to 0-255 range and uint8
            result = np.clip(result * 255.0, 0, 255).astype(np.uint8)
            return Image.fromarray(result)
            
        except Exception as e:
            print(f"Warning: Advanced blending failed ({str(e)}), using simple blend")
            # Fallback to simple blend with safety checks
            try:
                return Image.blend(base_image, texture_image, np.clip(intensity * 0.5, 0.0, 1.0))
            except:
                print("Warning: Simple blend also failed, returning original image")
                return base_image
    
    def _enhance_lace_texture(self, image: Image.Image) -> Image.Image:
        """
        Apply lace-specific enhancements to preserve delicate patterns
        """
        try:
            # Enhance contrast more aggressively for lace visibility
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.15)
            
            # Reduce color saturation slightly to maintain lace delicacy
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(0.95)
            
            # Increase brightness slightly for white lace visibility
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.05)
            
            # More aggressive sharpening for lace detail
            image = image.filter(ImageFilter.UnsharpMask(radius=0.8, percent=70, threshold=1))
            
            # Apply slight edge enhancement
            edge_enhance = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
            # Blend original with edge-enhanced version
            image = Image.blend(image, edge_enhance, 0.15)
            
            return image
            
        except Exception as e:
            print(f"Warning: Lace enhancement failed: {e}")
            return self._enhance_textured_result(image)

    def _enhance_textured_result(self, image: Image.Image) -> Image.Image:
        """
        Apply post-processing enhancements to textured image
        """
        try:
            # Enhance contrast slightly
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
            
            # Enhance color saturation
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.05)
            
            # Slight sharpening for texture detail
            image = image.filter(ImageFilter.UnsharpMask(radius=0.5, percent=50, threshold=2))
            
            return image
            
        except Exception as e:
            print(f"Warning: Enhancement failed: {e}")
            return image

# Example usage and testing
if __name__ == "__main__":
    service = TextureApplicationService()
    
    print("🧵 TEXTURE APPLICATION SERVICE")
    print("=" * 50)
    
    # Show available textures
    available = service.get_available_textures()
    print(f"Available Textures: {available['total_available']}")
    
    for name, info in available['textures'].items():
        print(f"  • {info['name']}: {info['recommended_for']}")
    
    # API status
    api_status = available['api_status']
    print(f"\nAPI Status:")
    print(f"  HuggingFace: {'✅' if api_status['huggingface'] == 'configured' else '❌'}")
    print(f"  Replicate: {'✅' if api_status['replicate'] == 'configured' else '❌'}")
    print(f"  Stability: {'✅' if api_status['stability'] == 'configured' else '❌'}")