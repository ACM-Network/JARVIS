def app(request):
    try:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/plain"
            },
            "body": "Jarvis backend is alive 🚀"
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": str(e)
        }
