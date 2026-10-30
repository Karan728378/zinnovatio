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

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

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
    print("Starting Parali Mitra on FastAPI + Uvicorn...")
    print(f"Local URL: http://{HOST}:{PORT}")
    print(f"Swagger API Docs: http://{HOST}:{PORT}/docs")
    print(f"Interactive Web App: http://{HOST}:{PORT}/paralimitra_app.html")
    print("=" * 60)
    import uvicorn
    # Add direct resolution hook for cross-platform safety
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
    print("WARNING: FastAPI not detected. API disabled; install requirements (pip install -r requirements.txt)")
    print("Running Standalone Standard-Library HTTP Fallback Server...")
    print(f"Application URL: http://{HOST}:{PORT}/")
    print("=" * 60)
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    import mimetypes

    candidate_files = [
        os.path.join(BASE_DIR, "paralimitra_app.html"),
        os.path.join(BASE_DIR, "index.html"),
        os.path.join(BASE_DIR, "frontend", "index.html"),
        os.path.join(BASE_DIR, "artifacts", "file_generation", "ttl=63d", "output", "kilnlink_app.html"),
        os.path.join(BASE_DIR, "kilnlink_app.html")
    ]
    app_html_path = None
    for cand in candidate_files:
        if os.path.exists(cand):
            app_html_path = cand
            break

    static_allow_dir = os.path.join(BASE_DIR, "frontend", "public")

    class ParaliMitraHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            clean_path = self.path.split("?")[0].split("#")[0]
            if clean_path in ("/", "/index.html", "/paralimitra_app.html", "/app"):
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                if app_html_path and os.path.exists(app_html_path):
                    with open(app_html_path, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self.wfile.write(b"<h1>Parali Mitra is loading...</h1>")
                return
            elif clean_path == "/health":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "app": "Parali Mitra", "version": "1.0.0"}).encode())
                return
            elif clean_path.startswith("/static/") and os.path.exists(static_allow_dir):
                rel_sub = clean_path[len("/static/"):].lstrip("/\\")
                target_file = os.path.abspath(os.path.join(static_allow_dir, rel_sub))
                if target_file.startswith(static_allow_dir) and os.path.isfile(target_file):
                    mime, _ = mimetypes.guess_type(target_file)
                    self.send_response(200)
                    self.send_header("Content-type", mime or "application/octet-stream")
                    self.end_headers()
                    with open(target_file, "rb") as f:
                        self.wfile.write(f.read())
                    return

            # Explicit 404 for all other paths - never serve repo root
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"detail": "Not Found"}).encode())

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
