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
            --bg: #ffffff;
            --surface: #f8f9fa;
            --surface-elevated: #eaecf0;
            --border: #a2a9b1;
            --border-light: #c8ccd1;
            --text: #202122;
            --text-muted: #54595d;
            --primary: #3366cc;
            --primary-hover: #0645ad;
            --accent: #72777d;
            --success: #14866d;
            --kbd-bg: #f8f9fa;
            --serif: 'Linux Libertine', 'Georgia', 'Times New Roman', serif;
            --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background: #ffffff;
            color: #202122;
            font-family: var(--sans);
            font-size: 14px;
            line-height: 1.6;
            min-height: 100vh;
        }

        /* TOP WIKIPEDIA HEADER */
        .wiki-header {
            background: #ffffff;
            border-bottom: 1px solid #c8ccd1;
            padding: 10px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            gap: 16px;
        }
        .wiki-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            color: #202122;
            cursor: pointer;
        }
        .wiki-globe {
            font-size: 26px;
        }
        .wiki-brand-text h1 {
            font-family: var(--serif);
            font-size: 20px;
            font-weight: 500;
            letter-spacing: -0.5px;
            color: #202122;
            margin: 0;
            line-height: 1.1;
        }
        .wiki-brand-text p {
            font-size: 11px;
            color: #54595d;
            margin: 0;
        }

        .wiki-search-bar {
            flex: 1;
            max-width: 480px;
            position: relative;
            display: flex;
        }
        .wiki-search-input {
            width: 100%;
            background: #ffffff;
            border: 1px solid #a2a9b1;
            color: #202122;
            padding: 7px 12px 7px 34px;
            border-radius: 2px;
            font-size: 13.5px;
            outline: none;
        }
        .wiki-search-input:focus {
            border-color: #3366cc;
            box-shadow: inset 0 0 0 1px #3366cc;
        }
        .search-icon {
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 13px;
            color: #54595d;
        }

        .wiki-header-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .btn-wiki {
            background: #f8f9fa;
            color: #202122;
            border: 1px solid #a2a9b1;
            padding: 6px 12px;
            border-radius: 2px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.1s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            text-decoration: none;
        }
        .btn-wiki:hover {
            background: #eaecf0;
            border-color: #72777d;
        }
        .btn-wiki-primary {
            background: #3366cc;
            color: #ffffff;
            border: 1px solid #2a4b8d;
            font-weight: 600;
        }
        .btn-wiki-primary:hover {
            background: #2a4b8d;
            color: #ffffff;
        }

        /* TWO-COLUMN LAYOUT */
        .wiki-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            min-height: calc(100vh - 65px);
            background: #ffffff;
        }

        /* LEFT SIDEBAR */
        .wiki-sidebar {
            width: 220px;
            flex-shrink: 0;
            border-right: 1px solid #c8ccd1;
            padding: 16px 14px;
            font-size: 13px;
            background: #ffffff;
        }
        .sidebar-section {
            margin-bottom: 20px;
        }
        .sidebar-title {
            font-size: 12px;
            font-weight: bold;
            color: #54595d;
            margin-bottom: 6px;
            padding-bottom: 4px;
            border-bottom: 1px solid #eaecf0;
        }
        .sidebar-menu {
            list-style: none;
        }
        .sidebar-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 5px 6px;
            color: #3366cc;
            text-decoration: none;
            cursor: pointer;
            border-radius: 2px;
        }
        .sidebar-item:hover {
            text-decoration: underline;
            color: #0645ad;
        }
        .sidebar-item.active {
            font-weight: bold;
            color: #202122;
            text-decoration: none;
            background: #f8f9fa;
        }
        .sidebar-badge {
            font-size: 11px;
            background: #f8f9fa;
            color: #54595d;
            padding: 1px 5px;
            border-radius: 9999px;
            border: 1px solid #c8ccd1;
        }

        /* MAIN CONTENT ARTICLE AREA */
        .wiki-main {
            flex: 1;
            padding: 20px 40px;
            background: #ffffff;
            color: #202122;
            overflow-x: hidden;
        }

        /* ARTICLE TABS (Article, Talk, Read, Edit, View history) */
        .article-tabs-bar {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            border-bottom: 1px solid #a2a9b1;
            margin-bottom: 14px;
        }
        .tabs-left, .tabs-right {
            display: flex;
            gap: 2px;
        }
        .article-tab {
            padding: 6px 12px;
            font-size: 13px;
            color: #3366cc;
            text-decoration: none;
            cursor: pointer;
            border-bottom: 2px solid transparent;
        }
        .article-tab:hover {
            text-decoration: underline;
        }
        .article-tab.active {
            color: #202122;
            font-weight: 500;
            border-bottom: 2px solid #3366cc;
            background: #ffffff;
        }

        .article-header {
            margin-bottom: 16px;
        }
        .article-title {
            font-family: var(--serif);
            font-size: 30px;
            font-weight: normal;
            color: #202122;
            margin-bottom: 2px;
            line-height: 1.2;
            border-bottom: 1px solid #a2a9b1;
            padding-bottom: 4px;
        }
        .article-tagline {
            font-size: 12.5px;
            color: #54595d;
            margin-top: 4px;
        }
        .hatnote {
            padding: 4px 0;
            font-size: 13px;
            color: #54595d;
            font-style: italic;
            margin-bottom: 16px;
        }
        .hatnote a, p a {
            color: #3366cc;
            text-decoration: none;
        }
        .hatnote a:hover, p a:hover {
            text-decoration: underline;
        }

        /* WIKIPEDIA INFOBOX */
        .infobox {
            float: right;
            width: 300px;
            margin: 0 0 16px 20px;
            background: #f8f9fa;
            border: 1px solid #a2a9b1;
            font-size: 12.5px;
            padding: 5px;
            line-height: 1.5;
        }
        .infobox-title {
            background: transparent;
            padding: 4px 6px;
            font-family: var(--sans);
            font-size: 14px;
            font-weight: bold;
            text-align: center;
            color: #202122;
        }
        .infobox-image {
            text-align: center;
            padding: 10px;
            font-size: 42px;
        }
        .infobox table {
            width: 100%;
            border-collapse: collapse;
        }
        .infobox th {
            text-align: left;
            padding: 4px 6px;
            color: #202122;
            width: 40%;
            font-weight: bold;
            vertical-align: top;
            border-top: 1px solid #eaecf0;
        }
        .infobox td {
            padding: 4px 6px;
            color: #202122;
            border-top: 1px solid #eaecf0;
        }

        /* TABLE OF CONTENTS */
        .toc-box {
            background: #f8f9fa;
            border: 1px solid #a2a9b1;
            padding: 10px 16px;
            margin: 16px 0 20px 0;
            display: inline-block;
            min-width: 240px;
        }
        .toc-title {
            font-weight: bold;
            font-size: 13px;
            text-align: center;
            margin-bottom: 8px;
            color: #202122;
        }
        .toc-list {
            list-style: none;
            padding-left: 0;
            font-size: 13px;
        }
        .toc-item {
            margin-bottom: 4px;
        }
        .toc-link {
            color: #3366cc;
            text-decoration: none;
        }
        .toc-link:hover {
            text-decoration: underline;
        }

        /* HEADINGS */
        .wiki-h2 {
            font-family: var(--serif);
            font-size: 21px;
            font-weight: normal;
            color: #202122;
            margin: 24px 0 10px 0;
            padding-bottom: 4px;
            border-bottom: 1px solid #a2a9b1;
            clear: both;
        }
        .wiki-h2 .edit-link {
            font-family: var(--sans);
            font-size: 11px;
            font-weight: normal;
            margin-left: 8px;
            color: #3366cc;
            text-decoration: none;
        }
        .wiki-h2 .edit-link:hover {
            text-decoration: underline;
        }

        /* WIKIPEDIA TABLES */
        .wikitable {
            width: 100%;
            border-collapse: collapse;
            background: #ffffff;
            border: 1px solid #a2a9b1;
            margin: 12px 0 20px 0;
            font-size: 13px;
        }
        .wikitable th {
            background: #eaecf0;
            padding: 6px 10px;
            text-align: left;
            font-weight: bold;
            color: #202122;
            border: 1px solid #a2a9b1;
        }
        .wikitable td {
            padding: 6px 10px;
            border: 1px solid #a2a9b1;
            color: #202122;
            background: #ffffff;
        }
        .wikitable tr:hover td {
            background: #f8f9fa;
        }

        /* KBD TAGS */
        .kbd-cap {
            background: #f8f9fa;
            color: #202122;
            font-family: monospace;
            font-size: 11.5px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 2px;
            border: 1px solid #c8ccd1;
            box-shadow: 0 1px 1px rgba(0,0,0,0.1);
            display: inline-block;
        }

        /* WELCOME BANNER */
        .welcome-banner {
            background: #f8f9fa;
            border: 1px solid #a2a9b1;
            padding: 16px 20px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }
        .welcome-title {
            font-family: var(--serif);
            font-size: 24px;
            font-weight: normal;
            color: #202122;
            margin-bottom: 4px;
        }
        .welcome-sub {
            font-size: 13.5px;
            color: #54595d;
        }
        .stats-strip {
            display: flex;
            gap: 18px;
            background: #ffffff;
            padding: 8px 16px;
            border: 1px solid #a2a9b1;
        }
        .stat-item {
            text-align: center;
        }
        .stat-val {
            font-size: 19px;
            font-weight: bold;
            color: #3366cc;
        }
        .stat-lbl {
            font-size: 11px;
            color: #54595d;
            text-transform: uppercase;
        }

        /* APP CARDS GRID */
        .encyclopedia-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 14px;
            margin: 14px 0;
        }
        .encyclo-card {
            background: #ffffff;
            border: 1px solid #a2a9b1;
            padding: 14px;
            cursor: pointer;
            text-decoration: none;
            color: inherit;
            transition: all 0.15s;
        }
        .encyclo-card:hover {
            background: #f8f9fa;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
        .encyclo-card h4 {
            font-family: var(--serif);
            font-size: 17px;
            color: #3366cc;
            margin-bottom: 4px;
        }
        .encyclo-card:hover h4 {
            text-decoration: underline;
        }
        .encyclo-card p {
            font-size: 12.5px;
            color: #54595d;
            line-height: 1.4;
        }

        .last-scan-banner {
            background: #f8f9fa;
            border-left: 4px solid #3366cc;
            border-top: 1px solid #c8ccd1;
            border-right: 1px solid #c8ccd1;
            border-bottom: 1px solid #c8ccd1;
            padding: 8px 14px;
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 13px;
            color: #202122;
            gap: 12px;
        }
        .scan-badge {
            display: inline-block;
            padding: 1px 7px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 2px;
            background: #eaecf0;
            color: #202122;
            border: 1px solid #a2a9b1;
            margin: 0 4px;
        }
        .scan-badge-deepdive {
            background: #eaf3ff;
            color: #3366cc;
            border-color: #a3c7ff;
        }
        .scan-badge-autotour {
            background: #e6f9f0;
            color: #14866d;
            border-color: #8be0bf;
        }
        .scan-badge-hoverrecord {
            background: #fdf2e9;
            color: #b75500;
            border-color: #f5b977;
        }
        .scan-badge-systemprelearn {
            background: #f3e8fd;
            color: #6929c4;
            border-color: #d4bbff;
        }
        .item-chip {
            background: #f8f9fa;
            border: 1px solid #c8ccd1;
            padding: 1px 6px;
            border-radius: 2px;
            font-size: 11.5px;
            display: inline-block;
            margin: 2px 3px 2px 0;
            color: #202122;
        }

        #toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #202122;
            color: white;
            padding: 12px 18px;
            border-radius: 3px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.35);
            font-size: 13px;
            font-weight: 500;
            display: none;
            z-index: 1000;
            max-width: 440px;
            line-height: 1.4;
        }
        #toast a {
            color: #6bb9f0;
            text-decoration: underline;
            margin-left: 8px;
            cursor: pointer;
            font-weight: bold;
        }
        #toast .toast-close {
            float: right;
            margin-left: 12px;
            cursor: pointer;
            color: #a2a9b1;
            font-weight: bold;
            font-size: 14px;
        }
        #toast .toast-close:hover {
            color: #ffffff;
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
            <button id="btnDeepDive" class="btn-wiki btn-wiki-primary" onclick="triggerDeepDive()" title="Exhaustive deep dive: learn every menu, button, and shortcut in the target app">🔬 Deep Dive</button>
            <button id="btnAutoRecord" class="btn-wiki" onclick="triggerAutoMoveRecord()" title="Automatically move mouse over window controls and record into Wikipedia">🎯 Auto-Tour</button>
            <button id="btnRecordCursor" class="btn-wiki" onclick="triggerRecordCursor()" title="Move mouse over any button to record into Wikipedia">🎯 Hover Record</button>
            <button id="btnLog" class="btn-wiki" onclick="navigateTo('history')" title="View recent scan and recording activity log">📜 Scan Log</button>
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
                    <li><a class="sidebar-item" id="menu-history" onclick="navigateTo('history')"><span>📜 Scan History</span> <span class="sidebar-badge" id="sideBadgeScans">0</span></a></li>
                    <li><a class="sidebar-item" id="menu-hotkeys" onclick="navigateTo('hotkeys')"><span>⌨️ Universal Hotkeys</span> <span class="sidebar-badge" id="sideBadgeHotkeys">31</span></a></li>
                    <li><a class="sidebar-item" id="menu-fastpaths" onclick="navigateTo('fastpaths')"><span>⚡ OS Fastpaths</span> <span class="sidebar-badge" id="sideBadgeFastpaths">33</span></a></li>
                    <li><a class="sidebar-item" id="menu-tester" onclick="navigateTo('tester')"><span>🧪 Controls & Tester</span></a></li>
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
                    <li><a class="sidebar-item" href="https://github.com/robertbeck-stack/deskdriver" target="_blank"><span>📦 GitHub Repo</span></a></li>
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

        let toastTimer = null;
        function showToast(msg, duration = 8000) {
            const t = document.getElementById('toast');
            if (!t) return;
            if (toastTimer) clearTimeout(toastTimer);
            t.innerHTML = `
                <span class="toast-close" onclick="document.getElementById('toast').style.display='none'">&times;</span>
                <div style="display: inline-block;">${msg}</div>
                <a onclick="navigateTo('history'); document.getElementById('toast').style.display='none';">[View Log]</a>
            `;
            t.style.display = 'block';
            toastTimer = setTimeout(() => { t.style.display = 'none'; }, duration);
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
            else if (view === 'history') document.getElementById('menu-history')?.classList.add('active');
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
            const scanCount = data.total_scans || 0;
            const badgeHk = document.getElementById('sideBadgeHotkeys');
            const badgeFp = document.getElementById('sideBadgeFastpaths');
            const badgeScans = document.getElementById('sideBadgeScans');
            if (badgeHk) badgeHk.innerText = hkCount;
            if (badgeFp) badgeFp.innerText = fpCount;
            if (badgeScans) badgeScans.innerText = scanCount;
        }

        function getLastScanBannerHtml(data) {
            const lastScan = data?.last_scan;
            if (!lastScan) return '';
            const badgeClass = 'scan-badge-' + (lastScan.action || '').toLowerCase().replace(/[^a-z]/g, '');
            return `
                <div class="last-scan-banner">
                    <div>
                        🕒 <strong>Last Scanned:</strong> 
                        <span class="scan-badge ${badgeClass}">${lastScan.action}</span>
                        <strong>${lastScan.app}</strong> at ${lastScan.time_str || lastScan.timestamp} &mdash; ${lastScan.summary}
                    </div>
                    <button class="btn-wiki" style="font-size: 11px; padding: 2px 8px; white-space: nowrap;" onclick="navigateTo('history')">View Scan Log &rarr;</button>
                </div>
            `;
        }

        function renderCurrentView() {
            if (!fullData) return;
            const container = document.getElementById('wikiArticle');

            if (currentView === 'main') renderMainPage(container);
            else if (currentView === 'history') renderHistoryPage(container);
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

                ${getLastScanBannerHtml(data)}

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
                <div class="article-tabs-bar">
                    <div class="tabs-left">
                        <span class="article-tab active">Article</span>
                        <span class="article-tab">Talk</span>
                    </div>
                    <div class="tabs-right">
                        <span class="article-tab active">Read</span>
                        <span class="article-tab" onclick="navigateTo('history')">View history</span>
                    </div>
                </div>

                ${getLastScanBannerHtml(fullData)}

                <!-- WIKIPEDIA INFOBOX -->
                <div class="infobox">
                    <div class="infobox-title">${appKey.charAt(0).toUpperCase() + appKey.slice(1)} (software)</div>
                    <div class="infobox-image">🖥️</div>
                    <table>
                        <tr><th>Family</th><td>${appKey}</td></tr>
                        <tr><th>Indexed Controls</th><td><strong>${elements.length}</strong> items</td></tr>
                        <tr><th>Shortcuts</th><td><strong>${hotkeyElements.length}</strong> hotkeys</td></tr>
                        <tr><th>Positioning</th><td>Relative + Anchors</td></tr>
                        <tr><th>Cache Storage</th><td><code>ui_roadmap.json</code></td></tr>
                    </table>
                </div>

                <div class="article-header">
                    <h1 class="article-title">${appKey.charAt(0).toUpperCase() + appKey.slice(1)}</h1>
                    <div class="article-tagline">From DeskDriver Wiki, the free encyclopedia</div>
                </div>

                <div class="hatnote">
                    "<em>${appKey} (software)</em>" redirects here. This article documents interactive controls and keyboard accelerators indexed for <strong>${appKey}</strong>.
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

        /* 3. SCAN & REVISION HISTORY PAGE */
        async function renderHistoryPage(container) {
            container.innerHTML = `
                <div class="article-tabs-bar">
                    <div class="tabs-left">
                        <span class="article-tab" onclick="navigateTo('main')">Article</span>
                        <span class="article-tab">Talk</span>
                    </div>
                    <div class="tabs-right">
                        <span class="article-tab" onclick="navigateTo('main')">Read</span>
                        <span class="article-tab active">View history</span>
                    </div>
                </div>

                <div class="article-header">
                    <h1 class="article-title">Scan & Revision History</h1>
                    <div class="article-tagline">From DeskDriver Wiki, the free desktop automation encyclopedia</div>
                </div>

                <div class="hatnote">
                    Chronological record of automated spatial tours, deep dives, and cursor captures recorded into <code>ui_roadmap.json</code>.
                </div>

                <div id="historyTableContainer">
                    <p style="color: var(--text-muted); padding: 12px 0;">Loading activity log...</p>
                </div>
            `;

            try {
                const res = await fetch('/api/logs');
                const data = await res.json();
                const logs = data.logs || [];
                const tableContainer = document.getElementById('historyTableContainer');
                if (!tableContainer) return;

                if (logs.length === 0) {
                    tableContainer.innerHTML = `
                        <div style="background: var(--surface); border: 1px solid var(--border); padding: 32px; text-align: center; margin-top: 16px;">
                            <div style="font-size: 32px; margin-bottom: 8px;">📜</div>
                            <h3 style="font-family: var(--serif); font-size: 19px; margin-bottom: 8px;">No Scans Performed Yet</h3>
                            <p style="color: var(--text-muted); font-size: 13px; max-width: 480px; margin: 0 auto 16px auto;">
                                Click <strong>🔬 Deep Dive</strong> or <strong>🎯 Auto-Tour</strong> in the top header bar to index any open Windows application. Discovered controls and keyboard accelerators will be permanently recorded here.
                            </p>
                            <button class="btn-wiki btn-wiki-primary" onclick="triggerDeepDive()">🔬 Start Deep Dive</button>
                            <button class="btn-wiki" onclick="triggerAutoMoveRecord()" style="margin-left: 8px;">🎯 Start Auto-Tour</button>
                        </div>
                    `;
                    return;
                }

                let rows = '';
                for (const log of logs) {
                    const badgeClass = 'scan-badge-' + (log.action || '').toLowerCase().replace(/[^a-z]/g, '');
                    const appKey = (log.app || '').toLowerCase();
                    const appLink = log.app ? `<a onclick="navigateTo('app', '${appKey}')" style="color: var(--primary); font-weight: bold; cursor: pointer;">${log.app}</a>` : '<span style="color: var(--text-muted);">(System)</span>';
                    const itemsList = (log.items && log.items.length > 0)
                        ? `<div style="margin-top: 6px;">${log.items.slice(0, 12).map(i => `<span class="item-chip">${i}</span>`).join('')}${log.items.length > 12 ? `<span style="font-size: 11px; color: var(--text-muted); margin-left: 4px;">+${log.items.length - 12} more</span>` : ''}</div>`
                        : '';

                    rows += `
                        <tr>
                            <td style="white-space: nowrap; font-size: 12px; color: var(--text-muted); vertical-align: top;">
                                <strong>${log.time_str || ''}</strong><br>
                                <span style="font-size: 11px;">${log.timestamp?.split(' ')[0] || ''}</span>
                            </td>
                            <td style="vertical-align: top;"><span class="scan-badge ${badgeClass}">${log.action}</span></td>
                            <td style="vertical-align: top;">${appLink}</td>
                            <td style="vertical-align: top;">
                                <div><strong>${log.summary}</strong> ${log.duration ? `<small style="color: var(--text-muted);">(${log.duration})</small>` : ''}</div>
                                ${itemsList}
                            </td>
                            <td style="text-align: right; white-space: nowrap; vertical-align: top;">
                                <button class="btn-wiki" style="font-size: 11.5px; padding: 3px 8px;" onclick="navigateTo('app', '${appKey}')">Open Article &rarr;</button>
                            </td>
                        </tr>
                    `;
                }

                tableContainer.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <p style="font-size: 13px; color: var(--text-muted);">
                            Showing <strong>${logs.length}</strong> recorded scan entries (most recent first).
                        </p>
                        <button class="btn-wiki" onclick="renderHistoryPage(document.getElementById('wikiArticle'))">🔄 Refresh Log</button>
                    </div>
                    <table class="wikitable">
                        <thead>
                            <tr>
                                <th style="width: 130px;">Time / Date</th>
                                <th style="width: 130px;">Action</th>
                                <th style="width: 140px;">Application</th>
                                <th>Scan Summary & Discovered Controls</th>
                                <th style="width: 110px; text-align: right;">Roadmap</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows}
                        </tbody>
                    </table>
                `;
            } catch (e) {
                console.error("Error loading logs:", e);
            }
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

        /* 5. TESTER & CONTROLS PAGE */
        function renderTesterPage(container) {
            container.innerHTML = `
                <div class="article-header">
                    <h1 class="article-title">Desktop Automation Controls & Laboratory</h1>
                    <div class="article-tagline">Interactive tools for testing atomic SendInput, window snapping, and clipboard fastpaths</div>
                </div>

                <div class="welcome-banner" style="margin-top: 20px; flex-direction: column; gap: 20px;">
                    <div>
                        <h3 style="color: #fff; margin-bottom: 8px;">🪟 Window Layout & Snapping</h3>
                        <p style="color: var(--text-muted); margin-bottom: 14px;">Reposition or snap any open window to screen halves or center using native Win32 <code>SetWindowPos</code>.</p>
                        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px;">
                            <input type="text" id="snapWindowInput" class="wiki-search-input" style="flex: 1; min-width: 200px; border-radius: 6px; padding: 10px 14px; font-size: 14px;" placeholder="Window title (e.g. Brave, Notepad, Explorer)...">
                            <button class="btn-wiki" onclick="testSnapWindow('left')">⬅️ Left Half</button>
                            <button class="btn-wiki" onclick="testSnapWindow('right')">➡️ Right Half</button>
                            <button class="btn-wiki" onclick="testSnapWindow('center')">🔲 Center</button>
                            <button class="btn-wiki" onclick="testSnapWindow('full')">🗖 Maximize</button>
                            <button class="btn-wiki" onclick="testSnapWindow('minimize')">🗕 Minimize</button>
                        </div>
                    </div>

                    <hr style="border: 0; border-top: 1px solid var(--border-color); width: 100%;">

                    <div>
                        <h3 style="color: #fff; margin-bottom: 8px;">📋 Instant Clipboard Fastpath (0.5 ms Paste)</h3>
                        <p style="color: var(--text-muted); margin-bottom: 14px;">Loads text onto Windows clipboard and triggers atomic <code>Ctrl+V</code> for instant entry of large multi-line text blocks.</p>
                        <div style="display: flex; gap: 10px;">
                            <input type="text" id="pasteTextInput" class="wiki-search-input" style="border-radius: 6px; padding: 10px 14px; font-size: 14px;" placeholder="Text or multiline code to instantly paste...">
                            <button class="btn-wiki btn-wiki-primary" onclick="testPasteClipboard()">⚡ Instant Paste</button>
                        </div>
                    </div>

                    <hr style="border: 0; border-top: 1px solid var(--border-color); width: 100%;">

                    <div>
                        <h3 style="color: #fff; margin-bottom: 8px;">⌨️ Direct SendInput Typing Tester</h3>
                        <p style="color: var(--text-muted); margin-bottom: 14px;">Types Unicode text directly into whatever window currently has focus using atomic Windows <code>SendInput</code>.</p>
                        <div style="display: flex; gap: 10px;">
                            <input type="text" id="typeTextInput" class="wiki-search-input" style="border-radius: 6px; padding: 10px 14px; font-size: 14px;" placeholder="Type text to send to focused window...">
                            <button class="btn-wiki" onclick="testTypeText()">Send Text</button>
                        </div>
                    </div>
                </div>
            `;
        }

        async function triggerRecordCursor() {
            const btn = document.getElementById('btnRecordCursor');
            if (btn) btn.disabled = true;
            showToast("🎯 Move mouse over any UI button (capturing in 3 seconds)...", 3500);
            let left = 3;
            const timer = setInterval(() => {
                left--;
                if (btn) btn.innerText = `🎯 Capturing (${left}s)...`;
                if (left <= 0) {
                    clearInterval(timer);
                    doCapture();
                }
            }, 1000);

            async function doCapture() {
                try {
                    const res = await fetch('/api/record_cursor', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({})
                    });
                    const data = await res.json();
                    if (btn) {
                        btn.disabled = false;
                        btn.innerText = '🎯 Hover Record';
                    }
                    if (data.status === 'element_recorded') {
                        showToast(`✅ Captured "${data.element}" for ${data.app}!`);
                        await fetchStats();
                    } else {
                        showToast(`Capture failed: ${data.error || 'Unknown'}`);
                    }
                } catch (e) {
                    if (btn) {
                        btn.disabled = false;
                        btn.innerText = '🎯 Hover Record';
                    }
                    showToast('Capture error: ' + e);
                }
            }
        }

        async function triggerAutoMoveRecord(appKey) {
            const btn = document.getElementById('btnAutoRecord');
            if (btn) {
                btn.disabled = true;
                btn.innerText = '🎯 Moving Mouse & Scanning...';
            }
            showToast('Starting automated cursor tour: DeskDriver is physically moving the mouse over controls...', 5000);
            try {
                const res = await fetch('/api/auto_record', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ window: appKey || currentApp || '' })
                });
                const data = await res.json();
                if (data.status === 'auto_recorded') {
                    showToast(`✅ Auto-tour complete! Moved cursor and recorded ${data.count} controls for ${data.app}!`);
                    await fetchStats();
                    if (data.app) navigateTo('app', data.app);
                } else {
                    showToast('Scan error: ' + (data.error || 'Unknown error'));
                }
            } catch (e) {
                showToast('Auto-record error: ' + e);
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerText = '🎯 Auto-Tour';
                }
            }
        }

        async function triggerDeepDive(appKey) {
            const btn = document.getElementById('btnDeepDive');
            let target = appKey || (currentView === 'app' ? currentApp : '');
            if (!target) {
                target = prompt('Enter application name or window title to Deep Dive (e.g. Notepad, Brave, Explorer):');
                if (!target) return;
            }

            if (btn) {
                btn.disabled = true;
                btn.innerText = '🔬 Deep Diving...';
            }
            showToast(`🔬 Exhaustive Deep Dive initiated for '${target}': Learning every menu, button, and shortcut...`, 6000);

            try {
                const res = await fetch('/api/deepdive', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ window: target })
                });
                const data = await res.json();
                if (data.status === 'deep_dive_complete') {
                    showToast(`✅ Deep Dive Complete! Indexed ${data.total_elements} controls & ${data.total_shortcuts} shortcuts for ${data.app}!`, 8000);
                    await fetchStats();
                    if (data.app) navigateTo('app', data.app);
                } else {
                    showToast('Deep dive error: ' + (data.error || 'Unknown error'));
                }
            } catch (e) {
                showToast('Deep dive error: ' + e);
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerText = '🔬 Deep Dive';
                }
            }
        }

        async function testSnapWindow(side) {
            const win = document.getElementById('snapWindowInput')?.value || '';
            try {
                const res = await fetch('/api/snap_window', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ window: win, side: side })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(`Snapped window '${win || 'active'}' to ${side}`);
                } else {
                    showToast(`Could not snap window '${win}'`);
                }
            } catch (e) {
                alert("Error: " + e);
            }
        }

        async function testPasteClipboard() {
            const val = document.getElementById('pasteTextInput')?.value;
            if (!val) return;
            try {
                await fetch('/api/paste', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: val })
                });
                showToast(`Pasted ${val.length} chars via clipboard (0.5 ms)`);
                document.getElementById('pasteTextInput').value = '';
            } catch (e) {
                alert("Error: " + e);
            }
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


LOG_FILE = Path(__file__).parent / "scan_history.json"


def load_scan_logs():
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_scan_logs(logs):
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs[:150], f, indent=2, ensure_ascii=False)
    except Exception:
        pass


SCAN_LOGS = load_scan_logs()


def add_scan_log(
    action: str,
    app: str,
    summary: str,
    count: int = 0,
    shortcuts_count: int = 0,
    items: list | None = None,
    duration: float = 0.0,
    status: str = "success",
):
    entry = {
        "id": len(SCAN_LOGS) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "time_str": datetime.now().strftime("%H:%M:%S"),
        "action": action,
        "app": app,
        "summary": summary,
        "count": count,
        "shortcuts_count": shortcuts_count,
        "items": items or [],
        "duration": f"{duration:.2f}s" if duration else "",
        "status": status,
    }
    SCAN_LOGS.insert(0, entry)
    if len(SCAN_LOGS) > 150:
        SCAN_LOGS.pop()
    save_scan_logs(SCAN_LOGS)
    return entry


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
                "last_scan": SCAN_LOGS[0] if SCAN_LOGS else None,
                "total_scans": len(SCAN_LOGS),
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        elif clean_path == "/api/logs":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            self.wfile.write(
                json.dumps(
                    {
                        "logs": SCAN_LOGS,
                        "last_scan": SCAN_LOGS[0] if SCAN_LOGS else None,
                        "total_scans": len(SCAN_LOGS),
                    },
                    ensure_ascii=False,
                ).encode("utf-8")
            )
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
            if isinstance(res, dict):
                apps = res.get("scanned_apps", [])
                add_scan_log(
                    action="System Pre-Learn",
                    app=f"{len(apps)} Apps",
                    summary=f"Full scan indexed {res.get('total_new_elements', 0)} controls across {len(apps)} applications",
                    count=res.get("total_new_elements", 0),
                    items=apps,
                )
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

        elif clean_path == "/api/record_cursor":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            res = am.record_element_at_cursor(custom_name=req_data.get("name", ""))
            if isinstance(res, dict) and res.get("status") == "element_recorded":
                add_scan_log(
                    action="Hover Record",
                    app=res.get("app") or "Application",
                    summary=f"Captured '{res.get('element')}' ({res.get('control_type')})",
                    count=1,
                    items=[res.get("element")],
                )
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))

        elif clean_path == "/api/auto_record":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            win = req_data.get("window", "")
            res = am.auto_record_window(window_search=win, move_cursor=True)
            if isinstance(res, dict) and res.get("status") == "auto_recorded":
                add_scan_log(
                    action="Auto-Tour",
                    app=res.get("app") or win or "Application",
                    summary=f"Automated cursor tour recorded {res.get('count', 0)} controls",
                    count=res.get("count", 0),
                    items=res.get("recorded_elements", [])[:25],
                )
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))

        elif clean_path == "/api/deepdive":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            win = req_data.get("window", "")
            res = am.deep_dive_app(window_search=win)
            if isinstance(res, dict) and res.get("status") == "deep_dive_complete":
                discovered = [el.get("name") for el in res.get("discovered_elements", []) if el.get("name")]
                add_scan_log(
                    action="Deep Dive",
                    app=res.get("app") or win or "Application",
                    summary=f"Indexed {res.get('total_elements', 0)} controls & {res.get('total_shortcuts', 0)} shortcuts",
                    count=res.get("total_elements", 0),
                    shortcuts_count=res.get("total_shortcuts", 0),
                    items=discovered[:25],
                    duration=res.get("duration_seconds", 0.0),
                )
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))

        elif clean_path == "/api/snap_window":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            win = req_data.get("window", "")
            side = req_data.get("side", "left")
            ok = am.snap_window(win, side=side)
            self.wfile.write(json.dumps({"success": ok, "window": win, "side": side}).encode("utf-8"))

        elif clean_path == "/api/paste":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            text = req_data.get("text", "")
            ok = am.clipboard_paste(text) if text else False
            self.wfile.write(json.dumps({"success": ok, "length": len(text)}).encode("utf-8"))
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
