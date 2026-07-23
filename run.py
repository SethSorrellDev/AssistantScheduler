from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    # socketio.run replaces app.run — eventlet handles persistent connections.
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
