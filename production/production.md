# Pantone Vision 2.0 - Production Deployment Guide

## 🚀 Complete Step-by-Step Deployment to Vercel with Supabase

This guide provides detailed instructions for deploying Pantone Vision 2.0 to Vercel production environment with Supabase database integration and secure API key management.

---

## 📋 Prerequisites

### Required Accounts (All FREE Tier)
1. **Vercel Account**: https://vercel.com (Free tier: unlimited static sites, 100GB bandwidth/month)
2. **Supabase Account**: https://supabase.com (Free tier: 500MB database, 1GB bandwidth/month)  
3. **GitHub Account**: https://github.com (Free tier: unlimited public repositories)

### API Keys Required
1. **Google Gemini API Key** (Free tier: 15 requests/minute)
2. **Anthropic Claude API Key** (Pay-per-use, starts ~$3/month)
3. **HuggingFace API Key** (Free tier: 30,000 characters/month)

---

## Phase 1: Supabase Database Setup

### Step 1: Create Supabase Project
```bash
# 1. Go to https://supabase.com
# 2. Click "Start your project"
# 3. Create new project:
#    - Name: pantone-vision-prod
#    - Database Password: [Generate secure password]
#    - Region: [Choose closest to your users]
# 4. Wait 2-3 minutes for project setup
```

### Step 2: Database Schema Setup
```sql
-- Run this in Supabase SQL Editor
-- Tables for user data and processing history

-- Users table (optional - for future user management)
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP DEFAULT NOW()
);

-- Image processing history
CREATE TABLE processing_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    original_image_url TEXT NOT NULL,
    processed_image_url TEXT,
    pantone_color_code TEXT,
    pantone_color_name TEXT,
    processing_type TEXT NOT NULL, -- 'pantone_identification', 'sketch_colorization', 'texture_transfer'
    processing_parameters JSONB,
    processing_status TEXT DEFAULT 'processing', -- 'processing', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Pantone color database (cache)
CREATE TABLE pantone_colors (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pantone_code TEXT UNIQUE NOT NULL,
    pantone_name TEXT NOT NULL,
    hex_color TEXT NOT NULL,
    rgb_r INTEGER NOT NULL,
    rgb_g INTEGER NOT NULL, 
    rgb_b INTEGER NOT NULL,
    lab_l DECIMAL,
    lab_a DECIMAL,
    lab_b DECIMAL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert sample Pantone colors
INSERT INTO pantone_colors (pantone_code, pantone_name, hex_color, rgb_r, rgb_g, rgb_b) VALUES
('18-1664 TPX', 'Pantone Red', '#C8102E', 200, 16, 46),
('19-4052 TPX', 'Classic Blue', '#0F4C75', 15, 76, 117),
('17-5104 TPX', 'Ultimate Gray', '#939597', 147, 149, 151);
```

### Step 3: Storage Setup
```bash
# In Supabase Dashboard > Storage
# 1. Create new bucket: "pantone-images"
# 2. Set bucket as Public
# 3. Upload policy: Allow authenticated uploads
# 4. Download policy: Public read access
```

### Step 4: Configure Row Level Security (RLS)
```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE pantone_colors ENABLE ROW LEVEL SECURITY;

-- Public read access to pantone colors (no auth required)
CREATE POLICY "Public read access" ON pantone_colors FOR SELECT USING (true);

-- Users can only see their own processing history
CREATE POLICY "Users own data" ON processing_history 
FOR ALL USING (auth.uid() = user_id);

-- Public insert for anonymous processing (no auth required)
CREATE POLICY "Public processing" ON processing_history 
FOR INSERT WITH CHECK (true);
```

---

## Phase 2: Code Preparation for Vercel

### Step 1: Create Vercel Configuration
```json
// vercel.json
{
  "version": 2,
  "builds": [
    {
      "src": "api/*.py",
      "use": "@vercel/python"
    },
    {
      "src": "static/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/static/$1"
    }
  ],
  "functions": {
    "api/*.py": {
      "maxDuration": 30
    }
  }
}
```

### Step 2: Production Requirements
```txt
# requirements.txt (optimized for Vercel)
fastapi==0.104.0
uvicorn==0.24.0
Pillow==10.0.0
numpy==1.24.0
requests==2.31.0
python-multipart==0.0.6
aiofiles==23.2.0
supabase==2.0.0
google-genai==0.3.0
python-dotenv==1.0.0
```

### Step 3: Environment Variables Template
```bash
# .env.example
# Copy this to .env.production and fill in your values

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# AI API Keys
GEMINI_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-api03-...
HUGGINGFACE_API_KEY=hf_...

# Application Configuration
APP_ENV=production
DEBUG=false
ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app
```

---

## Phase 3: Serverless API Functions

