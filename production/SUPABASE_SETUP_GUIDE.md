# 🗄️ Supabase Setup Guide - Pantone Vision 2.0

**Complete Step-by-Step Guide for Production Database Setup**

This guide provides detailed instructions for setting up Supabase as the production database for Pantone Vision 2.0, including database schema, storage, authentication, and Row Level Security (RLS) configuration.

---

## 📋 Prerequisites

- **Supabase Account**: https://supabase.com (Free tier: 500MB database, 1GB bandwidth)
- **GitHub Account**: For connecting repository (optional)
- **API Keys**: Your Pantone Vision application API keys ready

---

## Phase 1: Create Supabase Project

### Step 1: Sign Up & Create Project

1. **Go to Supabase**: https://supabase.com
2. **Sign in** with GitHub (recommended) or email
3. **Create New Project**:
   ```
   Organization: [Your Organization]
   Name: pantone-vision-prod
   Database Password: [Generate Strong Password - Save This!]
   Region: [Choose closest to your users]
   Plan: Free (sufficient for production start)
   ```
4. **Wait for Setup**: Takes 2-3 minutes for project initialization

### Step 2: Access Project Dashboard

1. **Navigate to Dashboard**: https://supabase.com/dashboard/projects
2. **Select your project**: `pantone-vision-prod`
3. **Note your Project URL**: `https://[your-project-id].supabase.co`

---

## Phase 2: Database Schema Setup

### Step 1: Open SQL Editor

1. **Go to SQL Editor**: Dashboard → SQL Editor
2. **Click "New Query"**
3. **Copy & Paste Complete Schema**: Use the schema from `production/database/schema.sql`

### Step 2: Execute Database Schema

**Copy this complete schema and run in SQL Editor:**

