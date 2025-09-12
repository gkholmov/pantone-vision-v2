#!/usr/bin/env python3
"""
Configuration module for Pantone Vision API
Handles environment variables and constants for serverless deployment
"""

import os
from typing import Optional

# Environment setup for serverless
def get_env_var(key: str, default: Optional[str] = None, required: bool = True) -> str:
    """Get environment variable with validation"""
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

# API Configuration
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
PROCESSING_TIMEOUT = 300  # 5 minutes (Vercel limit)

# API Keys (loaded from environment with fallbacks for import safety)
try:
    GEMINI_API_KEY = get_env_var("GEMINI_API_KEY")
    ANTHROPIC_API_KEY = get_env_var("ANTHROPIC_API_KEY") 
    HUGGINGFACE_API_KEY = get_env_var("HUGGINGFACE_API_KEY")
    SUPABASE_URL = get_env_var("SUPABASE_URL")
    SUPABASE_ANON_KEY = get_env_var("SUPABASE_ANON_KEY")
    REPLICATE_API_KEY = get_env_var("REPLICATE_API_KEY", required=False)
    STABILITY_API_KEY = get_env_var("STABILITY_API_KEY", required=False)
    SUPABASE_SERVICE_ROLE_KEY = get_env_var("SUPABASE_SERVICE_ROLE_KEY", required=False)
except ValueError as e:
    print(f"Warning: Config loading failed ({e}), using fallback values")
    # Fallback values for import safety
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "") 
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
    REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY", "")
    STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Application Settings
APP_VERSION = "2.0.0"
DEBUG = get_env_var("DEBUG", "false").lower() == "true"

# Image Processing Settings
MAX_IMAGE_SIZE = int(get_env_var("MAX_IMAGE_SIZE", "2048"))
DELTA_E_THRESHOLD = float(get_env_var("DELTA_E_THRESHOLD", "0.5"))
CONFIDENCE_THRESHOLD = float(get_env_var("CONFIDENCE_THRESHOLD", "0.97"))