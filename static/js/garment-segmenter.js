/**
 * Intelligent garment segmentation for mask generation
 * Excludes background and skin tones while preserving fabric areas
 */
class GarmentSegmenter {
    constructor() {
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Skin tone detection ranges (HSV)
        this.skinTones = [
            { hMin: 0, hMax: 25, sMin: 0.23, sMax: 0.68, vMin: 0.35, vMax: 0.95 },   // Pink/Red tones
            { hMin: 25, hMax: 50, sMin: 0.15, sMax: 0.68, vMin: 0.20, vMax: 0.95 },  // Orange/Yellow tones
        ];
        
        // Background detection thresholds
        this.backgroundThresholds = {
            uniformityThreshold: 15,  // Color uniformity in background
            edgeThreshold: 5,         // Low edge density for background
            brightnessVariance: 20    // Low brightness variance for background
        };
        
        console.log('✅ GarmentSegmenter initialized');
    }
    
    /**
     * Generate garment mask from input image
     */
    async generateMask(garmentImage, options = {}) {
        const {
            excludeSkin = true,
            excludeBackground = true,
            morphologyIterations = 2,
            minRegionSize = 100,
            debug = false
        } = options;
        
        // Set up canvas with garment image
        this.canvas.width = garmentImage.width;
        this.canvas.height = garmentImage.height;
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(garmentImage, 0, 0);
        
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        const maskData = new Uint8ClampedArray(imageData.data.length);
        
        // Initialize mask as white (all areas included)
        for (let i = 0; i < maskData.length; i += 4) {
            maskData[i] = 255;     // R
            maskData[i + 1] = 255; // G  
            maskData[i + 2] = 255; // B
            maskData[i + 3] = 255; // A
        }
        
        // Apply segmentation filters
        if (excludeBackground) {
            this.excludeBackground(imageData, maskData);
        }
        
        if (excludeSkin) {
            this.excludeSkinTones(imageData, maskData);
        }
        
        // Post-processing
        this.applyMorphologyOperations(maskData, this.canvas.width, this.canvas.height, morphologyIterations);
        this.removeSmallRegions(maskData, this.canvas.width, this.canvas.height, minRegionSize);
        
        // Create mask canvas
        const maskCanvas = document.createElement('canvas');
        maskCanvas.width = this.canvas.width;
        maskCanvas.height = this.canvas.height;
        
        const maskCtx = maskCanvas.getContext('2d');
        const finalMaskData = new ImageData(maskData, this.canvas.width, this.canvas.height);
        maskCtx.putImageData(finalMaskData, 0, 0);
        
        if (debug) {
            this.debugMaskGeneration(imageData, maskData, options);
        }
        
        console.log(`✅ Garment mask generated: ${this.canvas.width}x${this.canvas.height}`);
        
        return {
            canvas: maskCanvas,
            imageData: finalMaskData,
            stats: this.calculateMaskStats(maskData)
        };
    }
    
    /**
     * Exclude background areas from mask
     */
    excludeBackground(imageData, maskData) {
        const { data, width, height } = imageData;
        
        // Detect potential background regions
        const backgroundRegions = this.detectBackgroundRegions(data, width, height);
        
        // Apply background exclusion
        for (let i = 0; i < data.length; i += 4) {
            const pixelIndex = i / 4;
            const x = pixelIndex % width;
            const y = Math.floor(pixelIndex / width);
            
            // Check if pixel is in background region
            if (this.isBackgroundPixel(data, i, x, y, width, height, backgroundRegions)) {
                maskData[i] = 0;     // R
                maskData[i + 1] = 0; // G
                maskData[i + 2] = 0; // B
                // Keep alpha for debugging
            }
        }
    }
    
