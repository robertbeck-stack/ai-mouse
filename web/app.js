let fullData = null;
let currentView = 'main';
let currentApp = null;

// Everything rendered here comes from window titles, control names and saved
// actions - i.e. text other programs and web pages control. Always pass it through
// esc() for HTML and jsArg() for inline onclick arguments.
const HTML_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => HTML_ESCAPES[c]);
}
function jsArg(value) {
    return esc(JSON.stringify(String(value ?? '')));
}
// Apps are keyed by executable ("notepad.exe", "notepad.exe/page setup");
// show their display name and accept either form when matching.
function appLabel(key) {
    const entry = ((fullData && fullData.roadmap) || {})[key] || {};
    const name = entry.display_name || key;
    return entry.surface ? `${name} › ${entry.surface}` : name;
}
function findAppKey(name) {
    const roadmap = (fullData && fullData.roadmap) || {};
    const low = String(name || '').trim().toLowerCase();
    if (!low) return null;
    const keys = Object.keys(roadmap);
    // Exact key first, so "explorer.exe" isn't claimed by "explorer.exe#shell_traywnd"
    return keys.find(k => k.toLowerCase() === low) || keys.find(k => {
        const e = roadmap[k] || {};
        const exe = (e.exe || '').toLowerCase();
        const isMainWindow = k.toLowerCase() === exe;
        return !e.surface && ((e.display_name || '').toLowerCase() === low
            || (isMainWindow && exe.replace(/\.exe$/, '') === low));
    }) || null;
}
// Dialogs ("notepad.exe/page setup") are stored separately because their
// coordinates are relative to their own window, but they're listed under
// the app that owns them. A dialog whose owner isn't learned stays top-level.
function isSubWindow(key, roadmap) {
    const slash = key.indexOf('/');
    return slash > 0 && key.slice(0, slash) in roadmap;
}
function subWindowKeys(appKey) {
    const roadmap = (fullData && fullData.roadmap) || {};
    return Object.keys(roadmap).filter(k => k.startsWith(appKey + '/')).sort();
}
// "explorer.exe, notepad.exe (+2 more)" -> "File Explorer, Notepad (+2 more)"
function appListLabel(text) {
    return String(text || '').split(', ').map(part => {
        const key = findAppKey(part);
        return key ? appLabel(key) : part;
    }).join(', ');
}
function sortedAppKeys(roadmap) {
    return Object.keys(roadmap)
        .filter(k => !isSubWindow(k, roadmap))
        .sort((a, b) => appLabel(a).localeCompare(appLabel(b)));
}

let toastTimer = null;
function showToast(msg, duration = 8000) {
    const t = document.getElementById('toast');
    if (!t) return;
    if (toastTimer) clearTimeout(toastTimer);
    t.innerHTML = `
        <span class="toast-close" onclick="document.getElementById('toast').style.display='none'">&times;</span>
        <div style="display: inline-block;">${esc(msg)}</div>
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
    else if (view === 'actions') document.getElementById('menu-actions')?.classList.add('active');
    else if (view === 'history') document.getElementById('menu-history')?.classList.add('active');
    else if (view === 'hotkeys') document.getElementById('menu-hotkeys')?.classList.add('active');
    else if (view === 'fastpaths') document.getElementById('menu-fastpaths')?.classList.add('active');
    else if (view === 'tester') document.getElementById('menu-tester')?.classList.add('active');
    else if (view === 'mcp') document.getElementById('menu-mcp')?.classList.add('active');
    else if (view === 'app' && appKey) {
        document.getElementById('side-app-' + appKey.split('/')[0])?.classList.add('active');
    }

    renderCurrentView();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderSidebar(data) {
    const list = document.getElementById('sidebarAppsList');
    if (!list) return;
    list.innerHTML = '';

    const roadmap = data.roadmap || {};
    // Sidebar lists the raw app keys (executables); the main page shows display names
    for (const appKey of Object.keys(roadmap).filter(k => !isSubWindow(k, roadmap)).sort()) {
        const appData = roadmap[appKey];
        const count = Object.keys(appData.elements || {}).length;
        // A window class sharing another app's exe ("explorer.exe#shell_traywnd")
        // shows as "explorer.exe · Taskbar" instead of the raw class name
        const hash = appKey.indexOf('#');
        const keyHtml = hash > 0
            ? `${esc(appKey.slice(0, hash))}<span class="sidebar-key-sub"> · ${esc(appData.display_name || appKey.slice(hash + 1))}</span>`
            : esc(appKey);
        const li = document.createElement('li');
        li.innerHTML = `
            <a class="sidebar-item" id="side-app-${esc(appKey)}" title="${esc(appLabel(appKey))} (${esc(appKey)})" onclick="navigateTo('app', ${jsArg(appKey)})">
                <span class="sidebar-key">${keyHtml}</span>
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
    const badgeAct = document.getElementById('sideBadgeActions');
    if (badgeHk) badgeHk.innerText = hkCount;
    if (badgeFp) badgeFp.innerText = fpCount;
    if (badgeScans) badgeScans.innerText = scanCount;
    if (badgeAct && data.total_actions !== undefined) badgeAct.innerText = data.total_actions;
}

function getLastScanBannerHtml(data) {
    const lastScan = data?.last_scan;
    if (!lastScan) return '';
    const badgeClass = 'scan-badge-' + (lastScan.action || '').toLowerCase().replace(/[^a-z]/g, '');
    return `
        <div class="last-scan-banner">
            <div>
                🕒 <strong>Last Scanned:</strong> 
                <span class="scan-badge ${badgeClass}">${esc(lastScan.action)}</span>
                <strong>${esc(appListLabel(lastScan.app))}</strong> at ${esc(lastScan.time_str || lastScan.timestamp)} &mdash; ${esc(lastScan.summary)}
            </div>
            <button class="btn-wiki" style="font-size: 11px; padding: 2px 8px; white-space: nowrap;" onclick="navigateTo('history')">View Scan Log &rarr;</button>
        </div>
    `;
}