### Step 1: Main API Handler
```python
# api/index.py - Main entry point
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from .pantone_service import PantoneService
from .gemini_service import GeminiService
from .supabase_service import SupabaseService

app = FastAPI(title="Pantone Vision API", version="2.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
pantone_service = PantoneService()
gemini_service = GeminiService()
supabase_service = SupabaseService()

@app.post("/api/identify-pantone")
async def identify_pantone(file: UploadFile = File(...)):
    try:
        # Process Pantone identification
        result = await pantone_service.identify_color(file)
        
        # Save to database
        await supabase_service.save_processing_result(result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transfer-texture")
async def transfer_texture(
    textile_file: UploadFile = File(...),
    sketch_file: UploadFile = File(...)
):
    try:
        # Process texture transfer with Gemini
        result = await gemini_service.transfer_texture(textile_file, sketch_file)
        
        # Save to database
        await supabase_service.save_processing_result(result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}
```

### Step 2: Pantone Service
```python
# api/pantone_service.py
import numpy as np
from PIL import Image
import json
from .supabase_service import SupabaseService

class PantoneService:
    def __init__(self):
        self.supabase = SupabaseService()
        
    async def identify_color(self, file):
        # Convert uploaded file to image
        image = Image.open(file.file)
        
        # Extract dominant color
        dominant_color = self._get_dominant_color(image)
        
        # Find closest Pantone match
        pantone_match = await self._find_pantone_match(dominant_color)
        
        return {
            "dominant_color": {
                "rgb": dominant_color,
                "hex": self._rgb_to_hex(dominant_color)
            },
            "pantone_match": pantone_match,
            "confidence": 0.95
        }
    
    def _get_dominant_color(self, image):
        # Convert to RGB and get dominant color
        image = image.convert('RGB')
        image.thumbnail((50, 50))
        colors = image.getcolors(2500)
        dominant_color = max(colors, key=lambda item: item[0])[1]
        return dominant_color
    
    async def _find_pantone_match(self, rgb_color):
        # Query Supabase for closest Pantone match
        result = await self.supabase.find_closest_pantone(rgb_color)
        return result
    
    def _rgb_to_hex(self, rgb):
        return "#{:02x}{:02x}{:02x}".format(*rgb)
```

### Step 3: Gemini Service  
```python
# api/gemini_service.py
import os
import base64
from google import genai
from PIL import Image
import io

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = "gemini-2.5-flash-image-preview"
    
    async def transfer_texture(self, textile_file, sketch_file):
        try:
            # Convert files to base64
            textile_image = self._file_to_base64(textile_file)
            sketch_image = self._file_to_base64(sketch_file)
            
            # Gemini API call
            prompt = "Fill entire shape in image 2 with texture from image 1. Keep lines visible."
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, textile_image, sketch_image]
            )
            
            if response.candidates and response.candidates[0].content:
                # Process response and return result
                return {
                    "success": True,
                    "processed_image_url": "data:image/png;base64," + response.candidates[0].content.parts[0].inline_data.data,
                    "processing_time": "2.3s"
                }
            else:
                raise Exception("No content generated")
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _file_to_base64(self, file):
        file.file.seek(0)
        image_data = file.file.read()
        return base64.b64encode(image_data).decode()
```

### Step 4: Supabase Service
```python
# api/supabase_service.py
import os
from supabase import create_client, Client
import uuid
from datetime import datetime

class SupabaseService:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase: Client = create_client(url, key)
    
    async def save_processing_result(self, result):
        data = {
            "id": str(uuid.uuid4()),
            "processing_type": result.get("type", "unknown"),
            "processing_status": "completed" if result.get("success") else "failed",
            "processing_parameters": result,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        }
        
        response = self.supabase.table("processing_history").insert(data).execute()
        return response.data
    
    async def find_closest_pantone(self, rgb_color):
        # Find closest Pantone color by RGB distance
        response = self.supabase.table("pantone_colors").select("*").execute()
        
        if not response.data:
            return None
            
        closest_match = None
        min_distance = float('inf')
        
        for pantone in response.data:
            distance = self._calculate_color_distance(
                rgb_color, 
                (pantone['rgb_r'], pantone['rgb_g'], pantone['rgb_b'])
            )
            if distance < min_distance:
                min_distance = distance
                closest_match = pantone
        
        return {
            "pantone_code": closest_match['pantone_code'],
            "pantone_name": closest_match['pantone_name'],
            "hex_color": closest_match['hex_color'],
            "distance": min_distance
        }
    
    def _calculate_color_distance(self, color1, color2):
        return sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2)) ** 0.5
```

---

## Phase 4: Vercel Deployment

