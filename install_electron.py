# -*- coding: utf-8 -*-
"""
Installer for the **4.23118.x Electron standalone** Claude Desktop.

This build lives in a user-writable directory, so unlike the MSIX package it
needs no elevation, no takeown, no icacls. Just: stop it, swap two files, start it.

    <root>\\resources\\ion-dist.asar
    <root>\\claude.exe

Usage
    python install_electron.py                 # auto-detect %LOCALAPPDATA%\\Programs\\Claude
    python install_electron.py --dir "D:\\Claude"
    python install_electron.py --build build/v4 --dry-run

Safety
  - Refuses to run if the build directory lacks either artifact.
  - Keeps one pristine copy of each original as `*.bak` (never overwritten once it exists).
  - Verifies the asar header sha256 after copying; failure is reported, not swallowed.
  - Kills only processes whose executable path equals this install's claude.exe,
    so a coexisting MSIX install is left alone.
"""
import os
import sys
import time
import shutil
import struct
import hashlib
import argparse
import subprocess

DEFAULT_ROOT = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local")),
    "Programs", "Claude")

# Chromium's profile dir. The standalone build runs with --user-data-dir pointing
# here (visible in the child process command lines).
DEFAULT_USER_DATA = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local")),
    "Claude-3p")


def clear_code_cache(user_data):
    """Drop V8's compiled-JS cache.

    Chromium caches compiled scripts under the user-data dir, keyed by source.
    Swapping the asar without clearing it can leave the *old* bundle running even
    though the process restarted — the UI looks untouched and it is easy to blame
    the patch. Returns the entries actually removed.
    """
    removed = []
    for name in ('Code Cache', 'GPUCache'):
        d = os.path.join(user_data, name)
        if os.path.isdir(d):
            try:
                shutil.rmtree(d)
                removed.append(name)
            except Exception as e:
                log(f'  [cache] could not remove {d}: {e}')
    return removed


def log(msg):
    print(msg, flush=True)


def asar_header_sha(path):
    with open(path, 'rb') as f:
        d = f.read()
    hs = struct.unpack('<I', d[12:16])[0]
    return hashlib.sha256(d[16:16 + hs]).hexdigest()


def kill_this_install(exe_path):
    """Kill only processes running from *this* install.

    `taskkill /im claude.exe` would also kill the MSIX install — both ship an
    executable with the same name.
    """
    safe = exe_path.replace("'", "''")
    ps = ("Get-Process claude -ErrorAction SilentlyContinue | "
          f"Where-Object {{ $_.Path -eq '{safe}' }} | Stop-Process -Force")
    subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True)


def count_running(exe_path):
    safe = exe_path.replace("'", "''")
    ps = ("@(Get-Process claude -ErrorAction SilentlyContinue | "
          f"Where-Object {{ $_.Path -eq '{safe}' }}).Count")
    r = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                       capture_output=True, text=True)
    try:
        return int((r.stdout or '0').strip() or 0)
    except ValueError:
        return 0


def ensure_backup(path):
    bak = path + '.bak'
    if os.path.exists(path) and not os.path.exists(bak):
        shutil.copy2(path, bak)
        log(f'  [backup] {bak}')
    elif os.path.exists(bak):
        log(f'  [backup] exists, kept as-is: {bak}')


def main():
    ap = argparse.ArgumentParser(description='Install patched asar into Claude Desktop (Electron standalone)')
    ap.add_argument('--dir', default=DEFAULT_ROOT, help='install root (contains claude.exe)')
    ap.add_argument('--build', default='build/v4', help='directory with ion-dist.asar + claude.exe')
    ap.add_argument('--dry-run', action='store_true', help='report what would happen')
    ap.add_argument('--no-launch', action='store_true', help='do not start Claude afterwards')
    ap.add_argument('--user-data', default=DEFAULT_USER_DATA,
                    help='Chromium profile dir, used to clear the JS code cache')
    ap.add_argument('--keep-cache', action='store_true', help='do not clear the JS code cache')
    args = ap.parse_args()

    root = os.path.abspath(args.dir)
    build = os.path.abspath(args.build)
    dst_asar = os.path.join(root, 'resources', 'ion-dist.asar')
    dst_exe = os.path.join(root, 'claude.exe')
    src_asar = os.path.join(build, 'ion-dist.asar')
    src_exe = os.path.join(build, 'claude.exe')

    log(f'[install root] {root}')
    log(f'[build dir]    {build}')

    for p, what in ((root, 'install root'), (dst_asar, 'target asar'),
                    (src_asar, 'built asar'), (src_exe, 'built exe')):
        if not os.path.exists(p):
            log(f'[FAIL] {what} missing: {p}')
            return 1

    target_hash = asar_header_sha(src_asar)
    current_hash = asar_header_sha(dst_asar)
    log(f'[hash] current = {current_hash}')
    log(f'[hash] target  = {target_hash}')
    if current_hash == target_hash:
        log('[skip] already on the patched build')
        return 0

    running = count_running(dst_exe)
    log(f'[state] {running} process(es) running from this install')

    if args.dry_run:
        log('[dry-run] would stop those processes, back up originals, copy 2 files, relaunch')
        return 0

    if running:
        log('[stop] terminating this install only ...')
        kill_this_install(dst_exe)
        time.sleep(3)
        running = count_running(dst_exe)
        if running:
            log(f'[FAIL] {running} process(es) still alive; close Claude and retry')
            return 1

    if not args.keep_cache:
        removed = clear_code_cache(args.user_data)
        if removed:
            log(f'[cache] cleared: {", ".join(removed)}')
        else:
            log('[cache] nothing to clear')

    log('[backup]')
    ensure_backup(dst_asar)
    ensure_backup(dst_exe)

    log('[copy]')
    try:
        shutil.copy2(src_asar, dst_asar)
        shutil.copy2(src_exe, dst_exe)
    except Exception as e:
        log(f'[FAIL] copy failed: {e}')
        log('       originals are intact as *.bak — restore with: copy /y x.bak x')
        return 1

    after = asar_header_sha(dst_asar)
    if after != target_hash:
        log(f'[FAIL] post-copy verification failed: got {after}')
        return 1
    log('[ok] asar header sha256 verified')

    if not args.no_launch:
        log('[launch]')
        subprocess.Popen([dst_exe], cwd=root)
        time.sleep(8)
        n = count_running(dst_exe)
        log(f'[state] {n} process(es) running')
        if n == 0:
            log('[WARN] Claude did not start; restore with the .bak files')

    log('DONE')
    return 0


if __name__ == '__main__':
    sys.exit(main())