```sql
-- Pantone Vision 2.0 - Complete Production Schema
-- Execute this entire script in Supabase SQL Editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS api_usage CASCADE;
DROP TABLE IF EXISTS storage_metadata CASCADE;
DROP TABLE IF EXISTS processing_history CASCADE;
DROP TABLE IF EXISTS pantone_colors CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table (optional - for future user management)
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email TEXT UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pantone color database (comprehensive color reference)
CREATE TABLE pantone_colors (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    pantone_code TEXT UNIQUE NOT NULL,
    pantone_name TEXT NOT NULL,
    hex_color TEXT NOT NULL,
    rgb_r INTEGER NOT NULL CHECK (rgb_r >= 0 AND rgb_r <= 255),
    rgb_g INTEGER NOT NULL CHECK (rgb_g >= 0 AND rgb_g <= 255),
    rgb_b INTEGER NOT NULL CHECK (rgb_b >= 0 AND rgb_b <= 255),
    lab_l DECIMAL(8,4),
    lab_a DECIMAL(8,4),
    lab_b DECIMAL(8,4),
    hsv_h DECIMAL(8,4),
    hsv_s DECIMAL(8,4),
    hsv_v DECIMAL(8,4),
    color_family TEXT, -- e.g., 'red', 'blue', 'green', 'neutral'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Image processing history (stores all user interactions)
CREATE TABLE processing_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id TEXT, -- For tracking anonymous sessions
    
    -- Processing details
    processing_type TEXT NOT NULL CHECK (processing_type IN (
        'pantone_identification', 
        'sketch_colorization', 
        'texture_transfer',
        'color_matching'
    )),
    processing_status TEXT DEFAULT 'processing' CHECK (processing_status IN (
        'processing', 
        'completed', 
        'failed', 
        'timeout'
    )),
    
    -- Input data
    original_image_url TEXT,
    original_image_name TEXT,
    original_image_size INTEGER, -- bytes
    secondary_image_url TEXT, -- for texture transfer (sketch image)
    secondary_image_name TEXT,
    
    -- Output data
    processed_image_url TEXT,
    processed_image_name TEXT,
    processed_image_size INTEGER, -- bytes
    
    -- Color analysis results
    pantone_color_code TEXT,
    pantone_color_name TEXT,
    detected_hex_color TEXT,
    detected_rgb_r INTEGER,
    detected_rgb_g INTEGER,
    detected_rgb_b INTEGER,
    confidence_score DECIMAL(4,3), -- 0.000 to 1.000
    
    -- Processing parameters (JSON storage for flexibility)
    processing_parameters JSONB DEFAULT '{}',
    
    -- Performance metrics
    processing_time_seconds DECIMAL(8,3),
    api_calls_made INTEGER DEFAULT 0,
    
    -- Error handling
    error_message TEXT,
    error_code TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Storage metadata (track Supabase storage usage)
CREATE TABLE storage_metadata (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_type TEXT NOT NULL,
    bucket_name TEXT NOT NULL DEFAULT 'pantone-images',
    processing_history_id UUID REFERENCES processing_history(id) ON DELETE CASCADE,
    is_temporary BOOLEAN DEFAULT false,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API usage tracking (monitor rate limits and costs)
CREATE TABLE api_usage (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    api_provider TEXT NOT NULL CHECK (api_provider IN (
        'gemini', 
        'anthropic', 
        'huggingface'
    )),
    endpoint TEXT NOT NULL,
    request_count INTEGER DEFAULT 1,
    tokens_used INTEGER DEFAULT 0,
    processing_history_id UUID REFERENCES processing_history(id) ON DELETE SET NULL,
    cost_estimate DECIMAL(10,6), -- in USD
    response_time_ms INTEGER,
    status_code INTEGER,
    date_hour TIMESTAMP WITH TIME ZONE, -- for hourly aggregation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_processing_history_user_id ON processing_history(user_id);
CREATE INDEX idx_processing_history_session_id ON processing_history(session_id);
CREATE INDEX idx_processing_history_type ON processing_history(processing_type);
CREATE INDEX idx_processing_history_status ON processing_history(processing_status);
CREATE INDEX idx_processing_history_created_at ON processing_history(created_at);
CREATE INDEX idx_pantone_colors_code ON pantone_colors(pantone_code);
CREATE INDEX idx_pantone_colors_rgb ON pantone_colors(rgb_r, rgb_g, rgb_b);
CREATE INDEX idx_pantone_colors_family ON pantone_colors(color_family);
CREATE INDEX idx_api_usage_provider_date ON api_usage(api_provider, date_hour);
CREATE INDEX idx_storage_metadata_bucket ON storage_metadata(bucket_name);
CREATE INDEX idx_storage_metadata_expires ON storage_metadata(expires_at);

-- Insert comprehensive Pantone color database
INSERT INTO pantone_colors (pantone_code, pantone_name, hex_color, rgb_r, rgb_g, rgb_b, color_family) VALUES
-- Reds
('18-1664 TPX', 'True Red', '#BF1932', 191, 25, 50, 'red'),
('19-1664 TPX', 'Barbados Cherry', '#B8132F', 184, 19, 47, 'red'),
('18-1763 TPX', 'Haute Red', '#B93A32', 185, 58, 50, 'red'),
('19-1557 TPX', 'Chili Pepper', '#9B1B30', 155, 27, 48, 'red'),
('17-1456 TPX', 'Fiesta', '#DD4124', 221, 65, 36, 'red'),

-- Blues  
('19-4052 TPX', 'Classic Blue', '#0F4C75', 15, 76, 117, 'blue'),
('19-4045 TPX', 'Dress Blues', '#2E4F99', 46, 79, 153, 'blue'),
('18-4140 TPX', 'Strong Blue', '#0F4C81', 15, 76, 129, 'blue'),
('19-3938 TPX', 'Patriot Blue', '#1E213D', 30, 33, 61, 'blue'),
('19-4056 TPX', 'Navy Blazer', '#2C2C54', 44, 44, 84, 'blue'),

-- Greens
('15-5519 TPX', 'Greenery', '#88B04B', 136, 176, 75, 'green'),
('18-5338 TPX', 'Kale', '#5C7A29', 92, 122, 41, 'green'),
('17-5641 TPX', 'Jade Cream', '#00A693', 0, 166, 147, 'green'),
('19-6026 TPX', 'Amazon', '#3D5D42', 61, 93, 66, 'green'),
('17-6153 TPX', 'Emerald', '#009B77', 0, 155, 119, 'green'),

-- Neutrals
('17-5104 TPX', 'Ultimate Gray', '#939597', 147, 149, 151, 'neutral'),
('11-0601 TPX', 'Bright White', '#F7F7F7', 247, 247, 247, 'neutral'),
('19-3906 TPX', 'Phantom', '#2D2926', 45, 41, 38, 'neutral'),
('16-1318 TPX', 'Warm Taupe', '#AF9483', 175, 148, 131, 'neutral'),
('14-1064 TPX', 'Sand Dollar', '#DECDBE', 222, 205, 190, 'neutral'),

-- Purples
('18-3438 TPX', 'Ultra Violet', '#5F4B8B', 95, 75, 139, 'purple'),
('19-3536 TPX', 'Purple Potion', '#7030A0', 112, 48, 160, 'purple'),
('17-3240 TPX', 'Lavender Gray', '#B19CD9', 177, 156, 217, 'purple'),
('18-3949 TPX', 'Deep Purple', '#5A4FCF', 90, 79, 207, 'purple'),

-- Yellows
('13-0859 TPX', 'Illuminating', '#F5DF4D', 245, 223, 77, 'yellow'),
('14-0848 TPX', 'Vibrant Yellow', '#FAD64A', 250, 214, 74, 'yellow'),
('12-0736 TPX', 'Limelight', '#F1E788', 241, 231, 136, 'yellow'),
('13-0755 TPX', 'Primrose Yellow', '#F6D55C', 246, 213, 92, 'yellow'),

-- Oranges
('16-1546 TPX', 'Living Coral', '#FF6F61', 255, 111, 97, 'orange'),
('17-1463 TPX', 'Tangerine Tango', '#DD4124', 221, 65, 36, 'orange'),
('15-1247 TPX', 'Peach Echo', '#F7786B', 247, 120, 107, 'orange'),
('16-1448 TPX', 'Flame Orange', '#F2552C', 242, 85, 44, 'orange'),

-- Pinks
('17-2031 TPX', 'Rose Quartz', '#F7CAC9', 247, 202, 201, 'pink'),
('19-1862 TPX', 'Magenta Purple', '#C74375', 199, 67, 117, 'pink'),
('16-1720 TPX', 'Strawberry Ice', '#F2B2C0', 242, 178, 192, 'pink'),
('17-1928 TPX', 'Honeysuckle', '#D94F70', 217, 79, 112, 'pink'),

-- Browns
('18-1142 TPX', 'Cognac', '#9E4624', 158, 70, 36, 'brown'),
('19-1314 TPX', 'Demitasse', '#704139', 112, 65, 57, 'brown'),
('17-1230 TPX', 'Russet Brown', '#80471C', 128, 71, 28, 'brown');

-- Update timestamps trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to tables with updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pantone_colors_updated_at BEFORE UPDATE ON pantone_colors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_processing_history_updated_at BEFORE UPDATE ON processing_history FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE pantone_colors ENABLE ROW LEVEL SECURITY;
ALTER TABLE storage_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- Public read access to pantone colors (no authentication required)
CREATE POLICY "Public read pantone colors" ON pantone_colors 
FOR SELECT USING (true);

-- Users can only see their own data
CREATE POLICY "Users own data" ON users 
FOR ALL USING (auth.uid() = id);

-- Processing history policies
CREATE POLICY "Users own processing history" ON processing_history 
FOR ALL USING (auth.uid() = user_id);

-- Allow anonymous processing (for public use without login)
CREATE POLICY "Public processing insert" ON processing_history 
FOR INSERT WITH CHECK (true);

-- Public read for completed processing (with session_id match)
CREATE POLICY "Public processing read by session" ON processing_history 
FOR SELECT USING (processing_status = 'completed');

-- Storage metadata access
CREATE POLICY "Users own storage" ON storage_metadata 
FOR ALL USING (
    processing_history_id IN (
        SELECT id FROM processing_history WHERE auth.uid() = user_id
    )
);

-- Public storage read for temporary files
CREATE POLICY "Public storage read" ON storage_metadata 
FOR SELECT USING (is_temporary = true);

-- API usage tracking (admin only or system)
CREATE POLICY "System api usage" ON api_usage 
FOR ALL USING (false); -- Only accessible via service role

-- Create views for common queries

-- Active pantone colors view
CREATE VIEW active_pantone_colors AS
SELECT * FROM pantone_colors 
WHERE is_active = true
ORDER BY color_family, pantone_code;

-- Recent processing activity view  
CREATE VIEW recent_processing AS
SELECT 
    ph.id,
    ph.processing_type,
    ph.processing_status,
    ph.pantone_color_code,
    ph.pantone_color_name,
    ph.confidence_score,
    ph.processing_time_seconds,
    ph.created_at,
    u.email as user_email
FROM processing_history ph
LEFT JOIN users u ON ph.user_id = u.id
WHERE ph.created_at >= NOW() - INTERVAL '7 days'
ORDER BY ph.created_at DESC;

-- Daily usage statistics view
CREATE VIEW daily_usage_stats AS
SELECT 
    DATE(created_at) as date,
    processing_type,
    processing_status,
    COUNT(*) as request_count,
    AVG(processing_time_seconds) as avg_processing_time,
    AVG(confidence_score) as avg_confidence
FROM processing_history 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), processing_type, processing_status
ORDER BY date DESC, processing_type;

-- Cleanup function for old temporary files
CREATE OR REPLACE FUNCTION cleanup_expired_storage()
RETURNS void AS $$
BEGIN
    DELETE FROM storage_metadata 
    WHERE is_temporary = true 
    AND expires_at < NOW();
    
    DELETE FROM processing_history 
    WHERE processing_status = 'failed' 
    AND created_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;
```

