# AI Mouse & UI Automation MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-2.3+-green.svg)](https://modelcontextprotocol.io)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()

Fast, human-like AI mouse controller and desktop UI automation server for Windows, communicating via the **Model Context Protocol (MCP)**.

---

## Eiginleikar

- **Eðlileg mannleg hreyfing:** Notar Bézier-ferla og *smoothstep easing* með náttúrulegri hröðun og sveiflu til að hreyfa bendilinn mjúklega yfir skjáinn (150–250 ms) án vélrænna stökka.
- **Hvað er undir músinni?** Greinir samstundis nákvæmt heiti, tegund (`ButtonControl`, `EditControl`, `MenuItem` o.fl.), glugga og hnit stjórntækisins beint undir bendlinum.
- **Sjálfvirkt Vegvísakort (UI Roadmap & Learning):** Lærir á forrit og vistar afstæð hnit (`rel_x, rel_y`) í [`ui_roadmap.json`](ui_roadmap.json). Uppfletting tekur $< 1$ ms í stað hægrar trjáleitar.
- **Beinar stýrikerfisvísanir (OS Fastpaths – 0 ms):** Styður bein URI skipanir (t.d. `ms-settings:system`, `display`, `sound`, `calc:`) sem opna réttar síður samstundis án nokkurra músarsmella.
- **Hreint og mátbundið skipulag (Modular Architecture):** Aðskilið í sjálfstæðar einingar fyrir mús, stýrikerfi, UI automation og leiðsögn.

---

## Verkefnaskipulag (Architecture)

```text
ai-mouse/
├── src/
│   └── ai_mouse/
│       ├── core/
│       │   ├── desktop.py       # Win32 desktop station & thread input samstilling
│       │   └── mouse.py         # Bézier hreyfingar, bendilhnit og smellaðgerðir
│       ├── automation/
│       │   ├── windows.py       # Gluggagreining og virkjun í forgrunni
│       │   └── uia.py           # UIAutomation element-leit og skoðun
│       ├── navigation/
│       │   ├── fastpaths.py     # OS URI tenglar (ms-settings, calc, taskmgr)
│       │   └── roadmap.py       # Minnisgeymsla og O(1) hraðsmellir
│       ├── server.py            # FastMCP Server með öllum verkfærum
│       └── __init__.py          # Aðalútflutningur á öllum aðgerðum
├── tests/
│   └── test_ai_mouse.py         # Sjálfvirk einingapróf
├── server.py                    # Aðalinngangur fyrir MCP þjóninn
├── demo.py                      # Gagnvirkt sýniforrit í skel
├── pyproject.toml               # Uppsetningarpakki
└── requirements.txt             # Kröfur
```

---

## Uppsetning

```powershell
# Búa til sýndarumhverfi
python -m venv .venv

# Virkja og setja upp pakka
.\.venv\Scripts\pip install -r requirements.txt
```

---

## Prófun

Keyrðu gagnvirka sýniforritið:
```powershell
.\.venv\Scripts\python demo.py
```

Eða keyrðu einingaprófin:
```powershell
.\.venv\Scripts\python tests/test_ai_mouse.py
```

---

## MCP Verkfæri (Tools)

Þegar þjónninn er tengdur við MCP biðlara (Claude Desktop, Cursor, Antigravity o.fl.) hefur gervigreindin aðgang að eftirfarandi verkfærum:

| Verkfæri | Lýsing |
| :--- | :--- |
| `fast_click(element_name, window_search, instant=True)` | **Sjálfvirk flýtirás:** Ef takki hefur flýtilykil (`Ctrl+S`, `Ctrl+T`) notar hann hann á **0.5 ms**. Annars smellir hann á hnit úr Roadmap á $< 1$ ms. |
| `press_hotkey(hotkey)` | **Flýtilykill (0.5 ms):** Sendir lyklaborðssamsetningu (t.d. `ctrl+s`, `win+shift+s`, `ctrl+t`, `alt+f4`, `enter`). |
| `type_text(text, enter=False)` | **Slá inn texta:** Sendir Unicode texta beint inn í virkan reit (t.d. leitarstiku eða textaskjal). |
| `open_fastpath(target)` | **Bein flýtivísun í OS (0 ms):** Opnar stillingar samstundis (t.d. `system`, `display`, `sound`, `bluetooth`, `wifi`, `calculator`). |
| `system_prelearn(max_elements_per_app=150)` | **Djúpskönnun:** Skannar öll opin forrit og verkstikuna og kennir Roadmap-inu alla takka fyrirfram. |
| `get_roadmap_stats()` | Sýnir lista yfir forrit og takka sem þjónninn hefur kortlagt í minni. |
| `get_mouse_position()` | Skilar núverandi `(x, y)` hnitum músarinnar á skjánum. |
| `move_mouse(x, y, smooth=True, duration=0.25)` | Hreyfir músina á mjúkan, mannlegan hátt með Bézier-kúrfulíkani. |
| `click(button="left", clicks=1)` | Smellir á núverandi stað (styður vinstri, hægri og tvísmell). |
| `move_and_click(x, y, button="left", clicks=1)` | Færir músina og smellir í einni samfelldri aðgerð. |
| `inspect_under_cursor()` | Greinir hvaða UI stjórntæki er beint undir bendlinum (tegund, heiti, gluggi). |
| `inspect_at(x, y)` | Greinir stjórntæki á tilteknum hnitum án þess að færa bendilinn. |
| `list_windows()` | Skilar lista yfir alla sýnilega glugga (heiti, stærð og staðsetning). |
| `focus_window(title_or_hwnd)` | Setur tiltekinn glugga í forgrunn. |
| `list_clickable_elements(window_search="", max_elements=40)` | Finnur alla smellanlega hnappa og tengla í virka glugganum með miðjuhnitum. |


---

## Tenging við MCP biðlara

Bættu þessari uppsetningu við í `claude_desktop_config.json` eða stillingaskrá biðlarans:

```json
{
  "mcpServers": {
    "ai-mouse": {
      "command": "c:\\Users\\rober\\Downloads\\ai-mouse\\.venv\\Scripts\\python.exe",
      "args": [
        "c:\\Users\\rober\\Downloads\\ai-mouse\\server.py"
      ]
    }
  }
}
```

---

## Leyfi
MIT License.
