"""
AI Mouse - Live Web Stats Dashboard
Serves an interactive real-time web dashboard at http://localhost:8765
Run: .\\.venv\\Scripts\\python dashboard.py
"""

import sys
import json
import webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Add src to python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import ai_mouse as am
from ai_mouse.navigation.fastpaths import FASTPATHS

PORT = 8765

HTML_CONTENT = """<!DOCTYPE html>
<html lang="is">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Mouse - Live Stats & Roadmap Dashboard</title>
    <style>
        :root {
            --bg: #0f172a;
            --card: #1e293b;
            --card-border: #334155;
            --primary: #38bdf8;
            --primary-hover: #0284c7;
            --accent: #a855f7;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --success: #22c55e;
            --badge-bg: #0f2744;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 24px; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; }
        
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--card-border); }
        .header-title h1 { font-size: 24px; font-weight: 700; color: var(--primary); display: flex; align-items: center; gap: 8px; }
        .header-title p { font-size: 14px; color: var(--text-muted); margin-top: 4px; }
        .live-indicator { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; background: rgba(34, 197, 94, 0.1); color: var(--success); padding: 6px 14px; border-radius: 9999px; border: 1px solid rgba(34, 197, 94, 0.3); }
        .pulse { width: 8px; height: 8px; background: var(--success); border-radius: 50%; box-shadow: 0 0 8px var(--success); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.85); } }

        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .metric-card { background: var(--card); border: 1px solid var(--card-border); border-radius: 12px; padding: 18px; }
        .metric-card .label { font-size: 13px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
        .metric-card .val { font-size: 28px; font-weight: 700; color: var(--text); margin-top: 6px; }
        .metric-card .sub { font-size: 12px; color: var(--primary); margin-top: 4px; }

        .section-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; }
        .search-box { background: var(--card); border: 1px solid var(--card-border); color: var(--text); padding: 8px 14px; border-radius: 8px; font-size: 14px; width: 260px; outline: none; }
        .search-box:focus { border-color: var(--primary); }

        .apps-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 20px; margin-bottom: 24px; }
        .app-card { background: var(--card); border: 1px solid var(--card-border); border-radius: 14px; overflow: hidden; display: flex; flex-direction: column; }
        .app-header { background: rgba(255,255,255,0.03); padding: 16px 20px; border-bottom: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center; }
        .app-title { font-size: 18px; font-weight: 700; text-transform: capitalize; color: var(--primary); }
        .app-count { background: var(--badge-bg); color: var(--primary); font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 9999px; border: 1px solid rgba(56, 189, 248, 0.3); }
        
        .element-list { padding: 12px 16px; max-height: 380px; overflow-y: auto; flex: 1; }
        .element-list::-webkit-scrollbar { width: 6px; }
        .element-list::-webkit-scrollbar-thumb { background: var(--card-border); border-radius: 3px; }
        
        .element-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-radius: 8px; margin-bottom: 6px; background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255,255,255,0.02); }
        .element-item:hover { background: rgba(56, 189, 248, 0.08); border-color: rgba(56, 189, 248, 0.2); }
        .el-info { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 220px; }
        .el-name { font-size: 13.5px; font-weight: 600; }
        .el-type { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
        .el-coords { font-family: monospace; font-size: 12px; color: var(--accent); background: rgba(168, 85, 247, 0.1); padding: 3px 8px; border-radius: 6px; border: 1px solid rgba(168, 85, 247, 0.2); }

        .live-panel { background: var(--card); border: 1px solid var(--card-border); border-radius: 12px; padding: 20px; margin-bottom: 24px; }
        .live-row { display: flex; flex-wrap: wrap; gap: 20px; }
        .live-col { flex: 1; min-width: 260px; }
        .live-col strong { color: var(--text-muted); font-size: 13px; display: block; margin-bottom: 4px; }
        .live-val { font-size: 15px; font-weight: 600; color: var(--text); background: rgba(15,23,42,0.6); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); }

        footer { text-align: center; font-size: 13px; color: var(--text-muted); margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--card-border); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <h1>⚡ AI Mouse - Live Stats & Roadmap</h1>
                <p>Rauntíma yfirlit yfir bendil, virk forrit og lærða gagnvirka takka</p>
            </div>
            <div class="live-indicator">
                <span class="pulse"></span>
                <span>RAUNTÍMA TENGT</span>
            </div>
        </header>

        <!-- TOP METRICS -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="label">Kortlögð forrit</div>
                <div class="val" id="totalApps">-</div>
                <div class="sub">Í ui_roadmap.json</div>
            </div>
            <div class="metric-card">
                <div class="label">Lærðir takkar / stjórntæki</div>
                <div class="val" id="totalElements">-</div>
                <div class="sub" id="elementsSub">O(1) hraðsmellir</div>
            </div>
            <div class="metric-card">
                <div class="label">Músarstaða (X, Y)</div>
                <div class="val" id="cursorPos">-</div>
                <div class="sub" id="cursorSub">Raunhnit á skjánum</div>
            </div>
            <div class="metric-card">
                <div class="label">OS Fastpaths (0 ms)</div>
                <div class="val" id="fastpathsCount">33</div>
                <div class="sub">Beinar URI flýtivísanir</div>
            </div>
        </div>

        <!-- LIVE DESKTOP INSPECTION PANEL -->
        <div class="live-panel">
            <div class="section-title">
                <span>🖥️ Núverandi staða á skjáborðinu</span>
            </div>
            <div class="live-row">
                <div class="live-col">
                    <strong>Virkur gluggi í forgrunni:</strong>
                    <div class="live-val" id="activeWindow">-</div>
                </div>
                <div class="live-col">
                    <strong>Hvað er beint undir bendlinum núna:</strong>
                    <div class="live-val" id="underCursor">-</div>
                </div>
            </div>
        </div>

        <!-- ROADMAP KNOWLEDGE CARDS -->
        <div class="section-title">
            <span>🗺️ Lærdómskortið (Kortlögð forrit og hnappar)</span>
            <input type="text" id="searchInput" class="search-box" placeholder="Leita að takka eða forriti..." oninput="filterElements()">
        </div>

        <div class="apps-grid" id="appsGrid">
            <!-- Dynamically populated -->
        </div>

        <footer>
            AI Mouse & UI Automation MCP Server &bull; <a href="https://github.com/robertbeck-stack/ai-mouse" target="_blank" style="color: var(--primary); text-decoration: none;">GitHub Repository</a>
        </footer>
    </div>

    <script>
        let fullData = null;

        async function fetchStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                fullData = data;
                renderData(data);
            } catch (e) {
                console.error("Villa við að sækja stöðu:", e);
            }
        }

        function renderData(data) {
            document.getElementById('totalApps').innerText = data.total_apps || 0;
            document.getElementById('totalElements').innerText = data.total_elements || 0;
            document.getElementById('cursorPos').innerText = `(${data.mouse.x}, ${data.mouse.y})`;
            document.getElementById('activeWindow').innerText = data.active_window || "(Enginn)";
            
            const under = data.under_cursor;
            if (under && !under.error) {
                document.getElementById('underCursor').innerText = `${under.name || '(án heitis)'} [${under.control_type}]`;
            } else {
                document.getElementById('underCursor').innerText = "(Ekkert stjórntæki greint)";
            }

            renderAppsGrid(data.roadmap, document.getElementById('searchInput').value);
        }

        function renderAppsGrid(roadmap, query) {
            const grid = document.getElementById('appsGrid');
            const q = (query || "").toLowerCase().trim();
            grid.innerHTML = '';

            for (const [appName, appData] of Object.entries(roadmap)) {
                const elements = Object.values(appData.elements || {});
                const filtered = elements.filter(el => {
                    if (!q) return true;
                    return appName.toLowerCase().includes(q) || 
                           (el.name && el.name.toLowerCase().includes(q)) ||
                           (el.control_type && el.control_type.toLowerCase().includes(q));
                });

                if (q && filtered.length === 0) continue;

                const card = document.createElement('div');
                card.className = 'app-card';

                const header = document.createElement('div');
                header.className = 'app-header';
                header.innerHTML = `
                    <div class="app-title">${appName}</div>
                    <div class="app-count">${filtered.length} takkar</div>
                `;
                card.appendChild(header);

                const list = document.createElement('div');
                list.className = 'element-list';

                if (filtered.length === 0) {
                    list.innerHTML = '<div style="color: var(--text-muted); font-size: 13px; padding: 12px;">Engir takkar fundust.</div>';
                } else {
                    for (const el of filtered) {
                        const item = document.createElement('div');
                        item.className = 'element-item';
                        item.innerHTML = `
                            <div class="el-info">
                                <div class="el-name" title="${el.name}">${el.name}</div>
                                <div class="el-type">${el.control_type}</div>
                            </div>
                            <div class="el-coords">rel: (${el.rel_x}, ${el.rel_y})</div>
                        `;
                        list.appendChild(item);
                    }
                }
                card.appendChild(list);
                grid.appendChild(card);
            }
        }

        function filterElements() {
            if (fullData) {
                renderAppsGrid(fullData.roadmap, document.getElementById('searchInput').value);
            }
        }

        // Poll every 1.5 seconds for real-time updates
        fetchStats();
        setInterval(fetchStats, 1500);
    </script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        clean_path = self.path.split("?")[0].rstrip("/")
        if clean_path in ("", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        elif clean_path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()


            # Gather live data
            try:
                mx, my = am.get_mouse_position()
                under = am.get_element_under_cursor()
                wins = am.list_windows()
                active_win = wins[0]["title"] if wins else "Unknown"
            except Exception as e:
                mx, my = 0, 0
                under = {"error": str(e)}
                active_win = "Unknown"

            roadmap_data = am.roadmap.map
            total_elements = sum(len(app.get("elements", {})) for app in roadmap_data.values())

            data = {
                "mouse": {"x": mx, "y": my},
                "under_cursor": under,
                "active_window": active_win,
                "total_apps": len(roadmap_data),
                "total_elements": total_elements,
                "fastpaths_count": len(FASTPATHS),
                "roadmap": roadmap_data,
                "timestamp": datetime.now().isoformat(),
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress noisy HTTP request logging in terminal
        pass


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
    print("=" * 65)
    print("  [+] AI MOUSE LIVE DASHBOARD ER I GANGI:")
    print(f"  [>] Opnadu i vafra: {url}")
    print("  (Yttu a Ctrl+C til ad stodva)")
    print("=" * 65)


    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStodvadi vefthjoninn.")
        server.server_close()



if __name__ == "__main__":
    run_dashboard()
