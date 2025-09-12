/**
 * Improved mask generator that properly excludes skin and handles orientation
 */
class ImprovedMaskGenerator {
    constructor() {
        // Improved skin tone detection ranges (HSV)
        this.skinTones = [
            { hMin: 0, hMax: 50, sMin: 0.15, sMax: 0.8, vMin: 0.2, vMax: 0.95 },   // Pink to orange skin tones
            { hMin: 15, hMax: 35, sMin: 0.25, sMax: 0.7, vMin: 0.3, vMax: 0.85 },  // Typical skin range
        ];
        
        console.log('✅ ImprovedMaskGenerator initialized with better skin detection');
    }
    
    /**
     * Generate mask with proper skin exclusion and white fabric detection
     */
    generateMask(garmentImage, options = {}) {
        const {
            excludeSkin = true,
            excludeBackground = true,
            whiteThreshold = 230,
            debug = false
        } = options;
        
        // Create canvas for processing
        const canvas = document.createElement('canvas');
        canvas.width = garmentImage.width;
        canvas.height = garmentImage.height;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(garmentImage, 0, 0);
        
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const { data, width, height } = imageData;
        
        // Create mask data
        const maskData = new Uint8ClampedArray(data.length);
        
        let includedPixels = 0;
        let totalPixels = 0;
        let skinPixels = 0;
        let whitePixels = 0;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            const a = data[i + 3];
            
            totalPixels++;
            let includePixel = true;
            let exclusionReason = '';
            
            // Skip transparent pixels
            if (a < 200) {
                includePixel = false;
                exclusionReason = 'transparent';
            }
            
            // Exclude skin tones
            if (includePixel && excludeSkin && this.isSkinTone(r, g, b)) {
                includePixel = false;
                exclusionReason = 'skin';
                skinPixels++;
            }
            
            // Exclude very white background (but be more selective)
            if (includePixel && excludeBackground) {
                const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
                if (r > whiteThreshold && g > whiteThreshold && b > whiteThreshold && 
                    Math.abs(r - g) < 10 && Math.abs(g - b) < 10 && Math.abs(r - b) < 10) {
                    // This is pure white/gray background
                    includePixel = false;
                    exclusionReason = 'white_background';
                    whitePixels++;
                }
            }
            
            // Look for white fabric (different from background)
            if (includePixel && r > 200 && g > 200 && b > 200) {
                // Check if this white pixel has texture/detail around it
                const hasDetail = this.hasLocalDetail(data, i, width, height);
                if (!hasDetail) {
                    includePixel = false;
                    exclusionReason = 'plain_white';
                }
            }
            
            if (includePixel) {
                // White mask = include this pixel for texture
                maskData[i] = 255;
                maskData[i + 1] = 255;
                maskData[i + 2] = 255;
                maskData[i + 3] = 255;
                includedPixels++;
            } else {
                // Black mask = exclude this pixel
                maskData[i] = 0;
                maskData[i + 1] = 0;
                maskData[i + 2] = 0;
                maskData[i + 3] = 255;
            }
        }
        
        // Create mask canvas
        const maskCanvas = document.createElement('canvas');
        maskCanvas.width = width;
        maskCanvas.height = height;
        const maskCtx = maskCanvas.getContext('2d');
        
        const finalMaskData = new ImageData(maskData, width, height);
        maskCtx.putImageData(finalMaskData, 0, 0);
        
        const coverage = includedPixels / totalPixels;
        
        if (debug) {
            console.log('🔍 Improved mask generation:', {
                totalPixels,
                includedPixels, 
                skinPixels,
                whitePixels,
                coverage: `${(coverage * 100).toFixed(1)}%`,
                skinExclusion: `${(skinPixels / totalPixels * 100).toFixed(1)}%`,
                whiteExclusion: `${(whitePixels / totalPixels * 100).toFixed(1)}%`
            });
        }
        