function renderCurrentView() {
    if (!fullData) return;
    const container = document.getElementById('wikiArticle');

    if (currentView === 'main') renderMainPage(container);
    else if (currentView === 'actions') renderActionsPage(container);
    else if (currentView === 'history') renderHistoryPage(container);
    else if (currentView === 'app') renderAppPage(container, currentApp);
    else if (currentView === 'hotkeys') renderHotkeysPage(container);
    else if (currentView === 'fastpaths') renderFastpathsPage(container);
    else if (currentView === 'tester') renderTesterPage(container);
    else if (currentView === 'mcp') renderMcpPage(container);
}

/* 1. MAIN ENCYCLOPEDIA PAGE */
function renderMainPage(container) {
    const data = fullData;
    const roadmap = data.roadmap || {};
    const appCount = sortedAppKeys(roadmap).length;
    const elCount = data.total_elements || 0;
    const hkCount = Object.keys(data.common_hotkeys || {}).length;
    const fpCount = Object.keys(data.fastpaths || {}).length;

    let appsCardsHtml = '';
    for (const key of sortedAppKeys(roadmap)) {
        const val = roadmap[key];
        const count = Object.keys(val.elements || {}).length;
        appsCardsHtml += `
            <a class="encyclo-card" title="${esc(key)} · ${count} controls" onclick="navigateTo('app', ${jsArg(key)})">
                <span class="card-name">${esc(appLabel(key))}</span>
                <span class="card-count">${count}</span>
            </a>`;
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
        <p style="color: var(--text-muted); margin-bottom: 4px; font-size: 12.5px;">${appCount} apps learned into <code>ui_roadmap/</code> · number = indexed controls</p>
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
                    <td>${hkCount} Global Windows Accelerators (Save, Copy, Paste, Snip, Task Manager)</td>
                    <td><span style="color: var(--success); font-weight: 600;">0.5 ms</span></td>
                    <td><button class="btn-wiki btn-sm" onclick="navigateTo('hotkeys')">Open Article</button></td>
                </tr>
                <tr>
                    <td><strong><a onclick="navigateTo('fastpaths')" style="color: var(--primary); cursor: pointer;">Windows OS Fastpaths</a></strong></td>
                    <td>${fpCount} Zero-click URI schemes for native settings, apps, and diagnostics</td>
                    <td><span style="color: var(--success); font-weight: 600;">0.0 ms</span></td>
                    <td><button class="btn-wiki btn-sm" onclick="navigateTo('fastpaths')">Open Article</button></td>
                </tr>
                <tr>
                    <td><strong><a onclick="navigateTo('mcp')" style="color: var(--primary); cursor: pointer;">AI / MCP Setup</a></strong></td>
                    <td>Give Claude, Cursor or another MCP client access to this desktop</td>
                    <td>&mdash;</td>
                    <td><button class="btn-wiki btn-sm" onclick="navigateTo('mcp')">Open Article</button></td>
                </tr>
            </tbody>
        </table>
    `;
}

/* 2. APPLICATION ARTICLE PAGE */
function renderAppPage(container, appKey) {
    const appData = (fullData.roadmap || {})[appKey];
    if (!appData) {
        container.innerHTML = `<h2>Application '${esc(appKey)}' not found.</h2>`;
        return;
    }

    const appTitle = appLabel(appKey);
    const ownerKey = isSubWindow(appKey, fullData.roadmap) ? appKey.slice(0, appKey.indexOf('/')) : null;
    const subKeys = subWindowKeys(appKey);
    const subWindowNote = ownerKey ? `
        <div class="hatnote">This is a dialog of <a onclick="navigateTo('app', ${jsArg(ownerKey)})" style="color: var(--primary); cursor: pointer;">${esc(appLabel(ownerKey))}</a>, stored separately because its coordinates are relative to the dialog window.</div>
    ` : subKeys.length ? `
        <div class="hatnote">Dialogs: ${subKeys.map(k => `<a onclick="navigateTo('app', ${jsArg(k)})" style="color: var(--primary); cursor: pointer;">${esc(fullData.roadmap[k].surface || k)}</a> (${Object.keys(fullData.roadmap[k].elements || {}).length})`).join(' · ')}</div>
    ` : '';
    const elements = Object.values(appData.elements || {});
    const hotkeyElements = elements.filter(e => e.shortcut);
    // Pure hotkey entries have no position; they're listed under Keyboard Accelerators only
    const ctrlElements = elements.filter(e => e.control_type !== 'HotkeyAction');
    const proc = appData.process_info || {};

    const btnCount = ctrlElements.filter(e => /button|toolbar/i.test(e.control_type || '')).length;
    const menuCount = ctrlElements.filter(e => /menu/i.test(e.control_type || '')).length;
    const inputCount = ctrlElements.filter(e => /edit|combobox|spinner|document/i.test(e.control_type || '')).length;
    const tabCount = ctrlElements.filter(e => /tab|list|tree|item/i.test(e.control_type || '')).length;
    const toggleCount = ctrlElements.filter(e => /check|radio|toggle/i.test(e.control_type || '')).length;

    let hkRows = '';
    for (const h of hotkeyElements) {
        const actionCode = h.ai_action || `hotkey:${h.shortcut.toLowerCase()}`;
        hkRows += `
            <tr>
                <td title="${esc(h.name)}"><strong>${esc(h.name)}</strong></td>
                <td><kbd class="kbd-cap">${esc(h.shortcut.toUpperCase())}</kbd></td>
                <td><code class="recipe" title="Click to copy" onclick="copyAndToast(${jsArg(actionCode)})">${esc(actionCode)}</code></td>
                <td><button class="btn-wiki btn-sm" onclick="triggerHotkey(${jsArg(h.shortcut)})">Press</button></td>
            </tr>`;
    }

    const ANCHOR_MARK = { rb: ' ↘', r: ' →', b: ' ↓' };
    // Run focuses the app first (dialogs: their owner) so the recipe hits the right window
    const focusKey = ownerKey || appKey;
    let elRows = '';
    for (const el of ctrlElements) {
        const anchor = el.anchor_right && el.anchor_bottom ? 'rb' : el.anchor_right ? 'r' : el.anchor_bottom ? 'b' : '';
        const anchorTitle = { rb: 'anchored to bottom-right', r: 'anchored to right edge', b: 'anchored to bottom edge' }[anchor] || 'relative to top-left';
        const actionCode = el.ai_action || (el.shortcut ? `hotkey:${el.shortcut.toLowerCase()}` : `click:${el.name}`);
        const tooltip = [el.name, el.help_text, el.container_path && `in: ${el.container_path}`].filter(Boolean).join('\n');
        const shortType = (el.control_type || '').replace(/Control$/, '');

        elRows += `
            <tr class="ctrl-row" data-type="${esc((el.control_type || '').toLowerCase())}" data-shortcut="${el.shortcut ? '1' : '0'}">
                <td title="${esc(tooltip)}"><strong>${esc(el.name)}</strong>${el.shortcut ? ` <kbd class="kbd-cap">${esc(el.shortcut.toUpperCase())}</kbd>` : ''}</td>
                <td class="ctrl-type">${esc(shortType)}</td>
                <td><code class="recipe" title="Click to copy" onclick="copyAndToast(${jsArg(actionCode)})">${esc(actionCode)}</code></td>
                <td class="ctrl-pos" title="${esc(anchorTitle)}">${esc(el.rel_x)}, ${esc(el.rel_y)}${ANCHOR_MARK[anchor] || ''}</td>
                <td>${actionCode.startsWith('fill:') ? '' : `<button class="btn-wiki btn-wiki-primary btn-sm" title="Focus ${esc(appLabel(focusKey))} and run" onclick="runCustomActionString(${jsArg(`focus:${focusKey} | ${actionCode}`)})">▶ Run</button>`}</td>
            </tr>`;
    }

    const canvasBadge = proc.is_canvas_game ? `
        <tr><th>Engine</th><td><span class="scan-badge scan-badge-actionpipeline" style="font-weight:bold;">🎮 ${esc(proc.engine)}</span></td></tr>
    ` : '';

    const procRows = proc.pid ? `
        <tr><th>Process</th><td><code>${esc(proc.exe_name || 'N/A')}</code> · PID ${esc(proc.pid)}</td></tr>
        <tr><th>Class</th><td><code>${esc(proc.class_name || 'N/A')}</code></td></tr>
        ${canvasBadge}
        <tr><th>DPI</th><td>${esc(proc.dpi || 96)} · ${esc(proc.architecture || 'x64')}</td></tr>
    ` : '';

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

        <!-- WIKIPEDIA INFOBOX -->
        <div class="infobox">
            <div class="infobox-title">${esc(appTitle)} (software)</div>
            <div class="infobox-image">🖥️</div>
            <table>
                <tr><th>App Key</th><td><code>${esc(appKey)}</code></td></tr>
                ${procRows}
                <tr><th>Controls</th><td><strong>${elements.length}</strong></td></tr>
                <tr><th>Shortcuts</th><td><strong>${hotkeyElements.length}</strong></td></tr>
                <tr><th>Storage</th><td><code>${esc((fullData.storage_files || {})[appKey] || 'ui_roadmap/')}</code></td></tr>
            </table>
        </div>

        <div class="article-header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap;">
                <div>
                    <h1 class="article-title">${esc(appTitle)}</h1>
                    <div class="article-tagline">From DeskDriver Wiki, the free desktop automation encyclopedia</div>
                </div>
                <div style="display: flex; gap: 8px; margin-top: 6px;">
                    <button id="btnDeepDive" class="btn-wiki btn-wiki-primary" onclick="triggerDeepDive(${jsArg(appKey)})" title="Exhaustive deep dive: inspect process specs, menus, toolbars, buttons, inputs, and shortcuts">🔬 Deep Dive</button>
                </div>
            </div>
        </div>

        ${proc.is_canvas_game ? `
            <div class="hatnote" style="border-left: 4px solid #f2994a; background: #fffdf5; padding: 10px 14px; margin-bottom: 16px;">
                🎮 <strong>Hardware Canvas / Game Engine Detected (${esc(proc.engine)}):</strong><br>
                This application renders directly to the GPU without native Windows UIA controls. DeskDriver automatically controls it using <strong>Zero-Latency Keyboard Accelerators</strong> and <strong>Responsive Spatial Grid Anchors</strong>.
            </div>
        ` : ''}

        ${subWindowNote}

        <div class="toc-box">
            <div class="toc-title">Contents</div>
            <ul class="toc-list">
                <li class="toc-item"><a class="toc-link" href="#sec-shortcuts">1 Keyboard Accelerators (${hotkeyElements.length})</a></li>
                <li class="toc-item"><a class="toc-link" href="#sec-controls">2 UI Elements & Recipes (${ctrlElements.length})</a></li>
                <li class="toc-item" id="tocTree" style="display: none;"><a class="toc-link" href="#sec-tree">3 Menu Hierarchy</a></li>
            </ul>
        </div>

        <h2 class="wiki-h2" id="sec-shortcuts">1 Keyboard Accelerators</h2>
        <table class="wikitable compact-table">
            <colgroup><col style="width:34%"><col style="width:16%"><col><col style="width:70px"></colgroup>
            <thead>
                <tr><th>Action / Control</th><th>Key</th><th>Recipe (click to copy)</th><th></th></tr>
            </thead>
            <tbody>
                ${hkRows || '<tr><td colspan="4" style="color: var(--text-muted);">No specific hotkeys mapped yet.</td></tr>'}
            </tbody>
        </table>

        <h2 class="wiki-h2" id="sec-controls">2 UI Elements & Recipes</h2>

        <div class="wiki-filter-bar" style="margin-bottom: 12px; display: flex; gap: 6px; flex-wrap: wrap;">
            <button class="btn-wiki btn-filter active" onclick="filterCtrlTable('all', this)">All (${ctrlElements.length})</button>
            ${menuCount ? `<button class="btn-wiki btn-filter" onclick="filterCtrlTable('menu', this)">📂 Menus (${menuCount})</button>` : ''}
            ${btnCount ? `<button class="btn-wiki btn-filter" onclick="filterCtrlTable('button', this)">🔘 Buttons (${btnCount})</button>` : ''}
            ${inputCount ? `<button class="btn-wiki btn-filter" onclick="filterCtrlTable('edit', this)">📝 Inputs (${inputCount})</button>` : ''}
            ${tabCount ? `<button class="btn-wiki btn-filter" onclick="filterCtrlTable('tab', this)">📑 Tabs & Lists (${tabCount})</button>` : ''}
            ${toggleCount ? `<button class="btn-wiki btn-filter" onclick="filterCtrlTable('toggle', this)">🎛️ Toggles (${toggleCount})</button>` : ''}
            ${hotkeyElements.length ? `<button class="btn-wiki btn-filter" onclick="filterCtrlTable('shortcut', this)">⌨️ Shortcuts (${hotkeyElements.length})</button>` : ''}
        </div>

        <table class="wikitable compact-table" id="ctrlTable">
            <colgroup><col style="width:34%"><col style="width:12%"><col><col style="width:90px"><col style="width:64px"></colgroup>
            <thead>
                <tr><th>Control</th><th>Type</th><th>Recipe (click to copy)</th><th title="Window-relative position; arrows mark right/bottom anchoring">Position</th><th></th></tr>
            </thead>
            <tbody>
                ${elRows || '<tr><td colspan="5" style="color: var(--text-muted);">No controls indexed yet. Click 🔬 Deep Dive above.</td></tr>'}
            </tbody>
        </table>

        <div id="treeSection" style="display: none;">
            <h2 class="wiki-h2" id="sec-tree">3 Menu Hierarchy</h2>
            <div id="appTreeContainer"></div>
        </div>
    `;

    // Infobox values are cut to one line; show the full text on hover
    container.querySelectorAll('.infobox td').forEach(td => { td.title = td.textContent.trim(); });
    loadAppTree(appKey);
}

// Section 3 lists only what the controls table can't: submenu contents from the
// built-in menu hierarchies (Notepad, Paint) and the Windows Settings categories.
// Apps without either keep the section hidden.
async function loadAppTree(appKey) {
    const container = document.getElementById('appTreeContainer');
    if (!container) return;
    let data;
    try {
        const res = await fetch(`/api/app_tree?app=${encodeURIComponent(appKey)}`);
        data = await res.json();
    } catch (e) {
        return;
    }
    if (currentApp !== appKey || !document.getElementById('appTreeContainer')) return;

    const branches = data.tree || [];
    const folders = data.is_settings
        ? branches
        : branches.flatMap(b => (b.sub_branches || []).filter(sub => sub.type === 'MenuFolder'));
    if (!folders.length) return;

    const focusKey = appKey.split('/')[0];
    let html = '';
    for (const folder of folders) {
        let rows = '';
        for (const item of folder.children || []) {
            const chain = item.action_chain || '';
            const runChain = data.is_settings ? chain : `focus:${focusKey} | ${chain}`;
            rows += `
                <tr>
                    <td title="${esc(item.name)}"><strong>${esc(item.name)}</strong>${item.shortcut ? ` <kbd class="kbd-cap">${esc(item.shortcut)}</kbd>` : ''}</td>
                    <td><code class="recipe" title="Click to copy" onclick="copyAndToast(${jsArg(chain)})">${esc(chain)}</code></td>
                    <td><button class="btn-wiki btn-wiki-primary btn-sm" onclick="runCustomActionString(${jsArg(runChain)})">▶ Run</button></td>
                </tr>`;
        }
        html += `
            <details class="tree-folder" ${folders.length <= 6 ? 'open' : ''}>
                <summary>${esc(folder.name)} <span style="font-weight: normal; color: var(--text-muted); font-size: 11px;">(${(folder.children || []).length})</span></summary>
                <table class="wikitable compact-table">
                    <colgroup><col style="width:40%"><col><col style="width:64px"></colgroup>
                    <tbody>${rows}</tbody>
                </table>
            </details>`;
    }
    container.innerHTML = html;
    document.getElementById('treeSection').style.display = '';
    document.getElementById('tocTree').style.display = '';
}

async function runCustomActionString(actStr) {
    if (!actStr) return;
    showToast(`⚡ Running action chain: ${actStr}...`, 3000);
    try {
        const res = await fetch('/api/run_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: actStr })
        });
        const data = await res.json();
        if (data.status === 'completed') {
            showToast(`✅ Executed chain '${actStr}' (${data.duration_seconds}s)!`, 5000);
        } else {
            showToast(`Chain: ${data.error || 'finished'}`);
        }
    } catch (e) {
        showToast(`Error: ${e}`);
    }
}