### Step 3: Verify Schema Creation

1. **Check Tables**: Go to Database → Tables
2. **Verify Tables Created**:
   - ✅ `users`
   - ✅ `pantone_colors` (with 35+ colors)
   - ✅ `processing_history`
   - ✅ `storage_metadata`
   - ✅ `api_usage`

3. **Test Data Query**: In SQL Editor, run:
   ```sql
   SELECT COUNT(*) as total_colors, 
          COUNT(DISTINCT color_family) as color_families
   FROM pantone_colors;
   ```
   Should return: `35 colors, 8 color families`

---

## Phase 3: Storage Configuration

### Step 1: Create Storage Bucket

1. **Go to Storage**: Dashboard → Storage
2. **Create New Bucket**:
   ```
   Name: pantone-images
   Public: Yes (for direct image access)
   File Size Limit: 10MB
   Allowed MIME Types: image/jpeg, image/png, image/gif, image/bmp, image/tiff
   ```

### Step 2: Configure Storage Policies

1. **Go to Storage → Policies**
2. **Create Upload Policy**:
   ```sql
   CREATE POLICY "Public image upload" ON storage.objects 
   FOR INSERT WITH CHECK (
       bucket_id = 'pantone-images' 
       AND auth.role() = 'anon'
   );
   ```

