/**
 * Simple and effective mask generator
 * Focuses on basic color thresholding rather than complex analysis
 */
class SimpleMaskGenerator {
    constructor() {
        console.log('✅ SimpleMaskGenerator initialized');
    }
    
    /**
     * Generate mask using simple color-based thresholding
     */
    generateMask(garmentImage, options = {}) {
        const {
            excludeWhite = true,
            excludeVeryLight = true,
            whiteThreshold = 240,
            lightThreshold = 200,
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
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            const a = data[i + 3];
            
            totalPixels++;
            
            // Calculate luminance
            const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
            
            let includePixel = true;
            
            // Exclude very white pixels (likely background)
            if (excludeWhite && r > whiteThreshold && g > whiteThreshold && b > whiteThreshold) {
                includePixel = false;
            }
            
            // Exclude very light pixels
            if (excludeVeryLight && luminance > lightThreshold) {
                includePixel = false;
            }
            
            // Exclude transparent pixels
            if (a < 200) {
                includePixel = false;
            }
            
            if (includePixel) {
                // White mask = include this pixel
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
            console.log('🔍 Simple mask generation:', {
                totalPixels,
                includedPixels, 
                coverage: `${(coverage * 100).toFixed(1)}%`,
                excludeWhite,
                whiteThreshold,
                lightThreshold
            });
        }
        
        return {
            canvas: maskCanvas,
            imageData: finalMaskData,
            stats: {
                totalPixels,
                whitePixels: includedPixels,
                blackPixels: totalPixels - includedPixels,
                coverage,
                exclusion: 1 - coverage
            }
        };
    }
    
    /**
     * Generate mask that includes everything (for testing)
     */
    generateFullMask(garmentImage) {
        const canvas = document.createElement('canvas');
        canvas.width = garmentImage.width;
        canvas.height = garmentImage.height;
        
        const ctx = canvas.getContext('2d');
        
        // Fill entire canvas with white (include everything)
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        return {
            canvas,
            imageData,
            stats: {
                totalPixels: canvas.width * canvas.height,
                whitePixels: canvas.width * canvas.height,
                blackPixels: 0,
                coverage: 1.0,
                exclusion: 0.0
            }
        };
    }
    
    /**
     * Auto-adjust thresholds based on image characteristics
     */
    autoAdjustThresholds(garmentImage) {
        const canvas = document.createElement('canvas');
        canvas.width = garmentImage.width;
        canvas.height = garmentImage.height;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(garmentImage, 0, 0);
        
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const { data } = imageData;
        
        let totalBrightness = 0;
        let pixelCount = 0;
        let brightPixels = 0;
        
        for (let i = 0; i < data.length; i += 4) {
            const luminance = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
            totalBrightness += luminance;
            pixelCount++;
            
            if (luminance > 200) {
                brightPixels++;
            }
        }
        
        const avgBrightness = totalBrightness / pixelCount;
        const brightRatio = brightPixels / pixelCount;
        
        // Adjust thresholds based on image characteristics
        let whiteThreshold = 240;
        let lightThreshold = 200;
        
        if (avgBrightness > 180) {
            // Very bright image, be more lenient
            whiteThreshold = 250;
            lightThreshold = 220;
        } else if (avgBrightness < 100) {
            // Dark image, be more aggressive
            whiteThreshold = 200;
            lightThreshold = 150;
        }
        
        if (brightRatio > 0.7) {
            // Mostly bright image, probably needs more exclusion
            whiteThreshold = 230;
            lightThreshold = 180;
        }
        
        console.log('🎯 Auto-adjusted thresholds:', {
            avgBrightness: avgBrightness.toFixed(1),
            brightRatio: `${(brightRatio * 100).toFixed(1)}%`,
            whiteThreshold,
            lightThreshold
        });
        
        return {
            whiteThreshold,
            lightThreshold,
            excludeWhite: brightRatio > 0.3,
            excludeVeryLight: avgBrightness > 150
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SimpleMaskGenerator;
}