    /**
     * Detect background regions using edge detection and uniformity
     */
    detectBackgroundRegions(data, width, height) {
        const regions = [];
        
        // Analyze border regions (likely background)
        const borderWidth = Math.min(width, height) * 0.1;
        
        // Top and bottom borders
        for (let y = 0; y < borderWidth; y++) {
            regions.push(...this.analyzeBorderRegion(data, width, height, 0, y, width, 1));
        }
        for (let y = height - borderWidth; y < height; y++) {
            regions.push(...this.analyzeBorderRegion(data, width, height, 0, y, width, 1));
        }
        
        // Left and right borders  
        for (let x = 0; x < borderWidth; x++) {
            regions.push(...this.analyzeBorderRegion(data, width, height, x, 0, 1, height));
        }
        for (let x = width - borderWidth; x < width; x++) {
            regions.push(...this.analyzeBorderRegion(data, width, height, x, 0, 1, height));
        }
        
        return regions;
    }
    
    /**
     * Analyze border region for background characteristics
     */
    analyzeBorderRegion(data, width, height, startX, startY, regionWidth, regionHeight) {
        const regions = [];
        const colors = [];
        
        // Sample colors in region
        for (let y = startY; y < Math.min(startY + regionHeight, height); y++) {
            for (let x = startX; x < Math.min(startX + regionWidth, width); x++) {
                const idx = (y * width + x) * 4;
                colors.push({
                    r: data[idx],
                    g: data[idx + 1], 
                    b: data[idx + 2],
                    x, y
                });
            }
        }
        
        if (colors.length === 0) return regions;
        
        // Check for color uniformity
        const avgColor = this.calculateAverageColor(colors);
        let uniformPixels = 0;
        
        for (const color of colors) {
            const distance = this.colorDistance(color, avgColor);
            if (distance < this.backgroundThresholds.uniformityThreshold) {
                uniformPixels++;
            }
        }
        
        const uniformity = uniformPixels / colors.length;
        
        // If region is uniform enough, mark as background
        if (uniformity > 0.8) {
            regions.push({
                color: avgColor,
                uniformity,
                bounds: { startX, startY, width: regionWidth, height: regionHeight }
            });
        }
        
        return regions;
    }
    
    /**
     * Check if pixel is likely background
     */
    isBackgroundPixel(data, idx, x, y, width, height, backgroundRegions) {
        const pixelColor = {
            r: data[idx],
            g: data[idx + 1],
            b: data[idx + 2]
        };
        
        // Check against detected background regions
        for (const region of backgroundRegions) {
            const distance = this.colorDistance(pixelColor, region.color);
            if (distance < this.backgroundThresholds.uniformityThreshold * 1.5) {
                return true;
            }
        }
        
        // Check for edge-based background detection
        const edgeDensity = this.calculateLocalEdgeDensity(data, x, y, width, height, 5);
        if (edgeDensity < this.backgroundThresholds.edgeThreshold / 100) {
            return true;
        }
        
        return false;
    }
    
    /**
     * Exclude skin tone areas from mask
     */
    excludeSkinTones(imageData, maskData) {
        const { data } = imageData;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1]; 
            const b = data[i + 2];
            