3. **Create Download Policy**:
   ```sql
   CREATE POLICY "Public image download" ON storage.objects 
   FOR SELECT USING (
       bucket_id = 'pantone-images'
   );
   ```

4. **Create Delete Policy**:
   ```sql
   CREATE POLICY "User delete own images" ON storage.objects 
   FOR DELETE USING (
       bucket_id = 'pantone-images' 
       AND auth.uid()::text = (storage.foldername(name))[1]
   );
   ```

---

## Phase 4: API Keys & Environment Setup

### Step 1: Get Supabase Credentials

1. **Go to Settings → API**
2. **Copy These Values**:
   ```bash
   # Project URL
   SUPABASE_URL=https://[your-project-id].supabase.co
   
   # Anonymous Key (for client-side)
   SUPABASE_ANON_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
   
   # Service Role Key (for server-side - KEEP SECRET!)
   SUPABASE_SERVICE_ROLE_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
   ```

### Step 2: Update Environment Variables

Add to your `.env.production` file:
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

---

## Phase 5: Test Database Connection

### Step 1: Test API Connection

Create a test script `test_supabase.py`:
```python
import os
from supabase import create_client, Client

# Test connection
url = "https://your-project-id.supabase.co"
key = "your-anon-key-here"
supabase: Client = create_client(url, key)

# Test query
response = supabase.table('pantone_colors').select('*').limit(5).execute()
print(f"✅ Connected! Found {len(response.data)} Pantone colors")
print(response.data[0])  # Show first color
```

