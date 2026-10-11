# 🗺️ AI Mouse - Project Roadmap & Community Cloud Architecture

A strategic roadmap for scaling **AI Mouse** from a high-performance local MCP server into a collaborative, crowdsourced spatial database for desktop automation ("Waze for Desktop AI").

---

## 🎯 The Vision
Modern computer-use models (Claude 3.5 Sonnet, OpenAI Operator) are bottlenecked by slow, expensive pixel-screenshot loops (3–8s per action). 

**AI Mouse** bypasses vision latency by leveraging:
1. **OS Fastpaths** (0 ms navigation via URI protocols).
2. **Keyboard Accelerators & Hotkeys** (0.5 ms actions via Windows `SendInput`).
3. **UI Automation & Spatial Roadmap** (<1 ms cache retrieval).

### The Opportunity: The Global UI Knowledge Graph
99% of desktop applications have standard, identical interfaces across millions of computers (Notepad, Brave, Chrome, Excel, VS Code, Discord, Spotify, specialized enterprise tools). 

Instead of requiring every local user's machine to independently discover and learn buttons from scratch, **AI Mouse** can synchronize sanitized UI profiles to a central community registry.

---

## 🏗️ Architecture & Privacy Model

```
┌─────────────────────────────────────────────────────────────┐
│                       LOCAL DESKTOP                         │
│                                                             │
│   [Windows Apps] ──> [UIA Scanner] ──> [ui_roadmap/*.json]  │
│                                               │             │
│                                               ▼             │
│                                    ┌─────────────────────┐  │
│                                    │ Sanitization Filter │  │
│                                    │   (PII Stripping)   │  │
│                                    └──────────┬──────────┘  │
└───────────────────────────────────────────────┼─────────────┘
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 │                                                             │
                 ▼                                                             ▼
 ┌───────────────────────────────┐                             ┌───────────────────────────────┐
 │     PRIVATE CLOUD SYNC        │                             │  PUBLIC COMMUNITY REGISTRY    │
 │     (Per-User / Authenticated)│                             │    (Opt-in / Curated Waze)    │
 │                               │                             │                               │
 │ • Syncs across user's devices │                             │ • Universal App Profiles      │
 │ • Multi-monitor presets       │                             │ • Community-verified hotkeys  │
 │ • Encrypted backup            │                             │ • Zero-day instant automation │
 └───────────────────────────────┘                             └───────────────────────────────┘
```

---

## 🔒 Privacy & Sanitization First

A crowdsourced UI database must guarantee zero leakage of Personally Identifiable Information (PII).

### Rules for Public Sharing:
1. **Title Stripping:** Window titles like `Bank_Statement_2026.pdf - Acrobat` are normalized strictly to `Acrobat` / `Adobe Acrobat`.
2. **Content Exclusion:** Input field contents, document bodies, URLs, file paths, and usernames are **never** exported.
3. **Static Control Whitelisting:** Only durable UI controls are eligible for community export:
   - `ButtonControl` (Save, Export, Print, Settings, New Tab)
   - `MenuItemControl` (File, Edit, View, Help)
   - `TabItemControl`
   - `CheckBoxControl` & `RadioButtonControl`
   - Accelerators / Hotkeys (`Ctrl+S`, `F12`)
4. **Explicit Consent:** Nothing is published without an explicit user action (`public=True` flag or dashboard button).

---

## 📅 Phased Implementation Plan

### Phase 1: Local Mastery (Completed ✅)
- [x] Sub-millisecond cursor control with human-like Bézier easing.
- [x] Win32 / UIA element inspection and fallback name generation.
- [x] Persistent local roadmap cache (`ui_roadmap/`, one file per app) with relative offset indexing.
- [x] Universal Hotkeys engine & standard application profiles (`APP_PROFILES`).
- [x] 33+ Windows zero-click OS Fastpaths (`ms-settings:`, `calc:`, `taskmgr`).
- [x] Modern, atomic `SendInput` Unicode typing and hotkey execution.
- [x] Interactive real-time Web Wiki Dashboard.
- [x] DPI-Awareness (Per-Monitor V2) and responsive window anchoring.
- [x] Fluid composite AI action (`fill_input`).

---

### Phase 2: Sanitization Engine & Profile Export (Current Skeleton 🚧)
- [ ] Implement `src/ai_mouse/sync/sanitizer.py` to validate and strip PII from roadmap entries.
- [ ] Exportable JSON bundle format (`*.aimouse.json`) for manual sharing / backups.
- [ ] Dashboard UI: "Export App Profile" and "Import App Profile" buttons.

---

### Phase 3: Cloud Synchronization & Community Hub (Planned 🔮)
- [ ] **Private Cloud Sync:** User authentication (API keys) to sync roadmaps between a user's laptops and workstations.
- [ ] **Community Hub API:** REST endpoint allowing opt-in uploads of sanitized app profiles.
- [ ] **Community Verification:** Versioning and scoring of community maps (e.g. `brave@v1.2`, `blender@v4.1`).
- [ ] **Auto-Fetch on Launch:** When an AI detects an unknown window (e.g. `Slack`), query the community hub before triggering local scans.
