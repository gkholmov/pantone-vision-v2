/**
 * Texture processor with intelligent pattern detection
 * Handles texture loading, analysis, and preprocessing
 */
class TextureProcessor {
    constructor(renderer = null) {
        this.renderer = renderer;
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Pattern detection thresholds
        this.patterns = {
            lace: {
                edgeDensityMin: 0.15,     // Lace has high edge density due to intricate patterns
                edgeDensityMax: 0.8,      // Can be very high for complex lace
                brightnessMin: 50,        // Can have dark patterns on light background
                transparencyMin: 0.05,    // Even slight transparency suggests lace
                patternComplexity: 0.3,   // Complex ornate patterns
                contrastRatio: 2.0        // High contrast between dark/light areas
            },
            silk: {
                edgeDensityMax: 0.08,     // Silk is smooth with low edge density
                brightnessMin: 120,       // Generally lighter/more uniform
                smoothnessMin: 0.85,      // Very smooth texture
                uniformityMin: 0.6        // More uniform color distribution
            },
            embroidery: {
                edgeDensityMin: 0.12,
                colorVarianceMin: 800,    // Lower threshold for better detection
                patternComplexity: 0.4,
                brightnessVariance: 50    // Embroidery has varied brightness
            },
            mesh: {
                edgeDensityMin: 0.25,
                holesRatio: 0.4,
                regularityScore: 0.8,     // Mesh patterns are more regular
                openworkRatio: 0.3        // Significant open areas
            }
        };
        
        console.log('✅ TextureProcessor initialized');
    }
    
    /**
     * Load texture from various sources
     */
    async loadTexture(source) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            
            img.onload = () => {
                // Resize if too large for performance
                const maxSize = 1024;
                let { width, height } = img;
                
                if (width > maxSize || height > maxSize) {
                    const scale = Math.min(maxSize / width, maxSize / height);
                    width *= scale;
                    height *= scale;
                }
                
                this.canvas.width = width;
                this.canvas.height = height;
                
                // Clear and draw
                this.ctx.clearRect(0, 0, width, height);
                this.ctx.drawImage(img, 0, 0, width, height);
                
                console.log(`✅ Texture loaded: ${width}x${height}`);
                resolve({
                    image: img,
                    canvas: this.canvas,
                    width,
                    height
                });
            };
            
            img.onerror = (error) => {
                console.error('❌ Failed to load texture:', error);
                reject(new Error('Failed to load texture image'));
            };
            
