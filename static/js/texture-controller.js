/**
 * Texture Controller - Integration layer for client-side texture processing
 * Orchestrates WebGL renderer, Canvas 2D fallback, texture processor, and garment segmenter
 */
class TextureController {
    constructor(options = {}) {
        this.options = {
            preferWebGL: true,
            enableDebug: false,
            autoOptimize: true,
            maxTextureSize: 2048,
            fallbackToCanvas2D: true,
            ...options
        };
        
        // Core components
        this.renderer = null;
        this.textureProcessor = null;
        this.garmentSegmenter = null;
        
        // State management
        this.isInitialized = false;
        this.renderingMode = null; // 'webgl' | 'canvas2d' | null
        this.currentTexture = null;
        this.currentGarment = null;
        this.currentMask = null;
        this.patternInfo = null;
        
        // Performance tracking
        this.stats = {
            renderCount: 0,
            totalRenderTime: 0,
            avgRenderTime: 0,
            lastRenderTime: 0
        };
        
        console.log('🎨 TextureController created with options:', this.options);
    }
    
    /**
     * Initialize the texture controller and detect best rendering mode
     */
    async initialize() {
        if (this.isInitialized) {
            console.log('⚠️ TextureController already initialized');
            return this.renderingMode;
        }
        
        try {
            // Initialize garment segmenter (always needed)
            this.garmentSegmenter = new GarmentSegmenter();
            
            // Initialize texture processor (always needed)
            this.textureProcessor = new TextureProcessor();
            
            // Detect and initialize best renderer
            this.renderingMode = await this.detectBestRenderingMode();
            
            if (this.renderingMode === 'webgl') {
                await this.initializeWebGLRenderer();
            } else if (this.renderingMode === 'canvas2d') {
                await this.initializeCanvas2DRenderer();
            } else {
                throw new Error('No suitable rendering mode available');
            }
            
            this.isInitialized = true;
            
            console.log(`✅ TextureController initialized with ${this.renderingMode.toUpperCase()} renderer`);
            
            return this.renderingMode;
            
        } catch (error) {
            console.error('❌ TextureController initialization failed:', error);
            throw error;
        }
    }
    
    /**
     * Detect the best available rendering mode
     */
    async detectBestRenderingMode() {
        const capabilities = {
            webgl: WebGLTextureRenderer.isSupported(),
            canvas2d: Canvas2DRenderer.isSupported()
        };
        
        if (this.options.preferWebGL && capabilities.webgl) {
            return 'webgl';
        } else if (capabilities.canvas2d && this.options.fallbackToCanvas2D) {
            return 'canvas2d';
        }
        
        throw new Error('No supported rendering mode available');
    }
    
    /**
     * Initialize WebGL renderer
     */
    async initializeWebGLRenderer() {
        const canvas = document.createElement('canvas');
        canvas.width = this.options.maxTextureSize;
        canvas.height = this.options.maxTextureSize;
        
        this.renderer = new WebGLTextureRenderer(canvas);
        
        if (this.options.enableDebug) {
            const caps = WebGLTextureRenderer.getCapabilities();
            console.log('🔍 WebGL Capabilities:', caps);
        }
    }
    
    /**
     * Initialize Canvas 2D renderer
     */
    async initializeCanvas2DRenderer() {
        const canvas = document.createElement('canvas');
        canvas.width = this.options.maxTextureSize;
        canvas.height = this.options.maxTextureSize;
        
        this.renderer = new Canvas2DRenderer(canvas);
        
        if (this.options.enableDebug) {
            const caps = Canvas2DRenderer.getCapabilities();
            console.log('🔍 Canvas 2D Capabilities:', caps);
        }
    }
    
