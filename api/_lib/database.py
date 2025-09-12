#!/usr/bin/env python3
"""
Database connection utilities for serverless deployment
Implements connection pooling and reuse patterns for Supabase
"""

import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY

# Global connection cache for serverless function reuse
_supabase_client: Optional[Client] = None
_connection_config = None

def get_supabase_client(use_service_role: bool = False) -> Client:
    """
    Get Supabase client with connection reuse for serverless
    """
    global _supabase_client, _connection_config
    
    # Determine which key to use
    api_key = SUPABASE_SERVICE_ROLE_KEY if use_service_role and SUPABASE_SERVICE_ROLE_KEY else SUPABASE_ANON_KEY
    
    # Create connection config for comparison
    current_config = {
        'url': SUPABASE_URL,
        'key': api_key,
        'service_role': use_service_role
    }
    
    # Reuse existing connection if config matches
    if _supabase_client and _connection_config == current_config:
        return _supabase_client
    
    # Create new client with optimized settings for serverless
    try:
        _supabase_client = create_client(
            SUPABASE_URL, 
            api_key,
            options={
                'schema': 'public',
                'headers': {
                    'apikey': api_key,
                    'authorization': f'Bearer {api_key}',
                    'prefer': 'return=minimal'  # Reduce response size
                },
                'auto_refresh_token': False,  # Disable in serverless
                'persist_session': False,     # Don't persist sessions
                'detect_session_in_url': False,  # Serverless optimization
                'headers': {
                    'x-client-info': 'pantone-vision-v2-serverless'
                }
            }
        )
        _connection_config = current_config
        return _supabase_client
        
    except Exception as e:
        print(f"Supabase connection error: {e}")
        raise ConnectionError(f"Failed to connect to Supabase: {str(e)}")

def store_processing_result(result_data: Dict[str, Any], 
                          result_type: str = 'general',
                          user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Store processing result in database with error handling
    """
    try:
        client = get_supabase_client()
        
        # Prepare data for storage
        record = {
            'result_type': result_type,
            'result_data': result_data,
            'user_id': user_id,
            'created_at': 'now()',
            'processing_version': '2.0.0'
        }
        
        # Insert with minimal return for performance
        result = client.table('processing_results').insert(record).execute()
        
        return {
            'success': True,
            'id': result.data[0]['id'] if result.data else None,
            'stored_at': record['created_at']
        }
        
    except Exception as e:
        # Don't fail the main process if storage fails
        print(f"Database storage error: {e}")
        return {
            'success': False,
            'error': str(e),
            'note': 'Processing succeeded but storage failed'
        }

def get_processing_history(user_id: Optional[str] = None, 
                          limit: int = 10) -> Dict[str, Any]:
    """
    Retrieve processing history with pagination
    """
    try:
        client = get_supabase_client()
        
        query = client.table('processing_results').select(
            'id, result_type, created_at, processing_version'
        ).order('created_at', desc=True).limit(limit)
        
        if user_id:
            query = query.eq('user_id', user_id)
        
        result = query.execute()
        
        return {
            'success': True,
            'history': result.data,
            'count': len(result.data)
        }
        
    except Exception as e:
        print(f"History retrieval error: {e}")
        return {
            'success': False,
            'error': str(e),
            'history': []
        }

def health_check() -> Dict[str, Any]:
    """
    Check database connection health
    """
    try:
        client = get_supabase_client()
        
        # Simple query to test connection
        result = client.rpc('check_connection').execute()
        
        return {
            'success': True,
            'status': 'connected',
            'timestamp': 'now()'
        }
        
    except Exception as e:
        return {
            'success': False,
            'status': 'disconnected', 
            'error': str(e)
        }

# Connection cleanup for end-of-function lifecycle
def cleanup_connections():
    """
    Clean up database connections - called at end of serverless function
    """
    global _supabase_client, _connection_config
    
    try:
        if _supabase_client:
            # Supabase client doesn't need explicit cleanup
            # but we can clear the cache
            _supabase_client = None
            _connection_config = None
    except Exception as e:
        print(f"Connection cleanup warning: {e}")