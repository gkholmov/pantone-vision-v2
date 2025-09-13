#!/usr/bin/env python3
"""
Universal Pantone Color Identification System
Can identify ANY color using AI and comprehensive color science
"""

import os
import json
import math
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

class UniversalColorMatcher:
    """
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
                model="claude-sonnet-4-20250514",
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
    
    def identify_colors_from_image(self, image):
        """
        Main entry point for Pantone color identification from PIL Image
        Returns multiple detected colors with their Pantone matches
        """
        try:
            # Convert PIL Image to numpy array
            if hasattr(image, 'convert'):
                image = image.convert('RGB')
                image_array = np.array(image)
            else:
                image_array = image
            
            # Extract multiple colors using different methods
            colors_to_analyze = []
            
            # 1. Dominant color
            dominant_rgb = self.analyze_image_color(image_array, method="dominant")
            colors_to_analyze.append(('dominant', dominant_rgb))
            
            # 2. Center color
            center_rgb = self.analyze_image_color(image_array, method="center")
            if center_rgb != dominant_rgb:
                colors_to_analyze.append(('center', center_rgb))
            
            # 3. Sample grid colors (3x3 grid)
            h, w = image_array.shape[:2]
            grid_colors = []
            for i in range(3):
                for j in range(3):
                    y_start = i * h // 3
                    y_end = (i + 1) * h // 3
                    x_start = j * w // 3
                    x_end = (j + 1) * w // 3
                    region = image_array[y_start:y_end, x_start:x_end]
                    region_color = tuple(int(x) for x in np.mean(region.reshape(-1, 3), axis=0))
                    if region_color not in [dominant_rgb, center_rgb] and region_color not in grid_colors:
                        grid_colors.append(region_color)
            
            # Add up to 3 unique grid colors
            for idx, color in enumerate(grid_colors[:3]):
                colors_to_analyze.append((f'region_{idx+1}', color))
            
            # Analyze each color with AI
            results = []
            for method_name, rgb in colors_to_analyze[:5]:  # Limit to 5 colors
                color_result = self.identify_color_with_ai(rgb, f"Extracted using {method_name} method")
                
                if 'primary_match' in color_result:
                    match = color_result['primary_match']
                    results.append({
                        'pantone_code': match.get('pantone_code', 'Unknown'),
                        'pantone_name': match.get('name', 'Unknown Color'),
                        'rgb': list(rgb),
                        'hex': f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}",
                        'confidence': match.get('confidence', 0.5),
                        'category': match.get('category', 'Unknown'),
                        'extraction_method': method_name,
                        'delta_e': match.get('delta_e_estimated', 0),
                        'collection': match.get('collection', 'N/A'),
                        'alternatives': color_result.get('alternative_matches', []),
                        'color_analysis': color_result.get('color_analysis', {}),
                        'preview_css': f"background: linear-gradient(135deg, rgb{rgb}, rgb({max(0,rgb[0]-20)},{max(0,rgb[1]-20)},{max(0,rgb[2]-20)}))"
                    })
            
            return {
                'success': True,
                'colors': results,
                'image_info': {
                    'size': image.size if hasattr(image, 'size') else image_array.shape[:2],
                    'mode': image.mode if hasattr(image, 'mode') else 'RGB',
                    'colors_detected': len(results)
                },
                'confidence': np.mean([c['confidence'] for c in results]) if results else 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'colors': []
            }
    
    def analyze_image_color(self, image_array: np.ndarray, method: str = "dominant") -> Tuple[int, int, int]:
        """
        Extract representative color from image
        Supports multiple extraction methods
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

# Example usage and testing
if __name__ == "__main__":
    matcher = UniversalColorMatcher()
    
    # Test with various colors
    test_colors = [
        (255, 0, 0),      # Pure red
        (0, 255, 0),      # Pure green  
        (0, 0, 255),      # Pure blue
        (184, 58, 75),    # Tango red
        (123, 67, 200),   # Purple
        (200, 180, 140),  # Beige
        (50, 50, 50),     # Dark gray
    ]
    
    print("🎨 UNIVERSAL COLOR IDENTIFICATION SYSTEM")
    print("=" * 60)
    
    for rgb in test_colors:
        print(f"\nTesting RGB{rgb}:")
        result = matcher.identify_color_with_ai(rgb)
        
        if 'primary_match' in result:
            match = result['primary_match']
            print(f"  ✅ {match['pantone_code']} - {match['name']}")
            print(f"  🎯 Confidence: {match.get('confidence', 0):.0%}")
            print(f"  📁 Category: {match.get('category', 'N/A')}")
        
        print(f"  🔧 Technical: {result.get('technical_data', {})}")