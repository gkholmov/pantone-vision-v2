/**
 * WebGL-based texture renderer for high-quality texture application
 * Eliminates corruption issues from Python numpy operations
 */
class WebGLTextureRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.gl = canvas.getContext('webgl2') || canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        
        if (!this.gl) {
            throw new Error('WebGL not supported');
        }
        
        console.log('✅ WebGL context created:', this.gl.getParameter(this.gl.VERSION));
        
        this.programs = {};
        this.textures = {};
        this.buffers = {};
        
        this.initializeWebGL();
        this.createShaderPrograms();
        this.setupBuffers();
    }
    
    initializeWebGL() {
        const gl = this.gl;
        
        // Enable blending for transparency
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        
        // Set viewport
        gl.viewport(0, 0, this.canvas.width, this.canvas.height);
        
        // Clear color
        gl.clearColor(0.0, 0.0, 0.0, 0.0);
    }
    
    createShaderPrograms() {
        // Vertex shader - handles positioning and texture coordinates
        const vertexShaderSource = `
            attribute vec2 a_position;
            attribute vec2 a_texCoord;
            
            varying vec2 v_texCoord;
            
            void main() {
                gl_Position = vec4(a_position, 0.0, 1.0);
                v_texCoord = a_texCoord;
            }
        `;
        
        // Fragment shader - handles texture blending with proper lace support
        const fragmentShaderSource = `
            precision mediump float;
            
            uniform sampler2D u_garment;
            uniform sampler2D u_texture;
            uniform sampler2D u_mask;
            uniform float u_intensity;
            uniform int u_blendMode; // 0=multiply, 1=overlay, 2=softlight, 3=lace
            
            varying vec2 v_texCoord;
            
            vec3 blendMultiply(vec3 base, vec3 texture) {
                return base * texture;
            }
            
            vec3 blendOverlay(vec3 base, vec3 texture) {
                return vec3(
                    base.r < 0.5 ? 2.0 * base.r * texture.r : 1.0 - 2.0 * (1.0 - base.r) * (1.0 - texture.r),
                    base.g < 0.5 ? 2.0 * base.g * texture.g : 1.0 - 2.0 * (1.0 - base.g) * (1.0 - texture.g),
                    base.b < 0.5 ? 2.0 * base.b * texture.b : 1.0 - 2.0 * (1.0 - base.b) * (1.0 - texture.b)
                );
            }
            
            vec3 blendSoftLight(vec3 base, vec3 texture) {
                return vec3(
                    texture.r < 0.5 ? base.r * (2.0 * texture.r + base.r * (1.0 - 2.0 * texture.r)) :
                                     base.r + (2.0 * texture.r - 1.0) * (sqrt(base.r) - base.r),
                    texture.g < 0.5 ? base.g * (2.0 * texture.g + base.g * (1.0 - 2.0 * texture.g)) :
                                     base.g + (2.0 * texture.g - 1.0) * (sqrt(base.g) - base.g),
                    texture.b < 0.5 ? base.b * (2.0 * texture.b + base.b * (1.0 - 2.0 * texture.b)) :
                                     base.b + (2.0 * texture.b - 1.0) * (sqrt(base.b) - base.b)
                );
            }
            
            vec3 blendLace(vec3 base, vec3 texture) {
                // Special blend mode for lace - preserves white transparency
                float luminance = 0.299 * texture.r + 0.587 * texture.g + 0.114 * texture.b;
                
                if (luminance > 0.8) {
                    // White lace areas - subtle overlay
                    return mix(base, blendOverlay(base, texture), 0.3);
                } else {
                    // Dark lace pattern - more pronounced
                    return mix(base, blendMultiply(base, texture), 0.7);
                }
            }
            
            void main() {
                vec4 garmentColor = texture2D(u_garment, v_texCoord);
                vec4 textureColor = texture2D(u_texture, v_texCoord);
                float maskValue = texture2D(u_mask, v_texCoord).r;
                
                // Skip processing if mask is zero (background)
                if (maskValue < 0.01) {
                    gl_FragColor = garmentColor;
                    return;
                }
                
                vec3 blendedColor;
                
                // Apply different blend modes based on texture type
                if (u_blendMode == 0) {
                    blendedColor = blendMultiply(garmentColor.rgb, textureColor.rgb);
                } else if (u_blendMode == 1) {
                    blendedColor = blendOverlay(garmentColor.rgb, textureColor.rgb);
                } else if (u_blendMode == 2) {
                    blendedColor = blendSoftLight(garmentColor.rgb, textureColor.rgb);
                } else if (u_blendMode == 3) {
                    blendedColor = blendLace(garmentColor.rgb, textureColor.rgb);
                } else {
                    blendedColor = mix(garmentColor.rgb, textureColor.rgb, 0.5);
                }
                
                // Apply intensity and mask
                vec3 finalColor = mix(garmentColor.rgb, blendedColor, u_intensity * maskValue);
                
                // Preserve alpha channel with slight transparency for lace effect
                float alpha = garmentColor.a;
                if (u_blendMode == 3 && maskValue > 0.5) {
                    // Add slight transparency for lace effect
                    alpha *= mix(1.0, 0.9, textureColor.a * u_intensity);
                }
                
                gl_FragColor = vec4(finalColor, alpha);
            }
        `;
        
        // Create and compile shaders
        const vertexShader = this.createShader(this.gl.VERTEX_SHADER, vertexShaderSource);
        const fragmentShader = this.createShader(this.gl.FRAGMENT_SHADER, fragmentShaderSource);
        
        // Create shader program
        this.programs.texture = this.createProgram(vertexShader, fragmentShader);
        
        // Get attribute and uniform locations
        const program = this.programs.texture;
        this.attribLocations = {
            position: this.gl.getAttribLocation(program, 'a_position'),
            texCoord: this.gl.getAttribLocation(program, 'a_texCoord')
        };
        
        this.uniformLocations = {
            garment: this.gl.getUniformLocation(program, 'u_garment'),
            texture: this.gl.getUniformLocation(program, 'u_texture'),
            mask: this.gl.getUniformLocation(program, 'u_mask'),
            intensity: this.gl.getUniformLocation(program, 'u_intensity'),
            blendMode: this.gl.getUniformLocation(program, 'u_blendMode')
        };
        
        console.log('✅ WebGL shaders compiled and linked successfully');
    }
    
    createShader(type, source) {
        const gl = this.gl;
        const shader = gl.createShader(type);
        
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            const error = gl.getShaderInfoLog(shader);
            gl.deleteShader(shader);
            throw new Error(`Shader compilation error: ${error}`);
        }
        
        return shader;
    }
    
    createProgram(vertexShader, fragmentShader) {
        const gl = this.gl;
        const program = gl.createProgram();
        
        gl.attachShader(program, vertexShader);
        gl.attachShader(program, fragmentShader);
        gl.linkProgram(program);
        
        if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
            const error = gl.getProgramInfoLog(program);
            gl.deleteProgram(program);
            throw new Error(`Program linking error: ${error}`);
        }
        
        return program;
    }
    
    setupBuffers() {
        const gl = this.gl;
        
        // Create vertex buffer for full-screen quad
        const positions = [
            -1.0, -1.0,  // Bottom left
             1.0, -1.0,  // Bottom right
            -1.0,  1.0,  // Top left
             1.0,  1.0   // Top right
        ];
        
        this.buffers.position = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.position);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW);
        
        // Create texture coordinate buffer
        const texCoords = [
            0.0, 0.0,  // Bottom left
            1.0, 0.0,  // Bottom right
            0.0, 1.0,  // Top left
            1.0, 1.0   // Top right
        ];
        
        this.buffers.texCoord = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.texCoord);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(texCoords), gl.STATIC_DRAW);
        
        console.log('✅ WebGL buffers created');
    }
    
    createTextureFromImage(image) {
        const gl = this.gl;
        const texture = gl.createTexture();
        
        gl.bindTexture(gl.TEXTURE_2D, texture);
        
        // Upload image data
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
        
        // Set texture parameters for non-power-of-2 textures
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        
        return texture;
    }
    
    createTextureFromCanvas(canvas) {
        return this.createTextureFromImage(canvas);
    }
    
    renderTexture(garmentImage, textureImage, maskCanvas, options = {}) {
        const {
            intensity = 0.8,
            blendMode = 3, // Default to lace blend mode
            debug = false
        } = options;
        
        const gl = this.gl;
        
        try {
            // Create textures from images
            const garmentTexture = this.createTextureFromImage(garmentImage);
            const textureTexture = this.createTextureFromImage(textureImage);
            const maskTexture = this.createTextureFromCanvas(maskCanvas);
            
            // Clear canvas
            gl.clear(gl.COLOR_BUFFER_BIT);
            
            // Use shader program
            gl.useProgram(this.programs.texture);
            
            // Bind textures
            gl.activeTexture(gl.TEXTURE0);
            gl.bindTexture(gl.TEXTURE_2D, garmentTexture);
            gl.uniform1i(this.uniformLocations.garment, 0);
            
            gl.activeTexture(gl.TEXTURE1);
            gl.bindTexture(gl.TEXTURE_2D, textureTexture);
            gl.uniform1i(this.uniformLocations.texture, 1);
            
            gl.activeTexture(gl.TEXTURE2);
            gl.bindTexture(gl.TEXTURE_2D, maskTexture);
            gl.uniform1i(this.uniformLocations.mask, 2);
            
            // Set uniforms
            gl.uniform1f(this.uniformLocations.intensity, intensity);
            gl.uniform1i(this.uniformLocations.blendMode, blendMode);
            
            // Bind vertex attributes
            gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.position);
            gl.vertexAttribPointer(this.attribLocations.position, 2, gl.FLOAT, false, 0, 0);
            gl.enableVertexAttribArray(this.attribLocations.position);
            
            gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.texCoord);
            gl.vertexAttribPointer(this.attribLocations.texCoord, 2, gl.FLOAT, false, 0, 0);
            gl.enableVertexAttribArray(this.attribLocations.texCoord);
            
            // Draw
            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
            
            // Clean up textures
            gl.deleteTexture(garmentTexture);
            gl.deleteTexture(textureTexture);
            gl.deleteTexture(maskTexture);
            
            if (debug) {
                console.log('✅ WebGL texture rendered successfully', {
                    intensity,
                    blendMode,
                    canvasSize: [this.canvas.width, this.canvas.height]
                });
            }
            
            return this.canvas;
            
        } catch (error) {
            console.error('❌ WebGL rendering failed:', error);
            throw error;
        }
    }
    
    // Get canvas as image data for further processing
    getImageData() {
        const gl = this.gl;
        const pixels = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
        gl.readPixels(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
        
        // Flip Y coordinate (WebGL vs Canvas coordinate system)
        const flippedPixels = new Uint8Array(pixels.length);
        const width = gl.drawingBufferWidth;
        const height = gl.drawingBufferHeight;
        
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const srcOffset = ((height - 1 - y) * width + x) * 4;
                const dstOffset = (y * width + x) * 4;
                
                flippedPixels[dstOffset] = pixels[srcOffset];
                flippedPixels[dstOffset + 1] = pixels[srcOffset + 1];
                flippedPixels[dstOffset + 2] = pixels[srcOffset + 2];
                flippedPixels[dstOffset + 3] = pixels[srcOffset + 3];
            }
        }
        
        return new ImageData(new Uint8ClampedArray(flippedPixels), width, height);
    }
    
    // Convert to blob for download
    async toBlob(type = 'image/png', quality = 0.92) {
        return new Promise(resolve => {
            this.canvas.toBlob(resolve, type, quality);
        });
    }
    
    // Check if WebGL extensions are available
    static isSupported() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl2') || 
                      canvas.getContext('webgl') || 
                      canvas.getContext('experimental-webgl');
            return !!gl;
        } catch (e) {
            return false;
        }
    }
    
    // Get WebGL capabilities info
    static getCapabilities() {
        if (!this.isSupported()) {
            return null;
        }
        
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        
        return {
            version: gl.getParameter(gl.VERSION),
            shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
            vendor: gl.getParameter(gl.VENDOR),
            renderer: gl.getParameter(gl.RENDERER),
            maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
            maxCombinedTextureImageUnits: gl.getParameter(gl.MAX_COMBINED_TEXTURE_IMAGE_UNITS),
            extensions: gl.getSupportedExtensions()
        };
    }
    
    cleanup() {
        const gl = this.gl;
        
        // Delete shaders and programs
        if (this.programs.texture) {
            gl.deleteProgram(this.programs.texture);
        }
        
        // Delete buffers
        Object.values(this.buffers).forEach(buffer => {
            gl.deleteBuffer(buffer);
        });
        
        console.log('✅ WebGL resources cleaned up');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebGLTextureRenderer;
}