function copyToClipboard(txt) {
    navigator.clipboard.writeText(txt).then(() => {
        showToast(`📋 Copied to clipboard: ${txt}`, 3000);
    });
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
            Chronological record of automated spatial tours, deep dives, and cursor captures recorded into <code>ui_roadmap/</code>.
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
                        Click <strong>🔬 Deep Dive</strong> in the top header bar to index any open Windows application. Discovered controls, process specs, and keyboard accelerators will be permanently recorded here.
                    </p>
                    <button class="btn-wiki btn-wiki-primary" onclick="triggerDeepDive()">🔬 Start Deep Dive</button>
                </div>
            `;
            return;
        }

        let rows = '';
        for (const log of logs) {
            const badgeClass = 'scan-badge-' + (log.action || '').toLowerCase().replace(/[^a-z]/g, '');
            // Only link apps that have an article; "3 Apps", "Action Pipeline" etc. do not.
            const appKey = findAppKey(log.app);
            const appLink = appKey
                ? `<a onclick="navigateTo('app', ${jsArg(appKey)})" style="color: var(--primary); font-weight: bold; cursor: pointer;">${esc(appLabel(appKey))}</a>`
                : (log.app ? `<span style="font-weight: bold;">${esc(log.app)}</span>` : '<span style="color: var(--text-muted);">(System)</span>');
            let newSection = '';
            if (log.new_items && log.new_items.length > 0) {
                newSection = `
                    <div style="margin-top: 6px;">
                        <span style="font-size: 11px; font-weight: bold; color: #14866d; background: #e6f9f0; border: 1px solid #8be0bf; padding: 1px 6px; border-radius: 2px;">
                            ✨ Newly Discovered (+${log.new_count || log.new_items.length}):
                        </span>
                        <div style="margin-top: 4px;">
                            ${log.new_items.slice(0, 15).map(i => {
                                const label = (typeof i === 'object' && i !== null) ? (i.name || i.window_title || i.app || JSON.stringify(i)) : i;
                                return `<span class="item-chip" style="background: #e6f9f0; border-color: #8be0bf; color: #14866d; font-weight: 600;">+ ${esc(label)}</span>`;
                            }).join('')}
                            ${log.new_items.length > 15 ? `<span style="font-size: 11px; color: var(--text-muted); margin-left: 4px;">+${log.new_items.length - 15} more</span>` : ''}
                        </div>
                    </div>
                `;
            } else if (log.new_count === 0 && log.count > 0) {
                newSection = `
                    <div style="margin-top: 4px; font-size: 11.5px; color: var(--text-muted); font-style: italic;">
                        (0 new &mdash; all ${esc(log.count)} controls were already indexed in roadmap)
                    </div>
                `;
            }

            const itemsList = (log.items && log.items.length > 0)
                ? `<div style="margin-top: 6px; font-size: 11.5px; color: var(--text-muted);"><span style="font-weight: 600;">All scanned:</span> ${log.items.slice(0, 10).map(i => {
                    const label = (typeof i === 'object' && i !== null) ? (i.window_title ? `${i.window_title} (${i.elements_count || 0})` : (i.app || i.name || JSON.stringify(i))) : i;
                    return `<span class="item-chip">${esc(label)}</span>`;
                }).join('')}${log.items.length > 10 ? `<span style="font-size: 11px; color: var(--text-muted); margin-left: 4px;">+${log.items.length - 10} more</span>` : ''}</div>`
                : '';

            rows += `
                <tr>
                    <td style="white-space: nowrap; font-size: 12px; color: var(--text-muted); vertical-align: top;">
                        <strong>${esc(log.time_str || '')}</strong><br>
                        <span style="font-size: 11px;">${esc(log.timestamp?.split(' ')[0] || '')}</span>
                    </td>
                    <td style="vertical-align: top;"><span class="scan-badge ${badgeClass}">${esc(log.action)}</span></td>
                    <td style="vertical-align: top;">${appLink}</td>
                    <td style="vertical-align: top;">
                        <div><strong>${esc(log.summary)}</strong> ${log.duration ? `<small style="color: var(--text-muted);">(${esc(log.duration)})</small>` : ''}</div>
                        ${newSection}
                        ${itemsList}
                    </td>
                    <td style="text-align: right; white-space: nowrap; vertical-align: top;">
                        ${appKey ? `<button class="btn-wiki" style="font-size: 11.5px; padding: 3px 8px;" onclick="navigateTo('app', ${jsArg(appKey)})">Open Article &rarr;</button>` : ''}
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
        const tc = document.getElementById('historyTableContainer');
        if (tc) tc.innerHTML = `<p style="color: #d33;">Error loading activity log: ${esc(e)}</p>`;
    }
}

