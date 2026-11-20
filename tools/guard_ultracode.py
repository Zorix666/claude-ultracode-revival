# -*- coding: utf-8 -*-
"""
Login guard: detect that a Claude Desktop update wiped the patch and re-apply it.

This is a CONFIG-DRIVEN reference implementation. Targets and hashes live in
`guard_config.json` next to this file (see `guard_config.example.json`).

    python guard_ultracode.py [--config guard_config.json]

Design rules that matter (each one cost real debugging time):

  1. NEVER `taskkill /im claude.exe`. A machine can host both the MSIX package
     and the Electron standalone build; both executables are named claude.exe.
     Kill by full path only:
         Get-Process claude | Where-Object { $_.Path -eq '<exe>' } | Stop-Process -Force

  2. Path layout differs per channel, so it cannot be shared:
         msix     : <root>\\app\\resources\\ion-dist.asar   <root>\\app\\claude.exe
         electron : <root>\\resources\\ion-dist.asar        <root>\\claude.exe

  3. Require an `orig_hash` allow-list. Overwriting on "hash != patched" means
     that after an upstream upgrade the guard marches a stale build over the new
     version's JS — instant white screen. Three states only:
         == patched_hash -> up to date, skip
         == orig_hash    -> pristine, safe to re-apply
         anything else   -> VERSION DRIFT, skip loudly, a human must re-patch

  4. The scheduled task runs under pythonw.exe (GUI subsystem): sys.stdout is
     None and a bare print() raises AttributeError, taking the whole guard down.
     Wrap print() in try/except, and log to a file with a UTF-8 BOM so Windows
     tools (PowerShell Get-Content, Notepad) do not render it as mojibake.
"""
import os
import sys
import glob
import time
import json
import shutil
import struct
import hashlib
import argparse
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def log(msg, logfile):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        print(line)
    except Exception:          # pythonw.exe: sys.stdout is None
        pass
    if not logfile:
        return
    try:
        # First write gets a BOM; later appends must not (utf-8-sig would add
        # one every single time).
        exists = os.path.exists(logfile) and os.path.getsize(logfile) > 0
        with open(logfile, "a", encoding="utf-8" if exists else "utf-8-sig") as f:
            f.write(line + "\n")
    except Exception:
        pass


def asar_header_sha(path):
    with open(path, 'rb') as f:
        d = f.read()
    hs = struct.unpack('<I', d[12:16])[0]
    return hashlib.sha256(d[16:16 + hs]).hexdigest()


def paths_for(root, layout):
    if layout == "msix":
        return (os.path.join(root, "app", "resources", "ion-dist.asar"),
                os.path.join(root, "app", "claude.exe"))
    return (os.path.join(root, "resources", "ion-dist.asar"),
            os.path.join(root, "claude.exe"))


def active_msix_pkg(pkg_glob):
    try:
        r = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             'Get-AppxPackage Claude | Select-Object -ExpandProperty InstallLocation'],
            capture_output=True, text=True)
        out = (r.stdout or '').strip()
        if out and os.path.isdir(out):
            return out
    except Exception:
        pass
    cands = [p for p in glob.glob(pkg_glob) if os.path.isdir(p)] if pkg_glob else []
    if not cands:
        return None

    def ver(p):
        base = os.path.basename(p)
        parts = [x for x in base.split('_') if x and x[0].isdigit()]
        return tuple(int(n) for n in parts[0].split('.')) if parts else (0,)

    return sorted(cands, key=ver)[-1]


def kill_for(exe_path):
    safe = exe_path.replace("'", "''")
    ps = ("Get-Process claude -ErrorAction SilentlyContinue | "
          f"Where-Object {{ $_.Path -eq '{safe}' }} | Stop-Process -Force")
    subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True)
    time.sleep(2)


def launch(exe_path, layout, msix_aumid):
    if layout == "msix":
        subprocess.Popen(['explorer.exe', f'shell:AppsFolder\\{msix_aumid}'])
    else:
        subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))


def ensure(name, root, layout, cfg, logfile, msix_aumid):
    dst_asar, dst_exe = paths_for(root, layout)
    tag = cfg.get("label", name)

    if not os.path.exists(dst_asar):
        log(f"[{tag}] asar missing at {dst_asar}", logfile)
        return
    try:
        h = asar_header_sha(dst_asar)
    except Exception as e:
        log(f"[{tag}] cannot read asar header: {e}", logfile)
        return

    if h == cfg["patched_hash"]:
        log(f"[{tag}] already on latest patched hash {h[:10]}", logfile)
        return
    if h != cfg["orig_hash"]:
        log(f"[{tag}] VERSION DRIFT: {h[:10]} is neither orig ({cfg['orig_hash'][:10]}) "
            f"nor patched ({cfg['patched_hash'][:10]}) -> SKIPPING, re-patch needed", logfile)
        return

    build_asar = os.path.join(cfg["build_dir"], "ion-dist.asar")
    build_exe = os.path.join(cfg["build_dir"], "claude.exe")
    log(f"[{tag}] pristine build detected ({h[:10]}) -> re-applying patch", logfile)
    if not (os.path.exists(build_asar) and os.path.exists(build_exe)):
        log(f"[{tag}] build artifacts missing under {cfg['build_dir']}", logfile)
        return

    kill_for(dst_exe)
    if layout == "msix":
        for p in (dst_asar, dst_exe):
            subprocess.run(['takeown', '/f', p, '/a'], capture_output=True)
            subprocess.run(['takeown', '/f', p], capture_output=True)
            subprocess.run(['icacls', p, '/grant:r', 'administrators:F'], capture_output=True)
            subprocess.run(['icacls', p, '/grant:r', 'Everyone:F'], capture_output=True)

    try:
        shutil.copy2(build_asar, dst_asar)
        shutil.copy2(build_exe, dst_exe)
    except Exception as e:
        log(f"[{tag}] copy failed: {e}", logfile)
        return

    now = asar_header_sha(dst_asar)
    if now == cfg["patched_hash"]:
        log(f"[{tag}] re-applied successfully, relaunching", logfile)
        launch(dst_exe, layout, msix_aumid)
    else:
        log(f"[{tag}] post-copy verification FAILED, got {now}", logfile)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default=os.path.join(HERE, 'guard_config.json'))
    args = ap.parse_args()

    if not os.path.exists(args.config):
        print(f"config not found: {args.config}\nsee guard_config.example.json")
        return 1

    with open(args.config, encoding='utf-8') as f:
        conf = json.load(f)

    logfile = conf.get('log')
    if logfile and not os.path.isabs(logfile):
        logfile = os.path.join(HERE, logfile)

    pkg_glob = conf.get('msix_glob')
    msix_aumid = conf.get('msix_aumid', 'Claude_pzs8sxrjxfjjc!Claude')
    targets = conf.get('targets', {})
    did_any = False

    pkg = active_msix_pkg(pkg_glob)
    if pkg:
        name = os.path.basename(pkg)
        if name in targets:
            ensure(name, pkg, "msix", targets[name], logfile, msix_aumid)
            did_any = True
        else:
            log(f"UNKNOWN MSIX BUILD: {name} (not in config)", logfile)

    for name, cfg in targets.items():
        if cfg.get("layout") != "electron":
            continue
        root = cfg.get("root")
        if root and os.path.isdir(root):
            ensure(name, root, "electron", cfg, logfile, msix_aumid)
            did_any = True

    if not did_any:
        log("no Claude installation found, nothing to do", logfile)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        import traceback
        try:
            print(traceback.format_exc())
        except Exception:
            pass
        sys.exit(1)
