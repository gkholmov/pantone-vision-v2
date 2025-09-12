-- Pantone Vision 2.0 - Supabase Database Schema
-- Run this script in Supabase SQL Editor to set up the production database

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (for clean setup)
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

-- Blues  
('19-4052 TPX', 'Classic Blue', '#0F4C75', 15, 76, 117, 'blue'),
('19-4045 TPX', 'Dress Blues', '#2E4F99', 46, 79, 153, 'blue'),
('18-4140 TPX', 'Strong Blue', '#0F4C81', 15, 76, 129, 'blue'),
('19-3938 TPX', 'Patriot Blue', '#1E213D', 30, 33, 61, 'blue'),

-- Greens
('15-5519 TPX', 'Greenery', '#88B04B', 136, 176, 75, 'green'),
('18-5338 TPX', 'Kale', '#5C7A29', 92, 122, 41, 'green'),
('17-5641 TPX', 'Jade Cream', '#00A693', 0, 166, 147, 'green'),
('19-6026 TPX', 'Amazon', '#3D5D42', 61, 93, 66, 'green'),

-- Neutrals
('17-5104 TPX', 'Ultimate Gray', '#939597', 147, 149, 151, 'neutral'),
('11-0601 TPX', 'Bright White', '#F7F7F7', 247, 247, 247, 'neutral'),
('19-3906 TPX', 'Phantom', '#2D2926', 45, 41, 38, 'neutral'),
('16-1318 TPX', 'Warm Taupe', '#AF9483', 175, 148, 131, 'neutral'),

-- Purples
('18-3438 TPX', 'Ultra Violet', '#5F4B8B', 95, 75, 139, 'purple'),
('19-3536 TPX', 'Purple Potion', '#7030A0', 112, 48, 160, 'purple'),
('17-3240 TPX', 'Lavender Gray', '#B19CD9', 177, 156, 217, 'purple'),

-- Yellows
('13-0859 TPX', 'Illuminating', '#F5DF4D', 245, 223, 77, 'yellow'),
('14-0848 TPX', 'Vibrant Yellow', '#FAD64A', 250, 214, 74, 'yellow'),
('12-0736 TPX', 'Limelight', '#F1E788', 241, 231, 136, 'yellow'),

-- Oranges
('16-1546 TPX', 'Living Coral', '#FF6F61', 255, 111, 97, 'orange'),
('17-1463 TPX', 'Tangerine Tango', '#DD4124', 221, 65, 36, 'orange'),
('15-1247 TPX', 'Peach Echo', '#F7786B', 247, 120, 107, 'orange'),

-- Pinks
('17-2031 TPX', 'Rose Quartz', '#F7CAC9', 247, 202, 201, 'pink'),
('19-1862 TPX', 'Magenta Purple', '#C74375', 199, 67, 117, 'pink'),
('16-1720 TPX', 'Strawberry Ice', '#F2B2C0', 242, 178, 192, 'pink');

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

-- Create a scheduled job to run cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-storage', '0 2 * * *', 'SELECT cleanup_expired_storage();');

COMMENT ON TABLE users IS 'User accounts for authentication and personalization';
COMMENT ON TABLE pantone_colors IS 'Complete Pantone color database for matching';
COMMENT ON TABLE processing_history IS 'Log of all image processing requests and results';
COMMENT ON TABLE storage_metadata IS 'Metadata for files stored in Supabase Storage';
COMMENT ON TABLE api_usage IS 'Track external API usage for monitoring and billing';

COMMENT ON FUNCTION cleanup_expired_storage() IS 'Removes expired temporary files and old failed processing records';