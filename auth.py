from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import json
import webbrowser
import os

SHOP = os.environ["SHOPIFY_SHOP"]
CLIENT_ID = os.environ["SHOPIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SHOPIFY_CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:3000/callback"
SCOPES = "read_products,write_products"
TOKEN_FILE = ".shopify_token"

auth_url = (
    f"https://{SHOP}/admin/oauth/authorize"
    f"?client_id={CLIENT_ID}"
    f"&scope={SCOPES}"
    f"&redirect_uri={REDIRECT_URI}"
)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/callback":
            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            if code:
                data = json.dumps({
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "code": code
                }).encode()
                req = urllib.request.Request(
                    f"https://{SHOP}/admin/oauth/access_token",
                    data=data,
                    headers={"Content-Type": "application/json"}
                )
                resp = urllib.request.urlopen(req)
                token_data = json.loads(resp.read())
                token = token_data["access_token"]
                with open(TOKEN_FILE, "w") as f:
                    f.write(token)
                print(f"\n✅ Token saved to {TOKEN_FILE}")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Token saved! You can close this window.")
            else:
                self.send_response(400)
                self.end_headers()
        self.server.running = False

    def log_message(self, *args):
        pass

print(f"Opening browser for authentication...")
webbrowser.open(auth_url)
server = HTTPServer(("localhost", 3000), Handler)
server.running = True
while server.running:
    server.handle_request()
