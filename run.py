import os
from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_ENV") != "production"
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="127.0.0.1", port=port, debug=debug)
