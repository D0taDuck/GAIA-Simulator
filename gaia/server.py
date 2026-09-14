"""A loopback-only experiment monitor. The simulation also runs without a browser."""

import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import threading
from urllib.parse import urlparse

from .config import Config
from .engine import Simulation
from .storage import checkpoint, history_csv, render_report, restore

MAX_LIVE_TICKS = 100_000


class Controller:
    def __init__(self, sim):
        self.sim = sim
        self.running = False
        self.speed = 20
        self.ended = False
        self.error = None
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.work, name="Gaia-clock", daemon=True)
        self.thread.start()

    def work(self):
        while not self.stop.wait(0.1):
            with self.lock:
                if not self.running:
                    continue
                try:
                    ticks = min(max(1, self.speed // 10), MAX_LIVE_TICKS - self.sim.world.tick)
                    self.sim.step(ticks)
                    if self.sim.world.tick >= MAX_LIVE_TICKS:
                        self.running = False
                        self.error = "Live run reached 100,000 ticks. Export it and start a new experiment."
                except Exception as exc:
                    self.error = f"Simulation stopped: {exc}"
                    self.running = False

    def state(self):
        with self.lock:
            return dict(self.sim.snapshot(), running=self.running, ended=self.ended, speed=self.speed, error=self.error)

    def command(self, request):
        with self.lock:
            action = request.get("action")
            if action == "start":
                if self.ended:
                    raise ValueError("Run has ended; export it or create a new world")
                if self.sim.world.tick >= MAX_LIVE_TICKS:
                    raise ValueError("Live run tick limit reached")
                self.running = True
            elif action == "pause":
                self.running = False
            elif action == "step":
                if self.ended:
                    raise ValueError("Run has ended; export it or create a new world")
                count = request.get("ticks", 1)
                if type(count) is not int or not 1 <= count <= 1000:
                    raise ValueError("Step count must be between 1 and 1000")
                if self.sim.world.tick + count > MAX_LIVE_TICKS:
                    raise ValueError("Live run tick limit reached")
                self.running = False
                self.sim.step(count)
            elif action == "reset":
                config = Config.from_dict(request["config"])
                replacement = Simulation(config)
                self.sim, self.running, self.ended, self.error = replacement, False, False, None
            elif action == "restore":
                replacement = restore(request["checkpoint"])
                self.sim, self.running, self.ended, self.error = replacement, False, False, None
            elif action == "speed":
                speed = request.get("speed")
                if speed not in (10, 20, 50, 100, 200):
                    raise ValueError("Unsupported speed")
                self.speed = speed
            elif action == "schedule_event":
                if self.ended:
                    raise ValueError("Run has ended; create a new world to schedule events")
                self.sim.schedule_event(request.get("event"))
            elif action == "end":
                self.running, self.ended = False, True
                self.sim.log("Gaia", "Run ended by observer; CSV export unlocked")
            else:
                raise ValueError("Unknown command")
            return self.state()

    def close(self):
        self.stop.set()
        self.thread.join(timeout=5)


class GaiaServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, sim):
        super().__init__(address, Handler)
        self.controller = Controller(sim)
        self.token = secrets.token_urlsafe(32)

    def server_close(self):
        self.controller.close()
        super().server_close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, data, content_type="application/json", filename=None):
        if content_type == "application/json":
            data = json.dumps(data, allow_nan=False)
        encoded = data.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(encoded)

    def valid_host(self):
        port = self.server.server_address[1]
        if self.headers.get("Host") not in (f"127.0.0.1:{port}", f"localhost:{port}"):
            self.reply(403, {"error": "Local host required"})
            return False
        return True

    def do_GET(self):
        if not self.valid_host():
            return
        path = urlparse(self.path).path
        controller = self.server.controller
        if path == "/":
            template = (Path(__file__).parent / "monitor.html").read_text(encoding="utf-8")
            boot = json.dumps({"live": True, "token": self.server.token, "state": controller.state()}).replace("<", "\\u003c")
            self.reply(200, template.replace("__GAIA_BOOTSTRAP__", boot), "text/html")
        elif path == "/api/state":
            self.reply(200, controller.state())
        elif path.startswith("/api/export/"):
            with controller.lock:
                if path == "/api/export/checkpoint":
                    self.reply(200, checkpoint(controller.sim), filename="gaia-checkpoint.json")
                elif path == "/api/export/csv":
                    if not controller.ended:
                        self.reply(409, {"error": "End the run before exporting its CSV"})
                    else:
                        self.reply(200, history_csv(controller.sim), "text/csv", "gaia-history.csv")
                elif path == "/api/export/report":
                    self.reply(200, render_report(controller.sim), "text/html", "gaia-report.html")
                else:
                    self.reply(404, {"error": "Unknown export"})
        else:
            self.reply(404, {"error": "Not found"})

    def do_POST(self):
        if not self.valid_host():
            return
        if self.path != "/api/control":
            self.reply(404, {"error": "Not found"})
            return
        if not hmac.compare_digest(self.headers.get("X-Gaia-Token", ""), self.server.token):
            self.reply(403, {"error": "Invalid session token"})
            return
        origin = self.headers.get("Origin")
        if origin and origin != f'http://{self.headers.get("Host")}':
            self.reply(403, {"error": "Local origin required"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 32 * 1024 * 1024:
                raise ValueError("Request size must be between 1 byte and 32 MB")
            request = json.loads(self.rfile.read(length))
            if not isinstance(request, dict):
                raise ValueError("Expected a JSON object")
            self.reply(200, self.server.controller.command(request))
        except (ValueError, KeyError, TypeError) as exc:
            self.reply(400, {"error": str(exc)})


def serve(sim, port=8765, open_browser=True):
    import webbrowser
    with GaiaServer(("127.0.0.1", port), sim) as server:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        print(f"Gaia monitor: {url}\nCtrl+C stops the server. Export a checkpoint to keep your run.", flush=True)
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass
