# Claude Desktop: Ultracode Restoration & Slider Revival Engine

> **A cross-version AST patcher for Claude Desktop on Windows. Restores the hidden 6th Ultracode stop, un-folds the collapsed effort slider on Claude 3.x, unlocks third-party models (e.g., DeepSeek), and makes the trigger pill persistently purple.**  
> *English Documentation · [简体中文文档](README.zh-CN.md)*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D6)](#quick-start)
[![Claude Desktop](https://img.shields.io/badge/Claude%20Desktop-v2.x%20~%20v5.x-black)](#compatibility-matrix)
[![Release](https://img.shields.io/badge/Release-v2.0.0-purple.svg)](https://github.com/Zorix666/claude-ultracode-revival/releases)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#)

---

## Architectural Overview

```mermaid
flowchart TD
    subgraph UI ["Frontend Presentation"]
        Pill["Trigger Pill (Persistent Pro Purple)"]
        Slider["Effort Slider (6 Stops / Faster-Smarter)"]
        Menu["Claude 3.x Collapsed Submenu (Revived into Slider)"]
    end

    subgraph Logic ["Frontend Bundle Core"]
        ThinkingStyle["Layout Policy (thinkingStyle: separate)"]
        ScaleFilter["Scale Filter Chain (ip / Fn)"]
        Dispatch["Dispatch Handler (Ye / Ke / mt)"]
        ModelGate["3rd-Party Model Gate (he || oe / me || K)"]
        PresLevel["Presentation Hook (presentedEffortLevel)"]
    end

    subgraph State ["Runtime State & Gateway"]
        Session["Active Session (local_*.json)"]
        ThirdParty["3rd-Party Gateway (DeepSeek / OpenAI)"]
        Official["Anthropic Direct API"]
    end

    ThinkingStyle -- "Un-folds Submenu -> Standalone Slider" --> Slider
    ScaleFilter -- "Inject 6th Stop (Ultracode)" --> Slider
    Slider -- "Bidirectional Dispatch (xhigh / ultracode)" --> Dispatch
    ModelGate -- "Unlock 3P Models, Prevent Reset" --> ThirdParty
    Dispatch -- "Persist ultracode: true" --> Session
    Session -- "Hook presentedEffortLevel" --> PresLevel
    PresLevel -- "Dynamic Linkage & Purple Pro Accent" --> Pill
```

---

## Background & Root Causes

When running Claude Desktop on Windows (especially with third-party gateways like DeepSeek or alongside Claude Code), users encounter several architectural issues:

1. **Claude 3.x Collapses Slider into Dropdown Submenu**:
   - In Claude Desktop 3.x (e.g. `3.6556.2`), Anthropic redesigned the bottom chin layout. It leaves `thinkingStyle` undefined for composer chins, collapsing the slider into a nested submenu.
2. **Missing 6th "Ultracode" Effort Level**:
   - While the Claude Code CLI supports `/effort ultracode`, the desktop UI truncates the slider to 5 stops (`low` ~ `max`).
3. **Silent Reset on 3rd-Party Models (DeepSeek)**:
   - For non-Anthropic models lacking the proprietary `xhigh` flag, an internal gate `_e = (he || oe)` evaluates to `false` and triggers a background reset (`Ce({ultracode: false})`).
4. **Trigger Pill Locked on "High"**:
   - The trigger button rendered in the bottom chin hardcodes `label: q(L)` or `label: H(N)`, decoupling from the slider's active selection.
5. **MSIX Automatic Update Overwrites**:
   - WindowsApps quietly replaces entire installation directories on major updates, wiping manual patches.

---

## Solutions Provided

- **Forces Standalone Slider**: Overrides `thinkingStyle: "separate"` across all composer placements to permanently revive the slider.
- **Injects 6th Stop**: Dynamically extends the model option filter chain to include `{id: "ultracode", name: "Ultracode"}` with native `font-medium text-pro` purple styling.
- **Bypasses 3P Model Gate**: Disables model gating so DeepSeek and OpenAI-compatible proxies retain Ultracode.
- **Synchronizes Trigger Pill**: Dynamically binds the trigger pill label and purple accent to the active Ultracode state.
- **Idempotent Self-Elevating Installer**: Automatically handles Windows UAC elevation, process termination, ACL unlocks, and version detection.

---

## AST Replacement Specification (v2.x & v3.x)

| Target | File Pattern | Original (Old) | Patched |
| :--- | :--- | :--- | :--- |
| **Slider Revival** | `c227f4d5e-*.js` | `w$={shortcuts:!0}` | `w$={shortcuts:!0,thinkingStyle:"separate"}` |
| **6th Stop Injection** | `c227f4d5e-*.js` | `let i=e.filter(...)` | `let i=[...e.filter(...),{id:"ultracode",name:"Ultracode"}],a=i;` |
| **Bidirectional Dispatch** | `c9543da06-*.js` | `(e,t)=>mt(e,!1,{...})` | `(e,t)=>e==="ultracode"?mt("xhigh",!0,{...}):mt(e,!1,{...})` |
| **3P Model Gate Bypass** | `c9543da06-*.js` | `&&(me\|\|K)&&` / `&&(he\|\|oe)&&` | `&&(!0)&&` |
| **Presentation Hook** | `c9543da06-*.js` | `wt=pe?Y:null` / `tt=G?pe:null` | `wt=pe?(ye\|\|_e\|\|Y==="xhigh"?"ultracode":Y):null` |
| **Trigger Pill Linkage** | `c8e04f916-*.js` | `label:H(N)` / `label:q(L)` | `label:(I===g.length-1\|\|...?"Ultracode":H(N))` |

---

## Claude 5.x (asar) Mode

Starting with 5.x the frontend ships as a **single `ion-dist.asar`** instead of an unpacked
`ion-dist/assets/v1/` directory. Editing individual `.js` files no longer works, so 5.x has its
own pipeline: unpack → replace byte strings → repack → sync the hash embedded in `claude.exe`.

```bash
# 1. Point at the ORIGINAL (unpatched) files from the installed package
python build_asar.py --asar "<install>\app\resources\ion-dist.asar" \
                     --exe  "<install>\app\claude.exe"

# 2. Install (auto-elevates, health-checks for 40s, rolls back on failure)
python install_asar.py
```

The build refuses to finish if any target string is missing or ambiguous, and every patched
module must pass `node --check` before a single byte is written.

| Target | Module | Change |
| :--- | :--- | :--- |
| Slider mode | `shared-8` | `thinkingStyle:"inline"/"submenu"` → `"separate"` |
| 6th stop | `shared-36` / `shared-222` | append `{id:"ultra",name:"Ultracode"}` |
| Stop whitelists | `shared-4`, `shared-192`, `shared-0`, `cd4f82e77`, `c325ea79a` | add `"ultra"` (5 modules — miss one and the slider snaps back) |
| State clamp | `cc2521586`, `shared-33` | let `ultra` through the clamp and the session marker |
| Bottom pill | `c82492f2c`, `cc43287c9` | always render the standalone Effort pill, kill the model-name merge |
| Panel | `c8e04f916` | `w-[220px]` → `w-[260px]`, accent keys off `ultra` |

### Colours

The pill and the panel title must both resolve to the **same CSS variable**:

```js
color: "var(--cds-text-pro)"   // .text-pro → violet-600 #5437B8 (light) / violet-300 (dark)
```

Hard-coding a hex value, or using `--cds-violet-450` (`#785EE8`), makes the bottom pill visibly
brighter than the panel title. The project deliberately ships **no glow, no border, no background
tint** — glowing variants were tried and rejected.

### asar repacking rules

Three things must hold, or the app white-screens with an error that points nowhere near the cause:

1. **`offset` must be a string.** The Chromium C++ side reads it with `FindString("offset")`;
   an integer makes it return `nullptr` and every file becomes `ENOENT` — even `index.html`.
2. **Pickle header**: `f0=4`, `f1=4+f2`, `f2=4+padded_json_len`, `f3=json_len`, data starts at `8+f1`.
3. **`integrity`**: update `integrity.hash` **and** `integrity.blocks` (chunked by `blockSize`).

The header's sha256 is embedded in `claude.exe`; repacking without patching it back in gets you a
silent instant exit.

---

## Claude 4.23118 (Electron standalone) Mode

A **different distribution channel**: this build installs under
`%LOCALAPPDATA%\Programs\Claude` instead of `C:\Program Files\WindowsApps`, keeps its own
version numbering (4.23xxx, unrelated to the MSIX 5.x/6.x series), and uses an entirely
different set of module names.

Its layout drops the `app\` level:

```
<root>\resources\ion-dist.asar
<root>\claude.exe
```

Locate the install from the **running process** — directory listings and mtimes lie when two
channels coexist:

```powershell
Get-CimInstance Win32_Process -Filter "Name='claude.exe'" |
  Select-Object ProcessId, ExecutablePath | Format-List
```

```bash
# 1. Build, pointing at the PRISTINE files (the .bak copies)
python build_asar_v4.py --asar "<root>\resources\ion-dist.asar.bak" \
                        --exe  "<root>\claude.exe.bak" \
                        --out  build/v4

# 2. Install (no elevation needed — user-writable directory)
python install_electron.py --build build/v4
```

| Target | Module | Change |
| :--- | :--- | :--- |
| Slider mode | `shared-8` | `thinkingStyle:"inline"/"submenu"` → `"separate"` |
| Surface config | `c227f4d5e` | `case"chin"/"row"` returns the `separate` preset instead of plain `HR` |
| Slider glow | `c227f4d5e` | `fe` pinned to `$R` — lit only at the last stop, not whenever the flag is on |
| 6th stop | `shared-8` `Vb`, `shared-7` `GV()` | extend the zod enum; inject the stop **and strip the backend's `" · Ultracode"` name suffix** |
| Stop whitelists | `shared-0`, `shared-196`, `shared-4`, `cd4f82e77`, `c227f4d5e` | append `"ultracode"` |
| Ultracode flag | `c9543da06` | pick commits `id === "ultracode"` instead of carrying the previous flag forward |
| Bottom pill | `cc43287c9`, `c8e04f916` | always render, pure violet text, label from `G(R)`, no toggle label |
| Panel | `c8e04f916` | `w-[220px]` → `w-[260px]`, remove the standalone toggle row |

### Four independent failure paths

These look like one bug and are not. Fixing one leaves the others intact, which is
exactly why this takes several passes if you assume a single root cause:

| Symptom | Path |
| :--- | :--- |
| Pill reads `Extra · Ultracode` | The backend ships stop *names* with that suffix when the ultracode flag is on (i18n template `"{level} · {ultracode}"`). It is in the option name, **not** in `toggleLabel` — nulling the label does nothing. `GV()` has to strip it. |
| 6th stop selected, pill still says `Extra` | `c8e04f916` labels the trigger with `G(F)` — the backend's *effective* index, which still points at `xhigh` under ultracode. Use `G(R)`, the locally chosen position. |
| Track stays lit at Max/High | With `separate` forced, `fe` follows `v.on`: `ez` is always-lit, `tz` never. Once the flag has been true, the slider glows on every stop. Pin `fe` to `$R`. |
| Flag never clears | `c9543da06` commits `Pe()` (the current flag) as the second argument on every pick, so a previously-true value survives a switch back to High. |

Do **not** port the 5.x form `At(e, e>"max", …)` for the last one: that string
comparison is also true for `"xhigh"` (`'x' > 'm'`), so Extra gets misread as
ultracode. Use the explicit `e === "ultracode"`.

### Which surface preset wins

The list-vs-slider decision is made by one function in `c227f4d5e`:

```js
var zR={shortcuts:!0,thinkingStyle:"separate"}, BR=zR, VR={…zR,overflowSearch:!0},
    HR={shortcuts:!0}, WR={…HR,overflowStyle:"inline",thinkingStyle:"inline"}, …

function YR(e,t,n){switch(e){
  case"chin":case"row":return n?t?GR:WR:t?UR:HR;   // HR has no thinkingStyle -> submenu -> LIST
  case"titlebar":return t?JR:qR;
  case"rail":return t?VR:BR;                        // separate -> SLIDER
  case"composer":return t?VR:zR}}
```

The environment row under the composer is a `chin`/`row` surface, so it lands on `HR` and renders
a list. Patch it to return the `separate` preset and you get the slider.

### Why the 6th stop is `"ultracode"` here, not `"ultra"`

This build already knows `"ultracode"` end to end, so reusing that id for free is strictly better
than inventing `"ultra"` and patching every consumer by hand:

| Location | Code | with `"ultra"` you'd also need |
| :--- | :--- | :--- |
| `shared-33` | `var fT="ultracode"; function pT(e){return e===fT}` | `\|\|e==="ultra"` |
| `shared-7` | `m=t.id==="ultracode"?"text-pro font-medium":void 0` | `\|\|t.id==="ultra"` |
| `c10f0af0c` | `EX(e){if(e===void 0\|\|e==="ultracode")return e; let t=Ud.safeParse(e);…}` | same guard |

`EX()` short-circuiting before `safeParse` is the tell: the zod schema itself does **not**
accept `"ultracode"`, which is why the schema source `Vb` must be extended in the same patch.

---

## Quick Start

### Option 1: Download Release (Recommended)

1. Go to the [Releases](https://github.com/Zorix666/claude-ultracode-revival/releases) page and download `claude-ultracode-revival.zip`.
2. Extract the archive and double-click **`patch_ultracode.bat`**.
3. Accept the Windows UAC elevation prompt. The script will patch the bundle and restart Claude in under 1 second.

### Option 2: Clone & Run

```bash
git clone https://github.com/Zorix666/claude-ultracode-revival.git
cd claude-ultracode-revival
python apply_patch.py
```

---

## Compatibility Matrix

- [x] **Claude Desktop 5.11492.5.0** (asar mode — `build_asar.py` / `install_asar.py`)
- [x] **Claude Desktop 4.23118.x** (Electron standalone — `build_asar_v4.py` / `install_electron.py`)
- [x] **Claude Desktop v3.6556.2+** (Latest Claude 3.x, restores collapsed slider)
- [x] **Claude Desktop v2.42304+** (Classic v2.x, unlocks 6th stop)
- [x] **Claude Desktop v2.31226+**
- [x] **3rd-Party Gateway Support**: DeepSeek, OpenAI-compatible relays, direct APIs
- [x] **Operating System**: Windows 11 / Windows 10 (x64)

Other versions will fail loudly at the first unmatched target string — that is intentional.
Re-locating the patch points is a 10-minute job; silently producing a half-patched bundle is not.

## Known Pitfalls

These all cost real debugging time; they are documented so you don't pay for them twice.

| Symptom | Cause |
| :--- | :--- |
| Patch reports success, UI unchanged | **Two distribution channels coexist**: the MSIX package under `WindowsApps\Claude_<ver>` and the Electron standalone under `%LOCALAPPDATA%\Programs\Claude`. Both can be installed; only one is running, and you probably patched the other. Resolve the install path from the **running process** (`Get-CimInstance Win32_Process`), never from directory mtime — and note the two channels use unrelated version series, so comparing version numbers tells you nothing. |
| Patched standalone client hangs at launch or shows blank UI | The standalone channel needs the `.bak` originals as build input. Feeding it an already-patched `ion-dist.asar` produces a bundle whose header hash no longer matches the `claude.exe` you copied alongside it. |
| Patch applied, client restarted, UI still shows the old layout | Chromium caches compiled JS under the user-data dir (`Claude-3p\Code Cache`, `GPUCache`). Clear them when swapping the asar — `install_electron.py` does it by default (`--keep-cache` opts out). |
| Every anchor check fails after a previous successful install | The install's own `ion-dist.asar` is already patched. Build from the `.bak` originals and assert the input header hash, or the patch silently targets the wrong bytes. |
| Guard silently does nothing, or its log is mojibake | The scheduled task runs `pythonw.exe` (GUI subsystem): `sys.stdout` is `None`, so a bare `print()` raises `AttributeError` and kills the script. Wrap it in `try/except`. Write the log with a UTF-8 **BOM** on first creation — Windows tools read BOM-less UTF-8 as GBK. |
| Guard marches a stale build over a freshly updated app | A guard that re-applies on *any* hash mismatch will overwrite a newer version's JS. Require an `orig_hash` allow-list: patch only when the current header equals the pristine hash; anything else is version drift and must be skipped loudly. |
| Guard kills your other Claude window | `taskkill /im claude.exe` matches both channels — they ship executables with the same name. Kill by full path: `Get-Process claude \| Where-Object { $_.Path -eq '<exe>' } \| Stop-Process -Force`. |
| Patched client won't start or starts with an empty session list | Launched via `explorer.exe <dir>\app\claude.exe` instead of the package identity. Use `explorer.exe shell:AppsFolder\Claude_pzs8sxrjxfjjc!Claude`. |
| White screen, `ENOENT` for every asset | asar `offset` written as an integer instead of a string. |
| Instant exit after install | `integrity.blocks` not recomputed alongside `integrity.hash`. |
| Patch silently reverts after a reboot | A login guard task re-applies a stale build. Update the guard's target directory **and** its expected hash together. |

---

## License

This project is licensed under the [MIT License](LICENSE).