            if (this.isSkinTone(r, g, b)) {
                maskData[i] = 0;     // R
                maskData[i + 1] = 0; // G
                maskData[i + 2] = 0; // B
                // Keep alpha for debugging
            }
        }
    }
    
    /**
     * Check if RGB color is a skin tone
     */
    isSkinTone(r, g, b) {
        const hsv = this.rgbToHsv(r, g, b);
        
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
     * Apply morphological operations (erosion + dilation)
     */
    applyMorphologyOperations(maskData, width, height, iterations = 2) {
        for (let iter = 0; iter < iterations; iter++) {
            // Erosion pass
            const eroded = new Uint8ClampedArray(maskData);
            this.applyErosion(maskData, eroded, width, height);
            
            // Dilation pass
            this.applyDilation(eroded, maskData, width, height);
        }
    }
    
    /**
     * Apply erosion to remove noise
     */
    applyErosion(input, output, width, height) {
        const kernel = [
            [-1, -1], [-1, 0], [-1, 1],
            [0, -1],  [0, 0],  [0, 1],
            [1, -1],  [1, 0],  [1, 1]
        ];
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = (y * width + x) * 4;
                
                let minValue = 255;
                for (const [dy, dx] of kernel) {
                    const neighborIdx = ((y + dy) * width + (x + dx)) * 4;
                    minValue = Math.min(minValue, input[neighborIdx]);
                }
                
                output[idx] = minValue;
                output[idx + 1] = minValue;
                output[idx + 2] = minValue;
                output[idx + 3] = input[idx + 3]; // Preserve alpha
            }
        }
    }
    
    /**
     * Apply dilation to fill gaps
     */
    applyDilation(input, output, width, height) {
        const kernel = [
            [-1, -1], [-1, 0], [-1, 1],
            [0, -1],  [0, 0],  [0, 1], 
            [1, -1],  [1, 0],  [1, 1]
        ];
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = (y * width + x) * 4;
                
                let maxValue = 0;
                for (const [dy, dx] of kernel) {
                    const neighborIdx = ((y + dy) * width + (x + dx)) * 4;
                    maxValue = Math.max(maxValue, input[neighborIdx]);
                }
                
                output[idx] = maxValue;
                output[idx + 1] = maxValue;
                output[idx + 2] = maxValue;
                output[idx + 3] = input[idx + 3]; // Preserve alpha
            }
        }
    }
    
    /**
     * Remove small disconnected regions
     */
    removeSmallRegions(maskData, width, height, minSize) {
        const visited = new Array(width * height).fill(false);
        const regions = [];
        
        // Find all connected regions
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const idx = y * width + x;
                const pixelIdx = idx * 4;
                
                if (!visited[idx] && maskData[pixelIdx] > 127) { // White pixel
                    const region = this.floodFill(maskData, visited, x, y, width, height);
                    regions.push(region);
                }
            }
        }
        
        // Remove small regions
        for (const region of regions) {
            if (region.pixels.length < minSize) {
                for (const pixel of region.pixels) {
                    const pixelIdx = pixel * 4;
                    maskData[pixelIdx] = 0;     // R
                    maskData[pixelIdx + 1] = 0; // G
                    maskData[pixelIdx + 2] = 0; // B
                }
            }
        }
    }
    
    /**
     * Flood fill algorithm for region detection
     */
    floodFill(maskData, visited, startX, startY, width, height) {
        const region = { pixels: [], bounds: { minX: startX, maxX: startX, minY: startY, maxY: startY } };
        const stack = [{ x: startX, y: startY }];
        
        while (stack.length > 0) {
            const { x, y } = stack.pop();
            
            if (x < 0 || x >= width || y < 0 || y >= height) continue;
            
            const idx = y * width + x;
            const pixelIdx = idx * 4;
            
            if (visited[idx] || maskData[pixelIdx] < 127) continue;
            
            visited[idx] = true;
            region.pixels.push(idx);
            
            // Update bounds
            region.bounds.minX = Math.min(region.bounds.minX, x);
            region.bounds.maxX = Math.max(region.bounds.maxX, x);
            region.bounds.minY = Math.min(region.bounds.minY, y);
            region.bounds.maxY = Math.max(region.bounds.maxY, y);
            
            // Add neighbors
            stack.push({ x: x + 1, y }, { x: x - 1, y }, { x, y: y + 1 }, { x, y: y - 1 });
        }
        
        return region;
    }
    
    /**
     * Calculate local edge density around a pixel
     */
    calculateLocalEdgeDensity(data, x, y, width, height, radius) {
        let edgeCount = 0;
        let totalPixels = 0;
        
        for (let dy = -radius; dy <= radius; dy++) {
            for (let dx = -radius; dx <= radius; dx++) {
                const nx = x + dx;
                const ny = y + dy;
                
                if (nx >= 0 && nx < width - 1 && ny >= 0 && ny < height - 1) {
                    const idx = (ny * width + nx) * 4;
                    const rightIdx = idx + 4;
                    const downIdx = idx + width * 4;
                    
                    const currentLum = 0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2];
                    const rightLum = 0.299 * data[rightIdx] + 0.587 * data[rightIdx + 1] + 0.114 * data[rightIdx + 2];
                    const downLum = 0.299 * data[downIdx] + 0.587 * data[downIdx + 1] + 0.114 * data[downIdx + 2];
                    
                    const hGrad = Math.abs(currentLum - rightLum);
                    const vGrad = Math.abs(currentLum - downLum);
                    
                    if (hGrad > 20 || vGrad > 20) {
                        edgeCount++;
                    }
                    totalPixels++;
                }
            }
        }
        
        return totalPixels > 0 ? edgeCount / totalPixels : 0;
    }
    
    /**
     * Calculate color distance between two RGB colors
     */
    colorDistance(color1, color2) {
        const dr = color1.r - color2.r;
        const dg = color1.g - color2.g;
        const db = color1.b - color2.b;
        return Math.sqrt(dr * dr + dg * dg + db * db);
    }
    
    /**
     * Calculate average color from array of colors
     */
    calculateAverageColor(colors) {
        if (colors.length === 0) return { r: 0, g: 0, b: 0 };
        
        const sum = colors.reduce((acc, color) => ({
            r: acc.r + color.r,
            g: acc.g + color.g,
            b: acc.b + color.b
        }), { r: 0, g: 0, b: 0 });
        
        return {
            r: Math.round(sum.r / colors.length),
            g: Math.round(sum.g / colors.length),
            b: Math.round(sum.b / colors.length)
        };
    }
    
    /**
     * Convert RGB to HSV color space
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
     * Calculate mask statistics
     */
    calculateMaskStats(maskData) {
        let whitePixels = 0;
        let blackPixels = 0;
        
        for (let i = 0; i < maskData.length; i += 4) {
            if (maskData[i] > 127) {
                whitePixels++;
            } else {
                blackPixels++;
            }
        }
        
        const totalPixels = whitePixels + blackPixels;
        
        return {
            totalPixels,
            whitePixels,
            blackPixels,
            coverage: whitePixels / totalPixels,
            exclusion: blackPixels / totalPixels
        };
    }
    
    /**
     * Debug mask generation process
     */
    debugMaskGeneration(originalData, maskData, options) {
        const stats = this.calculateMaskStats(maskData);
        
        console.log('🔍 Mask Generation Debug:', {
            options,
            stats: {
                coverage: `${(stats.coverage * 100).toFixed(1)}%`,
                exclusion: `${(stats.exclusion * 100).toFixed(1)}%`,
                totalPixels: stats.totalPixels
            },
            dimensions: `${this.canvas.width}x${this.canvas.height}`
        });
        
        // Create debug visualization
        this.createDebugVisualization(originalData, maskData);
    }
    
    /**
     * Create debug visualization showing original vs mask
     */
    createDebugVisualization(originalData, maskData) {
        const debugCanvas = document.createElement('canvas');
        debugCanvas.width = this.canvas.width * 2; // Side by side
        debugCanvas.height = this.canvas.height;
        
        const debugCtx = debugCanvas.getContext('2d');
        
        // Draw original image
        debugCtx.putImageData(new ImageData(originalData.data.slice(), this.canvas.width, this.canvas.height), 0, 0);
        
        // Draw mask
        debugCtx.putImageData(new ImageData(maskData, this.canvas.width, this.canvas.height), this.canvas.width, 0);
        
        // Add to document for debugging (can be removed in production)
        if (typeof document !== 'undefined') {
            debugCanvas.style.border = '2px solid red';
            debugCanvas.style.position = 'fixed';
            debugCanvas.style.top = '10px';
            debugCanvas.style.left = '10px';
            debugCanvas.style.zIndex = '9999';
            debugCanvas.style.maxWidth = '50vw';
            debugCanvas.title = 'Debug: Original (left) vs Mask (right)';
            
            // Remove previous debug canvas
            const existingDebug = document.querySelector('.garment-segmenter-debug');
            if (existingDebug) {
                existingDebug.remove();
            }
            
            debugCanvas.className = 'garment-segmenter-debug';
            document.body.appendChild(debugCanvas);
            
            // Auto-remove after 5 seconds
            setTimeout(() => debugCanvas.remove(), 5000);
        }
    }
    
    /**
     * Create mask from existing segmentation data
     */
    createMaskFromSegmentation(segmentationData, targetClass = 'garment') {
        // This method can be extended to work with ML-based segmentation
        // For now, it's a placeholder for future TensorFlow.js integration
        console.log('🚧 ML-based segmentation not yet implemented');
        return null;
    }
    
    /**
     * Optimize mask for texture application
     */
    optimizeMaskForTexture(maskCanvas, textureType) {
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = maskCanvas.width;
        tempCanvas.height = maskCanvas.height;
        
        const tempCtx = tempCanvas.getContext('2d');
        tempCtx.drawImage(maskCanvas, 0, 0);
        
        const imageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
        const { data } = imageData;
        
        // Apply texture-specific optimizations
        switch (textureType) {
            case 'lace':
                // Soften edges for better lace blending
                this.softenMaskEdges(data, tempCanvas.width, tempCanvas.height, 3);
                break;
            case 'silk':
                // Smooth mask for elegant silk application
                this.smoothMask(data, tempCanvas.width, tempCanvas.height);
                break;
            case 'embroidery':
                // Sharpen mask for detailed embroidery
                this.sharpenMask(data, tempCanvas.width, tempCanvas.height);
                break;
            case 'mesh':
                // Preserve sharp edges for mesh visibility
                break;
        }
        
        tempCtx.putImageData(imageData, 0, 0);
        return tempCanvas;
    }
    
    /**
     * Soften mask edges
     */
    softenMaskEdges(data, width, height, radius) {
        const softened = new Uint8ClampedArray(data);
        
        for (let y = radius; y < height - radius; y++) {
            for (let x = radius; x < width - radius; x++) {
                const idx = (y * width + x) * 4;
                
                let sum = 0;
                let count = 0;
                
                for (let dy = -radius; dy <= radius; dy++) {
                    for (let dx = -radius; dx <= radius; dx++) {
                        const neighborIdx = ((y + dy) * width + (x + dx)) * 4;
                        sum += data[neighborIdx];
                        count++;
                    }
                }
                
                const avg = sum / count;
                softened[idx] = avg;
                softened[idx + 1] = avg;
                softened[idx + 2] = avg;
                softened[idx + 3] = data[idx + 3];
            }
        }
        
        // Copy back
        for (let i = 0; i < data.length; i++) {
            data[i] = softened[i];
        }
    }
    
    /**
     * Smooth mask for elegant textures
     */
    smoothMask(data, width, height) {
        this.softenMaskEdges(data, width, height, 2);
    }
    
    /**
     * Sharpen mask for detailed textures
     */
    sharpenMask(data, width, height) {
        const sharpened = new Uint8ClampedArray(data);
        const kernel = [0, -1, 0, -1, 5, -1, 0, -1, 0];
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = (y * width + x) * 4;
                
                let sum = 0;
                let ki = 0;
                
                for (let dy = -1; dy <= 1; dy++) {
                    for (let dx = -1; dx <= 1; dx++) {
                        const neighborIdx = ((y + dy) * width + (x + dx)) * 4;
                        sum += data[neighborIdx] * kernel[ki++];
                    }
                }
                
                sharpened[idx] = Math.max(0, Math.min(255, sum));
                sharpened[idx + 1] = sharpened[idx];
                sharpened[idx + 2] = sharpened[idx];
                sharpened[idx + 3] = data[idx + 3];
            }
        }
        
        // Copy back
        for (let i = 0; i < data.length; i++) {
            data[i] = sharpened[i];
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GarmentSegmenter;
}