#!/usr/bin/env python3
"""
Parali Mitra Universal Cross-Platform Launcher
Runs on Windows, macOS, and Linux out-of-the-box.
Automatically chooses between FastAPI/Uvicorn (if installed) or Python's built-in HTTP server.
Automatically opens your browser to the application.
"""
import sys
import os
import time
import webbrowser
import threading
import json

PORT = 8000
HOST = "127.0.0.1"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def check_dependencies():
    has_fastapi = False
    has_uvicorn = False
    try:
        import fastapi
        has_fastapi = True
    except ImportError:
        pass
    try:
        import uvicorn
        has_uvicorn = True
    except ImportError:
        pass
    return has_fastapi and has_uvicorn

def run_fastapi_server():
    print("=" * 60)
    print("🚀 Starting Parali Mitra on FastAPI + Uvicorn...")
    print(f"👉 Local URL: http://{HOST}:{PORT}")
    print(f"👉 Swagger API Docs: http://{HOST}:{PORT}/docs")
    print(f"👉 Interactive Web App: http://{HOST}:{PORT}/paralimitra_app.html")
    print("=" * 60)
    import uvicorn
    # Add direct resolution hook for 9p / cross-platform safety
    import importlib.util
    class DirectPathFinder:
        @classmethod
        def find_spec(cls, fullname, path=None, target=None):
            parts = fullname.split('.')
            rel_path = os.path.join(*parts)
            pkg_init = os.path.join(BASE_DIR, rel_path, '__init__.py')
            mod_py = os.path.join(BASE_DIR, rel_path + '.py')
            if os.path.exists(pkg_init):
                return importlib.util.spec_from_file_location(fullname, pkg_init, submodule_search_locations=[os.path.join(BASE_DIR, rel_path)])
            elif os.path.exists(mod_py):
                return importlib.util.spec_from_file_location(fullname, mod_py)
            return None
    if DirectPathFinder not in sys.meta_path:
        sys.meta_path.insert(0, DirectPathFinder)

    from backend.app.main import app
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")

def run_builtin_server():
    print("=" * 60)
    print("⚡ FastAPI not detected. Running Standalone Standard-Library HTTP Server...")
    print(f"👉 Running on any OS with pure Python standard library!")
    print(f"👉 Application URL: http://{HOST}:{PORT}/")
    print("=" * 60)
    from http.server import SimpleHTTPRequestHandler, HTTPServer

    app_html_path = os.path.join(BASE_DIR, "artifacts", "file_generation", "ttl=63d", "output", "kilnlink_app.html")
    if not os.path.exists(app_html_path):
        app_html_path = os.path.join(BASE_DIR, "kilnlink_app.html")

    class ParaliMitraHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html", "/paralimitra_app.html", "/app"):
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                if os.path.exists(app_html_path):
                    with open(app_html_path, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self.wfile.write(b"<h1>Parali Mitra is loading...</h1>")
                return
            elif self.path == "/health":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "app": "Parali Mitra", "version": "1.0.0"}).encode())
                return
            super().do_GET()

    server = HTTPServer((HOST, PORT), ParaliMitraHandler)
    server.serve_forever()

def open_browser():
    time.sleep(1.2)
    url = f"http://{HOST}:{PORT}/paralimitra_app.html" if check_dependencies() else f"http://{HOST}:{PORT}/"
    print(f"\n🌐 Opening default web browser to: {url}\n")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Notice: Open your browser and navigate to {url}")

if __name__ == "__main__":
    print(f"\n🌾 PARALI MITRA (पराली मित्र) — Universal Launcher")
    print(f"💻 Detected Operating System: {sys.platform.capitalize()} | Python {sys.version.split()[0]}")
    
    # Launch browser in a background thread
    threading.Thread(target=open_browser, daemon=True).start()

    if check_dependencies():
        run_fastapi_server()
    else:
        run_builtin_server()
