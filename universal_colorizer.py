#!/usr/bin/env python3
"""
UNIVERSAL FASHION SKETCH COLORIZER - ANY GARMENT TYPE
======================================================

HANDLES ALL GARMENT TYPES:
- Tops: shirts, blouses, corsets, jackets, coats
- Bottoms: pants, skirts, shorts
- Full body: dresses, jumpsuits, robes
- Accessories: bags, shoes, hats

CRITICAL SUCCESS FACTORS:
1. Works on model wearing ANY white garment with black lines
2. Distinguishes garment from skin/background
3. Handles various sketch styles and line weights
"""

import numpy as np
from typing import Tuple, Optional, List, Dict
from PIL import Image, ImageFilter
from scipy.ndimage import binary_erosion, binary_dilation, binary_closing, label

# Try to import cv2, but provide fallback if not available
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

def universal_garment_colorizer(sketch: Image.Image, target_color: str = None, 
                                white_threshold: int = 245, 
                                color_variance: int = 30, 
                                skin_protection: float = 0.3,
                                element_colors: Dict = None) -> Dict:
    """
    Universal colorizer that handles ANY garment type on a model
    Key insight: Focus on ENCLOSED WHITE REGIONS bounded by BLACK LINES
    
    Algorithm:
    1. Detect black lines (garment boundaries)
    2. Find enclosed white regions
    3. Filter out skin/background
    4. Apply gray to valid garment regions only
    """
    
    TARGET_GRAY = (168, 168, 168)  # Default gray target
    
    try:
        # Parse target color
        if target_color:
            try:
                # Handle hex format
                if target_color.startswith('#'):
                    hex_color = target_color.lstrip('#')
                    TARGET_GRAY = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    print(f"✅ Using hex color: {target_color} -> RGB{TARGET_GRAY}")
                # Handle RGB format  
                elif 'rgb' in target_color.lower() or '(' in target_color:
                    import re
                    numbers = re.findall(r'\d+', target_color)
                    if len(numbers) >= 3:
                        TARGET_GRAY = (int(numbers[0]), int(numbers[1]), int(numbers[2]))
                        print(f"✅ Using RGB color: {target_color} -> RGB{TARGET_GRAY}")
                else:
                    print(f"⚠️ Using default gray for color: {target_color}")
            except Exception as e:
                print(f"⚠️ Color parsing failed: {e}, using default gray")
        
        # Convert to numpy array for processing
        img = np.array(sketch)
        result = img.copy()
        h, w = img.shape[:2]
        
        print(f"🔍 UNIVERSAL GARMENT DETECTION: Processing {w}x{h} image")
        
        # Step 1: Detect black lines (garment boundaries)
        if len(img.shape) == 3:
            # Convert to grayscale using PIL
            gray_img = Image.fromarray(img).convert('L')
            gray = np.array(gray_img)
        else:
            gray = img.copy()
        
        # Detect black lines with simple threshold
        lines = (gray < 100).astype(np.uint8) * 255
        
        # Dilate lines to ensure closure using scipy
        lines_dilated = binary_dilation(lines > 0, structure=np.ones((3, 3)), iterations=1).astype(np.uint8) * 255
        
        print(f"   📏 Black line detection: {np.sum(lines > 0)} pixels")
        
        # Step 2: Find white regions (potential garment areas)
        if len(img.shape) == 3:
            # Multi-channel image
            b, g, r = img[:,:,0], img[:,:,1], img[:,:,2]
            
            # True white detection: high values + low variance between channels
            # Use configurable parameters
            white_variance = color_variance
            
            white_mask = np.logical_and.reduce([
                r > white_threshold,
                g > white_threshold, 
                b > white_threshold,
                np.abs(r.astype(int) - g.astype(int)) < white_variance,
                np.abs(g.astype(int) - b.astype(int)) < white_variance,
                np.abs(r.astype(int) - b.astype(int)) < white_variance
            ])
        else:
            # Grayscale image
            white_mask = gray > white_threshold
            
        white_areas = (white_mask * 255).astype(np.uint8)
        print(f"   ⚪ White area detection: {np.sum(white_areas > 0)} pixels")
        
        # Step 3: Remove line areas from white regions (find enclosed areas)
        if OPENCV_AVAILABLE:
            white_no_lines = cv2.bitwise_and(white_areas, cv2.bitwise_not(lines_dilated))
            # Step 4: Find connected components (individual garment regions)
            num_labels, labels = cv2.connectedComponents(white_no_lines)
        else:
            # Fallback without OpenCV
            white_no_lines = np.logical_and(white_areas > 0, lines_dilated == 0).astype(np.uint8) * 255
            # Use scipy for connected components
            labels, num_labels = label(white_no_lines > 0)
            num_labels += 1  # scipy starts from 0, cv2 starts from 1
        
        # Step 5: Filter regions by size and exclude edge-touching regions
        garment_mask = np.zeros_like(gray)
        min_area = 500  # Minimum region size
        
        for label_id in range(1, num_labels):
            region = (labels == label_id).astype(np.uint8) * 255
            
            if OPENCV_AVAILABLE:
                area = cv2.countNonZero(region)
            else:
                area = np.sum(region > 0)
            
            if area > min_area:
                # Check if region touches image border (likely background)
                border_mask = np.zeros_like(region)
                border_mask[0, :] = 1  # Top edge
                border_mask[-1, :] = 1  # Bottom edge  
                border_mask[:, 0] = 1  # Left edge
                border_mask[:, -1] = 1  # Right edge
                
                # Only keep regions that don't touch borders (enclosed garments)
                if OPENCV_AVAILABLE:
                    if cv2.countNonZero(cv2.bitwise_and(region, border_mask)) == 0:
                        garment_mask = cv2.bitwise_or(garment_mask, region)
                        print(f"   ✅ Kept enclosed region: {area} pixels")
                    else:
                        print(f"   ❌ Excluded border-touching region: {area} pixels")
                else:
                    # Fallback without OpenCV
                    if np.sum(np.logical_and(region > 0, border_mask > 0)) == 0:
                        garment_mask = np.logical_or(garment_mask > 0, region > 0).astype(np.uint8) * 255
                        print(f"   ✅ Kept enclosed region: {area} pixels")
                    else:
                        print(f"   ❌ Excluded border-touching region: {area} pixels")
        
        # Step 6: Additional skin/background filtering using HSV
        if len(img.shape) == 3:
            if OPENCV_AVAILABLE:
                hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
                
                # Exclude skin-colored regions
                skin_lower = np.array([0, 20, 70])
                skin_upper = np.array([20, 255, 255])
                skin_mask = cv2.inRange(hsv, skin_lower, skin_upper)
                
                # Dilate skin mask for safety margin based on protection level
                kernel_size = max(3, int(5 * skin_protection))
                iterations = max(1, int(2 * skin_protection))
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
                skin_mask = cv2.dilate(skin_mask, kernel, iterations=iterations)
                
                # Remove skin areas from garment mask
                garment_mask = cv2.bitwise_and(garment_mask, cv2.bitwise_not(skin_mask))
                print(f"   🚫 Skin exclusion applied")
            else:
                # Fallback skin detection using RGB
                # Convert RGB to approximate HSV using PIL
                pil_img = Image.fromarray(img)
                hsv_pil = pil_img.convert('HSV')
                hsv = np.array(hsv_pil)
                
                # Exclude skin-colored regions
                skin_mask = np.logical_and.reduce([
                    hsv[:,:,0] >= 0,    # Hue range for skin
                    hsv[:,:,0] <= 20,
                    hsv[:,:,1] >= 20,   # Saturation
                    hsv[:,:,2] >= 70    # Value
                ]).astype(np.uint8) * 255
                
                # Dilate skin mask using scipy based on protection level
                kernel_size = max(3, int(5 * skin_protection))
                iterations = max(1, int(2 * skin_protection))
                skin_mask_dilated = binary_dilation(skin_mask > 0, structure=np.ones((kernel_size, kernel_size)), iterations=iterations).astype(np.uint8) * 255
                
                # Remove skin areas from garment mask
                garment_mask = np.logical_and(garment_mask > 0, skin_mask_dilated == 0).astype(np.uint8) * 255
                print(f"   🚫 Skin exclusion applied (fallback)")
        
        # Step 7: Final morphological cleanup
        if OPENCV_AVAILABLE:
            kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            garment_mask = cv2.morphologyEx(garment_mask, cv2.MORPH_CLOSE, kernel_close)
            
            # Remove very small regions
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(garment_mask)
            for i in range(1, num_labels):
                if stats[i, cv2.CC_STAT_AREA] < min_area:
                    garment_mask[labels == i] = 0
        else:
            # Fallback morphological closing using scipy
            garment_mask_bool = garment_mask > 0
            closed = binary_closing(garment_mask_bool, structure=np.ones((5, 5)), iterations=1)
            garment_mask = closed.astype(np.uint8) * 255
            
            # Remove very small regions using scipy
            labels_final, num_labels_final = label(garment_mask > 0)
            for i in range(1, num_labels_final + 1):
                region_area = np.sum(labels_final == i)
                if region_area < min_area:
                    garment_mask[labels_final == i] = 0
        
        # Step 8: Prepare element-specific colorization
        element_regions = {}
        if element_colors and any(element_colors.values()):
            print(f"🎨 ELEMENT-SPECIFIC COLORIZATION: {element_colors}")
            # Analyze garment regions for element-specific coloring
            element_regions = _detect_garment_elements(garment_mask, img.shape)
            print(f"   📍 Detected regions: {list(element_regions.keys())}")
        
        # Step 9: Apply color while preserving brightness/shading
        garment_bool = garment_mask > 0
        total_garment_pixels = int(np.sum(garment_bool))  # Convert numpy.int64 to native Python int
        
        print(f"🎨 Final garment mask: {total_garment_pixels} pixels ({100*total_garment_pixels/(h*w):.1f}% coverage)")
        
        if total_garment_pixels > 0:
            # Apply color while preserving original brightness for shading
            for y in range(h):
                for x in range(w):
                    if garment_bool[y, x]:
                        # Determine which color to use for this pixel
                        target_color_rgb = TARGET_GRAY  # Default color
                        
                        if element_colors and element_regions:
                            # Check if pixel belongs to specific element region
                            target_color_rgb = _get_pixel_color(x, y, element_regions, element_colors, TARGET_GRAY)
                        
                        if len(img.shape) == 3:
                            # Get original brightness
                            brightness = gray[y, x] / 255.0
                            # Adjust target color based on original brightness
                            # Darker areas stay darker, lighter areas stay lighter  
                            factor = 0.6 + (brightness * 0.4)
                            
                            result[y, x] = [
                                int(target_color_rgb[0] * factor),  # R
                                int(target_color_rgb[1] * factor),  # G  
                                int(target_color_rgb[2] * factor)   # B
                            ]
                        else:
                            # Grayscale image
                            brightness = gray[y, x] / 255.0
                            factor = 0.6 + (brightness * 0.4)
                            gray_value = int(sum(target_color_rgb) / 3 * factor)
                            result[y, x] = gray_value
            
            print(f"✅ Color application complete (element-aware)" if element_colors else "✅ Color application complete")
        else:
            print(f"⚠️ No garment regions detected - returning original")
        
        colorized = Image.fromarray(result.astype(np.uint8))
        
        return {
            'success': True,
            'colorized_image': colorized,
            'method': 'universal_line_enclosed',
            'clothing_areas_detected': total_garment_pixels,  # Already converted to int above
            'processing_time': 1.0,
            'coverage_percent': float(round(100*total_garment_pixels/(h*w), 1))  # Ensure native float
        }
        
    except Exception as e:
        print(f"🚨 Universal colorization failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'colorized_image': sketch
        }