            // Handle different source types
            if (typeof source === 'string') {
                // URL or data URL
                img.src = source;
            } else if (source instanceof File) {
                // File object
                const reader = new FileReader();
                reader.onload = (e) => img.src = e.target.result;
                reader.onerror = reject;
                reader.readAsDataURL(source);
            } else if (source instanceof HTMLImageElement) {
                // Already an image
                img.src = source.src;
            } else {
                reject(new Error('Unsupported texture source type'));
            }
        });
    }
    
    /**
     * Detect texture pattern type and characteristics
     */
    detectPattern(imageData = null) {
        if (!imageData) {
            imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        }
        
        const analysis = this.analyzeImageFeatures(imageData);
        const patternType = this.classifyPattern(analysis);
        
        console.log('🔍 Pattern detection:', {
            type: patternType.type,
            confidence: patternType.confidence.toFixed(3),
            features: analysis
        });
        
        return {
            type: patternType.type,
            confidence: patternType.confidence,
            features: analysis,
            blendMode: this.getOptimalBlendMode(patternType.type),
            intensity: this.getRecommendedIntensity(patternType.type)
        };
    }
    
    /**
     * Analyze image features for pattern classification
     */
    analyzeImageFeatures(imageData) {
        const { data, width, height } = imageData;
        const totalPixels = width * height;
        
        let brightness = 0;
        let edgeCount = 0;
        let transparentPixels = 0;
        let colorVariance = 0;
        const colorCounts = new Map();
        
        // First pass - basic statistics
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            const a = data[i + 3];
            
            // Brightness calculation
            const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
            brightness += luminance;
            
            // Transparency detection
            if (a < 200) {
                transparentPixels++;
            }
            
            // Color variance calculation
            const colorKey = `${Math.floor(r/32)}-${Math.floor(g/32)}-${Math.floor(b/32)}`;
            colorCounts.set(colorKey, (colorCounts.get(colorKey) || 0) + 1);
        }
        
        brightness /= totalPixels;
        const transparency = transparentPixels / totalPixels;
        
        // Calculate color variance
        const uniqueColors = colorCounts.size;
        const colorDistribution = Array.from(colorCounts.values());
        const meanColorCount = totalPixels / uniqueColors;
        colorVariance = colorDistribution.reduce((sum, count) => 
            sum + Math.pow(count - meanColorCount, 2), 0) / uniqueColors;
        
        // Edge detection pass
        const edgeDensity = this.calculateEdgeDensity(data, width, height);
        
        // Pattern regularity
        const patternScore = this.calculatePatternRegularity(data, width, height);
        
        // Texture smoothness
        const smoothness = this.calculateSmoothness(data, width, height);
        
        // Contrast ratio for lace detection
        const contrastRatio = this.calculateContrastRatio(data, width, height);
        
        return {
            brightness,
            transparency,
            edgeDensity,
            colorVariance,
            uniqueColors,
            patternScore,
            smoothness,
            contrastRatio,
            width,
            height
        };
    }
    
    /**
     * Calculate edge density for texture classification
     */
    calculateEdgeDensity(data, width, height) {
        let edgePixels = 0;
        const threshold = 30;
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = (y * width + x) * 4;
                
                // Get current pixel luminance
                const current = 0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2];
                
                // Check horizontal gradient
                const right = 0.299 * data[idx + 4] + 0.587 * data[idx + 5] + 0.114 * data[idx + 6];
                const hGrad = Math.abs(current - right);
                
                // Check vertical gradient
                const down = 0.299 * data[idx + width * 4] + 0.587 * data[idx + width * 4 + 1] + 0.114 * data[idx + width * 4 + 2];
                const vGrad = Math.abs(current - down);
                
                if (hGrad > threshold || vGrad > threshold) {
                    edgePixels++;
                }
            }
        }
        
        return edgePixels / (width * height);
    }
    
    /**
     * Calculate pattern regularity score
     */
    calculatePatternRegularity(data, width, height) {
        // Simplified pattern analysis using autocorrelation
        const sampleSize = Math.min(64, width / 4);
        let correlationSum = 0;
        let samples = 0;
        
        for (let dy = -sampleSize / 2; dy <= sampleSize / 2; dy += 8) {
            for (let dx = -sampleSize / 2; dx <= sampleSize / 2; dx += 8) {
                if (dx === 0 && dy === 0) continue;
                
                let correlation = 0;
                let validPixels = 0;
                
                for (let y = sampleSize; y < height - sampleSize; y += 4) {
                    for (let x = sampleSize; x < width - sampleSize; x += 4) {
                        const idx1 = (y * width + x) * 4;
                        const idx2 = ((y + dy) * width + (x + dx)) * 4;
                        
                        if (idx2 >= 0 && idx2 < data.length - 3) {
                            const lum1 = 0.299 * data[idx1] + 0.587 * data[idx1 + 1] + 0.114 * data[idx1 + 2];
                            const lum2 = 0.299 * data[idx2] + 0.587 * data[idx2 + 1] + 0.114 * data[idx2 + 2];
                            
                            correlation += Math.abs(lum1 - lum2) < 20 ? 1 : 0;
                            validPixels++;
                        }
                    }
                }
                
                if (validPixels > 0) {
                    correlationSum += correlation / validPixels;
                    samples++;
                }
            }
        }
        
        return samples > 0 ? correlationSum / samples : 0;
    }
    
    /**
     * Calculate texture smoothness
     */
    calculateSmoothness(data, width, height) {
        let gradientSum = 0;
        let pixelCount = 0;
        
        for (let y = 0; y < height - 1; y++) {
            for (let x = 0; x < width - 1; x++) {
                const idx = (y * width + x) * 4;
                const rightIdx = idx + 4;
                const downIdx = idx + width * 4;
                
                // Calculate gradients
                const currentLum = 0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2];
                const rightLum = 0.299 * data[rightIdx] + 0.587 * data[rightIdx + 1] + 0.114 * data[rightIdx + 2];
                const downLum = 0.299 * data[downIdx] + 0.587 * data[downIdx + 1] + 0.114 * data[downIdx + 2];
                
                const hGrad = Math.abs(currentLum - rightLum);
                const vGrad = Math.abs(currentLum - downLum);
                
                gradientSum += Math.sqrt(hGrad * hGrad + vGrad * vGrad);
                pixelCount++;
            }
        }
        
        return 1.0 - Math.min(gradientSum / pixelCount / 100, 1.0);
    }
    
    /**
     * Calculate contrast ratio for lace detection
     */
    calculateContrastRatio(data, width, height) {
        let minLuminance = 255;
        let maxLuminance = 0;
        
        for (let i = 0; i < data.length; i += 4) {
            const luminance = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
            minLuminance = Math.min(minLuminance, luminance);
            maxLuminance = Math.max(maxLuminance, luminance);
        }
        
        // Calculate contrast ratio (typical lace has high contrast)
        return maxLuminance > 0 ? (maxLuminance + 5) / (minLuminance + 5) : 1.0;
    }
    
    /**
     * Classify pattern based on analyzed features
     */
    classifyPattern(features) {
        const scores = {
            lace: 0,
            silk: 0,
            embroidery: 0,
            mesh: 0,
            generic: 0.3
        };
        
        // Lace detection - improved algorithm
        let laceScore = 0;
        if (features.edgeDensity > this.patterns.lace.edgeDensityMin) {
            laceScore += 0.3; // High edge density is key for lace
        }
        if (features.contrastRatio > this.patterns.lace.contrastRatio) {
            laceScore += 0.25; // High contrast between dark patterns and light fabric
        }
        if (features.patternScore > this.patterns.lace.patternComplexity) {
            laceScore += 0.2; // Complex patterns typical of lace
        }
        if (features.transparency > this.patterns.lace.transparencyMin) {
            laceScore += 0.15; // Some transparency/openwork
        }
        if (features.brightness > this.patterns.lace.brightnessMin) {
            laceScore += 0.1; // Not too dark overall
        }
        scores.lace = laceScore;
        
        // Silk detection
        if (features.smoothness > this.patterns.silk.smoothnessMin &&
            features.brightness > this.patterns.silk.brightnessMin &&
            features.edgeDensity < this.patterns.silk.edgeDensityMax) {
            scores.silk = 0.6 + features.smoothness * 0.3 + 
                         (features.brightness / 255) * 0.1;
        }
        
        // Embroidery detection
        if (features.edgeDensity > this.patterns.embroidery.edgeDensityMin &&
            features.colorVariance > this.patterns.embroidery.colorVarianceMin &&
            features.patternScore > this.patterns.embroidery.patternComplexity) {
            scores.embroidery = 0.65 + (features.colorVariance / 5000) * 0.2 + 
                              features.patternScore * 0.15;
        }
        
        // Mesh detection
        if (features.edgeDensity > this.patterns.mesh.edgeDensityMin &&
            features.transparency > 0.1 &&
            features.patternScore > this.patterns.mesh.regularityScore) {
            scores.mesh = 0.6 + features.transparency * 0.25 + 
                         features.patternScore * 0.15;
        }
        
        // Find best match
        let bestType = 'generic';
        let bestScore = scores.generic;
        
        for (const [type, score] of Object.entries(scores)) {
            if (score > bestScore) {
                bestType = type;
                bestScore = score;
            }
        }
        
        return {
            type: bestType,
            confidence: Math.min(bestScore, 0.95)
        };
    }
    
    /**
     * Get optimal blend mode for pattern type
     */
    getOptimalBlendMode(patternType) {
        const blendModes = {
            lace: 3,        // Special lace blend mode
            silk: 2,        // Soft light
            embroidery: 1,  // Overlay
            mesh: 0,        // Multiply
            generic: 1      // Overlay default
        };
        
        return blendModes[patternType] || blendModes.generic;
    }
    
    /**
     * Get recommended intensity for pattern type
     */
    getRecommendedIntensity(patternType) {
        const intensities = {
            lace: 0.9,      // High intensity for visibility
            silk: 0.6,      // Subtle for elegance
            embroidery: 0.8, // Medium-high for details
            mesh: 0.7,      // Medium for breathability
            generic: 0.8    // Default medium-high
        };
        
        return intensities[patternType] || intensities.generic;
    }
    
    /**
     * Preprocess texture for better application
     */
    preprocessTexture(textureCanvas, patternType, targetWidth, targetHeight) {
        // Create processing canvas
        const processCanvas = document.createElement('canvas');
        const processCtx = processCanvas.getContext('2d');
        
        processCanvas.width = targetWidth;
        processCanvas.height = targetHeight;
        
        // Scale texture to fit target dimensions
        processCtx.drawImage(textureCanvas, 0, 0, targetWidth, targetHeight);
        
        // Apply pattern-specific preprocessing
        const imageData = processCtx.getImageData(0, 0, targetWidth, targetHeight);
        
        switch (patternType) {
            case 'lace':
                this.enhanceLaceTexture(imageData);
                break;
            case 'silk':
                this.smoothSilkTexture(imageData);
                break;
            case 'embroidery':
                this.enhanceEmbroideryDetails(imageData);
                break;
            case 'mesh':
                this.clarifyMeshPattern(imageData);
                break;
        }
        
        processCtx.putImageData(imageData, 0, 0);
        return processCanvas;
    }
    
    /**
     * Enhance lace texture for better visibility
     */
    enhanceLaceTexture(imageData) {
        const { data } = imageData;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            const a = data[i + 3];
            
            const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
            
            if (luminance > 200) {
                // Enhance white lace areas - increase contrast
                const factor = 1.1;
                data[i] = Math.min(255, r * factor);
                data[i + 1] = Math.min(255, g * factor);
                data[i + 2] = Math.min(255, b * factor);
            } else if (luminance < 100) {
                // Enhance dark lace pattern - increase contrast
                const factor = 0.8;
                data[i] = Math.max(0, r * factor);
                data[i + 1] = Math.max(0, g * factor);
                data[i + 2] = Math.max(0, b * factor);
            }
        }
    }
    
    /**
     * Smooth silk texture for elegance
     */
    smoothSilkTexture(imageData) {
        // Apply subtle smoothing to reduce noise
        const { data, width, height } = imageData;
        const smoothed = new Uint8ClampedArray(data);
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = (y * width + x) * 4;
                
                // 3x3 box blur
                for (let c = 0; c < 3; c++) {
                    let sum = 0;
                    for (let dy = -1; dy <= 1; dy++) {
                        for (let dx = -1; dx <= 1; dx++) {
                            sum += data[((y + dy) * width + (x + dx)) * 4 + c];
                        }
                    }
                    smoothed[idx + c] = sum / 9;
                }
            }
        }
        
        // Copy back smoothed values
        for (let i = 0; i < data.length; i++) {
            data[i] = smoothed[i];
        }
    }
    
    /**
     * Enhance embroidery details
     */
    enhanceEmbroideryDetails(imageData) {
        const { data } = imageData;
        
        // Increase saturation for embroidery
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            // Convert to HSV, increase saturation, convert back
            const hsv = this.rgbToHsv(r, g, b);
            hsv.s = Math.min(1, hsv.s * 1.2);
            
            const rgb = this.hsvToRgb(hsv.h, hsv.s, hsv.v);
            data[i] = rgb.r;
            data[i + 1] = rgb.g;
            data[i + 2] = rgb.b;
        }
    }
    
    /**
     * Clarify mesh pattern
     */
    clarifyMeshPattern(imageData) {
        // Increase contrast for mesh visibility
        const { data } = imageData;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            // Apply contrast enhancement
            const factor = 1.3;
            const offset = -30;
            
            data[i] = Math.max(0, Math.min(255, (r - 128) * factor + 128 + offset));
            data[i + 1] = Math.max(0, Math.min(255, (g - 128) * factor + 128 + offset));
            data[i + 2] = Math.max(0, Math.min(255, (b - 128) * factor + 128 + offset));
        }
    }
    
    /**
     * Color space conversion utilities
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
        
        return { h, s, v };
    }
    
    hsvToRgb(h, s, v) {
        const i = Math.floor(h * 6);
        const f = h * 6 - i;
        const p = v * (1 - s);
        const q = v * (1 - f * s);
        const t = v * (1 - (1 - f) * s);
        
        let r, g, b;
        switch (i % 6) {
            case 0: r = v; g = t; b = p; break;
            case 1: r = q; g = v; b = p; break;
            case 2: r = p; g = v; b = t; break;
            case 3: r = p; g = q; b = v; break;
            case 4: r = t; g = p; b = v; break;
            case 5: r = v; g = p; b = q; break;
        }
        
        return {
            r: Math.round(r * 255),
            g: Math.round(g * 255),
            b: Math.round(b * 255)
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TextureProcessor;
}