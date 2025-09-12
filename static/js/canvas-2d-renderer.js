/**
 * Canvas 2D fallback renderer for texture application
 * Provides similar functionality to WebGL renderer using Canvas 2D API
 */
class Canvas2DRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        
        if (!this.ctx) {
            throw new Error('Canvas 2D context not available');
        }
        
        // Working canvases for compositing
        this.workCanvas = document.createElement('canvas');
        this.workCtx = this.workCanvas.getContext('2d');
        
        this.tempCanvas = document.createElement('canvas');
        this.tempCtx = this.tempCanvas.getContext('2d');
        
        // Blend mode implementations
        this.blendModes = {
            0: this.blendMultiply.bind(this),
            1: this.blendOverlay.bind(this),
            2: this.blendSoftLight.bind(this),
            3: this.blendLace.bind(this)
        };
        
        console.log('✅ Canvas 2D renderer initialized');
    }
    
    /**
     * Render texture onto garment with mask
     */
    renderTexture(garmentImage, textureImage, maskCanvas, options = {}) {
        const {
            intensity = 0.8,
            blendMode = 3, // Default to lace blend mode
            debug = false
        } = options;
        
        try {
            // Set canvas dimensions to match garment
            this.canvas.width = garmentImage.width;
            this.canvas.height = garmentImage.height;
            
            this.workCanvas.width = garmentImage.width;
            this.workCanvas.height = garmentImage.height;
            
            this.tempCanvas.width = garmentImage.width;
            this.tempCanvas.height = garmentImage.height;
            
            // Clear canvases
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.workCtx.clearRect(0, 0, this.workCanvas.width, this.workCanvas.height);
            this.tempCtx.clearRect(0, 0, this.tempCanvas.width, this.tempCanvas.height);
            
            // Draw base garment
            this.ctx.drawImage(garmentImage, 0, 0);
            
            // Get image data for pixel-level processing
            const garmentData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
            
            // Scale and draw texture to work canvas
            this.workCtx.drawImage(textureImage, 0, 0, this.workCanvas.width, this.workCanvas.height);
            const textureData = this.workCtx.getImageData(0, 0, this.workCanvas.width, this.workCanvas.height);
            
            // Scale and draw mask to temp canvas
            this.tempCtx.drawImage(maskCanvas, 0, 0, this.tempCanvas.width, this.tempCanvas.height);
            const maskData = this.tempCtx.getImageData(0, 0, this.tempCanvas.width, this.tempCanvas.height);
            
            // Apply texture blending
            const blendedData = this.applyTextureBlend(
                garmentData, 
                textureData, 
                maskData, 
                blendMode, 
                intensity
            );
            
            // Draw final result
            this.ctx.putImageData(blendedData, 0, 0);
            
            if (debug) {
                console.log('✅ Canvas 2D texture rendered successfully', {
                    intensity,
                    blendMode,
                    canvasSize: [this.canvas.width, this.canvas.height]
                });
            }
            
            return this.canvas;
            
        } catch (error) {
            console.error('❌ Canvas 2D rendering failed:', error);
            throw error;
        }
    }
    
    /**
     * Apply texture blending with specified mode
     */
    applyTextureBlend(garmentData, textureData, maskData, blendMode, intensity) {
        const result = new ImageData(
            new Uint8ClampedArray(garmentData.data), 
            garmentData.width, 
            garmentData.height
        );
        
        const blendFunction = this.blendModes[blendMode] || this.blendModes[1]; // Default to overlay
        
        for (let i = 0; i < result.data.length; i += 4) {
            const maskValue = maskData.data[i] / 255; // Use red channel as mask
            
            // Skip processing if mask is zero (background)
            if (maskValue < 0.01) {
                continue;
            }
            
            const garmentColor = {
                r: garmentData.data[i],
                g: garmentData.data[i + 1],
                b: garmentData.data[i + 2],
                a: garmentData.data[i + 3]
            };
            
            const textureColor = {
                r: textureData.data[i],
                g: textureData.data[i + 1],
                b: textureData.data[i + 2],
                a: textureData.data[i + 3]
            };
            
            // Apply blend mode
            const blendedColor = blendFunction(garmentColor, textureColor);
            
            // Apply intensity and mask
            const finalColor = this.mixColors(garmentColor, blendedColor, intensity * maskValue);
            
            result.data[i] = finalColor.r;
            result.data[i + 1] = finalColor.g;
            result.data[i + 2] = finalColor.b;
            
            // Handle alpha for lace effect
            if (blendMode === 3 && maskValue > 0.5) {
                const alphaFactor = this.mixValues(1.0, 0.9, textureColor.a / 255 * intensity);
                result.data[i + 3] = Math.round(garmentColor.a * alphaFactor);
            } else {
                result.data[i + 3] = garmentColor.a;
            }
        }
        
        return result;
    }
    
    /**
     * Multiply blend mode
     */
    blendMultiply(base, texture) {
        return {
            r: Math.round((base.r * texture.r) / 255),
            g: Math.round((base.g * texture.g) / 255),
            b: Math.round((base.b * texture.b) / 255),
            a: base.a
        };
    }
    
    /**
     * Overlay blend mode
     */
    blendOverlay(base, texture) {
        return {
            r: base.r < 128 ? 
                Math.round(2 * base.r * texture.r / 255) : 
                Math.round(255 - 2 * (255 - base.r) * (255 - texture.r) / 255),
            g: base.g < 128 ? 
                Math.round(2 * base.g * texture.g / 255) : 
                Math.round(255 - 2 * (255 - base.g) * (255 - texture.g) / 255),
            b: base.b < 128 ? 
                Math.round(2 * base.b * texture.b / 255) : 
                Math.round(255 - 2 * (255 - base.b) * (255 - texture.b) / 255),
            a: base.a
        };
    }
    
    /**
     * Soft light blend mode
     */
    blendSoftLight(base, texture) {
        const softLightChannel = (base, texture) => {
            const b = base / 255;
            const t = texture / 255;
            
            let result;
            if (t < 0.5) {
                result = b * (2 * t + b * (1 - 2 * t));
            } else {
                result = b + (2 * t - 1) * (Math.sqrt(b) - b);
            }
            
            return Math.round(Math.max(0, Math.min(255, result * 255)));
        };
        
        return {
            r: softLightChannel(base.r, texture.r),
            g: softLightChannel(base.g, texture.g),
            b: softLightChannel(base.b, texture.b),
            a: base.a
        };
    }
    
    /**
     * Special lace blend mode
     */
    blendLace(base, texture) {
        // Calculate luminance
        const luminance = 0.299 * texture.r + 0.587 * texture.g + 0.114 * texture.b;
        
        if (luminance > 200) {
            // White lace areas - subtle overlay
            const overlayColor = this.blendOverlay(base, texture);
            return this.mixColors(base, overlayColor, 0.3);
        } else {
            // Dark lace pattern - more pronounced multiply
            const multiplyColor = this.blendMultiply(base, texture);
            return this.mixColors(base, multiplyColor, 0.7);
        }
    }
    
    /**
     * Mix two colors with specified ratio
     */
    mixColors(color1, color2, ratio) {
        const invRatio = 1 - ratio;
        
        return {
            r: Math.round(color1.r * invRatio + color2.r * ratio),
            g: Math.round(color1.g * invRatio + color2.g * ratio),
            b: Math.round(color1.b * invRatio + color2.b * ratio),
            a: Math.round(color1.a * invRatio + color2.a * ratio)
        };
    }
    
    /**
     * Mix two numeric values
     */
    mixValues(value1, value2, ratio) {
        return value1 * (1 - ratio) + value2 * ratio;
    }
    
    /**
     * Get canvas as image data for further processing
     */
    getImageData() {
        return this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
    }
    
    /**
     * Convert canvas to blob for download
     */
    async toBlob(type = 'image/png', quality = 0.92) {
        return new Promise(resolve => {
            this.canvas.toBlob(resolve, type, quality);
        });
    }
    
    /**
     * Apply post-processing effects
     */
    applyPostProcessing(effects = {}) {
        const {
            brightness = 0,
            contrast = 0,
            saturation = 0,
            sharpness = 0
        } = effects;
        
        if (brightness === 0 && contrast === 0 && saturation === 0 && sharpness === 0) {
            return; // No effects to apply
        }
        
        const imageData = this.getImageData();
        const { data } = imageData;
        
        // Apply brightness and contrast
        if (brightness !== 0 || contrast !== 0) {
            this.applyBrightnessContrast(data, brightness, contrast);
        }
        
        // Apply saturation
        if (saturation !== 0) {
            this.applySaturation(data, saturation);
        }
        
        // Apply sharpening
        if (sharpness > 0) {
            this.applySharpen(imageData, sharpness);
        }
        
        this.ctx.putImageData(imageData, 0, 0);
    }
    
    /**
     * Apply brightness and contrast adjustment
     */
    applyBrightnessContrast(data, brightness, contrast) {
        const brightnessFactor = brightness / 100;
        const contrastFactor = (259 * (contrast + 255)) / (255 * (259 - contrast));
        
        for (let i = 0; i < data.length; i += 4) {
            // Apply contrast first, then brightness
            for (let c = 0; c < 3; c++) {
                let value = data[i + c];
                
                // Contrast
                value = contrastFactor * (value - 128) + 128;
                
                // Brightness
                value += brightnessFactor * 255;
                
                data[i + c] = Math.max(0, Math.min(255, value));
            }
        }
    }
    
    /**
     * Apply saturation adjustment
     */
    applySaturation(data, saturation) {
        const saturationFactor = (saturation + 100) / 100;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            // Convert to grayscale
            const gray = 0.299 * r + 0.587 * g + 0.114 * b;
            
            // Apply saturation
            data[i] = Math.max(0, Math.min(255, gray + saturationFactor * (r - gray)));
            data[i + 1] = Math.max(0, Math.min(255, gray + saturationFactor * (g - gray)));
            data[i + 2] = Math.max(0, Math.min(255, gray + saturationFactor * (b - gray)));
        }
    }
    
    /**
     * Apply sharpening filter
     */
    applySharpen(imageData, strength) {
        const { data, width, height } = imageData;
        const sharpened = new Uint8ClampedArray(data);
        
        // Sharpening kernel
        const kernel = [
            0, -strength, 0,
            -strength, 1 + 4 * strength, -strength,
            0, -strength, 0
        ];
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = (y * width + x) * 4;
                
                for (let c = 0; c < 3; c++) {
                    let sum = 0;
                    let ki = 0;
                    
                    for (let dy = -1; dy <= 1; dy++) {
                        for (let dx = -1; dx <= 1; dx++) {
                            const neighborIdx = ((y + dy) * width + (x + dx)) * 4;
                            sum += data[neighborIdx + c] * kernel[ki++];
                        }
                    }
                    
                    sharpened[idx + c] = Math.max(0, Math.min(255, sum));
                }
                
                sharpened[idx + 3] = data[idx + 3]; // Preserve alpha
            }
        }
        
        // Copy sharpened data back
        for (let i = 0; i < data.length; i++) {
            data[i] = sharpened[i];
        }
    }
    
    /**
     * Resize canvas maintaining aspect ratio
     */
    resizeCanvas(maxWidth, maxHeight, maintainAspect = true) {
        const currentWidth = this.canvas.width;
        const currentHeight = this.canvas.height;
        
        if (!maintainAspect) {
            this.canvas.width = maxWidth;
            this.canvas.height = maxHeight;
            return;
        }
        
        const aspectRatio = currentWidth / currentHeight;
        let newWidth = maxWidth;
        let newHeight = maxHeight;
        
        if (maxWidth / maxHeight > aspectRatio) {
            newWidth = maxHeight * aspectRatio;
        } else {
            newHeight = maxWidth / aspectRatio;
        }
        
        // Create temporary canvas with current content
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        tempCanvas.width = currentWidth;
        tempCanvas.height = currentHeight;
        tempCtx.drawImage(this.canvas, 0, 0);
        
        // Resize main canvas and redraw
        this.canvas.width = newWidth;
        this.canvas.height = newHeight;
        this.ctx.drawImage(tempCanvas, 0, 0, currentWidth, currentHeight, 0, 0, newWidth, newHeight);
    }
    
    /**
     * Create a preview thumbnail
     */
    createThumbnail(maxSize = 200) {
        const thumbnailCanvas = document.createElement('canvas');
        const thumbnailCtx = thumbnailCanvas.getContext('2d');
        
        const aspectRatio = this.canvas.width / this.canvas.height;
        let thumbWidth = maxSize;
        let thumbHeight = maxSize;
        
        if (aspectRatio > 1) {
            thumbHeight = maxSize / aspectRatio;
        } else {
            thumbWidth = maxSize * aspectRatio;
        }
        
        thumbnailCanvas.width = thumbWidth;
        thumbnailCanvas.height = thumbHeight;
        
        thumbnailCtx.drawImage(this.canvas, 0, 0, this.canvas.width, this.canvas.height, 0, 0, thumbWidth, thumbHeight);
        
        return thumbnailCanvas;
    }
    
    /**
     * Check if Canvas 2D is supported
     */
    static isSupported() {
        try {
            const canvas = document.createElement('canvas');
            return !!canvas.getContext('2d');
        } catch (e) {
            return false;
        }
    }
    
    /**
     * Get Canvas 2D capabilities info
     */
    static getCapabilities() {
        if (!this.isSupported()) {
            return null;
        }
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        return {
            maxCanvasSize: this.getMaxCanvasSize(),
            supportedFormats: ['image/png', 'image/jpeg', 'image/webp'],
            compositeOperations: [
                'source-over', 'source-in', 'source-out', 'source-atop',
                'destination-over', 'destination-in', 'destination-out', 'destination-atop',
                'lighter', 'copy', 'xor', 'multiply', 'screen', 'overlay',
                'darken', 'lighten', 'color-dodge', 'color-burn',
                'hard-light', 'soft-light', 'difference', 'exclusion'
            ]
        };
    }
    
    /**
     * Get maximum canvas size supported
     */
    static getMaxCanvasSize() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Test increasing sizes until failure
        let maxSize = 2048;
        while (maxSize <= 32768) {
            canvas.width = maxSize;
            canvas.height = maxSize;
            
            try {
                ctx.createImageData(maxSize, maxSize);
                maxSize *= 2;
            } catch (e) {
                break;
            }
        }
        
        return maxSize / 2;
    }
    
    /**
     * Clean up resources
     */
    cleanup() {
        // Clear canvases
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.workCtx.clearRect(0, 0, this.workCanvas.width, this.workCanvas.height);
        this.tempCtx.clearRect(0, 0, this.tempCanvas.width, this.tempCanvas.height);
        
        console.log('✅ Canvas 2D renderer cleaned up');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Canvas2DRenderer;
}