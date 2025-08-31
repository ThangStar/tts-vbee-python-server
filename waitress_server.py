from waitress import serve
from app import app, socketio
import os

if __name__ == '__main__':
    # Production configuration
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting production server on {host}:{port}")
    print("Server accessible from:")
    print(f"- Localhost: http://127.0.0.1:{port}")
    print(f"- Network: http://YOUR_IP:{port}")
    
    # Run with Waitress (Windows-compatible WSGI server)
    serve(app, host=host, port=port, threads=4)
