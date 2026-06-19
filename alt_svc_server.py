"""TCP HTTPS bootstrap server - sends Alt-Svc header so Firefox upgrades to HTTP/3."""
import ssl, http.server

class AltSvcHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Alt-Svc", "h3=\":4433\"; ma=86400")
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Upgrading to HTTP/3...</h1><p>Refresh the page to use QUIC.</p></body></html>")

    def log_message(self, format, *args):
        print(f"[TCP] {args[0]}")

ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain("/tmp/quic_cert.pem", "/tmp/quic_key.pem")

server = http.server.HTTPServer(("0.0.0.0", 4433), AltSvcHandler)
server.socket = ctx.wrap_socket(server.socket, server_side=True)
print("TCP HTTPS bootstrap server on https://0.0.0.0:4433")
print("Serving Alt-Svc: h3=\":4433\"")
server.serve_forever()
