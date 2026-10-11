"""
DeskDriver - The Wikipedia of Desktop Automation & UI Roadmaps
Interactive encyclopedic knowledge base served locally at http://localhost:8765
Run: .\\.venv\\Scripts\\python dashboard.py
"""

import sys
import json
import webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime

# Add src to python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import deskdriver as am
from deskdriver.navigation.fastpaths import FASTPATHS
from deskdriver.core.keyboard import COMMON_HOTKEYS
from deskdriver.navigation.history import load_scan_logs, record_scan_log

PORT = 8765

# The page itself lives in web/ (index.html, style.css, app.js)
WEB_DIR = Path(__file__).parent / "web"
STATIC_FILES = {
    "/static/style.css": ("style.css", "text/css; charset=utf-8"),
    "/static/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class DashboardHandler(BaseHTTPRequestHandler):
    """
    Local JSON API behind the dashboard page. Each route returns a JSON-serializable
    object; errors become JSON {"error": ...} responses instead of dropped connections.
    """

    MAX_BODY_BYTES = 1_000_000

    # ------------------------------------------------------------------ plumbing

    def _is_trusted_request(self) -> bool:
        """
        Only serve the dashboard's own page. The API types text, launches programs and runs
        pipelines, so a web page in the browser must not be able to call it:
        - Host must be localhost / 127.0.0.1 on our port (blocks DNS-rebinding).
        - Origin, when a browser sends one, must be that same host (blocks cross-site POSTs).
        """
        port = self.server.server_address[1]
        allowed_hosts = {f"localhost:{port}", f"127.0.0.1:{port}"}
        if self.headers.get("Host", "") not in allowed_hosts:
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin in {f"http://{h}" for h in allowed_hosts}

    def _send(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, obj, status: int = 200):
        self._send(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _read_json_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        if length > self.MAX_BODY_BYTES:
            raise ValueError("request body too large")
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("request body is not valid JSON")
        if not isinstance(data, dict):
            raise ValueError("request body must be a JSON object")
        return data

    def _dispatch(self, routes: dict, get_arg):
        """Run the route for this path. get_arg supplies its argument (parsed URL or JSON body)."""
        if not self._is_trusted_request():
            return self._send(403, b"Forbidden: cross-origin requests are not allowed", "text/plain; charset=utf-8")
        path = urlparse(self.path).path.rstrip("/")
        handler = routes.get(path)
        if handler is None:
            return self._send_json({"error": f"unknown endpoint {path or '/'}"}, 404)
        try:
            result = handler(self, get_arg())
        except ValueError as e:
            return self._send_json({"error": str(e)}, 400)
        except Exception as e:
            return self._send_json({"error": f"{type(e).__name__}: {e}"}, 500)
        if result is not None:
            self._send_json(result, 400 if isinstance(result, dict) and "error" in result else 200)

    def do_GET(self):
        self._dispatch(GET_ROUTES, lambda: urlparse(self.path))

    def do_POST(self):
        self._dispatch(POST_ROUTES, self._read_json_body)

    def log_message(self, format, *args):
        pass

    # ------------------------------------------------------------------ GET routes

    def get_index(self, parsed):
        self._send(200, (WEB_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")

    def get_static(self, parsed):
        # Only the files listed in STATIC_FILES are served, so no path can escape web/
        name, content_type = STATIC_FILES[urlparse(self.path).path]
        self._send(200, (WEB_DIR / name).read_bytes(), content_type)

    def get_stats(self, parsed):
        roadmap_data = am.roadmap.reload()
        current_logs = load_scan_logs()
        return {
            "version": getattr(am, "__version__", "0.2.0"),
            "total_apps": len(roadmap_data),
            "total_elements": sum(len(app.get("elements", {})) for app in roadmap_data.values()),
            "total_actions": len(am.load_saved_actions()),
            "common_hotkeys": COMMON_HOTKEYS,
            "fastpaths": FASTPATHS,
            "roadmap": roadmap_data,
            "storage_files": {k: f"ui_roadmap/{am.roadmap.app_file(k).name}" for k in roadmap_data},
            "timestamp": datetime.now().isoformat(),
            "last_scan": current_logs[0] if current_logs else None,
            "total_scans": len(current_logs),
        }

    def get_actions(self, parsed):
        return {"actions": am.load_saved_actions()}

    def get_app_tree(self, parsed):
        query = parse_qs(parsed.query).get("app", [""])[0]
        return am.build_application_tree(query)

    def get_logs(self, parsed):
        current_logs = load_scan_logs()
        return {
            "logs": current_logs,
            "last_scan": current_logs[0] if current_logs else None,
            "total_scans": len(current_logs),
        }

    def get_record_status(self, parsed):
        return am.get_recording_status()

    # ------------------------------------------------------------------ POST routes

    def post_prelearn(self, req):
        res = am.run_system_prelearn()
        apps = res.get("scanned_apps", [])
        total_cnt = res.get("total_elements", 0)
        new_items = res.get("new_elements", [])
        new_cnt = res.get("total_new_elements", len(new_items))
        app_items = [
            f"{a.get('window_title') or a.get('app', 'app')} ({a.get('elements_count', 0)})"
            for a in apps
            if "elements_count" in a
        ]
        if new_cnt > 0:
            summary = f"Full scan indexed {total_cnt} controls across {len(apps)} applications (✨ {new_cnt} newly discovered)"
        else:
            summary = f"Full scan checked {total_cnt} controls across {len(apps)} applications (0 new — all already indexed)"
        record_scan_log(
            action="System Pre-Learn",
            app=f"{len(apps)} Apps",
            summary=summary,
            count=total_cnt,
            new_count=new_cnt,
            new_items=new_items,
            items=app_items,
            duration=res.get("duration_seconds", 0.0),
        )
        return res

    def post_hotkey(self, req):
        hk = str(req.get("hotkey", "")).strip()
        if not hk:
            return {"error": "hotkey is required"}
        am.press_hotkey(hk)
        return {"success": True, "hotkey": hk}

    def post_type(self, req):
        text = str(req.get("text", ""))
        if not text:
            return {"error": "text is required"}
        am.type_text(text, enter=bool(req.get("enter", False)))
        return {"success": True, "typed": text}

    def post_fastpath(self, req):
        target = str(req.get("target", ""))
        return {"success": am.execute_fastpath(target), "target": target}

    def post_record_cursor(self, req):
        res = am.record_element_at_cursor(custom_name=str(req.get("name", "")))
        if res.get("status") == "element_recorded":
            record_scan_log(
                action="Hover Record",
                app=res.get("app") or "Application",
                summary=f"Captured '{res.get('element')}' ({res.get('control_type')})",
                count=1,
                items=[res.get("element")],
            )
        return res

    def post_deepdive(self, req):
        return am.deep_dive_app(window_search=str(req.get("window", "")))

    def post_snap_window(self, req):
        win = str(req.get("window", ""))
        side = str(req.get("side", "left"))
        return {"success": am.snap_window(win, side=side), "window": win, "side": side}

    def post_paste(self, req):
        text = str(req.get("text", ""))
        if not text:
            return {"error": "text is required"}
        return {"success": am.clipboard_paste(text), "length": len(text)}

    def post_run_action(self, req):
        act_name = str(req.get("name", ""))
        act_str = str(req.get("action", ""))
        if not act_str and act_name:
            act_str = am.load_saved_actions().get(act_name, "")
            if not act_str:
                return {"error": f"no saved action named {act_name!r}"}
        if not act_str.strip():
            return {"error": "action string is empty"}

        res = am.execute_action(act_str)
        if "error" not in res:
            record_scan_log(
                action="Pipeline",
                app=act_name or "Action Pipeline",
                summary=f"Executed {res.get('steps_executed', 0)} steps: {act_str[:60]}",
                count=res.get("steps_executed", 0),
                items=[s.get("action") for s in res.get("steps", []) if s.get("action")],
                duration=res.get("duration_seconds", 0.0),
                status="success" if all(s.get("status") != "error" for s in res.get("steps", [])) else "error",
            )
        return res

    def post_save_action(self, req):
        return am.save_action(str(req.get("name", "")), str(req.get("action", "")))

    def post_delete_action(self, req):
        name = str(req.get("name", ""))
        return {"success": am.delete_action(name), "name": name}

    def post_record_start(self, req):
        return am.start_recording()

    def post_record_stop(self, req):
        return am.stop_recording()


GET_ROUTES = {
    "": DashboardHandler.get_index,
    "/index.html": DashboardHandler.get_index,
    **{path: DashboardHandler.get_static for path in STATIC_FILES},
    "/api/stats": DashboardHandler.get_stats,
    "/api/actions": DashboardHandler.get_actions,
    "/api/app_tree": DashboardHandler.get_app_tree,
    "/api/logs": DashboardHandler.get_logs,
    "/api/record/status": DashboardHandler.get_record_status,
}

POST_ROUTES = {
    "/api/prelearn": DashboardHandler.post_prelearn,
    "/api/hotkey": DashboardHandler.post_hotkey,
    "/api/type": DashboardHandler.post_type,
    "/api/fastpath": DashboardHandler.post_fastpath,
    "/api/record_cursor": DashboardHandler.post_record_cursor,
    "/api/auto_record": DashboardHandler.post_deepdive,
    "/api/deepdive": DashboardHandler.post_deepdive,
    "/api/snap_window": DashboardHandler.post_snap_window,
    "/api/paste": DashboardHandler.post_paste,
    "/api/run_action": DashboardHandler.post_run_action,
    "/api/save_action": DashboardHandler.post_save_action,
    "/api/delete_action": DashboardHandler.post_delete_action,
    "/api/record/start": DashboardHandler.post_record_start,
    "/api/record/stop": DashboardHandler.post_record_stop,
}


def find_available_port(preferred_port: int = PORT) -> int:
    import socket
    for p in range(preferred_port, preferred_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return preferred_port


def run_dashboard(port: int | None = None, open_browser: bool = True):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    actual_port = port or find_available_port(PORT)
    server = ThreadingHTTPServer(("127.0.0.1", actual_port), DashboardHandler)
    url = f"http://localhost:{actual_port}"
    version_str = getattr(am, "__version__", "0.2.0")
    print("=" * 65)
    print(f"  [+] DESKDRIVER WIKIPEDIA v{version_str} IS RUNNING:")
    print(f"  [>] Open in browser: {url}")
    print("  (Press Ctrl+C to terminate)")
    print("=" * 65)

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer terminated.")
        server.server_close()


if __name__ == "__main__":
    run_dashboard()