/* 3. UNIVERSAL HOTKEYS ARTICLE */
function renderHotkeysPage(container) {
    const hotkeys = fullData.common_hotkeys || {};
    let rows = '';
    for (const [action, key] of Object.entries(hotkeys)) {
        rows += `
            <tr>
                <td><strong>${esc(action)}</strong></td>
                <td><kbd class="kbd-cap">${esc(key.toUpperCase())}</kbd></td>
                <td><span style="color: var(--success); font-weight: 600;">0.5 ms</span></td>
                <td><button class="btn-wiki btn-sm" onclick="triggerHotkey(${jsArg(key)})">Press</button></td>
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
                <td><strong>${esc(key)}</strong></td>
                <td><code style="color: var(--primary);">${esc(uri)}</code></td>
                <td style="color: var(--text-muted);">Directly opens ${esc(key)} settings or native tool</td>
                <td><button class="btn-wiki btn-sm" onclick="launchFastpath(${jsArg(key)})">Launch</button></td>
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

/* 5. ACTION PIPELINES & MACROS PAGE */
async function renderActionsPage(container) {
    container.innerHTML = `
        <div class="article-header">
            <h1 class="article-title">⚡ Desktop Action Pipelines & Macros</h1>
            <div class="article-tagline">Chained sequences of desktop actions executed at zero AI token cost. Run, save, or test custom action strings.</div>
        </div>

        <div class="hatnote">
            <strong>Action String Syntax:</strong> Chain multiple actions using <code>|</code> or <code>&nbsp;-&gt;&nbsp;</code> (with spaces).<br>
            Commands supported: <code>open:&lt;app&gt;</code>, <code>focus:&lt;win&gt;</code>, <code>click:&lt;element or x,y&gt;</code>, <code>type:&lt;text&gt;</code>, <code>fill:&lt;field&gt;, &lt;text&gt;</code>, <code>key:&lt;hotkey&gt;</code>, <code>wait:&lt;seconds&gt;</code>, <code>snap:&lt;left|right&gt;</code>.
        </div>

        <!-- PIPELINE RUNNER & CREATOR -->
        <div style="background: var(--surface); border: 1px solid var(--border); padding: 18px 20px; margin: 18px 0;">
            <h3 style="font-family: var(--serif); font-size: 16px; margin-bottom: 8px;">▶ Custom Pipeline Console</h3>
            <p style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 12px;">Type or paste any action string below to test live execution on your Windows desktop:</p>
            <div style="display: flex; gap: 8px; margin-bottom: 10px;">
                <input type="text" id="customActionInput" class="wiki-search-input" style="flex: 1; padding: 8px 12px; font-family: monospace; font-size: 13px;" placeholder="e.g. open:notepad | wait:0.3 | hotkey:ctrl+n | type:Halló heimur | key:enter" value="open:notepad | wait:0.4 | hotkey:ctrl+n | type:Halló heimur | key:enter">
                <button class="btn-wiki btn-wiki-primary" onclick="runCustomAction()" id="btnRunCustom">⚡ Execute</button>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                <input type="text" id="customActionName" class="wiki-search-input" style="max-width: 240px; padding: 6px 10px; font-size: 12.5px;" placeholder="Macro name (e.g. minnisblad)...">
                <button class="btn-wiki" onclick="saveCustomAction()">💾 Save as Named Macro</button>
            </div>
        </div>

        <!-- SAVED ACTIONS LIST -->
        <h2 class="wiki-h2">Saved Reusable Action Pipelines</h2>
        <div id="savedActionsContainer" style="margin-top: 12px;">
            <p style="color: var(--text-muted); font-size: 13px;">Loading saved action pipelines...</p>
        </div>
    `;

    loadSavedActionsList();
}

async function loadSavedActionsList() {
    const container = document.getElementById('savedActionsContainer');
    if (!container) return;
    try {
        const res = await fetch('/api/actions');
        const data = await res.json();
        const actions = data.actions || {};
        const keys = Object.keys(actions);

        if (keys.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted);">No saved action pipelines yet.</p>';
            return;
        }

        let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';
        for (const name of keys) {
            const actStr = actions[name];
            // Same delimiters as parse_action_string (a bare "->" belongs to drag coordinates)
            const steps = actStr.split(/\s*(?:\||\s->\s|;|\n)\s*/).filter(Boolean);
            const stepsChips = steps.map(s => `<span class="item-chip" style="background:#f0f2f5; font-family:monospace;">${esc(s)}</span>`).join(' <span style="color:#a2a9b1;">&rarr;</span> ');
            html += `
                <div style="background: #ffffff; border: 1px solid var(--border); padding: 14px 16px; border-radius: 2px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 15px;">⚡</span>
                            <strong style="font-size: 14px; font-family: var(--serif);">${esc(name)}</strong>
                            <span style="font-size: 11px; color: var(--text-muted);">(${steps.length} steps)</span>
                        </div>
                        <div style="display: flex; gap: 6px;">
                            <button class="btn-wiki btn-wiki-primary" style="font-size: 12px; padding: 4px 10px;" onclick="runSavedAction(${jsArg(name)})">▶ Run</button>
                            <button class="btn-wiki" style="font-size: 12px; padding: 4px 8px; color: #d33;" onclick="deleteSavedAction(${jsArg(name)})">🗑️</button>
                        </div>
                    </div>
                    <div style="margin-top: 6px; font-size: 12px;">${stepsChips}</div>
                </div>
            `;
        }
        html += '</div>';
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<p style="color: #d33;">Error loading actions: ${esc(e)}</p>`;
    }
}

