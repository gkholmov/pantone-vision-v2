import os
import sys

# Absolute minimal test to see what's causing the crash
try:
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    @app.get("/api")
    @app.get("/api/test")
    async def test():
        return {
            "status": "working", 
            "message": "Minimal FastAPI is functioning",
            "python_version": sys.version,
            "environment_vars": {
                "SUPABASE_URL": bool(os.getenv('SUPABASE_URL')),
                "SUPABASE_ANON_KEY": bool(os.getenv('SUPABASE_ANON_KEY'))
            }
        }

    handler = app

except Exception as e:
    print(f"Minimal API creation failed: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a fallback that always works
    def handler(event, context):
        return {
            "statusCode": 200,
            "body": f"Fallback handler - Error: {str(e)}"
        }