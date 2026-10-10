"""
AI Mouse - Interactive Wiki, Pre-Learn, Hotkeys & Live Stats Dashboard
Serves a comprehensive real-time Wiki & Dashboard at http://localhost:8765
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
from ai_mouse.core.keyboard import COMMON_HOTKEYS

PORT = 8765

HTML_CONTENT = """<!DOCTYPE html>
<html lang="is">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Mouse - Live Stats, Roadmap & Hotkeys Wiki</title>
    <style>
        :root {
            --bg: #0b1120;
            --card: #151f32;
            --card-border: #243247;
            --primary: #38bdf8;
            --primary-hover: #0284c7;
            --accent: #c084fc;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --success: #22c55e;
            --badge-bg: #0f2744;
            --btn-bg: #1e293b;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 24px; min-height: 100vh; }
        .container { max-width: 1250px; margin: 0 auto; }
        
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--card-border); flex-wrap: wrap; gap: 12px; }
        .header-title h1 { font-size: 24px; font-weight: 700; color: var(--primary); display: flex; align-items: center; gap: 10px; }
        .header-title p { font-size: 14px; color: var(--text-muted); margin-top: 4px; }
        
        .header-actions { display: flex; align-items: center; gap: 12px; }
        .btn-prelearn { background: linear-gradient(135deg, #0284c7, #2563eb); color: #fff; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 700; font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: all 0.2s; box-shadow: 0 4px 14px rgba(37,99,235,0.3); }
        .btn-prelearn:hover { transform: translateY(-1px); filter: brightness(1.1); }
        .btn-prelearn:disabled { opacity: 0.6; cursor: not-allowed; }

        .live-indicator { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; background: rgba(34, 197, 94, 0.1); color: var(--success); padding: 7px 14px; border-radius: 9999px; border: 1px solid rgba(34, 197, 94, 0.3); }
        .pulse { width: 8px; height: 8px; background: var(--success); border-radius: 50%; box-shadow: 0 0 8px var(--success); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.85); } }

        /* NAV TABS */
        .tabs { display: flex; gap: 8px; margin-bottom: 24px; border-bottom: 1px solid var(--card-border); padding-bottom: 8px; flex-wrap: wrap; }
        .tab-btn { background: transparent; border: none; color: var(--text-muted); font-size: 15px; font-weight: 600; padding: 10px 18px; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
        .tab-btn:hover { color: var(--text); background: var(--card); }
        .tab-btn.active { color: var(--primary); background: var(--card); border: 1px solid var(--card-border); }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* METRICS */
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .metric-card { background: var(--card); border: 1px solid var(--card-border); border-radius: 12px; padding: 18px; }
        .metric-card .label { font-size: 13px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
        .metric-card .val { font-size: 28px; font-weight: 700; color: var(--text); margin-top: 6px; }
        .metric-card .sub { font-size: 12px; color: var(--primary); margin-top: 4px; }

        /* LIVE INSPECTOR PANEL */
        .live-panel { background: var(--card); border: 1px solid var(--card-border); border-radius: 12px; padding: 20px; margin-bottom: 24px; }
        .live-row { display: flex; flex-wrap: wrap; gap: 20px; }
        .live-col { flex: 1; min-width: 260px; }
        .live-col strong { color: var(--text-muted); font-size: 13px; display: block; margin-bottom: 4px; }
        .live-val { font-size: 15px; font-weight: 600; color: var(--text); background: rgba(11,17,32,0.6); padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); }

        /* SEARCH & FILTER BAR */
        .search-bar-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; flex-wrap: wrap; gap: 12px; }
        .search-box { background: var(--card); border: 1px solid var(--card-border); color: var(--text); padding: 10px 16px; border-radius: 8px; font-size: 14px; width: 320px; outline: none; }
        .search-box:focus { border-color: var(--primary); }

        /* APPS GRID & WIKI */
        .apps-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(370px, 1fr)); gap: 20px; margin-bottom: 24px; }
        .app-card { background: var(--card); border: 1px solid var(--card-border); border-radius: 14px; overflow: hidden; display: flex; flex-direction: column; }
        .app-header { background: rgba(255,255,255,0.03); padding: 16px 20px; border-bottom: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center; }
        .app-title { font-size: 18px; font-weight: 700; text-transform: capitalize; color: var(--primary); }
        .app-count { background: var(--badge-bg); color: var(--primary); font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 9999px; border: 1px solid rgba(56, 189, 248, 0.3); }
        
        .element-list { padding: 12px 16px; max-height: 400px; overflow-y: auto; flex: 1; }
        .element-list::-webkit-scrollbar { width: 6px; }
        .element-list::-webkit-scrollbar-thumb { background: var(--card-border); border-radius: 3px; }
        
        .element-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-radius: 8px; margin-bottom: 6px; background: rgba(11, 17, 32, 0.5); border: 1px solid rgba(255,255,255,0.03); }
        .element-item:hover { background: rgba(56, 189, 248, 0.08); border-color: rgba(56, 189, 248, 0.2); }
        .el-info { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 210px; }
        .el-name { font-size: 13.5px; font-weight: 600; color: #fff; display: flex; align-items: center; gap: 6px; }
        .el-type { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
        .el-coords { font-family: monospace; font-size: 12px; color: var(--accent); background: rgba(192, 132, 252, 0.1); padding: 3px 8px; border-radius: 6px; border: 1px solid rgba(192, 132, 252, 0.2); }

        .kbd-badge {
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: #fff;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 4px;
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            font-family: monospace;
            display: inline-block;
        }

        /* TABLES */
        .wiki-table { width: 100%; border-collapse: collapse; background: var(--card); border: 1px solid var(--card-border); border-radius: 12px; overflow: hidden; margin-bottom: 24px; }
        .wiki-table th { background: rgba(255,255,255,0.03); padding: 12px 16px; text-align: left; font-size: 13px; color: var(--text-muted); text-transform: uppercase; border-bottom: 1px solid var(--card-border); }
        .wiki-table td { padding: 12px 16px; border-bottom: 1px solid var(--card-border); font-size: 14px; }
        .wiki-table tr:hover td { background: rgba(56,189,248,0.04); }
        
        .btn-action { background: var(--btn-bg); color: var(--primary); border: 1px solid var(--card-border); padding: 5px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-action:hover { background: var(--primary); color: #fff; }

        /* INTERACTIVE TEST BOX */
        .test-box { background: var(--card); border: 1px solid var(--card-border); border-radius: 12px; padding: 20px; margin-bottom: 24px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
        .test-input { background: #0b1120; border: 1px solid var(--card-border); color: var(--text); padding: 10px 14px; border-radius: 8px; font-size: 14px; flex: 1; min-width: 240px; outline: none; }
        .test-input:focus { border-color: var(--primary); }

        #toast { position: fixed; bottom: 24px; right: 24px; background: #0284c7; color: white; padding: 12px 20px; border-radius: 8px; box-shadow: 0 4px 14px rgba(0,0,0,0.4); font-size: 14px; font-weight: 600; display: none; z-index: 1000; }

        footer { text-align: center; font-size: 13px; color: var(--text-muted); margin-top: 36px; padding-top: 18px; border-top: 1px solid var(--card-border); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <h1>⚡ AI Mouse & UI Wiki</h1>
                <p>Rauntíma Vegvísir, Flýtilyklar (Hotkeys) og Skjáborðsvöktun</p>
            </div>
            <div class="header-actions">
                <button class="btn-action" style="padding: 10px 16px; font-weight: 700; font-size: 13.5px;" onclick="fetchStats()">
                    <span>🔄 Uppfæra stöðu</span>
                </button>
                <button id="btnPrelearn" class="btn-prelearn" onclick="triggerPrelearn()">
                    <span>🚀 Byrja System Pre-Learn</span>
                </button>
                <div class="live-indicator">
                    <span class="pulse"></span>
                    <span>VIRKT</span>
                </div>
            </div>
        </header>

        <!-- NAVIGATION TABS -->
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('overview')">📊 Yfirlit & Staða</button>
            <button class="tab-btn" onclick="switchTab('wiki')">📖 Roadmap Wiki (Lærð forrit)</button>
            <button class="tab-btn" onclick="switchTab('hotkeys')">⌨️ Hotkeys Wiki (Flýtilyklar)</button>
            <button class="tab-btn" onclick="switchTab('fastpaths')">⚡ OS Fastpaths Wiki</button>
        </div>

        <!-- TAB 1: OVERVIEW & STATS -->
        <div id="tab-overview" class="tab-content active">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="label">Kortlögð forrit</div>
                    <div class="val" id="totalApps">-</div>
                    <div class="sub">Í ui_roadmap.json</div>
                </div>
                <div class="metric-card">
                    <div class="label">Lærðir takkar / stjórntæki</div>
                    <div class="val" id="totalElements">-</div>
                    <div class="sub">O(1) hraðsmellir (< 1 ms)</div>
                </div>
                <div class="metric-card">
                    <div class="label">Flýtilyklar (Hotkeys)</div>
                    <div class="val" id="totalShortcutsCount">-</div>
                    <div class="sub">0.5 ms beinar aðgerðir</div>
                </div>
                <div class="metric-card">
                    <div class="label">OS Fastpaths</div>
                    <div class="val" id="totalFastpathsCount">-</div>
                    <div class="sub">0 ms Windows URI slóðir</div>
                </div>
            </div>

            <div style="font-size: 16px; font-weight: 700; margin-bottom: 14px; color: var(--text);">Kortlögð forrit í fljótu bragði:</div>
            <div class="apps-grid" id="overviewAppsGrid"></div>
        </div>

        <!-- TAB 2: ROADMAP WIKI -->
        <div id="tab-wiki" class="tab-content">
            <div class="search-bar-row">
                <div style="font-size: 16px; font-weight: 700; color: var(--text);">Öll lærð stjórntæki og takkar í kerfinu:</div>
                <input type="text" id="wikiSearchInput" class="search-box" placeholder="Sía eftir takka, forriti eða flýtilykli..." oninput="filterWiki()">
            </div>
            <div class="apps-grid" id="wikiAppsGrid"></div>
        </div>

        <!-- TAB 3: HOTKEYS WIKI -->
        <div id="tab-hotkeys" class="tab-content">
            <div style="font-size: 16px; font-weight: 700; margin-bottom: 8px; color: var(--text);">⌨️ Flýtilyklar (Universal & App Hotkeys - 0.5 ms):</div>
            <p style="font-size: 14px; color: var(--text-muted); margin-bottom: 18px;">Þessir flýtilyklar framkvæma aðgerðir samstundis án þess að hreyfa músina. Þú getur prófað hvaða flýtilykil sem er með því að smella á „Prófa / Ýta“.</p>

            <!-- LIVE TEST KEYBOARD PANEL -->
            <div class="test-box">
                <strong style="color: var(--primary);">Prófa textainnslátt í virkan glugga:</strong>
                <input type="text" id="typeTextInput" class="test-input" placeholder="Sláðu inn texta sem á að senda inn...">
                <button class="btn-action" style="padding: 10px 16px;" onclick="testTypeText()">Senda texta</button>
            </div>

            <table class="wiki-table">
                <thead>
                    <tr>
                        <th>Aðgerð / Hlutverk</th>
                        <th>Flýtilykill</th>
                        <th>Hraði</th>
                        <th>Aðgerð</th>
                    </tr>
                </thead>
                <tbody id="hotkeysBody"></tbody>
            </table>
        </div>

        <!-- TAB 4: FASTPATHS WIKI -->
        <div id="tab-fastpaths" class="tab-content">
            <div style="font-size: 16px; font-weight: 700; margin-bottom: 14px; color: var(--text);">Windows Direct OS Fastpaths (0 ms Navigation):</div>
            <p style="font-size: 14px; color: var(--text-muted); margin-bottom: 18px;">Þessar flýtivísanir gera gervigreindinni kleift að hoppa beint inn í Windows stillingar eða forrit á 0 ms án nokkurra músarsmella.</p>
            
            <table class="wiki-table">
                <thead>
                    <tr>
                        <th>Skipun / Lykill</th>
                        <th>Windows URI</th>
                        <th>Lýsing</th>
                        <th>Aðgerð</th>
                    </tr>
                </thead>
                <tbody id="fastpathsBody"></tbody>
            </table>
        </div>

        <div id="toast"></div>

        <footer>
            AI Mouse & UI Automation MCP Server &bull; <a href="https://github.com/robertbeck-stack/ai-mouse" target="_blank" style="color: var(--primary); text-decoration: none;">GitHub Repository</a>
        </footer>
    </div>

    <script>
        let fullData = null;

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.display = 'block';
            setTimeout(() => { t.style.display = 'none'; }, 3500);
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            const tabMap = {
                'overview': [0, 'tab-overview'],
                'wiki': [1, 'tab-wiki'],
                'hotkeys': [2, 'tab-hotkeys'],
                'fastpaths': [3, 'tab-fastpaths']
            };
            const [idx, id] = tabMap[tabId];
            document.querySelectorAll('.tab-btn')[idx].classList.add('active');
            document.getElementById(id).classList.add('active');
        }

        async function fetchStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                fullData = data;
                renderData(data);
            } catch (e) {
                console.error("Villa við að sækja gögn:", e);
            }
        }

        function renderData(data) {
            document.getElementById('totalApps').innerText = data.total_apps || 0;
            document.getElementById('totalElements').innerText = data.total_elements || 0;
            const hkCount = Object.keys(data.common_hotkeys || {}).length;
            document.getElementById('totalShortcutsCount').innerText = hkCount;
            const fpCount = Object.keys(data.fastpaths || {}).length;
            document.getElementById('totalFastpathsCount').innerText = fpCount;

            renderAppsGrid('overviewAppsGrid', data.roadmap, '', 5);
            renderAppsGrid('wikiAppsGrid', data.roadmap, document.getElementById('wikiSearchInput').value, 999);
            renderHotkeysTable(data.common_hotkeys || {}, data.roadmap || {});
            renderFastpathsTable(data.fastpaths || {});
        }

        function renderAppsGrid(targetId, roadmap, query, maxItems) {
            const grid = document.getElementById(targetId);
            const q = (query || "").toLowerCase().trim();
            grid.innerHTML = '';

            for (const [appName, appData] of Object.entries(roadmap)) {
                const elements = Object.values(appData.elements || {});
                const filtered = elements.filter(el => {
                    if (!q) return true;
                    return appName.toLowerCase().includes(q) || 
                           (el.name && el.name.toLowerCase().includes(q)) ||
                           (el.shortcut && el.shortcut.toLowerCase().includes(q)) ||
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

                const itemsToShow = filtered.slice(0, maxItems);
                if (itemsToShow.length === 0) {
                    list.innerHTML = '<div style="color: var(--text-muted); font-size: 13px; padding: 12px;">Engir takkar fundust.</div>';
                } else {
                    for (const el of itemsToShow) {
                        const item = document.createElement('div');
                        item.className = 'element-item';
                        const shortcutBadge = el.shortcut ? `<span class="kbd-badge">${el.shortcut}</span>` : '';
                        item.innerHTML = `
                            <div class="el-info">
                                <div class="el-name" title="${el.name}">
                                    <span>${el.name}</span>
                                    ${shortcutBadge}
                                </div>
                                <div class="el-type">${el.control_type}</div>
                            </div>
                            <div class="el-coords">rel: (${el.rel_x}, ${el.rel_y})</div>
                        `;
                        list.appendChild(item);
                    }
                    if (filtered.length > maxItems) {
                        const more = document.createElement('div');
                        more.style.textAlign = 'center';
                        more.style.padding = '8px';
                        more.style.fontSize = '12px';
                        more.style.color = 'var(--primary)';
                        more.innerText = `+ ${filtered.length - maxItems} aðrir takkar (sjá í Roadmap Wiki)`;
                        list.appendChild(more);
                    }
                }
                card.appendChild(list);
                grid.appendChild(card);
            }
        }

        function filterWiki() {
            if (fullData) {
                renderAppsGrid('wikiAppsGrid', fullData.roadmap, document.getElementById('wikiSearchInput').value, 999);
            }
        }

        function renderHotkeysTable(commonHotkeys, roadmap) {
            const tbody = document.getElementById('hotkeysBody');
            if (tbody.children.length > 0) return; // Only populate once
            tbody.innerHTML = '';

            // 1. Universal hotkeys
            for (const [action, key] of Object.entries(commonHotkeys)) {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${action}</strong></td>
                    <td><kbd class="kbd-badge">${key.toUpperCase()}</kbd></td>
                    <td><span style="color: var(--success); font-weight: 600;">0.5 ms</span></td>
                    <td>
                        <button class="btn-action" onclick="triggerHotkey('${key}')">Prófa / Ýta</button>
                    </td>
                `;
                tbody.appendChild(tr);
            }
        }

        function renderFastpathsTable(fastpaths) {
            const tbody = document.getElementById('fastpathsBody');
            if (tbody.children.length > 0) return;
            tbody.innerHTML = '';

            for (const [key, uri] of Object.entries(fastpaths)) {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${key}</strong></td>
                    <td><code style="color: var(--primary); font-family: monospace;">${uri}</code></td>
                    <td style="color: var(--text-muted);">Opnar beint ${key} stillingar / forrit</td>
                    <td>
                        <button class="btn-action" onclick="launchFastpath('${key}')">Prófa / Opna</button>
                    </td>
                `;
                tbody.appendChild(tr);
            }
        }

        async function triggerHotkey(hotkey) {
            try {
                const res = await fetch('/api/hotkey', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ hotkey: hotkey })
                });
                showToast(`Sendi flýtilykil: ${hotkey.toUpperCase()}`);
            } catch (e) {
                alert("Villa: " + e);
            }
        }

        async function testTypeText() {
            const val = document.getElementById('typeTextInput').value;
            if (!val) return;
            try {
                await fetch('/api/type', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: val, enter: true })
                });
                showToast(`Skrifaði texta inn í virkan glugga: ${val}`);
                document.getElementById('typeTextInput').value = '';
            } catch (e) {
                alert("Villa: " + e);
            }
        }

        async function launchFastpath(target) {
            try {
                await fetch('/api/fastpath', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: target })
                });
                showToast(`Opnaði flýtivísun: ${target}`);
            } catch (e) {
                alert("Villa við að opna flýtivísun: " + e);
            }
        }

        async function triggerPrelearn() {
            const btn = document.getElementById('btnPrelearn');
            btn.disabled = true;
            btn.innerHTML = '<span>⏳ Skannar forrit og stiku...</span>';
            showToast('Hóf kerfisskönnun (System Pre-Learn)...');

            try {
                const res = await fetch('/api/prelearn', { method: 'POST' });
                const data = await res.json();
                showToast(`Pre-Learn lokið! Fann ${data.total_new_elements} takka í ${data.scanned_apps.length} forritum.`);
                await fetchStats();
            } catch (e) {
                alert("Pre-learn villa: " + e);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>🚀 Byrja System Pre-Learn</span>';
            }
        }

        fetchStats();
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

            roadmap_data = am.roadmap.map
            total_elements = sum(len(app.get("elements", {})) for app in roadmap_data.values())

            data = {
                "total_apps": len(roadmap_data),
                "total_elements": total_elements,
                "common_hotkeys": COMMON_HOTKEYS,
                "fastpaths": FASTPATHS,
                "roadmap": roadmap_data,
                "timestamp": datetime.now().isoformat(),
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        clean_path = self.path.split("?")[0].rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        if clean_path == "/api/prelearn":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            res = am.run_system_prelearn()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))

        elif clean_path == "/api/hotkey":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            hk = req_data.get("hotkey", "")
            if hk:
                am.press_hotkey(hk)
            self.wfile.write(json.dumps({"success": True, "hotkey": hk}).encode("utf-8"))

        elif clean_path == "/api/type":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            text = req_data.get("text", "")
            enter = req_data.get("enter", False)
            if text:
                am.type_text(text, enter=enter)
            self.wfile.write(json.dumps({"success": True, "typed": text}).encode("utf-8"))

        elif clean_path == "/api/fastpath":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            target = req_data.get("target", "")
            success = am.execute_fastpath(target)
            self.wfile.write(json.dumps({"success": success, "target": target}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
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
    print("  [+] AI MOUSE LIVE WIKI & DASHBOARD ER I GANGI:")
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
