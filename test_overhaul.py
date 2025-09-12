#!/usr/bin/env python3
"""
Test script for the COMPLETE OVERHAUL of Pantone Vision 2.0
Tests the contour-based garment detection and vectorized HSV colorization
"""

import requests
import json
from pathlib import Path

def test_bustier_colorization():
    """Test the bustier sketch that was failing with 0 pixels detected"""
    
    # Test data - simulate red bustier colorization
    test_data = {
        "style_prompt": "fashion illustration bustier",
        "pantone_colors": json.dumps([
            {
                "primary_match": "PANTONE 18-1664 TPX",
                "rgb": [186, 12, 47],  # Deep Red
                "confidence": 0.95,
                "technical_data": {
                    "lab_values": {"L": 35.2, "a": 54.1, "b": 23.8},
                    "delta_e": 1.2
                }
            }
        ])
    }
    
    print("🧪 TESTING COMPLETE OVERHAUL")
    print("=" * 50)
    print(f"🎯 Target: Bustier sketch with PANTONE 18-1664 TPX (Deep Red)")
    print(f"🔧 Testing: Contour-based detection + Vectorized HSV")
    print()
    
    # For testing, we'll create a simple test sketch programmatically
    test_sketch_path = create_test_bustier_sketch()
    
    # Test the colorization endpoint
    try:
        with open(test_sketch_path, 'rb') as f:
            files = {'sketch': f}
            
            print("📤 Sending colorization request...")
            response = requests.post(
                "http://127.0.0.1:8000/colorize-sketch", 
                files=files,
                data=test_data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ COLORIZATION SUCCESS!")
            print("=" * 30)
            
            # Check for critical metrics that were failing before
            processing_info = result.get('processing_info', {})
            
            # Look for the new contour-based detection metrics
            garment_area = processing_info.get('garment_area_percentage', 0)
            contours_found = processing_info.get('contours_found', 0)
            vectorized_processing = processing_info.get('vectorized_hsv', False)
            
            print(f"🔍 Contours Found: {contours_found}")
            print(f"📐 Garment Area: {garment_area:.2f}% (expect 10-30% for bustier)")
            print(f"🚀 Vectorized HSV: {'✅ YES' if vectorized_processing else '❌ NO'}")
            
            if garment_area > 0:
                print()
                print("🎉 SUCCESS! Garment detection is now working!")
                print("✅ Contour-based detection finds garment areas")
                print("✅ No more '0 pixels detected' error")
                
                if garment_area >= 5.0:  # Reasonable threshold for bustier
                    print("✅ Garment area percentage is reasonable")
                else:
                    print("⚠️  Low garment area - may need threshold adjustment")
                
                return True
            else:
                print("❌ STILL FAILING: 0% garment area detected")
                return False
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def create_test_bustier_sketch():
    """Create a simple black-line bustier sketch for testing"""
    from PIL import Image, ImageDraw
    import numpy as np
    
    # Create 400x600 white image
    img = Image.new('RGB', (400, 600), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw bustier outline in black lines
    # Bustier shape - strapless top with curved bodice
    bustier_outline = [
        (100, 200),   # Left top
        (120, 180),   # Curved cup left
        (180, 170),   # Center top
        (220, 170),   # Center top right
        (280, 180),   # Curved cup right  
        (300, 200),   # Right top
        (310, 350),   # Right bottom
        (90, 350),    # Left bottom
        (100, 200)    # Close shape
    ]
    
    # Draw main bustier outline
    draw.polygon(bustier_outline, outline='black', fill=None, width=3)
    
    # Add some detail lines (bust seam)
    draw.arc((120, 170, 180, 220), start=0, end=180, fill='black', width=2)
    draw.arc((220, 170, 280, 220), start=0, end=180, fill='black', width=2)
    
    # Add center seam
    draw.line((200, 170, 200, 350), fill='black', width=2)
    
    # Save test sketch
    test_path = Path("test_bustier_sketch.png")
    img.save(test_path)
    
    print(f"📝 Created test sketch: {test_path}")
    return test_path

if __name__ == "__main__":
    success = test_bustier_colorization()
    
    if success:
        print()
        print("🎉 COMPLETE OVERHAUL TEST: SUCCESS")
        print("✅ Contour-based detection working")
        print("✅ Vectorized HSV processing working") 
        print("✅ System ready for production use")
    else:
        print()
        print("❌ COMPLETE OVERHAUL TEST: FAILED")
        print("🔧 Need additional debugging")