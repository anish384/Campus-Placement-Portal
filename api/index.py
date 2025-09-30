from flaskr import create_app
from flask import jsonify
import os

app = create_app()

# This is the Vercel serverless function handler
# The path is set to match all routes in vercel.json
# The actual routing is handled by Flask

def handler(event, context):
    from flask import request
    with app.app_context():
        from werkzeug.wrappers import Response
        from werkzeug.test import create_environ
        
        # Create a test environment for the request
        environ = create_environ(
            path=event.get('path', '/'),
            method=event.get('httpMethod', 'GET'),
            headers=event.get('headers', {}),
            query_string=event.get('queryStringParameters', {}),
            json=event.get('body'),
            content_type=event.get('headers', {}).get('content-type')
        )
        
        # Process the request
        with app.request_context(environ):
            try:
                response = app.full_dispatch_request()
                
                # Handle redirects
                if response.status_code in (301, 302, 303, 305, 307, 308):
                    return {
                        'statusCode': response.status_code,
                        'headers': {
                            'Location': response.headers.get('Location')
                        },
                        'body': ''
                    }
                
                # Return the response
                return {
                    'statusCode': response.status_code,
                    'headers': dict(response.headers),
                    'body': response.get_data(as_text=True)
                }
            except Exception as e:
                # Log the error
                app.logger.error(f"Error handling request: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': 'Internal Server Error'
                }

# For local development
if __name__ == '__main__':
    app.run(debug=True)
