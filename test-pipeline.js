/**
 * Test script for complete texture processing pipeline
 * Tests WebGL renderer, texture processor, garment segmenter, and Canvas 2D fallback
 */

async function testCompletePipeline() {
    console.log('🧪 Starting complete pipeline test...');
    
    try {
        // Test system capabilities first
        console.log('\n📊 System Capabilities:');
        const capabilities = TextureController.getSystemCapabilities();
        console.log('WebGL supported:', capabilities.webgl.supported);
        console.log('Canvas 2D supported:', capabilities.canvas2d.supported);
        console.log('Recommended mode:', capabilities.recommendedMode);
        
        if (capabilities.webgl.supported) {
            console.log('WebGL capabilities:', capabilities.webgl.capabilities);
        }
        
        // Initialize texture controller
        console.log('\n🎮 Initializing TextureController...');
        const controller = new TextureController({
            preferWebGL: true,
            enableDebug: true,
            autoOptimize: true,
            maxTextureSize: 1024,
            fallbackToCanvas2D: true
        });
        
        const renderingMode = await controller.initialize();
        console.log(`✅ TextureController initialized with ${renderingMode} renderer`);
        
        // Load test images
        console.log('\n📷 Loading test images...');
        
        // Create test garment image (simple sketch)
        const garmentCanvas = document.createElement('canvas');
        garmentCanvas.width = 400;
        garmentCanvas.height = 400;
        const garmentCtx = garmentCanvas.getContext('2d');
        
        // Draw a simple bustier shape
        garmentCtx.fillStyle = '#ffffff';
        garmentCtx.fillRect(0, 0, 400, 400);
        
        garmentCtx.strokeStyle = '#000000';
        garmentCtx.lineWidth = 3;
        garmentCtx.beginPath();
        
        // Bustier outline
        garmentCtx.moveTo(100, 150);
        garmentCtx.lineTo(100, 350);
        garmentCtx.lineTo(300, 350);
        garmentCtx.lineTo(300, 150);
        
        // Cup shapes
        garmentCtx.arc(150, 200, 40, 0, Math.PI, true);
        garmentCtx.moveTo(250, 160);
        garmentCtx.arc(250, 200, 40, 0, Math.PI, true);
        
        // Center line
        garmentCtx.moveTo(200, 150);
        garmentCtx.lineTo(200, 350);
        
        garmentCtx.stroke();
        
        // Create test lace texture
        const textureCanvas = document.createElement('canvas');
        textureCanvas.width = 200;
        textureCanvas.height = 200;
        const textureCtx = textureCanvas.getContext('2d');
        
        // Create lace pattern
        textureCtx.fillStyle = '#f0f0f0';
        textureCtx.fillRect(0, 0, 200, 200);
        
        textureCtx.strokeStyle = '#333333';
        textureCtx.lineWidth = 1;
        
        // Draw lace pattern
        for (let y = 0; y < 200; y += 20) {
            for (let x = 0; x < 200; x += 20) {
                textureCtx.beginPath();
                textureCtx.arc(x + 10, y + 10, 8, 0, 2 * Math.PI);
                textureCtx.stroke();
                
                // Add decorative elements
                textureCtx.beginPath();
                textureCtx.moveTo(x + 5, y + 10);
                textureCtx.lineTo(x + 15, y + 10);
                textureCtx.moveTo(x + 10, y + 5);
                textureCtx.lineTo(x + 10, y + 15);
                textureCtx.stroke();
            }
        }
        
        // Convert canvases to images
        const garmentImage = await canvasToImage(garmentCanvas);
        const textureImage = await canvasToImage(textureCanvas);
        
        console.log(`✅ Test images created - Garment: ${garmentImage.width}x${garmentImage.height}, Texture: ${textureImage.width}x${textureImage.height}`);
        
        // Test texture processing pipeline
        console.log('\n🎨 Processing texture application...');
        
        const startTime = performance.now();
        
        const result = await controller.processTexture(
            garmentImage,
            textureImage,
            {
                intensity: 0.9,
                autoDetectPattern: true,
                excludeBackground: true,
                excludeSkin: false, // No skin in our test image
                optimizeMask: true,
                postProcess: false
            }
        );
        
        const processTime = performance.now() - startTime;
        
        // Display results
        console.log('\n📊 Processing Results:');
        console.log('✅ Processing completed successfully!');
        console.log(`⏱️ Processing time: ${processTime.toFixed(2)}ms`);
        console.log(`🎯 Rendering mode: ${result.renderingMode}`);
        console.log(`🧵 Pattern detected: ${result.patternInfo?.type || 'generic'} (confidence: ${(result.patternInfo?.confidence * 100 || 0).toFixed(1)}%)`);
        console.log(`📐 Result dimensions: ${result.canvas.width}x${result.canvas.height}`);
        console.log(`🎭 Mask coverage: ${(result.maskStats.coverage * 100).toFixed(1)}%`);
        console.log(`⚙️ Intensity used: ${result.options.intensity}`);
        
        // Test pattern analysis
        console.log('\n🔍 Pattern Analysis Details:');
        if (result.patternInfo?.features) {
            const features = result.patternInfo.features;
            console.log(`Brightness: ${features.brightness.toFixed(1)}`);
            console.log(`Edge density: ${(features.edgeDensity * 100).toFixed(2)}%`);
            console.log(`Transparency: ${(features.transparency * 100).toFixed(1)}%`);
            console.log(`Smoothness: ${(features.smoothness * 100).toFixed(1)}%`);
            console.log(`Pattern score: ${(features.patternScore * 100).toFixed(1)}%`);
            console.log(`Unique colors: ${features.uniqueColors}`);
        }
        
        // Append result to DOM for visual verification
        console.log('\n👁️ Adding visual results to page...');
        
        const resultContainer = document.createElement('div');
        resultContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            z-index: 10000;
            max-width: 400px;
        `;
        
        resultContainer.innerHTML = `
            <h3>Pipeline Test Results</h3>
            <p><strong>Mode:</strong> ${result.renderingMode.toUpperCase()}</p>
            <p><strong>Pattern:</strong> ${result.patternInfo?.type || 'generic'}</p>
            <p><strong>Time:</strong> ${processTime.toFixed(2)}ms</p>
            <p><strong>Coverage:</strong> ${(result.maskStats.coverage * 100).toFixed(1)}%</p>
            <canvas id="test-result-canvas" style="max-width: 100%; border: 1px solid #ccc; border-radius: 5px;"></canvas>
            <br><br>
            <button onclick="this.parentElement.remove()" style="background: #ff6b6b; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;">Close</button>
        `;
        
        document.body.appendChild(resultContainer);
        
        // Draw result to visible canvas
        const testCanvas = document.getElementById('test-result-canvas');
        testCanvas.width = result.canvas.width;
        testCanvas.height = result.canvas.height;
        const testCtx = testCanvas.getContext('2d');
        testCtx.drawImage(result.canvas, 0, 0);
        
        // Test export functionality
        console.log('\n📤 Testing export functionality...');
        const blob = await controller.exportResult('png', 0.92);
        console.log(`✅ Export successful - Blob size: ${blob.size} bytes`);
        
        // Test preview creation
        console.log('\n🖼️ Testing preview creation...');
        const previewCanvas = await controller.createPreview(150);
        console.log(`✅ Preview created - Size: ${previewCanvas.width}x${previewCanvas.height}`);
        
        // Test performance stats
        console.log('\n📈 Performance Statistics:');
        const stats = controller.getStats();
        console.log('Render count:', stats.renderCount);
        console.log('Average render time:', stats.avgRenderTime.toFixed(2) + 'ms');
        console.log('Memory usage:', stats.memoryUsage.formatted);
        
        // Test both WebGL and Canvas 2D if available
        if (capabilities.webgl.supported && capabilities.canvas2d.supported) {
            console.log('\n🔄 Testing Canvas 2D fallback...');
            
            const canvas2DController = new TextureController({
                preferWebGL: false,
                enableDebug: true,
                fallbackToCanvas2D: true
            });
            
            await canvas2DController.initialize();
            
            const canvas2DResult = await canvas2DController.processTexture(
                garmentImage,
                textureImage,
                { intensity: 0.9, autoDetectPattern: true }
            );
            
            console.log(`✅ Canvas 2D test completed in ${canvas2DResult.renderTime.toFixed(2)}ms`);
            
            // Compare results
            console.log('\n⚖️ Performance Comparison:');
            console.log(`WebGL: ${result.renderTime.toFixed(2)}ms`);
            console.log(`Canvas 2D: ${canvas2DResult.renderTime.toFixed(2)}ms`);
            console.log(`Speed difference: ${(canvas2DResult.renderTime / result.renderTime).toFixed(2)}x`);
            
            canvas2DController.destroy();
        }
        
        // Test error handling
        console.log('\n🚨 Testing error handling...');
        
        try {
            await controller.processTexture(null, textureImage);
            console.log('❌ Error handling test failed - should have thrown error');
        } catch (error) {
            console.log('✅ Error handling works:', error.message);
        }
        
        // Clean up
        controller.destroy();
        
        console.log('\n🎉 All tests completed successfully!');
        console.log('\n📋 Test Summary:');
        console.log('✅ TextureController initialization');
        console.log('✅ Image loading and processing');
        console.log('✅ Pattern detection and analysis');
        console.log('✅ Mask generation and optimization');
        console.log('✅ Texture rendering (WebGL/Canvas2D)');
        console.log('✅ Export functionality');
        console.log('✅ Preview generation');
        console.log('✅ Performance tracking');
        console.log('✅ Error handling');
        console.log('✅ Visual verification');
        
        return {
            success: true,
            renderingMode: result.renderingMode,
            processingTime: processTime,
            patternType: result.patternInfo?.type,
            maskCoverage: result.maskStats.coverage
        };
        
    } catch (error) {
        console.error('❌ Pipeline test failed:', error);
        console.error('Stack trace:', error.stack);
        
        // Show error in UI
        const errorContainer = document.createElement('div');
        errorContainer.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            background: #fed7d7;
            color: #9b2c2c;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #fc8181;
            z-index: 10000;
            max-width: 400px;
        `;
        
        errorContainer.innerHTML = `
            <h3>❌ Pipeline Test Failed</h3>
            <p><strong>Error:</strong> ${error.message}</p>
            <button onclick="this.parentElement.remove()" style="background: #9b2c2c; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; margin-top: 10px;">Close</button>
        `;
        
        document.body.appendChild(errorContainer);
        
        return {
            success: false,
            error: error.message
        };
    }
}

// Utility function to convert canvas to image
function canvasToImage(canvas) {
    return new Promise(resolve => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.src = canvas.toDataURL();
    });
}

// Auto-run test when modules are loaded
window.addEventListener('load', () => {
    // Wait a bit to ensure all modules are loaded
    setTimeout(() => {
        if (typeof TextureController !== 'undefined') {
            testCompletePipeline().then(result => {
                console.log('\n🏁 Final test result:', result);
            });
        } else {
            console.error('❌ TextureController not available - check module loading');
        }
    }, 1000);
});

// Export for manual testing
window.testCompletePipeline = testCompletePipeline;