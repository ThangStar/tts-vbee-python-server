import eventlet
eventlet.monkey_patch()

from app import app, socketio
import os

if __name__ == '__main__':
    # Production configuration
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    
    print("========================================")
    print("    TTS CLIENT SERVER - PRODUCTION")
    print("========================================")
    print(f"Starting production server on {host}:{port}")
    print("Server accessible from:")
    print(f"- Localhost: http://127.0.0.1:{port}")
    print(f"- Network: http://192.168.10.5:{port}")
    print("")
    print("Socket.IO is enabled for real-time communication")
    print("Press Ctrl+C to stop the server")
    print("")
    
    # Run with Eventlet (supports Socket.IO)
    socketio.run(app, host=host, port=port, debug=False, use_reloader=False)
