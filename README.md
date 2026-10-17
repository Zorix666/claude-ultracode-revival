# claude-ultracode-revival

> Restoring the hidden sixth **Ultracode** stop on the Claude Desktop effort slider — complete root cause analysis, persistent trigger capsule display, and a cross-version adaptive permanent patch.

[English](README.md) · [简体中文](README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078D6)](#usage)
[![Claude Desktop](https://img.shields.io/badge/claude%20desktop-2.31226%20~%202.42304+-black)](#how-it-works)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#)

---

## The Mysterious Symptoms

Developers connecting Claude Desktop to Claude Code (especially via 3p custom gateways or DeepSeek endpoints) frequently encounter these confusing issues:

1. **CLI has it, Desktop doesn't**:
   - Claude Code CLI clearly reports `Ultracode on (Tab to toggle) · dynamic workflows on every task` under `/effort`.
   - Claude Desktop effort slider only has 5 dots (`low` to `max`), with stop 6 completely missing.
2. **Dragging the slider makes it vanish permanently**:
   - Users who remember seeing it report that touching the slider makes Ultracode evaporate from the current session forever.
   - Typing `/effort ultracode` only degrades to `Extra` or `High`, and the slider stays clamped at dot 4 or 5.
3. **Bottom-right capsule stubbornly displays High**:
   - Even when selecting the 6th dot, the persistent bottom-right Trigger Pill remains stuck on `High` rather than displaying `Ultracode`.
4. **Rebooting undoes the manual edits**:
   - Files manually patched disappear after a Windows reboot, and Claude reverts back to 5 stops.
5. **Batch file closes immediately**:
   - Double-clicking custom `.bat` scripts flashes a console window for one second and closes without showing the UAC elevation prompt.

---

## Root Cause Analysis (Source-Level)

Reverse engineering the Rollup/Vite JavaScript bundles inside WindowsApps reveals the complete chain of events:

### 1. Slider interaction forcibly clears Ultracode
In the interaction bundle (e.g., `c9543da06-*.js`):
```javascript
be = h(e => {
  let { level: t, ultracode: n, silent: r = !1 } = e;
  let l = t === void 0 ? { ultracode: n } : { effortLevel: t, ultracode: n };
});
// Triggered on slider drag/click:
Ye = h((e, t) => Ke(e, !1, { recordAsPick: t?.recordAsPick }), [Ke]);
```
The second parameter passed to `Ke` is hard-coded to `!1` (`false`).  
**Every interaction with stops 1–5 dispatches `{ ultracode: false }`**, immediately clearing the flag from the active session!

### 2. Static catalog (`published.json`) lacks stop 6
The slider options are dynamically populated from the cached model catalog:
```javascript
function ip(e, t) {
  let i = e.filter(e => ri(e.id) ? t : Fn([e]).length > 0);
  return n.set(t, a), a;
}
```
`published.json` distributed by Anthropic only defines 5 stops (`[low, medium, high, xhigh, max]`). `ultracode` is never enumerated in the catalog, clamping the array to 5 items.

### 3. Native UI is fully implemented (just hidden)
In `c8e04f916-*.js`:
```javascript
let V = Math.min(L ?? z?.index ?? I, _.length - 1),
    H = _[V],
    ge = H?.id === te; // te === "ultracode"

re({ label: K(V), accent: ge, index: V });
// accent: ge triggers "font-medium text-pro" (purple highlighted bold text)
// overlay triggers glow animation: qf({ lit: e.atMax })
```
Anthropic already built the complete UI, purple accent, and light-up animation for the 6th stop.

### 4. Why did the bottom-right trigger capsule still show "High"?
Even when the slider reached stop 6, the bottom capsule displayed `High`:
- The variable `presentedEffortLevel` (variable `tt` in `c9543da06-*.js`) was coded as `tt = G ? pe : null`, which solely pushed the underlying numerical level (`"xhigh"` or degraded `"high"`), completely dropping the active `ultracode` boolean state.
- The trigger component (`c8e04f916-*.js`) evaluated `I = v.findIndex(e => e.id === y)`. Receiving `y = "high"`, it resolved to the 3rd/4th stop instead of the 6th stop (`"ultracode"`).
- **The fix**: Linking `presentedEffortLevel` directly to `"ultracode"` and updating trigger fallback mapping guarantees the trigger capsule persistently renders **`Ultracode`**.

### 5. Why does it vanish after reboot? (Silent MSIX Store Updates)
Claude Desktop is distributed as a packaged MSIX app. During system restart, Windows Store frequently performs silent background updates (e.g. from `2.31226.1.0` to `2.42304.0.0`):
- The old directory is destroyed, and pristine untouched JS files are unpacked.
- Build content hashes rotate completely (e.g., `c593f7513-*.js` became `c227f4d5e-*.js` and `c9543da06-*.js`).
- Scripts hardcoding static filenames or version numbers fail immediately.
- **Our solution**: Adaptive regex AST sniffing scans active bundles regardless of hash rotation.

### 6. Why did `.bat` close in 1 second?
Saving batch scripts in UTF-8 causes byte misalignment in Windows `cmd.exe`. Pure ANSI/GBK encoding with Python native `ShellExecuteW runas` completely solves this.

---

## Is Ultracode Actually Real?

**Yes, absolutely.**  
When Ultracode is active:
1. It injects a system-level prompt instruction forcing the `Workflow` tool suite.
2. It explicitly directs the model to decompose complex tasks into parallel subagents.
3. It bypasses default subagent concurrency caps, creating true multi-agent parallelism.

---

## Usage (Automated Adaptive Patch)

The patch script features **cross-version dynamic detection**:
- Queries `(Get-AppxPackage *Claude*).InstallLocation` dynamically.
- Locates target AST patterns in large bundles (>40KB) via regex without depending on fixed filenames.
- Triggers native Windows UAC elevation, unlocks system write permissions.
- **Clean Backups**: Backs up pristine files into `Claude_Patch_Backup` directory on Desktop, preventing unassociated blank white icons.
- Safely restarts Claude Desktop upon completion.

### Step 1: Clone or Download
```bash
git clone https://github.com/Zorix666/claude-ultracode-revival.git
cd claude-ultracode-revival
```

### Step 2: Run Patch
**Double-click [`patch_ultracode.bat`](patch_ultracode.bat)** or run in terminal:
```bash
python apply_patch.py
```
Click **Yes** on the Windows UAC prompt.

The script will automatically:
1. Terminate running Claude instances;
2. Auto-locate active Claude version path (e.g. `Claude_2.42304.0.0`);
3. Remove WindowsApps write protection (`takeown` / `icacls`);
4. Backup original files to `Claude_Patch_Backup` on Desktop;
5. Inject the 4-patch closure (scale, interaction, presented state, and capsule display);
6. Safely restart Claude Desktop.

---

## The 4-Patch System (Diffs)

### Patch 1: Stop 6 Catalog Expansion (`c227f4d5e-*.js`)
```diff
- let i=e.filter(e=>vc(e.id)?t:Ha([e]).length>0),a=i.length===e.length?e:i;
+ let i=[...e.filter(e=>!vc(e.id)&&Ha([e]).length>0),{id:"ultracode",name:"Ultracode"}],a=i;
```

### Patch 2: Bi-directional Drag Dispatch (`c9543da06-*.js`)
```diff
- Ze=x((e,t)=>Je(e,!1,{recordAsPick:t?.recordAsPick}),[Je]),
+ Ze=x((e,t)=>e==="ultracode"?Je("xhigh",!0,{recordAsPick:t?.recordAsPick}):Je(e,!1,{recordAsPick:t?.recordAsPick}),[Je]),
```

### Patch 3: Presentation Variable Hook (`c9543da06-*.js`)
```diff
- tt=G?pe:null
+ tt=G?(ye||K||pe==="xhigh"?"ultracode":pe):null
```

### Patch 4: Bottom-Right Trigger Capsule Binding (`c8e04f916-*.js`)
```diff
- I=v.findIndex(e=>e.id===y),L=I>=0?I:0
+ I=v.findIndex(e=>e.id===(y==="xhigh"?"ultracode":y)),L=I>=0?I:(y==="ultracode"||y==="xhigh"?v.length-1:0)
```

---

## Defensive Configuration

In `~/.claude/settings.json`:
```json
{
  "ultracode": true,
  "effortLevel": "high"
}
```

In `%LOCALAPPDATA%\Claude-3p\configLibrary\<id>.json` (for 3p users):
- Remove `maxEffort: "high"` to prevent clamping catalog to 3 stops.
- Set `defaultModelEffort` to `"high"` or `"xhigh"`.

---

## License
[MIT License](LICENSE) © 2026