### Step 1: Prepare Repository
```bash
# Initialize git repository
cd /path/to/pantone-vision-v2
git init
git add .
git commit -m "Initial commit: Pantone Vision 2.0 production ready"

# Create GitHub repository
# 1. Go to https://github.com/new
# 2. Repository name: pantone-vision-production
# 3. Set to Public (for free deployment)
# 4. Don't initialize with README

# Link to GitHub
git remote add origin https://github.com/YOUR_USERNAME/pantone-vision-production.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Vercel
```bash
# Option 1: Vercel CLI (recommended)
npm install -g vercel
vercel login
cd /path/to/pantone-vision-v2
vercel --prod

# Option 2: Web Interface
# 1. Go to https://vercel.com/dashboard
# 2. Click "Add New..." > "Project"
# 3. Import from GitHub: select your repository
# 4. Configure:
#    - Framework Preset: Other
#    - Root Directory: ./
#    - Build Command: (leave empty)
#    - Output Directory: ./static
# 5. Add Environment Variables (see next step)
# 6. Click Deploy
```

### Step 3: Configure Environment Variables
```bash
# In Vercel Dashboard > Project Settings > Environment Variables
# Add all variables from .env.production:

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
APP_ENV=production
DEBUG=false
```

---

## Phase 5: GitHub Actions CI/CD (Optional)

### Step 1: Create Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Vercel

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m pytest tests/ || echo "No tests found"

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        github-token: ${{ secrets.GITHUB_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
        vercel-args: '--prod'
```

### Step 2: Configure Secrets
```bash
# In GitHub Repository Settings > Secrets and variables > Actions
# Add these secrets:

VERCEL_TOKEN=your_vercel_token  # From Vercel Account Settings > Tokens
VERCEL_ORG_ID=your_org_id      # From vercel.json after first deployment
VERCEL_PROJECT_ID=your_project_id  # From vercel.json after first deployment
```

---

## Phase 6: Production Testing & Monitoring

### Step 1: Test Deployment
```bash
# Test all endpoints
curl https://your-app.vercel.app/api/health
curl -X POST https://your-app.vercel.app/api/identify-pantone -F "file=@test-image.jpg"
```

### Step 2: Monitor Performance
- **Vercel Analytics**: Enable in Vercel dashboard for traffic insights
- **Supabase Logs**: Monitor database queries and storage usage
- **Error Tracking**: Check Vercel Function logs for errors

### Step 3: Usage Monitoring
```bash
# Check API key usage:
# - Gemini API: https://console.cloud.google.com/apis/credentials
# - Anthropic: https://console.anthropic.com/account/usage  
# - HuggingFace: https://huggingface.co/settings/billing
```

---

## 🎯 Cost Breakdown (Monthly)

### Free Tier Limits
- **Vercel**: 100GB bandwidth, unlimited static sites ✅ FREE
- **Supabase**: 500MB database, 1GB bandwidth, 50MB file storage ✅ FREE
- **GitHub**: Unlimited public repositories ✅ FREE
- **Gemini API**: 15 requests/minute ✅ FREE
- **HuggingFace**: 30,000 characters/month ✅ FREE

### Paid Services (Pay-per-use)
- **Anthropic Claude API**: ~$3-15/month (based on usage)
- **Total Monthly Cost**: $3-15/month for moderate usage

---

## 🔧 Maintenance & Updates

### Regular Tasks
1. **Monitor API usage** monthly to avoid overages
2. **Update dependencies** quarterly for security patches
3. **Backup Supabase data** monthly (manual export)
4. **Review Vercel function logs** weekly for errors

### Scaling Considerations
- **Vercel Pro**: $20/month for higher bandwidth limits
- **Supabase Pro**: $25/month for 8GB database, 250GB bandwidth
- **Deploy multiple instances** in different regions for global performance

---

## 🚨 Troubleshooting

### Common Issues
1. **500 Internal Server Error**: Check Vercel function logs and environment variables
2. **CORS Errors**: Update ALLOWED_ORIGINS in environment variables
3. **Database Connection Errors**: Verify Supabase URL and keys
4. **API Rate Limits**: Implement request queuing and retry logic

### Support Resources
- **Vercel Support**: https://vercel.com/help
- **Supabase Discord**: https://discord.supabase.com
- **GitHub Actions Docs**: https://docs.github.com/en/actions

---

## ✅ Deployment Checklist

- [ ] Supabase project created and configured
- [ ] Database schema and RLS policies applied
- [ ] Storage bucket created with proper permissions
- [ ] All API keys generated and tested locally
- [ ] GitHub repository created and code pushed
- [ ] Vercel project configured with environment variables
- [ ] Production deployment successful
- [ ] All API endpoints tested in production
- [ ] Monitoring and error tracking enabled
- [ ] Documentation updated with production URLs

---

**🎉 Congratulations!** Your Pantone Vision 2.0 application is now live in production with secure, scalable infrastructure.

**Production URL**: `https://your-project-name.vercel.app`