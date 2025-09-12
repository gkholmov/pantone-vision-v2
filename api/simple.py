def handler(request):
    """Ultra-simple Vercel handler"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": '{"message": "Simple handler working", "status": "success"}'
    }