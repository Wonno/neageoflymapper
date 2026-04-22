"""Bookmarklet Installation Webserver

This module provides a minimal HTTP server to serve a local HTML page
for installing a browser bookmarklet. It opens a browser window to the
setup page and shuts down automatically when the user completes the process.
"""

import pathlib
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from app_console import console

# Read the HTML content to be served from the 'index.html' file located in the same directory as this script.
HTML = pathlib.Path(__file__).with_name("index.html").read_text(encoding="utf-8")

class Handler(BaseHTTPRequestHandler):
    """
    HTTP request handler for serving the bookmarklet installer page.

    - Serves the HTML page for any GET request except '/done'.
    - On GET '/done', responds and triggers server shutdown.
    - Suppresses default request logging.
    """

    # pylint: disable=C0103
    def do_GET(self):
        """
        Handle GET requests.

        - If the path is '/done', respond with 200 OK and shut down the server.
        - Otherwise, serve the static HTML content.
        """
        if self.path == "/done":
            self.send_response(200)
            self.end_headers()
            # Schedule server shutdown after a short delay to allow response to complete.
            threading.Timer(0.1, self.server.shutdown).start()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def log_message(self, format, *args):
        """
        Override to suppress default HTTP request logging.
        """


def get_free_port():
    """
    Find and return a free TCP port on localhost.

    Returns:
        int: An available port number.
    """
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def webserver():
    """
    Start the bookmarklet setup webserver.

    - Binds to a free local port.
    - Serves the HTML installer page.
    - Opens the default web browser to the setup page.
    - Shuts down automatically when the user completes the setup.
    """
    port = get_free_port()
    server = HTTPServer(("localhost", port), Handler)
    url = f"http://localhost:{port}"
    console.print("Starting webserver on http://localhost:{port} for manual Bookmarklet setup...")
    # Open the browser after a short delay to ensure the server is ready.
    threading.Timer(0.1, lambda: webbrowser.open(url)).start()
    server.serve_forever()