        return {
            canvas: maskCanvas,
            imageData: finalMaskData,
            stats: {
                totalPixels,
                whitePixels: includedPixels,
                blackPixels: totalPixels - includedPixels,
                skinPixels,
                coverage,
                exclusion: 1 - coverage
            }
        };
    }
    
    /**
     * Check if RGB color is a skin tone using improved detection
     */
    isSkinTone(r, g, b) {
        const hsv = this.rgbToHsv(r, g, b);
        
        // Additional RGB-based skin detection
        const rgbSkinCheck = this.isRGBSkinTone(r, g, b);
        if (rgbSkinCheck) return true;
        
        // HSV-based detection
        for (const skinRange of this.skinTones) {
            if (hsv.h >= skinRange.hMin && hsv.h <= skinRange.hMax &&
                hsv.s >= skinRange.sMin && hsv.s <= skinRange.sMax &&
                hsv.v >= skinRange.vMin && hsv.v <= skinRange.vMax) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * RGB-based skin tone detection (more accurate for some skin tones)
     */
    isRGBSkinTone(r, g, b) {
        // Typical skin tone characteristics in RGB
        if (r > g && g > b) {
            // Red dominance is common in skin tones
            const rg_ratio = r / Math.max(g, 1);
            const gb_ratio = g / Math.max(b, 1);
            
            if (rg_ratio > 1.1 && rg_ratio < 2.5 && gb_ratio > 1.2 && gb_ratio < 2.8) {
                // Check if it's in typical skin luminance range
                const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
                if (luminance > 80 && luminance < 220) {
                    return true;
                }
            }
        }
        
        return false;
    }
    
    /**
     * Check if a pixel has textural detail around it (indicates fabric vs plain background)
     */
    hasLocalDetail(data, pixelIndex, width, height) {
        const pixelPos = pixelIndex / 4;
        const x = pixelPos % width;
        const y = Math.floor(pixelPos / width);
        
        const radius = 3;
        const centerR = data[pixelIndex];
        const centerG = data[pixelIndex + 1];
        const centerB = data[pixelIndex + 2];
        
        let variations = 0;
        let samples = 0;
        
        for (let dy = -radius; dy <= radius; dy++) {
            for (let dx = -radius; dx <= radius; dx++) {
                const nx = x + dx;
                const ny = y + dy;
                
                if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                    const neighborIndex = (ny * width + nx) * 4;
                    const nr = data[neighborIndex];
                    const ng = data[neighborIndex + 1];
                    const nb = data[neighborIndex + 2];
                    
                    const colorDiff = Math.abs(centerR - nr) + Math.abs(centerG - ng) + Math.abs(centerB - nb);
                    if (colorDiff > 15) {
                        variations++;
                    }
                    samples++;
                }
            }
        }
        
        return samples > 0 && (variations / samples) > 0.3;
    }
    
    /**
     * Convert RGB to HSV
     */
    rgbToHsv(r, g, b) {
        r /= 255;
        g /= 255;
        b /= 255;
        
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const diff = max - min;
        
        let h = 0;
        const s = max === 0 ? 0 : diff / max;
        const v = max;
        
        if (diff !== 0) {
            switch (max) {
                case r: h = (g - b) / diff + (g < b ? 6 : 0); break;
                case g: h = (b - r) / diff + 2; break;
                case b: h = (r - g) / diff + 4; break;
            }
            h /= 6;
        }
        
        return { 
            h: h * 360, // Convert to degrees
            s, 
            v 
        };
    }
    
    /**
     * Auto-detect image orientation and suggest correction
     */
    detectOrientation(imageCanvas) {
        const ctx = imageCanvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, imageCanvas.width, imageCanvas.height);
        const { data, width, height } = imageData;
        
        // Look for body/head position indicators
        let topHalfSkinPixels = 0;
        let bottomHalfSkinPixels = 0;
        const midHeight = height / 2;
        
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const idx = (y * width + x) * 4;
                const r = data[idx];
                const g = data[idx + 1];
                const b = data[idx + 2];
                
                if (this.isSkinTone(r, g, b)) {
                    if (y < midHeight) {
                        topHalfSkinPixels++;
                    } else {
                        bottomHalfSkinPixels++;
                    }
                }
            }
        }
        
        // If more skin in bottom half, image might be upside down
        const needsRotation = bottomHalfSkinPixels > topHalfSkinPixels * 1.5;
        
        return {
            needsRotation,
            topSkinPixels: topHalfSkinPixels,
            bottomSkinPixels: bottomHalfSkinPixels,
            confidence: Math.abs(topHalfSkinPixels - bottomHalfSkinPixels) / Math.max(topHalfSkinPixels, bottomHalfSkinPixels, 1)
        };
    }
    
    /**
     * Correct image orientation
     */
    correctOrientation(imageCanvas) {
        const orientation = this.detectOrientation(imageCanvas);
        
        if (orientation.needsRotation && orientation.confidence > 0.3) {
            const correctedCanvas = document.createElement('canvas');
            correctedCanvas.width = imageCanvas.width;
            correctedCanvas.height = imageCanvas.height;
            
            const ctx = correctedCanvas.getContext('2d');
            
            // Rotate 180 degrees
            ctx.translate(correctedCanvas.width, correctedCanvas.height);
            ctx.rotate(Math.PI);
            ctx.drawImage(imageCanvas, 0, 0);
            
            console.log('🔄 Image rotated 180° due to orientation detection');
            return {
                canvas: correctedCanvas,
                rotated: true,
                confidence: orientation.confidence
            };
        }
        
        return {
            canvas: imageCanvas,
            rotated: false,
            confidence: orientation.confidence
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImprovedMaskGenerator;
}