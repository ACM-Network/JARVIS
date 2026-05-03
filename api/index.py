def app(request):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/plain"
        },
        "body": "Jarvis backend running successfully 🚀"
    }