    /**
     * Process texture application with full pipeline
     */
    async processTexture(garmentSource, textureSource, options = {}) {
        if (!this.isInitialized) {
            await this.initialize();
        }
        
        const startTime = performance.now();
        
        try {
            const config = {
                intensity: 0.8,
                autoDetectPattern: true,
                excludeBackground: true,
                excludeSkin: true,
                optimizeMask: true,
                postProcess: false,
                ...options
            };
            
            // Step 1: Load and prepare images
            const { garmentImage, textureImage } = await this.loadImages(garmentSource, textureSource);
            
            // Step 2: Generate garment mask
            const maskResult = await this.generateGarmentMask(garmentImage, config);
            
            // Step 3: Analyze texture pattern
            let patternInfo = null;
            if (config.autoDetectPattern) {
                patternInfo = await this.analyzeTexturePattern(textureImage);
                this.patternInfo = patternInfo;
            }
            
            // Step 4: Optimize components for rendering
            const optimizedComponents = await this.optimizeForRendering(
                garmentImage, 
                textureImage, 
                maskResult.canvas,
                patternInfo,
                config
            );
            
            // Step 5: Render texture application
            const renderOptions = this.buildRenderOptions(patternInfo, config);
            const resultCanvas = await this.renderTextureApplication(
                optimizedComponents.garment,
                optimizedComponents.texture,
                optimizedComponents.mask,
                renderOptions
            );
            
            // Step 6: Post-processing (if enabled)
            if (config.postProcess) {
                await this.applyPostProcessing(resultCanvas, config.postProcessOptions || {});
            }
            
            // Update stats
            const renderTime = performance.now() - startTime;
            this.updateStats(renderTime);
            
            const result = {
                canvas: resultCanvas,
                renderingMode: this.renderingMode,
                patternInfo,
                maskStats: maskResult.stats,
                renderTime,
                options: config
            };
            
            if (this.options.enableDebug) {
                console.log('✅ Texture processing complete:', {
                    renderTime: `${renderTime.toFixed(2)}ms`,
                    renderingMode: this.renderingMode,
                    patternType: patternInfo?.type,
                    patternConfidence: patternInfo?.confidence?.toFixed(3),
                    maskCoverage: `${(maskResult.stats.coverage * 100).toFixed(1)}%`
                });
            }
            
            return result;
            
        } catch (error) {
            console.error('❌ Texture processing failed:', error);
            throw error;
        }
    }
    
    /**
     * Load and prepare images from various sources
     */
    async loadImages(garmentSource, textureSource) {
        const [garmentData, textureData] = await Promise.all([
            this.loadImage(garmentSource),
            this.loadImage(textureSource)
        ]);
        
        return {
            garmentImage: garmentData.image,
            textureImage: textureData.image
        };
    }
    
    /**
     * Load single image from source
     */
    async loadImage(source) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            
            img.onload = () => {
                resolve({
                    image: img,
                    width: img.width,
                    height: img.height
                });
            };
            
            img.onerror = (error) => {
                reject(new Error(`Failed to load image: ${error.message}`));
            };
            
