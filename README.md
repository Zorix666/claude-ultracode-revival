# claude-ultracode-revival

Restoring the sixth **Ultracode** stop on the Claude Desktop effort slider — and a write-up of why it goes missing in the first place.

[English](README.md) · [简体中文](README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)](#usage)
[![Claude Desktop](https://img.shields.io/badge/claude%20desktop-2.31226-black)](#compatibility)

---

## What this is

Recent Claude Desktop builds ship a sixth effort stop called `ultracode`. The renderer, the styling, and the workflow behaviour behind it are all present in the app bundle — but the stop never shows up in the slider, and if you ever touch the slider it disappears for the rest of the session.

This repository does two things:

- Documents the four separate code paths that cause it (see [Root cause](#root-cause)).
- Provides two ways to bring the stop back: a persistent patch to the app bundle, and a DevTools hot patch that changes nothing on disk.

## Read this before patching

This is an unofficial patch. It is not affiliated with, endorsed by, or supported by Anthropic.

- **It edits files inside `C:\Program Files\WindowsApps`.** That directory is a protected location. `patch_ultracode.bat` takes ownership of one file there and grants broad ACLs on it, which persists after the patch is applied.
- **App updates undo it.** Any Claude Desktop update replaces the bundle. Re-run the script afterwards; it detects an already-patched file and exits without rewriting.
- **The patch matches minified code by exact substring.** A new build will rename the identifiers. When that happens the script prints `pattern not found` and exits without writing — the file is not left half-patched.
- **Keep the backup the script drops on your Desktop** (`c593f7513-DQShcHgn.js.bak-original`). That, or an app reinstall, is how you roll back.
- **What Ultracode actually does depends on your backend.** The client sends the instruction either way, but how many subagents fan out is up to your gateway and model. Third-party endpoints vary. See [Is Ultracode actually real?](#is-ultracode-actually-real).

## The symptom

Three versions of the same bug:

1. Claude Code CLI reports `Ultracode on (Tab to toggle) · dynamic workflows on every task` under `/effort`. Claude Desktop shows five dots and no sixth.
2. Users who remember seeing it report that one drag of the slider made it vanish permanently.
3. Typing `/effort ultracode` into the composer doesn't help — the capsule degrades to `Extra` or `High` and the slider parks at stop 4 or 5.

## Root cause

Four independent issues, in the order they compound.

### 1. The slider handler hard-codes the flag off

In the interaction bundle:

```js
be = h(e => {
  let { level: t, ultracode: n, silent: r = !1 } = e;
  let l = t === void 0 ? { ultracode: n } : { effortLevel: t, ultracode: n };
  // ...
});
// click / drag on the ordinary stops:
Ye = h((e, t) => Ke(e, !1, { recordAsPick: t?.recordAsPick }), [Ke]);
```

The second argument to `Ke` is literally `false`. Every interaction with stops 1–5 therefore dispatches `{ ultracode: false }` and clears the flag for the session. This is the one that makes the feature look like it "disappears" the moment you touch the slider, and why an external config rewrite that drops `"ultracode": true` appears to be the trigger.

### 2. The model catalog only has five stops

The slider's stops come from the cached model catalog (`published.json`), not from a constant:

```js
function ip(e, t) {
  let i = e.filter(e => ri(e.id) ? t : Fn([e]).length > 0);
  return n.set(t, a), a;
}
```

`ri(id)` resolves to `id === "ultracode"`. The published catalog lists `[low, medium, high, xhigh, max]` for every model, so the filtered array is always length 5. The sixth stop is filtered out before it is ever rendered.

### 3. The sixth stop is already implemented in the renderer

From `c8e04f916-CUEn4KMP.js`:

```js
let V = Math.min(L ?? z?.index ?? I, _.length - 1),
    H = _[V],
    ge = H?.id === te; // te === "ultracode"

re({ label: K(V), accent: ge, index: V });
```

`accent` is what turns on the purple `font-medium text-pro` label and the lit overlay (`qf({ lit: e.atMax })`). The release notes describe the feature directly: *"Added Ultracode to the effort slider, which selects the highest effort level and turns on dynamic workflows."* Only the missing catalog entry keeps it hidden.

### 4. Why the label reads `Extra` or `High`

`ultracode` maps to effort level `xhigh`, whose display string is `Extra`. If the model's capability table doesn't declare that level, a clamping function (`zV`) falls back further to `High`. That's a label problem only — the effort value actually sent is the real one.

## Is Ultracode actually real?

On the client side, yes. Entering the Ultracode state injects workflow instructions into the prompt that ask the model to decompose each substantive task into parallel subtasks and to bypass the normal subagent concurrency cap. With a tool-use-capable backend, the client will fan out many concurrent subagent requests.

How useful that is depends on the backend. With a third-party gateway, the parallelism is real but the quality of the decomposition is whatever your model does with the instruction. This repo does not make a claim either way.

## The patch

Target file:

```
%PROGRAMFILES%\WindowsApps\Claude_<version>\app\resources\ion-dist\assets\v1\c593f7513-DQShcHgn.js
```

**Patch 1 — add the sixth stop to the filtered options list:**

```diff
- let i=e.filter(e=>ri(e.id)?t:Fn([e]).length>0),a=i.length===e.length?e:i;
+ let i=[...e.filter(e=>!ri(e.id)&&Fn([e]).length>0),{id:"ultracode",name:"Ultracode"}],a=i;
```

**Patch 2 — set the flag instead of clearing it when stop 6 is selected:**

```diff
- Ye=h((e,t)=>Ke(e,!1,{recordAsPick:t?.recordAsPick}),[Ke]),
+ Ye=h((e,t)=>ri(e)?Ke(ti,!0,{recordAsPick:t?.recordAsPick}):Ke(e,!1,{recordAsPick:t?.recordAsPick}),[Ke]),
```

Both replacements are applied once each, in that order, by `apply_patch.py`.

## Usage

### Option A — persistent patch

Requirements: Windows 10/11, Claude Desktop installed from the Microsoft Store (MSIX, so it lives under `WindowsApps`), Python 3 on `PATH`, administrator rights.

```bash
git clone https://github.com/Zorix666/claude-ultracode-revival.git
cd claude-ultracode-revival
```

Right-click `patch_ultracode.bat` → **Run as administrator**. The script will:

1. Request elevation via UAC.
2. Kill any running `Claude.exe`.
3. Locate the bundle under `WindowsApps`.
4. Take ownership of that one file and grant write access (`takeown` / `icacls`).
5. Back the original up to your Desktop as `c593f7513-DQShcHgn.js.bak-original`.
6. Run `apply_patch.py`.
7. Relaunch Claude.

Open the effort capsule in the bottom right. Six dots. Drag to the far right for Ultracode; stops 1–5 keep working in both directions.

### Option B — DevTools hot patch

No files touched, no admin rights, gone on the next reload.

1. Set `allowDevTools: true` in your config, then open DevTools with `Ctrl + Alt + I`.
2. Switch to **Console**, type `allow pasting`, press Enter.
3. Click the effort capsule once so the popover component mounts.
4. Paste and run [`hotpatch_console.js`](hotpatch_console.js).
5. Open the capsule again — six dots.

The script walks the React fiber from `[data-cds="ModelSelectorEffort"]`, finds the closest ancestor whose `memoizedProps.options` is an array, and appends the `ultracode` entry.

Worth knowing: this only extends the options array. It does **not** apply patch 2, so the sixth dot renders but selecting it still dispatches `{ ultracode: false }` through the unpatched handler. Treat Option B as a way to confirm the root cause and see the UI, not as a usable toggle. Making it stick requires Option A.

## Configuration notes

Two settings outside the bundle are worth checking if the stop keeps resetting:

`~/.claude/settings.json` — keep the flag and a sane default:

```json
{
  "ultracode": true,
  "effortLevel": "high"
}
```

`%LOCALAPPDATA%\Claude-3p\configLibrary\<config-id>.json` — for third-party gateway builds:

- Remove `maxEffort: "high"`. It truncates the model's stop list to `[low, medium, high]`.
- Set `defaultModelEffort` to `"high"` or `"xhigh"`.

## Compatibility

Written against Claude Desktop **2.31226**. The bundle filename embeds a build hash, and both patches match minified substrings, so expect this to break on updates. When it does, the script refuses to write rather than producing a partially patched bundle.

If you hit a version where the patterns no longer match, open an issue with the build number and the surrounding code — the variable names are the only thing that usually changes.

## Rolling back

Copy `c593f7513-DQShcHgn.js.bak-original` from your Desktop back over the target file as administrator, or reinstall/repair the app. App updates overwrite the bundle anyway.

The ownership and ACL change on that single file survives the rollback. Reset it with `icacls "<path>" /reset` if you care about leaving the install in its original state.

## Repository layout

```
apply_patch.py            # applies the two substring patches, with a backup step
patch_ultracode.bat       # elevation, file location, takeover, restart
hotpatch_console.js       # DevTools one-liner, no disk changes
```

## License

[MIT](LICENSE)
