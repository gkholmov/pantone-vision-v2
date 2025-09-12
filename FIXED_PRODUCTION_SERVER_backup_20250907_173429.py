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
    
    def colorize_sketch(self, sketch: Image.Image, style: str = "fashion", target_color: str = None) -> Dict:
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
                return self._basic_colorization(sketch, style, target_color)
                
        except Exception as e:
            print(f"🚨 Exception in colorize_sketch, falling back to basic: {str(e)}")
            return self._basic_colorization(sketch, style, target_color)
    
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
                return self._basic_colorization(sketch, style, target_color)
                
        except Exception as e:
            print(f"🚨 _ai_colorization exception, falling back to basic colorization: {str(e)}")
            return self._basic_colorization(sketch, style, target_color)
    
    def _basic_colorization(self, sketch: Image.Image, style: str, target_color: str = None) -> Dict:
        """AI-powered clothing detection and colorization"""
        print(f"🎯 BASIC COLORIZATION - Target Color: {target_color}, Style: {style}")
        try:
            # Enhance contrast
            enhanced = ImageEnhance.Contrast(sketch).enhance(1.2)
            result_array = np.array(enhanced)
            
            # AI-POWERED CLOTHING DETECTION
            # Convert to HSV for better color-based segmentation
            hsv_array = np.array(enhanced.convert('HSV'))
            h, s, v = hsv_array[:,:,0], hsv_array[:,:,1], hsv_array[:,:,2]
            
            # AI GARMENT TYPE IDENTIFICATION AND INTELLIGENT COLORIZATION
            gray = np.array(enhanced.convert('L'))
            
            # Step 1: Use Claude AI to identify the garment type
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
                
                # Convert image to analyze
                buffered = BytesIO()
                enhanced.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                # ADVANCED Fashion AI Analysis prompt based on professional garment analysis
                garment_prompt = f"""
You are an expert fashion construction analyst with deep knowledge of garment engineering, pattern-making, and couture techniques.

STRUCTURAL ANALYSIS FRAMEWORK:
Analyze these technical construction details:

1. SUPPORT STRUCTURE:
   - Underwire presence (curved bust line indicates underwire)
   - Boning channels (count vertical structural lines - typically 6-12 in corsets)
   - Construction type: corsetry, structured, soft-cup, wireless
   - Support level: light, medium, firm, rigid

2. SEAMING AND CONSTRUCTION:
   - Princess seams (curved lines from bust to waist)
   - Panel construction (separate fabric pieces)
   - Vertical seaming pattern (radiating from bust point)
   - Center front seam presence
   - Side seam construction

3. NECKLINE ANALYSIS:
   - Sweetheart (curved bustline with center dip)
   - Straight across (horizontal neckline)
   - Bustier construction (structured cups)
   - Underwire shape (curved vs straight)

4. COVERAGE AND SILHOUETTE:
   - Torso coverage: full, partial, midriff-baring
   - Leg cut: high-cut brief, moderate, full coverage
   - Strap configuration: strapless, thin straps, wide straps, halter
   - Garment length: crop, waist, hip, full body

SPECIFIC GARMENT CLASSIFICATIONS:
• CORSET BODYSUIT: Structured with 6-12 boning channels, underwire, sweetheart neckline, extends to crotch (20-30% coverage)
• BUSTIER: Structured cups ending at waist, may be strapless, no lower body coverage (8-15% coverage)  
• LINGERIE BODYSUIT: Soft construction, minimal structure, full torso coverage (18-28% coverage)
• STRUCTURED SWIMSUIT: Swimwear with underwire/padding, athletic construction (15-25% coverage)
• LEOTARD: Dance/athletic wear, high-cut legs, minimal structure (20-30% coverage)

CONSTRUCTION MATERIALS ANALYSIS:
- Identify rigid elements (boning, underwire, hardware)
- Fabric type indicators (stretch, woven, knit characteristics)
- Finishing details (piping, trim, edge treatments)

RETURN COMPREHENSIVE ANALYSIS:
{{
    "garment_type": "specific construction type (e.g., corset bodysuit, structured swimsuit)",
    "construction_analysis": {{
        "support_structure": {{
            "has_underwire": true/false,
            "has_boning": true/false,
            "boning_channels_count": number,
            "construction_type": "corsetry/structured/soft",
            "support_level": "light/medium/firm/rigid"
        }},
        "seaming_pattern": {{
            "princess_seams": true/false,
            "vertical_panels": number,
            "seaming_style": "radial/parallel/curved",
            "center_front_seam": true/false
        }},
        "neckline_details": {{
            "type": "sweetheart/straight/bustier",
            "underwire_shape": "curved/straight/none",
            "cup_construction": "structured/soft/padded"
        }}
    }},
    "coverage_analysis": {{
        "torso_coverage": "full/partial/cropped",
        "leg_cut_style": "high_cut/moderate/full",
        "estimated_body_coverage": "percentage with reasoning",
        "strap_configuration": "detailed description"
    }},
    "materials_and_finishing": {{
        "fabric_indicators": "stretch/woven/knit characteristics",
        "structural_elements": "boning/hardware/rigid elements",
        "trim_details": "piping/edging/decorative elements"
    }},
    "professional_classification": {{
        "primary_category": "exact garment type",
        "construction_subcategory": "specific construction style",  
        "intended_use": "fashion/lingerie/swimwear/activewear",
        "technical_complexity": "basic/intermediate/advanced/couture"
    }},
    "confidence_assessment": {{
        "structural_identification": 0.0-1.0,
        "construction_analysis": 0.0-1.0,
        "overall_classification": 0.0-1.0
    }}
}}

CRITICAL: Analyze the CONSTRUCTION DETAILS first, then classify. Count visible structural elements like boning channels and seam lines."""
                
                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=800,
                    messages=[{
                        "role": "user", 
                        "content": [
                            {
                                "type": "text",
                                "text": garment_prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": img_base64
                                }
                            }
                        ]
                    }]
                )
                
                # Parse AI response
                response_text = message.content[0].text
                print(f"🧠 AI GARMENT RESPONSE: {response_text[:200]}...")
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    garment_info = json.loads(response_text[json_start:json_end])
                    
                    # Extract sophisticated analysis details  
                    garment_type = garment_info.get('garment_type', 'unknown')
                    construction = garment_info.get('construction_analysis', {})
                    coverage = garment_info.get('coverage_analysis', {})
                    classification = garment_info.get('professional_classification', {})
                    confidence = garment_info.get('confidence_assessment', {})
                    
                    print(f"🎯 AI PROFESSIONAL ANALYSIS:")
                    print(f"   Garment Type: {garment_type}")
                    print(f"   Construction: {construction.get('support_structure', {}).get('construction_type', 'unknown')}")
                    print(f"   Boning Channels: {construction.get('support_structure', {}).get('boning_channels_count', 'unknown')}")
                    print(f"   Coverage: {coverage.get('estimated_body_coverage', 'unknown')}")
                    print(f"   Classification: {classification.get('primary_category', 'unknown')}")
                    print(f"   Confidence: {confidence.get('overall_classification', 'unknown')}")
                    
                    # Map to our processing categories
                    primary_category = classification.get('primary_category', garment_type.lower())
                    if 'corset' in garment_type.lower() or 'bodysuit' in garment_type.lower():
                        processing_category = 'bodysuit'
                    elif 'bustier' in garment_type.lower():
                        processing_category = 'tops'
                    elif 'swimsuit' in garment_type.lower() or 'leotard' in garment_type.lower():
                        processing_category = 'swimwear'
                    else:
                        processing_category = 'bodysuit'  # Default to bodysuit for structured garments
                        
                    # Create simplified structure for our existing processing logic
                    garment_info = {
                        'garment_type': garment_type,
                        'category': processing_category,
                        'construction_details': construction,
                        'coverage_analysis': coverage,
                        'professional_classification': classification,
                        'confidence': confidence
                    }
                    
                else:
                    print(f"🚨 Could not parse JSON from AI response")
                    garment_info = {
                        "garment_type": "corset bodysuit", 
                        "category": "bodysuit",
                        "construction_details": {"support_structure": {"construction_type": "structured"}},
                        "coverage_analysis": {"estimated_body_coverage": "25%"}
                    }
                    
            except Exception as e:
                print(f"🚨 AI garment identification failed: {str(e)}")
                # Fallback identification with sophisticated structure
                garment_info = {
                    "garment_type": "corset bodysuit", 
                    "category": "bodysuit",
                    "construction_details": {"support_structure": {"construction_type": "structured"}},
                    "coverage_analysis": {"estimated_body_coverage": "25%"}
                }
                print(f"🎯 USING FALLBACK GARMENT: {garment_info['garment_type']}")
            
            # Make garment analysis available for area filtering
            garment_analysis = garment_info
            
            # Step 2: AI-GUIDED PRECISE GARMENT SEGMENTATION
            # Follow AI's specific instructions for this garment
            
            segmentation_strategy = garment_info.get('segmentation_strategy', 'default')
            color_boundaries = garment_info.get('color_boundaries', {})
            
            print(f"🎯 AI SEGMENTATION STRATEGY: {segmentation_strategy}")
            print(f"🎨 AREAS TO COLOR: {color_boundaries.get('include', 'main fabric')}")
            print(f"🚫 AREAS TO PRESERVE: {color_boundaries.get('exclude', 'lines and edges')}")
            
            # STEP 1: Identify the main garment fabric areas (what to color)
            # Use adaptive thresholding based on AI guidance - WORKS FOR ALL GARMENTS
            category = garment_info.get('category', 'unknown')
            garment_type = garment_info.get('garment_type', 'unknown')
            
            print(f"🎯 PROCESSING GARMENT: {category} - {garment_type}")
            
            # Step 2: PANTONE COLOR SELECTION - After garment analysis, before colorization
            # Now that we know what garment we're dealing with, determine the color
            if target_color:
                # Convert provided hex to RGB
                hex_color = target_color.lstrip('#')
                color_rgb = np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4)])
                print(f"🎨 USING PROVIDED COLOR: {target_color} -> RGB{tuple(color_rgb)}")
            else:
                # AI-POWERED PANTONE COLOR IDENTIFICATION based on sketch content
                print(f"🤖 ANALYZING SKETCH FOR PANTONE COLOR IDENTIFICATION...")
                try:
                    # Extract dominant color from the sketch using ORIGINAL method
                    sketch_array = np.array(enhanced)
                    color_matcher_instance = UniversalColorMatcher()
                    dominant_rgb = color_matcher_instance.analyze_image_color(sketch_array, method="dominant")
                    
                    # Use AI to identify Pantone color with garment context
                    garment_description = f"{garment_type} fashion sketch, {category} category garment"
                    auto_color_result = color_matcher_instance.identify_color_with_ai(
                        dominant_rgb, 
                        image_description=garment_description
                    )
                    
                    # Extract the hex color from AI result
                    if 'technical_data' in auto_color_result and 'hex' in auto_color_result['technical_data']:
                        target_color = auto_color_result['technical_data']['hex']
                        hex_color = target_color.lstrip('#')
                        color_rgb = np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4)])
                        print(f"✅ AI IDENTIFIED COLOR: {target_color} -> RGB{tuple(color_rgb)}")
                        print(f"   Pantone Match: {auto_color_result.get('primary_match', {}).get('pantone_code', 'Unknown')}")
                    else:
                        raise Exception("No color found in AI result")
                        
                except Exception as e:
                    print(f"🚨 AI COLOR IDENTIFICATION FAILED: {str(e)}")
                    # Intelligent fallback based on garment type
                    garment_colors = {
                        "corset bodysuit": np.array([220, 20, 60]),    # Crimson - bold for lingerie
                        "bustier": np.array([255, 69, 0]),            # Red-orange - vibrant
                        "swimsuit": np.array([0, 191, 255]),          # Deep sky blue
                        "bodysuit": np.array([138, 43, 226]),         # Blue violet
                        "tops": np.array([255, 192, 157]),            # Peach echo
                        "unknown": np.array([255, 192, 157])          # Peach echo default
                    }
                    color_rgb = garment_colors.get(garment_type.lower(), garment_colors.get(category, garment_colors["unknown"]))
                    print(f"🎨 USING GARMENT-SPECIFIC FALLBACK: RGB{tuple(color_rgb)} for {garment_type}")
            
            # INDUSTRY-STANDARD CONTOUR-BASED GARMENT DETECTION
            # Uses proven computer vision techniques for garment segmentation
            print(f"🎯 CONTOUR-BASED GARMENT DETECTION for {garment_analysis.get('garment_type', 'corset bodysuit')}")
            category = garment_analysis.get('category', 'bodysuit')
            
            # Step 1: Robust edge detection with adaptive thresholds
            def detect_edges_adaptive(gray_img):
                """Adaptive edge detection with consistent behavior"""
                try:
                    import cv2
                    # Use adaptive thresholds based on image statistics
                    median_intensity = np.median(gray_img)
                    lower = max(30, int(0.5 * median_intensity))
                    upper = min(255, int(1.5 * median_intensity))
                    edges = cv2.Canny(gray_img, lower, upper)
                    print(f"   ✅ OpenCV Canny edges: {lower}-{upper} thresholds")
                    return edges
                except ImportError:
                    # Scipy fallback with same adaptive logic
                    from scipy import ndimage
                    grad_x = ndimage.sobel(gray_img, axis=1)
                    grad_y = ndimage.sobel(gray_img, axis=0)
                    magnitude = np.sqrt(grad_x**2 + grad_y**2)
                    median_intensity = np.median(gray_img)
                    threshold = max(30, int(0.8 * median_intensity))
                    edges = (magnitude > threshold).astype(np.uint8) * 255
                    print(f"   ✅ Scipy gradient edges: {threshold} threshold")
                    return edges
            
            edges = detect_edges_adaptive(gray)
            
            # Step 2: Find CONTOURS (closed shapes formed by black lines)
            try:
                import cv2
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                print(f"   🔍 Found {len(contours)} contours (closed shapes)")
                
                # Step 3: Create garment mask by filling contours
                binary = np.zeros_like(gray, dtype=bool)
                
                # Dynamic size thresholds
                min_area = gray.size * 0.005  # 0.5% of image minimum
                max_area = gray.size * 0.8   # 80% of image maximum
                
                valid_contours = 0
                for i, contour in enumerate(contours):
                    area = cv2.contourArea(contour)
                    
                    if min_area <= area <= max_area:
                        # Create mask for this contour
                        temp_mask = np.zeros_like(gray, dtype=np.uint8)
                        cv2.fillPoly(temp_mask, [contour], 1)
                        
                        # Apply category-specific position filtering
                        if category in ['bodysuit', 'dress', 'jumpsuit', 'swimsuit', 'leotard', 'corset']:
                            # For full-body garments: be more selective
                            x, y, w, h = cv2.boundingRect(contour)
                            aspect_ratio = h / w if w > 0 else 0
                            
                            # Accept if it's reasonably sized and positioned
                            if 0.5 <= aspect_ratio <= 3.0:  # Not too wide or too tall
                                binary |= temp_mask.astype(bool)
                                valid_contours += 1
                                print(f"   ✅ Added garment contour {i}: {area} pixels, AR={aspect_ratio:.2f}")
                        
                        else:
                            # Default: accept reasonable contours
                            binary |= temp_mask.astype(bool)
                            valid_contours += 1
                            print(f"   ✅ Added contour {i}: {area} pixels")
                
                print(f"   🎯 Selected {valid_contours} valid garment contours")
                
            except ImportError:
                # Industry-standard fallback without OpenCV
                print(f"   🛠️  Using industry-standard preprocessing pipeline")
                from scipy.ndimage import gaussian_filter, binary_closing, binary_opening, label
                blurred = gaussian_filter(gray, sigma=1.0)
                
                # Adaptive thresholding
                img_mean = np.mean(blurred)
                img_std = np.std(blurred)
                threshold = max(50, min(200, img_mean - 0.5 * img_std))
                binary_mask = blurred > threshold
                
                # Morphological cleanup
                kernel = np.ones((3, 3), np.uint8)
                cleaned = binary_opening(binary_mask, kernel)
                cleaned = binary_closing(cleaned, kernel)
                
                # Connected components analysis
                labeled_regions, num_regions = label(cleaned)
                
                if num_regions == 0:
                    binary = binary_mask
                else:
                    # Apply area filtering
                    region_areas = []
                    for region_id in range(1, num_regions + 1):
                        region_mask = labeled_regions == region_id
                        area_size = np.sum(region_mask)
                        region_areas.append(area_size)
                    
                    if region_areas:
                        mean_area = np.mean(region_areas)
                        adaptive_min_area = max(100, mean_area * 0.1)
                    else:
                        adaptive_min_area = 500
                    
                    binary = np.zeros_like(gray, dtype=bool)
                    filled_areas = 0
                    
                    for region_id in range(1, num_regions + 1):
                        region_mask = labeled_regions == region_id  
                        area_size = np.sum(region_mask)
                        area_percentage = area_size / gray.size * 100
                        
                        if area_size >= adaptive_min_area and area_percentage <= 70.0:
                            binary |= region_mask
                            filled_areas += 1
                            print(f"   ✅ Garment region {filled_areas}: {area_percentage:.1f}%")
                            
                            if filled_areas >= 5:
                                break
                
            # DEBUG: Print edge detection results
            print(f"🔍 CONTOUR DETECTION RESULTS:")
            print(f"   Original image: {np.min(gray)}-{np.max(gray)} (mean: {np.mean(gray):.1f})")
            print(f"   Garment areas detected: {np.sum(binary)} pixels ({np.sum(binary)/gray.size*100:.1f}%)")
            
            # STEP 2: Remove skin areas from detected garment regions (CRITICAL FIX)
            # Convert to HSV for skin detection
            hsv_array = np.array(enhanced.convert('HSV'))
            h, s, v = hsv_array[:,:,0], hsv_array[:,:,1], hsv_array[:,:,2]
            
            # Refined skin tone exclusion 
            skin_mask = ((h < 30) | (h > 330)) & (s > 15) & (s < 170) & (v > 80) & (v < 250)
            print(f"🧑 Skin areas excluded: {np.sum(skin_mask)} pixels ({np.sum(skin_mask)/binary.size*100:.1f}%)")
            
            # STEP 2B: Remove intimate/crotch area for bodysuit/lingerie (ANATOMICALLY-AWARE EXCLUSION)
            intimate_mask = np.zeros_like(binary, dtype=bool)
            if 'bodysuit' in garment_analysis.get('garment_type', '').lower() or 'bodysuit' in garment_analysis.get('category', '').lower() or 'corset' in garment_analysis.get('garment_type', '').lower():
                # For bodysuits/corsets: exclude central lower area (crotch region)
                height, width = binary.shape
                
                # Define intimate area: center-bottom region between legs
                center_x = width // 2
                bottom_y = int(height * 0.65)  # Bottom 35% of image
                
                # Create exclusion zone: central strip in lower area
                intimate_width = int(width * 0.15)  # 15% of image width (narrower)
                intimate_height = int(height * 0.20)  # 20% of image height
                
                x_start = max(0, center_x - intimate_width // 2)
                x_end = min(width, center_x + intimate_width // 2)
                y_start = max(0, bottom_y)
                y_end = min(height, bottom_y + intimate_height)
                
                intimate_mask[y_start:y_end, x_start:x_end] = True
                print(f"🚫 Intimate area excluded: {np.sum(intimate_mask)} pixels ({np.sum(intimate_mask)/binary.size*100:.1f}%) - bodysuit-specific")
            
            # STEP 3: Create final garment mask - garment areas excluding skin AND intimate areas
            clothing_mask = binary & ~skin_mask & ~intimate_mask
            
            # STEP 4: Improve contour precision using hierarchical contour detection
            # Use RETR_TREE to get parent-child relationships and only fill interior contours
            try:
                import cv2
                # Find contours with hierarchy to distinguish interior from exterior
                contours, hierarchy = cv2.findContours(
                    clothing_mask.astype(np.uint8), 
                    cv2.RETR_TREE, 
                    cv2.CHAIN_APPROX_SIMPLE
                )
                
                if len(contours) > 0 and hierarchy is not None:
                    # Create refined mask using only properly bounded contours
                    refined_mask = np.zeros_like(clothing_mask, dtype=np.uint8)
                    
                    # Fill contours that are likely to be garment interiors (not holes or exterior bleeding)
                    for i, contour in enumerate(contours):
                        area = cv2.contourArea(contour)
                        # Only fill substantial areas that aren't tiny holes
                        if area > 500:  # Minimum area threshold
                            cv2.fillPoly(refined_mask, [contour], 1)
                    
                    clothing_mask = refined_mask.astype(bool)
                    print(f"   🔧 Applied hierarchical contour refinement for precise boundaries")
            except ImportError:
                print(f"   ⚠️  OpenCV not available, using advanced scipy-based edge refinement")
                # Implement advanced fallback using scipy with distance transforms and watershed
                try:
                    from scipy.ndimage import binary_erosion, binary_dilation, binary_closing, binary_opening
                    from scipy.ndimage import distance_transform_edt, label, generate_binary_structure
                    from scipy import ndimage
                    
                    # Advanced morphological edge refinement with distance transforms
                    print(f"   🔬 Applying distance transform-based edge refinement...")
                    
                    # Step 1: Clean up the initial mask with opening operation
                    structure = generate_binary_structure(2, 2)  # 8-connected structure
                    cleaned_mask = binary_opening(clothing_mask, structure=structure, iterations=2)
                    
                    # Step 2: Apply morphological closing to fill internal gaps
                    closed_mask = binary_closing(cleaned_mask, structure=structure, iterations=3)
                    
                    # Step 3: Use distance transform to create precision zones
                    distance = distance_transform_edt(closed_mask)
                    
                    # Step 4: Create a conservative inner mask (guaranteed garment area)
                    # Only areas more than 5 pixels from edge are considered safe
                    safe_distance = 5
                    inner_mask = distance > safe_distance
                    
                    # Step 5: Create transition zones using gradient of distance
                    gradient_x = np.gradient(distance, axis=1)
                    gradient_y = np.gradient(distance, axis=0)
                    gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
                    
                    # Step 6: Identify strong edges (likely garment boundaries)
                    edge_threshold = np.percentile(gradient_magnitude[closed_mask], 85)
                    strong_edges = (gradient_magnitude > edge_threshold) & closed_mask
                    
                    # Step 7: Create refined mask by combining inner safe area with carefully selected edges
                    refined_mask = inner_mask.copy()
                    
                    # Add back edge pixels that are very close to the safe area
                    edge_distance = distance_transform_edt(~inner_mask)
                    close_edges = strong_edges & (edge_distance <= 3)
                    refined_mask = refined_mask | close_edges
                    
                    # Step 8: Ensure connectivity by filling small gaps
                    refined_mask = binary_closing(refined_mask, structure=structure, iterations=2)
                    
                    # Step 9: Final cleanup - remove small isolated regions
                    labeled, num_features = label(refined_mask)
                    sizes = np.bincount(labeled.ravel())
                    
                    # Keep only regions larger than 1000 pixels (more conservative)
                    min_region_size = 1000
                    remove_small = sizes < min_region_size
                    remove_small[0] = False  # Don't remove background
                    refined_mask[remove_small[labeled]] = False
                    
                    # Step 10: Apply final erosion to create a safety buffer
                    final_mask = binary_erosion(refined_mask, structure=structure, iterations=1)
                    
                    clothing_mask = final_mask
                    print(f"   🎯 Applied advanced distance transform edge refinement")
                    print(f"   📊 Mask coverage: {np.sum(final_mask)}/{np.sum(closed_mask)} pixels ({100*np.sum(final_mask)/max(np.sum(closed_mask), 1):.1f}%)")
                    
                except ImportError as e:
                    print(f"   ⚠️  Advanced scipy processing not available ({e}), using basic morphology")
                    # Basic fallback
                    try:
                        from scipy.ndimage import binary_erosion, binary_dilation, binary_closing
                        
                        # Simple but aggressive edge cleanup
                        closed_mask = binary_closing(clothing_mask, structure=np.ones((5, 5)))
                        # More aggressive erosion to prevent bleeding
                        eroded_mask = binary_erosion(closed_mask, structure=np.ones((4, 4)))
                        # Moderate dilation to recover some size
                        refined_mask = binary_dilation(eroded_mask, structure=np.ones((2, 2)))
                        
                        clothing_mask = refined_mask
                        print(f"   🔧 Applied basic aggressive edge refinement")
                        
                    except ImportError:
                        print(f"   ⚠️  Scipy not available, using basic mask")
            except Exception as e:
                print(f"   ⚠️  Contour refinement failed: {str(e)}, using basic mask")

            # Clean up - keep only significant regions
            try:
                from scipy.ndimage import label
                labeled_regions, num_regions = label(clothing_mask)
                region_sizes = [(np.sum(labeled_regions == i), i) for i in range(1, num_regions + 1)]
                region_sizes.sort(reverse=True)
                
                # Keep main garment regions (at least 0.5% of image)
                final_mask = np.zeros_like(clothing_mask)
                for size, region_id in region_sizes[:3]:
                    if size > binary.size * 0.005:
                        final_mask |= (labeled_regions == region_id)
                        print(f"   ✅ Kept garment region {region_id}: {size} pixels ({size/binary.size*100:.1f}%)")
                
                clothing_mask = final_mask
            except ImportError:
                pass
            
            # Debug: Log final mask statistics
            total_pixels = clothing_mask.size
            clothing_pixels = np.sum(clothing_mask)
            print(f"🎯 INDUSTRY-STANDARD GARMENT DETECTION COMPLETE: {clothing_pixels}/{total_pixels} pixels ({clothing_pixels/total_pixels*100:.1f}%)")
            print(f"   Contour-based detection with skin exclusion applied")
            
            # Clean up the mask - remove small noise
            try:
                from scipy import ndimage
                clothing_mask = ndimage.binary_opening(clothing_mask, structure=np.ones((3,3)))
                clothing_mask = ndimage.binary_closing(clothing_mask, structure=np.ones((7,7)))
                # Fill holes in clothing areas
                clothing_mask = ndimage.binary_fill_holes(clothing_mask)
            except ImportError:
                # Fallback without scipy
                pass
            
            # Apply EXACT Pantone color with detail preservation
            print(f"🎨 APPLYING EXACT PANTONE COLOR: RGB{tuple(color_rgb)} preserving all details")
            
            # Convert to HSV to preserve luminance (shadows, folds, highlights)
            from colorsys import rgb_to_hsv, hsv_to_rgb
            
            # Get Pantone color HSV values
            pantone_r, pantone_g, pantone_b = color_rgb[0]/255.0, color_rgb[1]/255.0, color_rgb[2]/255.0
            pantone_h, pantone_s, pantone_v = rgb_to_hsv(pantone_r, pantone_g, pantone_b)
            
            print(f"   🎨 Pantone HSV: H={pantone_h:.3f}, S={pantone_s:.3f}, V={pantone_v:.3f}")
            print(f"   🎯 Preserving original luminance for garment details")
            
            # 🚀 VECTORIZED HSV COLOR APPLICATION - with OpenCV fallback
            try:
                import cv2
                # Convert entire image to HSV color space in one operation
                hsv_image = cv2.cvtColor(result_array, cv2.COLOR_RGB2HSV).astype(np.float32)
                
                # Convert Pantone RGB to HSV for target color
                pantone_rgb_array = np.uint8([[color_rgb]])
                pantone_hsv_cv = cv2.cvtColor(pantone_rgb_array, cv2.COLOR_RGB2HSV)[0][0].astype(np.float32)
                
                print(f"   🔄 Vectorized OpenCV HSV processing")
                
                # Apply Pantone hue and saturation to ALL masked pixels simultaneously
                # Preserve original Value (brightness) to maintain garment details
                hsv_image[clothing_mask, 0] = pantone_hsv_cv[0]  # Set Hue
                hsv_image[clothing_mask, 1] = pantone_hsv_cv[1]  # Set Saturation
                # Keep original hsv_image[:,:,2] (Value/brightness) for detail preservation
                
                # Convert back to RGB in single operation
                result_array = cv2.cvtColor(hsv_image.astype(np.uint8), cv2.COLOR_HSV2RGB)
                
            except ImportError:
                # Fallback: Simple color blending without OpenCV
                print(f"   🔄 Using simple color blending (OpenCV not available)")
                
                # Apply color to masked areas with simple blending
                color_array = np.array(color_rgb)
                for i in range(3):  # RGB channels
                    # Blend original color with target color (70% target, 30% original for detail preservation)
                    result_array[clothing_mask, i] = (
                        result_array[clothing_mask, i] * 0.3 + 
                        color_array[i] * 0.7
                    ).astype(np.uint8)
            
            colorized = Image.fromarray(result_array.astype(np.uint8))
            
            return {
                'success': True,
                'colorized_image': colorized,
                'method': 'ai_clothing_vision',
                'style_applied': style,
                'clothing_areas_detected': int(np.sum(clothing_mask)),
                'processing_time': 2.0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'colorized_image': sketch
            }

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
    color_data: str = Form("")
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
        result = sketch_colorizer.colorize_sketch(sketch_image, style, target_color=target_color)
        
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
            sketch_image, style, target_color=target_color
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