            // Handle different source types
            if (typeof source === 'string') {
                img.src = source;
            } else if (source instanceof File) {
                const reader = new FileReader();
                reader.onload = (e) => img.src = e.target.result;
                reader.onerror = reject;
                reader.readAsDataURL(source);
            } else if (source instanceof HTMLImageElement) {
                img.src = source.src;
            } else if (source instanceof HTMLCanvasElement) {
                img.src = source.toDataURL();
            } else {
                reject(new Error('Unsupported image source type'));
            }
        });
    }
    
    /**
     * Generate garment mask using segmenter
     */
    async generateGarmentMask(garmentImage, config) {
        const maskOptions = {
            excludeSkin: config.excludeSkin,
            excludeBackground: config.excludeBackground,
            morphologyIterations: 2,
            minRegionSize: 100,
            debug: this.options.enableDebug
        };
        
        return await this.garmentSegmenter.generateMask(garmentImage, maskOptions);
    }
    
    /**
     * Analyze texture pattern using processor
     */
    async analyzeTexturePattern(textureImage) {
        await this.textureProcessor.loadTexture(textureImage);
        return this.textureProcessor.detectPattern();
    }
    
    /**
     * Optimize components for rendering
     */
    async optimizeForRendering(garmentImage, textureImage, maskCanvas, patternInfo, config) {
        const maxSize = this.options.maxTextureSize;
        
        // Determine target dimensions based on garment image
        let targetWidth = garmentImage.width;
        let targetHeight = garmentImage.height;
        
        // Scale down if too large
        if (targetWidth > maxSize || targetHeight > maxSize) {
            const scale = Math.min(maxSize / targetWidth, maxSize / targetHeight);
            targetWidth = Math.round(targetWidth * scale);
            targetHeight = Math.round(targetHeight * scale);
        }
        
        // Resize garment
        const optimizedGarment = await this.resizeImage(garmentImage, targetWidth, targetHeight);
        
        // Preprocess and resize texture
        let optimizedTexture = textureImage;
        if (patternInfo && this.options.autoOptimize) {
            const processedCanvas = this.textureProcessor.preprocessTexture(
                await this.imageToCanvas(textureImage),
                patternInfo.type,
                targetWidth,
                targetHeight
            );
            optimizedTexture = await this.canvasToImage(processedCanvas);
        } else {
            optimizedTexture = await this.resizeImage(textureImage, targetWidth, targetHeight);
        }
        
        // Resize and optimize mask
        let optimizedMask = await this.resizeCanvas(maskCanvas, targetWidth, targetHeight);
        if (patternInfo && config.optimizeMask) {
            optimizedMask = this.garmentSegmenter.optimizeMaskForTexture(optimizedMask, patternInfo.type);
        }
        
        return {
            garment: optimizedGarment,
            texture: optimizedTexture,
            mask: optimizedMask
        };
    }
    
    /**
     * Build render options from pattern info and config
     */
    buildRenderOptions(patternInfo, config) {
        const options = {
            intensity: config.intensity,
            blendMode: 1, // Default overlay
            debug: this.options.enableDebug
        };
        
        if (patternInfo) {
            options.blendMode = patternInfo.blendMode;
            if (config.intensity === 0.8) { // Use auto intensity if default
                options.intensity = patternInfo.intensity;
            }
        }
        
        return options;
    }
    
    /**
     * Render texture application using appropriate renderer
     */
    async renderTextureApplication(garmentImage, textureImage, maskCanvas, options) {
        // Ensure renderer canvas is correct size
        this.renderer.canvas.width = garmentImage.width;
        this.renderer.canvas.height = garmentImage.height;
        
        if (this.renderingMode === 'webgl') {
            // Update WebGL viewport
            this.renderer.gl.viewport(0, 0, garmentImage.width, garmentImage.height);
        }
        
        return this.renderer.renderTexture(garmentImage, textureImage, maskCanvas, options);
    }
    
    /**
     * Apply post-processing effects
     */
    async applyPostProcessing(canvas, postProcessOptions) {
        if (this.renderingMode === 'canvas2d') {
            this.renderer.applyPostProcessing(postProcessOptions);
        }
        // Note: WebGL post-processing could be added here with additional shaders
    }
    
    /**
     * Get current processing statistics
     */
    getStats() {
        return {
            ...this.stats,
            renderingMode: this.renderingMode,
            isInitialized: this.isInitialized,
            memoryUsage: this.estimateMemoryUsage()
        };
    }
    
    /**
     * Update performance statistics
     */
    updateStats(renderTime) {
        this.stats.renderCount++;
        this.stats.totalRenderTime += renderTime;
        this.stats.avgRenderTime = this.stats.totalRenderTime / this.stats.renderCount;
        this.stats.lastRenderTime = renderTime;
    }
    
    /**
     * Estimate current memory usage
     */
    estimateMemoryUsage() {
        let memoryEstimate = 0;
        
        if (this.renderer && this.renderer.canvas) {
            const canvas = this.renderer.canvas;
            memoryEstimate += canvas.width * canvas.height * 4; // RGBA bytes
        }
        
        // Add estimates for working canvases, textures, etc.
        memoryEstimate *= 3; // Rough multiplier for working memory
        
        return {
            estimated: memoryEstimate,
            formatted: this.formatBytes(memoryEstimate)
        };
    }
    
    /**
     * Format bytes into human-readable string
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    /**
     * Utility: Convert image to canvas
     */
    async imageToCanvas(image) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = image.width;
        canvas.height = image.height;
        
        ctx.drawImage(image, 0, 0);
        return canvas;
    }
    
    /**
     * Utility: Convert canvas to image
     */
    async canvasToImage(canvas) {
        return new Promise(resolve => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.src = canvas.toDataURL();
        });
    }
    
    /**
     * Utility: Resize image
     */
    async resizeImage(image, width, height) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = width;
        canvas.height = height;
        
        ctx.drawImage(image, 0, 0, image.width, image.height, 0, 0, width, height);
        
        return this.canvasToImage(canvas);
    }
    
    /**
     * Utility: Resize canvas
     */
    async resizeCanvas(sourceCanvas, width, height) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = width;
        canvas.height = height;
        
        ctx.drawImage(sourceCanvas, 0, 0, sourceCanvas.width, sourceCanvas.height, 0, 0, width, height);
        
        return canvas;
    }
    
    /**
     * Export current result
     */
    async exportResult(format = 'png', quality = 0.92) {
        if (!this.renderer || !this.renderer.canvas) {
            throw new Error('No result to export');
        }
        
        return this.renderer.toBlob(`image/${format}`, quality);
    }
    
    /**
     * Create preview thumbnail
     */
    async createPreview(maxSize = 300) {
        if (!this.renderer || !this.renderer.canvas) {
            throw new Error('No result to preview');
        }
        
        if (this.renderingMode === 'canvas2d') {
            return this.renderer.createThumbnail(maxSize);
        } else {
            // Create thumbnail for WebGL renderer
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            const sourceCanvas = this.renderer.canvas;
            const aspectRatio = sourceCanvas.width / sourceCanvas.height;
            
            let thumbWidth = maxSize;
            let thumbHeight = maxSize;
            
            if (aspectRatio > 1) {
                thumbHeight = maxSize / aspectRatio;
            } else {
                thumbWidth = maxSize * aspectRatio;
            }
            
            canvas.width = thumbWidth;
            canvas.height = thumbHeight;
            
            ctx.drawImage(sourceCanvas, 0, 0, thumbWidth, thumbHeight);
            return canvas;
        }
    }
    
    /**
     * Reset controller state
     */
    reset() {
        this.currentTexture = null;
        this.currentGarment = null;
        this.currentMask = null;
        this.patternInfo = null;
        
        // Reset stats
        this.stats = {
            renderCount: 0,
            totalRenderTime: 0,
            avgRenderTime: 0,
            lastRenderTime: 0
        };
        
        console.log('🔄 TextureController reset');
    }
    
    /**
     * Clean up resources and destroy controller
     */
    destroy() {
        if (this.renderer && this.renderer.cleanup) {
            this.renderer.cleanup();
        }
        
        this.renderer = null;
        this.textureProcessor = null;
        this.garmentSegmenter = null;
        this.isInitialized = false;
        
        console.log('🗑️ TextureController destroyed');
    }
    
    /**
     * Get system capabilities
     */
    static getSystemCapabilities() {
        return {
            webgl: {
                supported: WebGLTextureRenderer.isSupported(),
                capabilities: WebGLTextureRenderer.isSupported() ? WebGLTextureRenderer.getCapabilities() : null
            },
            canvas2d: {
                supported: Canvas2DRenderer.isSupported(),
                capabilities: Canvas2DRenderer.isSupported() ? Canvas2DRenderer.getCapabilities() : null
            },
            recommendedMode: WebGLTextureRenderer.isSupported() ? 'webgl' : 
                            Canvas2DRenderer.isSupported() ? 'canvas2d' : null
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TextureController;
}