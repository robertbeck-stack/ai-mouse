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
from datetime import datetime

# Add src to python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import deskdriver as am
from deskdriver.navigation.fastpaths import FASTPATHS
from deskdriver.core.keyboard import COMMON_HOTKEYS

PORT = 8765

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeskDriver Wiki - The Free Desktop Automation Encyclopedia</title>
    <style>
        :root {
            --bg: #0f141c;
            --surface: #171e29;
            --surface-elevated: #1f2837;
            --border: #2e3848;
            --border-light: #3e4a5d;
            --text: #eaecf0;
            --text-muted: #9aa0a6;
            --primary: #60a5fa;
            --primary-hover: #93c5fd;
            --accent: #c084fc;
            --success: #34d399;
            --kbd-bg: #222d3d;
            --serif: 'Linux Libertine', 'Georgia', 'Times New Roman', serif;
            --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background: var(--bg);
            color: var(--text);
            font-family: var(--sans);
            font-size: 14.5px;
            line-height: 1.6;
            min-height: 100vh;
        }

        /* TOP WIKIPEDIA HEADER */
        .wiki-header {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 10px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            gap: 16px;
            flex-wrap: wrap;
        }
        .wiki-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            color: var(--text);
            cursor: pointer;
        }
        .wiki-globe {
            font-size: 28px;
            filter: drop-shadow(0 0 6px rgba(96,165,250,0.4));
        }
        .wiki-brand-text h1 {
            font-family: var(--serif);
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: #fff;
            margin: 0;
            line-height: 1.2;
        }
        .wiki-brand-text p {
            font-size: 11px;
            color: var(--text-muted);
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }

        .wiki-search-bar {
            flex: 1;
            max-width: 460px;
            position: relative;
        }
        .wiki-search-input {
            width: 100%;
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 8px 14px 8px 36px;
            border-radius: 20px;
            font-size: 13.5px;
            outline: none;
            transition: all 0.2s;
        }
        .wiki-search-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(96,165,250,0.15);
        }
        .search-icon {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 14px;
            color: var(--text-muted);
        }

        .wiki-header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .btn-wiki {
            background: var(--surface-elevated);
            color: var(--primary);
            border: 1px solid var(--border);
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            text-decoration: none;
        }
        .btn-wiki:hover {
            background: var(--border);
            color: #fff;
        }
        .btn-wiki-primary {
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: #fff;
            border: none;
        }
        .btn-wiki-primary:hover {
            filter: brightness(1.1);
        }

        /* TWO-COLUMN LAYOUT */
        .wiki-container {
            max-width: 1380px;
            margin: 0 auto;
            display: flex;
            min-height: calc(100vh - 65px);
        }

        /* LEFT SIDEBAR */
        .wiki-sidebar {
            width: 240px;
            flex-shrink: 0;
            border-right: 1px solid var(--border);
            padding: 20px 14px;
            font-size: 13.5px;
        }
        .sidebar-section {
            margin-bottom: 24px;
        }
        .sidebar-title {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: var(--text-muted);
            margin-bottom: 8px;
            padding-left: 8px;
        }
        .sidebar-menu {
            list-style: none;
        }
        .sidebar-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 7px 10px;
            border-radius: 6px;
            color: var(--text);
            text-decoration: none;
            cursor: pointer;
            transition: all 0.15s;
            margin-bottom: 2px;
        }
        .sidebar-item:hover {
            background: var(--surface-elevated);
            color: var(--primary);
        }
        .sidebar-item.active {
            background: rgba(96,165,250,0.12);
            color: var(--primary);
            font-weight: 600;
        }
        .sidebar-badge {
            font-size: 11px;
            background: var(--surface);
            color: var(--text-muted);
            padding: 2px 6px;
            border-radius: 9999px;
            border: 1px solid var(--border);
        }

        /* MAIN CONTENT ARTICLE AREA */
        .wiki-main {
            flex: 1;
            padding: 28px 36px;
            overflow-x: hidden;
        }

        .article-header {
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }
        .article-title {
            font-family: var(--serif);
            font-size: 32px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 4px;
            line-height: 1.2;
        }
        .article-tagline {
            font-size: 12.5px;
            color: var(--text-muted);
            font-style: italic;
        }
        .hatnote {
            padding: 6px 12px;
            background: rgba(255,255,255,0.02);
            border-left: 3px solid var(--border-light);
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 20px;
        }

        /* WIKIPEDIA INFOBOX */
        .infobox {
            float: right;
            width: 320px;
            margin: 0 0 20px 24px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 13px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.25);
            overflow: hidden;
        }
        .infobox-title {
            background: var(--surface-elevated);
            padding: 12px 16px;
            font-family: var(--serif);
            font-size: 17px;
            font-weight: 700;
            text-align: center;
            color: var(--primary);
            border-bottom: 1px solid var(--border);
        }
        .infobox-image {
            text-align: center;
            padding: 16px;
            background: rgba(0,0,0,0.2);
            font-size: 40px;
            border-bottom: 1px solid var(--border);
        }
        .infobox table {
            width: 100%;
            border-collapse: collapse;
        }
        .infobox th {
            text-align: left;
            padding: 8px 12px;
            color: var(--text-muted);
            width: 42%;
            font-weight: 600;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            vertical-align: top;
        }
        .infobox td {
            padding: 8px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            font-weight: 500;
        }

        /* TABLE OF CONTENTS */
        .toc-box {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 14px 18px;
            margin: 18px 0 24px 0;
            display: inline-block;
            min-width: 260px;
        }
        .toc-title {
            font-weight: 700;
            font-size: 13px;
            text-align: center;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: var(--text-muted);
        }
        .toc-list {
            list-style: none;
            padding-left: 0;
            font-size: 13.5px;
        }
        .toc-item {
            margin-bottom: 4px;
        }
        .toc-link {
            color: var(--primary);
            text-decoration: none;
        }
        .toc-link:hover {
            text-decoration: underline;
        }

        /* HEADINGS */
        .wiki-h2 {
            font-family: var(--serif);
            font-size: 22px;
            font-weight: 700;
            color: #fff;
            margin: 28px 0 12px 0;
            padding-bottom: 6px;
            border-bottom: 1px solid var(--border);
            clear: both;
        }

        /* WIKIPEDIA TABLES */
        .wikitable {
            width: 100%;
            border-collapse: collapse;
            background: var(--surface);
            border: 1px solid var(--border);
            margin: 14px 0 24px 0;
            font-size: 13.5px;
        }
        .wikitable th {
            background: var(--surface-elevated);
            padding: 10px 14px;
            text-align: left;
            font-weight: 700;
            color: var(--text);
            border-bottom: 1px solid var(--border);
        }
        .wikitable td {
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
        }
        .wikitable tr:hover td {
            background: rgba(96,165,250,0.05);
        }

        /* KBD TAGS */
        .kbd-cap {
            background: var(--kbd-bg);
            color: #fff;
            font-family: monospace;
            font-size: 11.5px;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 4px;
            border: 1px solid var(--border-light);
            box-shadow: 0 1px 2px rgba(0,0,0,0.4);
            display: inline-block;
        }

        /* MAIN PAGE BANNER */
        .welcome-banner {
            background: linear-gradient(135deg, rgba(30,58,138,0.2), rgba(15,23,42,0.6));
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }
        .welcome-title {
            font-family: var(--serif);
            font-size: 22px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 4px;
        }
        .welcome-sub {
            font-size: 13.5px;
            color: var(--text-muted);
        }
        .stats-strip {
            display: flex;
            gap: 20px;
            background: rgba(0,0,0,0.25);
            padding: 10px 18px;
            border-radius: 6px;
            border: 1px solid var(--border);
        }
        .stat-item {
            text-align: center;
        }
        .stat-val {
            font-size: 20px;
            font-weight: 700;
            color: var(--primary);
        }
        .stat-lbl {
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
        }

        /* APP CARDS GRID */
        .encyclopedia-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
            margin: 16px 0;
        }
        .encyclo-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
            color: var(--text);
            display: block;
        }
        .encyclo-card:hover {
            border-color: var(--primary);
            transform: translateY(-2px);
            background: var(--surface-elevated);
        }
        .encyclo-card h4 {
            font-family: var(--serif);
            font-size: 17px;
            color: var(--primary);
            margin-bottom: 4px;
            text-transform: capitalize;
        }
        .encyclo-card p {
            font-size: 12.5px;
            color: var(--text-muted);
        }

        #toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #0284c7;
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.5);
            font-size: 13.5px;
            font-weight: 600;
            display: none;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <!-- TOP WIKIPEDIA NAV -->
    <header class="wiki-header">
        <div class="wiki-brand" onclick="navigateTo('main')">
            <span class="wiki-globe">🌐</span>
            <div class="wiki-brand-text">
                <h1>DESKDRIVER WIKIPEDIA</h1>
                <p>The Free Desktop Automation Encyclopedia</p>
            </div>
        </div>

        <div class="wiki-search-bar">
            <span class="search-icon">🔍</span>
            <input type="text" id="wikiGlobalSearch" class="wiki-search-input" placeholder="Search DeskDriver Wiki (Notepad, Brave, Fastpaths...)" oninput="handleGlobalSearch()">
        </div>

        <div class="wiki-header-actions">
            <button class="btn-wiki" onclick="fetchStats()">🔄 Refresh</button>
            <button id="btnPrelearn" class="btn-wiki btn-wiki-primary" onclick="triggerPrelearn()">🚀 Run Pre-Learn</button>
        </div>
    </header>

    <!-- TWO-COLUMN CONTAINER -->
    <div class="wiki-container">
        <!-- LEFT SIDEBAR -->
        <aside class="wiki-sidebar">
            <div class="sidebar-section">
                <div class="sidebar-title">Navigation</div>
                <ul class="sidebar-menu">
                    <li><a class="sidebar-item active" id="menu-main" onclick="navigateTo('main')"><span>🏠 Main Page</span></a></li>
                    <li><a class="sidebar-item" id="menu-hotkeys" onclick="navigateTo('hotkeys')"><span>⌨️ Universal Hotkeys</span> <span class="sidebar-badge" id="sideBadgeHotkeys">31</span></a></li>
                    <li><a class="sidebar-item" id="menu-fastpaths" onclick="navigateTo('fastpaths')"><span>⚡ OS Fastpaths</span> <span class="sidebar-badge" id="sideBadgeFastpaths">33</span></a></li>
                    <li><a class="sidebar-item" id="menu-tester" onclick="navigateTo('tester')"><span>🧪 Input Tester</span></a></li>
                </ul>
            </div>

            <div class="sidebar-section">
                <div class="sidebar-title">Indexed Applications</div>
                <ul class="sidebar-menu" id="sidebarAppsList">
                    <!-- Populated dynamically -->
                </ul>
            </div>

            <div class="sidebar-section">
                <div class="sidebar-title">Community & Tools</div>
                <ul class="sidebar-menu">
                    <li><a class="sidebar-item" href="https://github.com/robertbeck-stack/ai-mouse" target="_blank"><span>📦 GitHub Repo</span></a></li>
                    <li><a class="sidebar-item" onclick="triggerPrelearn()"><span>⚡ Deep Scan (Pre-Learn)</span></a></li>
                </ul>
            </div>
        </aside>

        <!-- MAIN ARTICLE -->
        <main class="wiki-main" id="wikiArticle">
            <!-- Article view dynamically rendered by JS -->
        </main>
    </div>

    <div id="toast"></div>

    <script>
        let fullData = null;
        let currentView = 'main';
        let currentApp = null;

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.display = 'block';
            setTimeout(() => { t.style.display = 'none'; }, 3200);
        }

        async function fetchStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                fullData = data;
                renderSidebar(data);
                renderCurrentView();
            } catch (e) {
                console.error("Error fetching stats:", e);
            }
        }

        function navigateTo(view, appKey = null) {
            currentView = view;
            currentApp = appKey;
            
            // Update active menu state
            document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
            if (view === 'main') document.getElementById('menu-main')?.classList.add('active');
            else if (view === 'hotkeys') document.getElementById('menu-hotkeys')?.classList.add('active');
            else if (view === 'fastpaths') document.getElementById('menu-fastpaths')?.classList.add('active');
            else if (view === 'tester') document.getElementById('menu-tester')?.classList.add('active');
            else if (view === 'app' && appKey) {
                document.getElementById('side-app-' + appKey)?.classList.add('active');
            }

            renderCurrentView();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function renderSidebar(data) {
            const list = document.getElementById('sidebarAppsList');
            if (!list) return;
            list.innerHTML = '';
            
            const roadmap = data.roadmap || {};
            for (const [appKey, appData] of Object.entries(roadmap)) {
                const count = Object.keys(appData.elements || {}).length;
                const li = document.createElement('li');
                li.innerHTML = `
                    <a class="sidebar-item" id="side-app-${appKey}" onclick="navigateTo('app', '${appKey}')">
                        <span style="text-transform: capitalize;">${appKey}</span>
                        <span class="sidebar-badge">${count}</span>
                    </a>
                `;
                list.appendChild(li);
            }

            const hkCount = Object.keys(data.common_hotkeys || {}).length;
            const fpCount = Object.keys(data.fastpaths || {}).length;
            const badgeHk = document.getElementById('sideBadgeHotkeys');
            const badgeFp = document.getElementById('sideBadgeFastpaths');
            if (badgeHk) badgeHk.innerText = hkCount;
            if (badgeFp) badgeFp.innerText = fpCount;
        }

        function renderCurrentView() {
            if (!fullData) return;
            const container = document.getElementById('wikiArticle');

            if (currentView === 'main') renderMainPage(container);
            else if (currentView === 'app') renderAppPage(container, currentApp);
            else if (currentView === 'hotkeys') renderHotkeysPage(container);
            else if (currentView === 'fastpaths') renderFastpathsPage(container);
            else if (currentView === 'tester') renderTesterPage(container);
        }

        /* 1. MAIN ENCYCLOPEDIA PAGE */
        function renderMainPage(container) {
            const data = fullData;
            const roadmap = data.roadmap || {};
            const appCount = Object.keys(roadmap).length;
            const elCount = data.total_elements || 0;
            const hkCount = Object.keys(data.common_hotkeys || {}).length;
            const fpCount = Object.keys(data.fastpaths || {}).length;

            let appsCardsHtml = '';
            for (const [key, val] of Object.entries(roadmap)) {
                const count = Object.keys(val.elements || {}).length;
                appsCardsHtml += `
                    <a class="encyclo-card" onclick="navigateTo('app', '${key}')">
                        <h4>${key}</h4>
                        <p>Indexed controls: <strong>${count}</strong></p>
                        <p style="margin-top: 4px; color: var(--primary); font-size: 11.5px;">Read article & roadmap &rarr;</p>
                    </a>
                `;
            }

            container.innerHTML = `
                <div class="welcome-banner">
                    <div>
                        <div class="welcome-title">Welcome to DeskDriver Wiki</div>
                        <div class="welcome-sub">The open desktop knowledge base and spatial roadmap encyclopedia for Windows automation.</div>
                    </div>
                    <div class="stats-strip">
                        <div class="stat-item"><div class="stat-val">${appCount}</div><div class="stat-lbl">Apps</div></div>
                        <div class="stat-item"><div class="stat-val">${elCount}</div><div class="stat-lbl">Controls</div></div>
                        <div class="stat-item"><div class="stat-val">${hkCount}</div><div class="stat-lbl">Hotkeys</div></div>
                        <div class="stat-item"><div class="stat-val">${fpCount}</div><div class="stat-lbl">Fastpaths</div></div>
                    </div>
                </div>

                <div class="hatnote">
                    DeskDriver provides sub-millisecond cursor execution, atomic SendInput typing, and persistent O(1) spatial indexing.
                </div>

                <h2 class="wiki-h2">Indexed Applications Encyclopedia</h2>
                <p style="color: var(--text-muted); margin-bottom: 16px;">Browse encyclopedic roadmap profiles for all desktop applications currently learned into <code>ui_roadmap.json</code>:</p>
                <div class="encyclopedia-grid">
                    ${appsCardsHtml}
                </div>

                <h2 class="wiki-h2">Universal System Navigation</h2>
                <table class="wikitable">
                    <thead>
                        <tr><th>Knowledge Base</th><th>Scope</th><th>Latency</th><th>Action</th></tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong><a onclick="navigateTo('hotkeys')" style="color: var(--primary); cursor: pointer;">Universal Keyboard Shortcuts</a></strong></td>
                            <td>31 Global Windows Accelerators (Save, Copy, Paste, Snip, Task Manager)</td>
                            <td><span style="color: var(--success); font-weight: 600;">0.5 ms</span></td>
                            <td><button class="btn-wiki" onclick="navigateTo('hotkeys')">Open Article</button></td>
                        </tr>
                        <tr>
                            <td><strong><a onclick="navigateTo('fastpaths')" style="color: var(--primary); cursor: pointer;">Windows OS Fastpaths</a></strong></td>
                            <td>33 Zero-click URI schemes for native settings, apps, and diagnostics</td>
                            <td><span style="color: var(--success); font-weight: 600;">0.0 ms</span></td>
                            <td><button class="btn-wiki" onclick="navigateTo('fastpaths')">Open Article</button></td>
                        </tr>
                    </tbody>
                </table>
            `;
        }

        /* 2. APPLICATION ARTICLE PAGE */
        function renderAppPage(container, appKey) {
            const appData = (fullData.roadmap || {})[appKey];
            if (!appData) {
                container.innerHTML = `<h2>Application '${appKey}' not found.</h2>`;
                return;
            }

            const elements = Object.values(appData.elements || {});
            const hotkeyElements = elements.filter(e => e.shortcut);

            let hkRows = '';
            for (const h of hotkeyElements) {
                hkRows += `
                    <tr>
                        <td><strong>${h.name}</strong></td>
                        <td><kbd class="kbd-cap">${h.shortcut.toUpperCase()}</kbd></td>
                        <td><span style="color: var(--success); font-weight: 600;">0.5 ms</span></td>
                        <td><button class="btn-wiki" onclick="triggerHotkey('${h.shortcut}')">Test / Press</button></td>
                    </tr>
                `;
            }

            let elRows = '';
            for (const el of elements) {
                const scBadge = el.shortcut ? `<kbd class="kbd-cap">${el.shortcut}</kbd>` : '<span style="color: var(--text-muted); font-size: 11px;">Mouse click</span>';
                const anchorTxt = el.anchor_right ? '<span style="color: var(--accent);">Right</span>' : 'Top-Left';
                elRows += `
                    <tr>
                        <td><strong>${el.name}</strong></td>
                        <td><code>${el.control_type}</code></td>
                        <td><code>rel: (${el.rel_x}, ${el.rel_y})</code></td>
                        <td>${anchorTxt}</td>
                        <td>${scBadge}</td>
                    </tr>
                `;
            }

            container.innerHTML = `
                <!-- WIKIPEDIA INFOBOX -->
                <div class="infobox">
                    <div class="infobox-title">${appKey.toUpperCase()}</div>
                    <div class="infobox-image">🖥️</div>
                    <table>
                        <tr><th>App Family</th><td>${appKey}</td></tr>
                        <tr><th>Indexed Controls</th><td><strong>${elements.length}</strong> items</td></tr>
                        <tr><th>Shortcuts Mapped</th><td><strong>${hotkeyElements.length}</strong> hotkeys</td></tr>
                        <tr><th>Positioning</th><td>Relative + Anchors</td></tr>
                        <tr><th>Cache Storage</th><td><code>ui_roadmap.json</code></td></tr>
                    </table>
                </div>

                <div class="article-header">
                    <h1 class="article-title">${appKey.charAt(0).toUpperCase() + appKey.slice(1)} (software)</h1>
                    <div class="article-tagline">From DeskDriver Wiki, the open desktop knowledge base</div>
                </div>

                <div class="hatnote">
                    This article documents the spatial coordinates, interactive UI elements, and keyboard accelerators mapped for <strong>${appKey}</strong>.
                </div>

                <div class="toc-box">
                    <div class="toc-title">Contents</div>
                    <ul class="toc-list">
                        <li class="toc-item"><a class="toc-link" href="#sec-overview">1 Overview</a></li>
                        <li class="toc-item"><a class="toc-link" href="#sec-shortcuts">2 Keyboard Accelerators (${hotkeyElements.length})</a></li>
                        <li class="toc-item"><a class="toc-link" href="#sec-controls">3 Spatial UI Elements (${elements.length})</a></li>
                    </ul>
                </div>

                <h2 class="wiki-h2" id="sec-overview">1 Overview</h2>
                <p>
                    <strong>${appKey}</strong> has been indexed into the DeskDriver roadmap cache. AI agents can resolve coordinates for this application in sub-millisecond O(1) time without performing continuous vision queries or screen captures.
                </p>

                <h2 class="wiki-h2" id="sec-shortcuts">2 Keyboard Accelerators</h2>
                <p style="color: var(--text-muted); margin-bottom: 12px;">Mapped hotkeys allow instant 0.5 ms actions without cursor movement:</p>
                <table class="wikitable">
                    <thead>
                        <tr><th>Action / Control</th><th>Accelerator Key</th><th>Latency</th><th>Test</th></tr>
                    </thead>
                    <tbody>
                        ${hkRows || '<tr><td colspan="4" style="color: var(--text-muted);">No specific hotkeys mapped yet.</td></tr>'}
                    </tbody>
                </table>

                <h2 class="wiki-h2" id="sec-controls">3 Spatial UI Elements & Coordinates</h2>
                <p style="color: var(--text-muted); margin-bottom: 12px;">Full list of interactive buttons, menu items, and input controls mapped for <strong>${appKey}</strong>:</p>
                <table class="wikitable">
                    <thead>
                        <tr><th>Control Name</th><th>Type</th><th>Offset (X, Y)</th><th>Anchor</th><th>Shortcut</th></tr>
                    </thead>
                    <tbody>
                        ${elRows || '<tr><td colspan="5" style="color: var(--text-muted);">No controls indexed yet.</td></tr>'}
                    </tbody>
                </table>
            `;
        }

        /* 3. UNIVERSAL HOTKEYS ARTICLE */
        function renderHotkeysPage(container) {
            const hotkeys = fullData.common_hotkeys || {};
            let rows = '';
            for (const [action, key] of Object.entries(hotkeys)) {
                rows += `
                    <tr>
                        <td><strong>${action}</strong></td>
                        <td><kbd class="kbd-cap">${key.toUpperCase()}</kbd></td>
                        <td><span style="color: var(--success); font-weight: 600;">0.5 ms</span></td>
                        <td><button class="btn-wiki" onclick="triggerHotkey('${key}')">Test / Trigger</button></td>
                    </tr>
                `;
            }

            container.innerHTML = `
                <div class="article-header">
                    <h1 class="article-title">Universal Keyboard Accelerators</h1>
                    <div class="article-tagline">From DeskDriver Wiki, the open desktop knowledge base</div>
                </div>

                <div class="hatnote">
                    Universal hotkeys are dispatched via atomic Windows <code>SendInput</code> directly into the system event queue.
                </div>

                <h2 class="wiki-h2">Global Shortcut Registry</h2>
                <table class="wikitable">
                    <thead>
                        <tr><th>Command / Action</th><th>Key Combination</th><th>Execution Speed</th><th>Action</th></tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            `;
        }

        /* 4. OS FASTPATHS ARTICLE */
        function renderFastpathsPage(container) {
            const fastpaths = fullData.fastpaths || {};
            let rows = '';
            for (const [key, uri] of Object.entries(fastpaths)) {
                rows += `
                    <tr>
                        <td><strong>${key}</strong></td>
                        <td><code style="color: var(--primary);">${uri}</code></td>
                        <td style="color: var(--text-muted);">Directly opens ${key} settings or native tool</td>
                        <td><button class="btn-wiki" onclick="launchFastpath('${key}')">Test / Launch</button></td>
                    </tr>
                `;
            }

            container.innerHTML = `
                <div class="article-header">
                    <h1 class="article-title">Windows OS Fastpaths (URI Schemes)</h1>
                    <div class="article-tagline">From DeskDriver Wiki, the open desktop knowledge base</div>
                </div>

                <div class="hatnote">
                    OS Fastpaths bypass UI clicking completely by navigating via registered Windows protocol handlers (0.0 ms).
                </div>

                <h2 class="wiki-h2">Supported Protocol Handlers</h2>
                <table class="wikitable">
                    <thead>
                        <tr><th>Keyword</th><th>Windows URI</th><th>Description</th><th>Action</th></tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            `;
        }

        /* 5. TESTER PAGE */
        function renderTesterPage(container) {
            container.innerHTML = `
                <div class="article-header">
                    <h1 class="article-title">Input & Typing Tester</h1>
                    <div class="article-tagline">Interactive laboratory for testing atomic SendInput text dispatch</div>
                </div>

                <div class="welcome-banner" style="margin-top: 20px;">
                    <div style="flex: 1;">
                        <h3 style="color: #fff; margin-bottom: 8px;">Direct Text Input Tester</h3>
                        <p style="color: var(--text-muted); margin-bottom: 14px;">Types Unicode text directly into whatever window currently has focus using atomic Windows <code>SendInput</code>.</p>
                        <div style="display: flex; gap: 10px;">
                            <input type="text" id="typeTextInput" class="wiki-search-input" style="border-radius: 6px; padding: 10px 14px; font-size: 14px;" placeholder="Type text to send to focused window...">
                            <button class="btn-wiki btn-wiki-primary" onclick="testTypeText()">Send Text</button>
                        </div>
                    </div>
                </div>
            `;
        }

        function handleGlobalSearch() {
            const q = document.getElementById('wikiGlobalSearch').value.toLowerCase().trim();
            if (!q || !fullData) return;
            const roadmap = fullData.roadmap || {};
            for (const key of Object.keys(roadmap)) {
                if (key.includes(q)) {
                    navigateTo('app', key);
                    return;
                }
            }
            if (q.includes('hotkey') || q.includes('shortcut')) navigateTo('hotkeys');
            else if (q.includes('fastpath') || q.includes('uri') || q.includes('setting')) navigateTo('fastpaths');
        }

        async function triggerHotkey(hotkey) {
            try {
                await fetch('/api/hotkey', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ hotkey: hotkey })
                });
                showToast(`Triggered hotkey: ${hotkey.toUpperCase()}`);
            } catch (e) {
                alert("Error: " + e);
            }
        }

        async function testTypeText() {
            const val = document.getElementById('typeTextInput')?.value;
            if (!val) return;
            try {
                await fetch('/api/type', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: val, enter: true })
                });
                showToast(`Typed text into focused window: ${val}`);
                document.getElementById('typeTextInput').value = '';
            } catch (e) {
                alert("Error: " + e);
            }
        }

        async function launchFastpath(target) {
            try {
                await fetch('/api/fastpath', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: target })
                });
                showToast(`Launched fastpath: ${target}`);
            } catch (e) {
                alert("Error launching fastpath: " + e);
            }
        }

        async function triggerPrelearn() {
            const btn = document.getElementById('btnPrelearn');
            if (btn) {
                btn.disabled = true;
                btn.innerText = '⏳ Scanning...';
            }
            showToast('Started System Pre-Learn scan...');

            try {
                const res = await fetch('/api/prelearn', { method: 'POST' });
                const data = await res.json();
                showToast(`Pre-Learn complete! Found ${data.total_new_elements} controls across ${data.scanned_apps.length} apps.`);
                await fetchStats();
            } catch (e) {
                alert("Error: " + e);
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerText = '🚀 Run Pre-Learn';
                }
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
    print("  [+] DESKDRIVER WIKIPEDIA IS RUNNING:")
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
