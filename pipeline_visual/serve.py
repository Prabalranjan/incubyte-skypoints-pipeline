"""
Lightweight local HTTP development server for viewing the SkyPoints Visual Presentation.
Usage:
    python pipeline_visual/serve.py
    Then open http://localhost:8080 in your browser.
"""
import http.server
import socketserver
import webbrowser
from pathlib import Path

PORT = 8080
DIRECTORY = Path(__file__).resolve().parent


class VisualPresentationHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)


def serve():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), VisualPresentationHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 70)
        print("  SKYPOINTS PIPELINE VISUAL PRESENTATION SERVER")
        print("=" * 70)
        print(f"  * Serving directory: {DIRECTORY}")
        print(f"  * Server URL       : {url}")
        print("  * Press Ctrl+C to terminate.")
        print("=" * 70)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server gracefully.")


if __name__ == "__main__":
    serve()