def _detect_garment_elements(garment_mask: np.ndarray, img_shape: Tuple) -> Dict:
    """
    Detect different garment elements based on position and geometry.
    For Chinese dress/qipao: collar (top), straps/toggles (top-sides), main body (center), trim (edges)
    """
    h, w = img_shape[:2]
    regions = {}
    
    try:
        # Define region zones based on image geometry
        top_zone = slice(0, h//4)  # Top 25% for collar
        top_side_zones = (slice(0, h//3), [slice(0, w//4), slice(3*w//4, w)])  # Top-left and top-right for straps
        edge_zone_width = max(5, min(w, h) // 20)  # Edge width for trim
        
        # Create masks for different regions
        garment_pixels = garment_mask > 0
        
        # Collar region (top center)
        collar_mask = np.zeros_like(garment_mask)
        collar_mask[top_zone, w//4:3*w//4] = garment_pixels[top_zone, w//4:3*w//4]
        if np.sum(collar_mask) > 0:
            regions['collar'] = collar_mask > 0
            
        # Straps/toggles regions (top sides)
        straps_mask = np.zeros_like(garment_mask) 
        # Left strap
        straps_mask[top_side_zones[0], top_side_zones[1][0]] = garment_pixels[top_side_zones[0], top_side_zones[1][0]]
        # Right strap  
        straps_mask[top_side_zones[0], top_side_zones[1][1]] = garment_pixels[top_side_zones[0], top_side_zones[1][1]]
        if np.sum(straps_mask) > 0:
            regions['straps'] = straps_mask > 0
            
        # Trim regions (edges of garment)
        if OPENCV_AVAILABLE:
            import cv2
            # Use morphological operations to find garment edges
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (edge_zone_width, edge_zone_width))
            garment_eroded = cv2.erode(garment_mask, kernel, iterations=1)
            trim_mask = cv2.subtract(garment_mask, garment_eroded)
            if np.sum(trim_mask) > 0:
                regions['trim'] = trim_mask > 0
        else:
            # Fallback edge detection using scipy
            from scipy.ndimage import binary_erosion
            garment_eroded = binary_erosion(garment_mask > 0, structure=np.ones((edge_zone_width, edge_zone_width)))
            trim_mask = np.logical_and(garment_mask > 0, ~garment_eroded)
            if np.sum(trim_mask) > 0:
                regions['trim'] = trim_mask
                
        # Main garment (everything else)
        main_mask = garment_pixels.copy()
        for region_name, region_mask in regions.items():
            if region_name != 'main':
                main_mask = np.logical_and(main_mask, ~region_mask)
        if np.sum(main_mask) > 0:
            regions['main'] = main_mask
            
        print(f"   🎨 Detected element regions: {[(name, np.sum(mask)) for name, mask in regions.items()]}")
        
    except Exception as e:
        print(f"   ⚠️ Element detection failed: {e}")
        regions = {'main': garment_mask > 0}  # Fallback to single region
    
    return regions

def _get_pixel_color(x: int, y: int, element_regions: Dict, element_colors: Dict, default_color: Tuple) -> Tuple:
    """
    Determine which color to use for a pixel based on element regions.
    Priority: straps > collar > trim > main > default
    """
    # Parse color strings to RGB tuples
    def parse_color(color_str: str) -> Tuple:
        if not color_str or color_str == '#000000':
            return None
        try:
            if color_str.startswith('#'):
                hex_color = color_str.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except:
            pass
        return None
    
    # Check regions in priority order
    priority_order = ['straps', 'collar', 'trim', 'main']
    
    for region_name in priority_order:
        if (region_name in element_regions and 
            region_name in element_colors and 
            element_regions[region_name][y, x]):  # y, x for numpy array indexing
            
            color_rgb = parse_color(element_colors[region_name])
            if color_rgb:
                return color_rgb
    
    return default_color