async function runCustomAction() {
    const input = document.getElementById('customActionInput');
    const btn = document.getElementById('btnRunCustom');
    const actStr = input ? input.value.trim() : '';
    if (!actStr) return alert('Please enter an action string to run.');

    if (btn) { btn.disabled = true; btn.innerText = '⏳ Running...'; }
    showToast(`⚡ Running action pipeline...`, 4000);

    try {
        const res = await fetch('/api/run_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: actStr })
        });
        const data = await res.json();
        if (data.status === 'completed') {
            showToast(`✅ Executed ${data.steps_executed} steps in ${data.duration_seconds}s!`, 6000);
        } else {
            showToast(`Pipeline: ${data.error || 'Execution finished'}`, 6000);
        }
        await fetchStats();
    } catch (e) {
        showToast(`Action error: ${e}`);
    } finally {
        if (btn) { btn.disabled = false; btn.innerText = '⚡ Execute'; }
    }
}

async function saveCustomAction() {
    const nameInput = document.getElementById('customActionName');
    const strInput = document.getElementById('customActionInput');
    const name = nameInput ? nameInput.value.trim() : '';
    const actStr = strInput ? strInput.value.trim() : '';
    if (!name || !actStr) return alert('Please enter both a macro name and an action string.');

    try {
        const res = await fetch('/api/save_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, action: actStr })
        });
        const data = await res.json();
        if (data.status === 'saved') {
            showToast(`💾 Saved action pipeline '${name}'!`);
            nameInput.value = '';
            loadSavedActionsList();
            await fetchStats();
        } else {
            showToast(`Error saving: ${data.error || 'unknown'}`);
        }
    } catch (e) {
        showToast(`Error: ${e}`);
    }
}