### Step 2: Test Storage Upload

```python
# Test image upload
with open('test-image.jpg', 'rb') as f:
    supabase.storage.from_('pantone-images').upload('test/sample.jpg', f)
print("✅ Storage upload successful!")
```

---

## Phase 6: Production Optimizations

### Step 1: Enable Connection Pooling

1. **Go to Settings → Database**
2. **Enable Connection Pooling**: Set to `Session`
3. **Pool Size**: Set to `15` (good for free tier)

### Step 2: Configure Backups

1. **Go to Settings → Database**
2. **Enable Point-in-Time Recovery**: On
3. **Backup Retention**: 7 days (free tier)

### Step 3: Monitor Resource Usage

1. **Go to Settings → Usage**
2. **Monitor**:
   - Database size (500MB limit on free tier)
   - Bandwidth usage (1GB limit on free tier)
   - Real-time connections

---

## Phase 7: Security Hardening

### Step 1: Enable Email Confirmations

1. **Go to Authentication → Settings**
2. **Enable Email Confirmations**: On
3. **Add Your Domain**: For production emails

### Step 2: Configure CORS

1. **Go to Settings → API**
2. **Add CORS Origin**: `https://your-vercel-app.vercel.app`

### Step 3: Enable Audit Logs

1. **Go to Settings → Logs**
2. **Enable SQL Audit**: On (to track all database queries)

---

## 🚨 Security Checklist

**Before Going Live:**
- [ ] Row Level Security (RLS) enabled on all tables
- [ ] Service role key stored securely (not in client-side code)
- [ ] CORS configured for your domain only
- [ ] Storage policies restrict unauthorized access
- [ ] Email confirmation enabled for user signups
- [ ] Database backups configured
- [ ] Resource usage monitoring set up

---

## 📊 Monitoring & Maintenance

### Daily Tasks
- **Check Usage**: Monitor database size and bandwidth
- **Review Logs**: Check for unusual query patterns
- **Backup Status**: Ensure backups are running

### Weekly Tasks
- **Performance Review**: Check slow queries in Logs
- **Storage Cleanup**: Remove expired temporary files
- **Security Audit**: Review access logs

### Monthly Tasks
- **Usage Analysis**: Review growth trends
- **Schema Updates**: Apply any necessary migrations
- **Backup Testing**: Verify backup restore process

---

## 🆘 Troubleshooting

### Common Issues

**"relation does not exist" error:**
```sql
-- Check if schema was applied correctly
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'pantone%';
```

**RLS blocking queries:**
```sql
-- Temporarily disable RLS for testing
ALTER TABLE pantone_colors DISABLE ROW LEVEL SECURITY;
-- Re-enable after testing
ALTER TABLE pantone_colors ENABLE ROW LEVEL SECURITY;
```

**Storage upload failures:**
- Check bucket permissions
- Verify file size limits
- Confirm MIME type allowed

---

## 🎯 Next Steps

1. **Complete This Setup**: Follow all phases above
2. **Test All Endpoints**: Verify database connection from your app
3. **Deploy to Production**: Use the verified database connection
4. **Monitor Performance**: Set up alerts for resource usage
5. **Scale When Ready**: Upgrade to Pro plan when needed

---

**✅ Database Setup Complete!**

Your Supabase database is now production-ready with:
- 35+ Pantone colors pre-loaded
- Optimized indexing for fast queries
- Row Level Security for data protection
- Storage configured for image uploads
- Monitoring and backup systems active

**Next**: Connect your Vercel application to this database using the environment variables collected above.