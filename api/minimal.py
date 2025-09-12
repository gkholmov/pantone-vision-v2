def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"status": "minimal handler working", "message": "Basic function without imports"}'
    }