async function runSavedAction(name) {
    showToast(`⚡ Running '${name}'...`, 4000);
    try {
        const res = await fetch('/api/run_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        const data = await res.json();
        if (data.status === 'completed') {
            showToast(`✅ '${name}' completed: ${data.steps_executed} steps in ${data.duration_seconds}s!`, 6000);
        } else {
            showToast(`Pipeline: ${data.error || 'finished'}`);
        }
        await fetchStats();
    } catch (e) {
        showToast(`Error: ${e}`);
    }
}

async function deleteSavedAction(name) {
    if (!confirm(`Delete action '${name}'?`)) return;
    try {
        await fetch('/api/delete_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        showToast(`Deleted action '${name}'.`);
        loadSavedActionsList();
        await fetchStats();
    } catch (e) {
        showToast(`Error: ${e}`);
    }
}

/* 6. TESTER & CONTROLS PAGE */
/* 7. AI / MCP SETUP PAGE */
// Config snippets shown on the page, copied by index so paths need no quoting in onclick
let mcpSnippets = [];

function copyMcpSnippet(i) {
    copyToClipboard(mcpSnippets[i]);
}

async function renderMcpPage(container) {
    container.innerHTML = '<p style="color: var(--text-muted);">Loading MCP setup...</p>';
    let setup;
    try {
        setup = await (await fetch('/api/mcp_setup')).json();
    } catch (e) {
        container.innerHTML = `<p style="color: #d33;">Could not load MCP setup: ${esc(e)}</p>`;
        return;
    }
    if (currentView !== 'mcp') return;

    const server = { command: setup.python, args: [setup.server_script] };
    mcpSnippets = [
        JSON.stringify({ mcpServers: { deskdriver: server } }, null, 2),
        `claude mcp add --scope user deskdriver -- "${setup.python}" "${setup.server_script}"`,
        JSON.stringify({ servers: { deskdriver: { type: 'stdio', ...server } } }, null, 2),
    ];
    const block = (i) => `
        <div class="mcp-snippet">
            <button class="btn-wiki btn-sm" onclick="copyMcpSnippet(${i})">Copy</button>
            <pre>${esc(mcpSnippets[i])}</pre>
        </div>`;

    const toolRows = (setup.tools || []).map(t => `
        <tr>
            <td><code>${esc(t.name)}</code></td>
            <td class="ctrl-type">${esc(t.params.join(', ')) || '&mdash;'}</td>
            <td title="${esc(t.summary)}">${esc(t.summary)}</td>
        </tr>`).join('');

    container.innerHTML = `
        <div class="article-header">
            <h1 class="article-title">Connecting an AI (MCP)</h1>
            <div class="article-tagline">From DeskDriver Wiki, the free desktop automation encyclopedia</div>
        </div>

        <div class="hatnote">
            DeskDriver is an <strong>MCP server</strong> (Model Context Protocol). An AI client that connects to it
            gets ${(setup.tools || []).length} tools to see and drive this desktop: list windows, click learned controls,
            press hotkeys, type and read the roadmap shown on this wiki. The client starts the server itself; this
            dashboard does not need to be running.
        </div>

        <div class="hatnote" style="border-left: 4px solid #f2994a; background: #fffdf5;">
            ⚠️ A connected AI controls your <strong>real</strong> mouse and keyboard. Keep an eye on it, and remove
            the <code>deskdriver</code> entry from the client's config to revoke access.
        </div>

        <h2 class="wiki-h2">1 Claude Desktop</h2>
        <p>Open <em>Settings → Developer → Edit Config</em>, merge this in, save, then quit Claude Desktop completely
           (also from the system tray) and start it again. The file is <code>%APPDATA%\\Claude\\claude_desktop_config.json</code>,
           or for the Microsoft Store version
           <code>%LOCALAPPDATA%\\Packages\\Claude_&lt;id&gt;\\LocalCache\\Roaming\\Claude\\claude_desktop_config.json</code>.</p>
        ${block(0)}

        <h2 class="wiki-h2">2 Claude Code</h2>
        <p>Run once in a terminal. <code>--scope user</code> makes DeskDriver available in every project; check it with <code>claude mcp list</code>.</p>
        ${block(1)}

        <h2 class="wiki-h2">3 Cursor, Antigravity and other MCP clients</h2>
        <p>Most clients use the same <code>mcpServers</code> format as Claude Desktop: in Cursor it goes in
           <code>%USERPROFILE%\\.cursor\\mcp.json</code>, in Antigravity under <em>Manage MCP Servers → View raw config</em>.
           VS Code (GitHub Copilot) uses <code>.vscode/mcp.json</code> with a <code>servers</code> key:</p>
        ${block(2)}

        <h2 class="wiki-h2">4 Check that it works</h2>
        <p>Start a new chat and ask: <em>"Use DeskDriver to list my open windows."</em> The AI should call
           <code>list_windows</code>. If the tools don't show up, restart the client, and make sure the paths above
           still exist (they point at this project's virtual environment and <code>server.py</code>).</p>

        <h2 class="wiki-h2">5 Available tools (${(setup.tools || []).length})</h2>
        <table class="wikitable compact-table">
            <colgroup><col style="width:24%"><col style="width:26%"><col></colgroup>
            <thead><tr><th>Tool</th><th>Parameters</th><th>What it does</th></tr></thead>
            <tbody>${toolRows}</tbody>
        </table>
    `;
}

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

function copyAndToast(text) {
    try {
        navigator.clipboard.writeText(text);
        showToast(`📋 Copied action recipe: ${text}`, 3000);
    } catch (e) {
        prompt('Copy action recipe:', text);
    }
}

function filterCtrlTable(category, btnElement) {
    document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
    if (btnElement) btnElement.classList.add('active');
    document.querySelectorAll('.ctrl-row').forEach(row => {
        const type = (row.dataset.type || '').toLowerCase();
        let match = true;
        if (category === 'button') match = /button|toolbar/.test(type);
        else if (category === 'menu') match = /menu/.test(type);
        else if (category === 'edit') match = /edit|combobox|spinner|document/.test(type);
        else if (category === 'tab') match = /tab|list|tree|item/.test(type);
        else if (category === 'toggle') match = /check|radio|toggle/.test(type);
        else if (category === 'shortcut') match = row.dataset.shortcut === '1';
        row.style.display = match ? '' : 'none';
    });
}

async function triggerDeepDive(appKey) {
    const btn = document.getElementById('btnDeepDive');
    let target = appKey || currentApp || '';
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
            const newTxt = (data.new_count > 0) ? ` (✨ ${data.new_count} newly discovered!)` : ' (all already in roadmap)';
            showToast(`✅ Deep Dive Complete! Indexed ${data.total_elements} controls & ${data.total_shortcuts} shortcuts${newTxt} for ${appLabel(data.app)}!`, 8000);
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
    for (const key of sortedAppKeys(roadmap)) {
        if (key.toLowerCase().includes(q) || appLabel(key).toLowerCase().includes(q)) {
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

async function triggerSystemScan() {
    const btn = document.getElementById('btnSystemScan');
    if (btn) {
        btn.disabled = true;
        btn.innerText = '⏳ Scanning System...';
    }
    showToast('⚡ Running Full System Scan across all open windows...', 5000);

    try {
        const res = await fetch('/api/prelearn', { method: 'POST' });
        const data = await res.json();
        const newCnt = data.total_new_elements || 0;
        const totalCnt = data.total_elements || 0;
        const appsCnt = (data.scanned_apps || []).length;
        if (newCnt > 0) {
            showToast(`✅ System Scan complete! Indexed ${totalCnt} controls across ${appsCnt} apps (✨ ${newCnt} newly found!).`, 8000);
        } else {
            showToast(`✅ System Scan complete! Re-verified ${totalCnt} controls across ${appsCnt} apps (all already indexed in roadmap).`, 8000);
        }
        await fetchStats();
    } catch (e) {
        showToast('System Scan error: ' + e);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = '⚡ System Scan';
        }
    }
}

let isRecordingLive = false;
let recInterval = null;
let recSeconds = 0;

async function toggleLiveRecording() {
    const btn = document.getElementById('btnLiveRecord');
    if (!isRecordingLive) {
        try {
            const res = await fetch('/api/record/start', { method: 'POST' });
            const data = await res.json();
            isRecordingLive = true;
            recSeconds = 0;
            btn.classList.add('recording');
            btn.innerText = '⏹️ Stop Recording (00:00)';
            showToast('🔴 Recording Started! Click buttons, open apps & switch windows — DeskDriver is monitoring & indexing in the background.', 7000);

            recInterval = setInterval(async () => {
                recSeconds++;
                const m = String(Math.floor(recSeconds / 60)).padStart(2, '0');
                const s = String(recSeconds % 60).padStart(2, '0');
                btn.innerText = `⏹️ Stop Recording (${m}:${s})`;

                if (recSeconds % 5 === 0) {
                    try {
                        const stRes = await fetch('/api/record/status');
                        const stData = await stRes.json();
                        if (stData.actions_count > 0) {
                            showToast(`🔴 Recording in progress: ${stData.actions_count} actions captured across ${stData.apps.length} apps...`, 3000);
                        }
                    } catch (_) {}
                }
            }, 1000);
        } catch (e) {
            showToast('Error starting recording: ' + e);
        }
    } else {
        clearInterval(recInterval);
        btn.disabled = true;
        btn.innerText = '⏳ Processing Session...';

        try {
            const res = await fetch('/api/record/stop', { method: 'POST' });
            const data = await res.json();
            isRecordingLive = false;
            btn.classList.remove('recording');
            btn.innerText = '🔴 Record Session';
            btn.disabled = false;

            await fetchStats();
            showRecModal(data);
        } catch (e) {
            showToast('Error stopping recording: ' + e);
            btn.disabled = false;
            btn.classList.remove('recording');
            btn.innerText = '🔴 Record Session';
            isRecordingLive = false;
        }
    }
}

function showRecModal(data) {
    const modal = document.getElementById('recModal');
    const stats = document.getElementById('recModalStats');
    const pipeInp = document.getElementById('recModalPipeline');
    if (!modal) return;

    const pipeline = data.pipeline || '';
    pipeInp.value = pipeline;

    const appsList = (data.apps_visited || []).join(', ') || 'Desktop';
    stats.innerHTML = `
        <div style="background:#f8f9fa; border:1px solid #c8ccd1; padding:12px 16px; margin-bottom:12px; display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:10px;">
            <div><span style="color:#54595d; font-size:11.5px; text-transform:uppercase;">Duration</span><div style="font-size:17px; font-weight:bold; color:#3366cc;">${esc(data.duration_seconds)}s</div></div>
            <div><span style="color:#54595d; font-size:11.5px; text-transform:uppercase;">Actions Captured</span><div style="font-size:17px; font-weight:bold; color:#14866d;">${esc(data.actions_count)} steps</div></div>
            <div><span style="color:#54595d; font-size:11.5px; text-transform:uppercase;">Apps Visited</span><div style="font-size:17px; font-weight:bold; color:#202122;">${(data.apps_visited || []).length} apps</div></div>
            <div><span style="color:#54595d; font-size:11.5px; text-transform:uppercase;">New Controls</span><div style="font-size:17px; font-weight:bold; color:#d33;">✨ ${esc(data.new_controls_count || 0)}</div></div>
        </div>
        <p style="margin-bottom:6px;"><strong>Apps Traverse Path:</strong> <code>${esc(appsList)}</code></p>
        <p style="color:var(--text-muted); font-size:12.5px;">All newly discovered controls from this session have been automatically indexed into <code>ui_roadmap/</code> and logged into <strong>📜 Scan History</strong>.</p>
    `;

    modal.style.display = 'flex';
}

function closeRecModal() {
    const modal = document.getElementById('recModal');
    if (modal) modal.style.display = 'none';
}

function copyModalPipeline() {
    const val = document.getElementById('recModalPipeline')?.value || '';
    copyAndToast(val);
}

async function runModalPipeline() {
    const val = document.getElementById('recModalPipeline')?.value || '';
    if (!val) return;
    closeRecModal();
    showToast(`⚡ Executing recorded pipeline: ${val}`, 6000);
    try {
        const res = await fetch('/api/run_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: val })
        });
        const d = await res.json();
        if (d.error) showToast(`Pipeline error: ${d.error}`, 6000);
        else showToast(`✅ Executed recorded pipeline (${d.steps_executed} steps)!`, 6000);
    } catch (e) {
        showToast('Execution error: ' + e);
    }
}

async function saveModalPipelinePrompt() {
    const val = document.getElementById('recModalPipeline')?.value || '';
    if (!val) return;
    const name = prompt('Enter a name for this recorded action pipeline:', 'My Recorded Workflow');
    if (!name) return;
    try {
        const res = await fetch('/api/save_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, action: val })
        });
        const d = await res.json();
        if (d.error) return showToast(`Save error: ${d.error}`);
        showToast(`💾 Saved recorded pipeline as '${name}'!`);
        await fetchStats();
        navigateTo('actions');
    } catch (e) {
        showToast('Save error: ' + e);
    }
}

fetchStats();
