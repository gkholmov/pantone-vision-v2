#!/usr/bin/env python3
"""
Main entry point for Vercel Python runtime
This file is required by some Vercel configurations
"""

# Import the actual handlers
from pantone import handler as pantone_handler
from texture import handler as texture_handler
from gemini import handler as gemini_handler
from app import handler as app_handler
from health import handler as health_handler

# Export handlers for Vercel to use
__all__ = [
    'pantone_handler',
    'texture_handler', 
    'gemini_handler',
    'app_handler',
    'health_handler'
]

# Default handler
handler = app_handler