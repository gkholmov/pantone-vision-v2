#!/usr/bin/env python3
"""
Test script for the fixed texture application system
Tests the lace texture with a sample colorized image
"""

import os
import sys
from PIL import Image, ImageDraw
import numpy as np
from datetime import datetime

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from services.texture_application_service import TextureApplicationService

def create_sample_colorized_image(width=400, height=600):
    """
    Create a sample colorized garment sketch for testing
    """
    # Create a white background
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple dress silhouette in color
    # Dress body
    draw.rectangle([100, 150, 300, 450], fill='#FFB6C1', outline='#FF69B4', width=2)
    
    # Dress top/bodice
    draw.rectangle([120, 150, 280, 250], fill='#FFC0CB', outline='#FF69B4', width=2)
    
    # Sleeves
    draw.ellipse([50, 140, 130, 200], fill='#FFB6C1', outline='#FF69B4', width=2)
    draw.ellipse([270, 140, 350, 200], fill='#FFB6C1', outline='#FF69B4', width=2)
    
    # Skirt with some detail lines
    for y in range(260, 440, 20):
        draw.line([110, y, 290, y], fill='#FF69B4', width=1)
    
    return img

def test_texture_application():
    """
    Test the texture application with the provided lace image
    """
    print("🧪 TESTING TEXTURE APPLICATION FIX")
    print("=" * 50)
    
    # Initialize the service
    service = TextureApplicationService()
    
    # Create sample colorized image
    print("📷 Creating sample colorized garment...")
    colorized_image = create_sample_colorized_image()
    
    # Load the lace texture
    lace_texture_path = '/Users/germankholmov/Downloads/Telegram Desktop/photo_2025-09-06_13-06-25.jpg'
    
    if not os.path.exists(lace_texture_path):
        print(f"❌ Lace texture not found at: {lace_texture_path}")
        print("Please ensure the texture image is at the correct path")
        return False
    
    print(f"🧵 Loading lace texture from: {lace_texture_path}")
    try:
        lace_texture = Image.open(lace_texture_path)
        print(f"   • Texture size: {lace_texture.size}")
        print(f"   • Texture mode: {lace_texture.mode}")
    except Exception as e:
        print(f"❌ Failed to load texture: {e}")
        return False
    
    # Test the texture application
    print("\n🎨 APPLYING TEXTURE...")
    start_time = datetime.now()
    
    try:
        result = service.apply_custom_texture(
            colorized_image=colorized_image,
            texture_image=lace_texture,
            intensity=0.8
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if result['success']:
            print(f"✅ TEXTURE APPLICATION SUCCESSFUL!")
            print(f"   • Processing Time: {processing_time:.1f}ms")
            print(f"   • Texture Type: {result.get('texture_type', 'unknown')}")
            print(f"   • Intensity Applied: {result.get('intensity_applied', 'unknown')}")
            
            # Print pattern analysis if available
            if 'pattern_analysis' in result:
                analysis = result['pattern_analysis']
                print(f"   • Detected Pattern: {analysis.get('detected_type', 'unknown')}")
                print(f"   • Confidence: {analysis.get('confidence', 0):.2f}")
                
                features = analysis.get('features', {})
                if features:
                    print(f"   • Edge Density: {features.get('edge_density', 0):.3f}")
                    print(f"   • Mean Brightness: {features.get('mean_brightness', 0):.1f}")
                    print(f"   • Std Deviation: {features.get('std_deviation', 0):.1f}")
            
            # Print mask info if available
            if 'mask_info' in result:
                mask_info = result['mask_info']
                print(f"   • Mask Coverage: {mask_info.get('coverage_percentage', 0):.1f}%")
                print(f"   • Adaptive Threshold: {mask_info.get('adaptive_threshold', 'N/A')}")
            
            # Save the result
            output_path = f'/Users/germankholmov/Desktop/qwen/products/pantone-vision/pantone-vision-v2/test_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            result['textured_image'].save(output_path)
            print(f"   • Result saved to: {output_path}")
            
            return True
            
        else:
            print(f"❌ TEXTURE APPLICATION FAILED!")
            print(f"   • Error: {result.get('error', 'Unknown error')}")
            print(f"   • Processing Time: {processing_time:.1f}ms")
            return False
            
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        print(f"❌ TEXTURE APPLICATION CRASHED!")
        print(f"   • Exception: {str(e)}")
        print(f"   • Processing Time: {processing_time:.1f}ms")
        return False

def test_pattern_detection():
    """
    Test just the pattern detection on the lace texture
    """
    print("\n🔍 TESTING PATTERN DETECTION...")
    
    service = TextureApplicationService()
    lace_texture_path = '/Users/germankholmov/Downloads/Telegram Desktop/photo_2025-09-06_13-06-25.jpg'
    
    if not os.path.exists(lace_texture_path):
        print(f"❌ Texture not found")
        return False
    
    try:
        lace_texture = Image.open(lace_texture_path)
        analysis = service._detect_texture_pattern(lace_texture)
        
        print(f"✅ PATTERN DETECTION RESULTS:")
        print(f"   • Detected Type: {analysis.get('detected_type', 'unknown')}")
        print(f"   • Confidence: {analysis.get('confidence', 0):.3f}")
        
        features = analysis.get('features', {})
        for feature_name, feature_value in features.items():
            if isinstance(feature_value, float):
                print(f"   • {feature_name.title()}: {feature_value:.3f}")
            else:
                print(f"   • {feature_name.title()}: {feature_value}")
        
        return analysis.get('detected_type') == 'lace'
        
    except Exception as e:
        print(f"❌ Pattern detection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 STARTING TEXTURE SYSTEM TESTS")
    print("=" * 60)
    
    # Test 1: Pattern Detection
    pattern_test_passed = test_pattern_detection()
    
    # Test 2: Full Texture Application
    texture_test_passed = test_texture_application()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"   • Pattern Detection: {'✅ PASS' if pattern_test_passed else '❌ FAIL'}")
    print(f"   • Texture Application: {'✅ PASS' if texture_test_passed else '❌ FAIL'}")
    
    if pattern_test_passed and texture_test_passed:
        print("\n🎉 ALL TESTS PASSED - TEXTURE CORRUPTION FIXED!")
    else:
        print("\n⚠️  SOME TESTS FAILED - REVIEW NEEDED")
    
    print("=" * 60)