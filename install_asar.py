# -*- coding: utf-8 -*-
"""
把 build_asar.py 产出的补丁装进已安装的 Claude Desktop（MSIX 商店版）。

流程：定位活跃包 -> 备份现场 -> 提权 -> 杀进程 -> takeown/icacls -> 拷贝
      -> 用 AUMID 拉起 -> 等 40 秒健康检查 -> 失败自动回滚

用法：
    python install_asar.py                 # 自动定位安装目录
    python install_asar.py --dir <out>     # 指定构建产物目录
"""
import os
import sys
import glob
import time
import shutil
import ctypes
import argparse
import hashlib
import struct
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BUILD = os.path.join(HERE, 'build', 'v5')
BACKUP_DIR = os.path.join(HERE, 'backup')
LOG = os.path.join(HERE, 'logs', 'install.log')

AUMID = 'Claude_pzs8sxrjxfjjc!Claude'

# 健康检查：这些串出现在启动后的日志里，说明渲染器已经炸了
ERROR_PATTERNS = (
    b'Uncaught SyntaxError',
    b'Uncaught ReferenceError',
    b'Uncaught TypeError',
    b'Uncaught Error',
    b"cannot read the app's bundled web page",
    b'Main view load failure',
    b'ERR_UNEXPECTED',
)


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def elevate():
    """提权重开自己时**必须带上原始参数**，否则子进程会退回默认 --dir。"""
    script = os.path.abspath(__file__)
    args = list(sys.argv[1:])
    # --dir 必须转成绝对路径：提权后的子进程工作目录不是当前目录
    for i, a in enumerate(args):
        if a == '--dir' and i + 1 < len(args):
            args[i + 1] = os.path.abspath(args[i + 1])
    params = f'"{script}"'
    if args:
        params += ' ' + subprocess.list2cmdline(args)
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, 'runas', sys.executable, params, None, 1)
    if ret <= 32:
        log(f'[!] 提权失败（ShellExecuteW 返回 {ret}），请手动以管理员身份运行本脚本')
    sys.exit(0)


def asar_header_sha(path):
    with open(path, 'rb') as f:
        d = f.read()
    hs = struct.unpack('<I', d[12:16])[0]
    return hashlib.sha256(d[16:16 + hs]).hexdigest()


def find_install_dir():
    """优先用 Appx 注册信息，其次按版本号解析目录名。

    注意：**不要按 mtime 排序** —— 多版本目录并存时，刚下载但没启用的
    那个版本 mtime 最新，会把补丁装进一个根本不会被运行的目录，
    装完界面一点变化都没有，日志还显示成功。
    """
    try:
        r = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             '(Get-AppxPackage Claude).InstallLocation'],
            capture_output=True, text=True)
        for line in (r.stdout or '').splitlines():
            p = line.strip()
            if p and os.path.isdir(p):
                return p
    except Exception:
        pass

    cands = [p for p in glob.glob(r'C:\Program Files\WindowsApps\Claude_*_x64__pzs8sxrjxfjjc')
             if os.path.isdir(p)]

    def ver(p):
        name = os.path.basename(p)
        parts = name.split('_')[1].split('.') if '_' in name else ['0']
        try:
            return tuple(int(x) for x in parts)
        except ValueError:
            return (0,)

    return sorted(cands, key=ver)[-1] if cands else None


def app_paths(install_dir):
    return (os.path.join(install_dir, 'app', 'resources', 'ion-dist.asar'),
            os.path.join(install_dir, 'app', 'claude.exe'))


def stop_claude():
    log('关闭运行中的 Claude ...')
    for name in ('claude.exe', 'Claude.exe'):
        subprocess.run(['taskkill', '/F', '/IM', name], capture_output=True)
    time.sleep(3)


def grant(paths):
    for p in paths:
        subprocess.run(['takeown', '/f', p, '/a'], capture_output=True)
        subprocess.run(['takeown', '/f', p], capture_output=True)
        subprocess.run(['icacls', p, '/grant:r', 'administrators:F'], capture_output=True)
        subprocess.run(['icacls', p, '/grant:r', 'Everyone:F'], capture_output=True)


def launch():
    """必须走 AUMID。

    直接 `explorer.exe <dir>\\app\\claude.exe` 会绕过 MSIX 包身份，
    轻则起不来，重则起成一个没有沙盒注册表的野进程，会话列表全空。
    """
    log('拉起 Claude（shell:AppsFolder\\AUMID）...')
    subprocess.Popen(['explorer.exe', f'shell:AppsFolder\\{AUMID}'])


def alive():
    r = subprocess.run(['tasklist', '/fi', 'IMAGENAME eq claude.exe'],
                       capture_output=True, text=True)
    return 'claude.exe' in (r.stdout or '').lower()


def tail_size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def read_since(path, offset):
    try:
        with open(path, 'rb') as f:
            f.seek(offset)
            return f.read()
    except OSError:
        return b''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', default=DEFAULT_BUILD, help='构建产物目录')
    ap.add_argument('--no-health', action='store_true', help='跳过健康检查（调试用）')
    args = ap.parse_args()

    if not is_admin():
        log('请求管理员权限 ...')
        elevate()

    build_dir = os.path.abspath(args.dir)
    src_asar = os.path.join(build_dir, 'ion-dist.asar')
    src_exe = os.path.join(build_dir, 'claude.exe')
    for p in (src_asar, src_exe):
        if not os.path.exists(p):
            log(f'[FATAL] 缺少构建产物：{p}')
            return 1

    install_dir = find_install_dir()
    if not install_dir:
        log('[FATAL] 没找到 Claude 安装目录')
        return 1
    dst_asar, dst_exe = app_paths(install_dir)
    log(f'目标：{install_dir}')

    sha = asar_header_sha(src_asar)
    if sha.encode() not in open(src_exe, 'rb').read():
        log('[FATAL] 构建出的 exe 里没有这份 asar 的 header 哈希，两个文件不是一对')
        return 1
    log(f'构建产物校验通过：header_sha={sha[:16]}...')

    # 备份"安装前现场"，失败时回滚到这里（不是回滚到上游原版）
    os.makedirs(BACKUP_DIR, exist_ok=True)
    prev_asar = os.path.join(BACKUP_DIR, 'ion-dist.asar.prev')
    prev_exe = os.path.join(BACKUP_DIR, 'claude.exe.prev')
    if not (os.path.exists(prev_asar) and os.path.exists(prev_exe)):
        log('备份当前现场 ...')
        shutil.copy2(dst_asar, prev_asar)
        shutil.copy2(dst_exe, prev_exe)
    log(f'回滚点：{asar_header_sha(prev_asar)[:16]}...')

    web_log = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Claude-3p', 'logs', 'claude.ai-web.log')
    main_log = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Claude-3p', 'logs', 'main.log')
    off_web, off_main = tail_size(web_log), tail_size(main_log)

    def rollback():
        stop_claude()
        grant([dst_asar, dst_exe])
        for src, dst in ((prev_asar, dst_asar), (prev_exe, dst_exe)):
            try:
                shutil.copy2(src, dst)
                log(f'  已还原 {dst}')
            except Exception as e:
                log(f'  还原失败 {dst}: {e}')
        launch()

    stop_claude()
    grant([dst_asar, dst_exe])

    try:
        shutil.copy2(src_asar, dst_asar)
        shutil.copy2(src_exe, dst_exe)
        log('[OK] 两个文件已写入')
    except Exception as e:
        log(f'[FAIL] 拷贝失败：{e}，回滚')
        rollback()
        return 1

    if asar_header_sha(dst_asar) != sha:
        log('[FAIL] 写入后哈希不一致，回滚')
        rollback()
        return 1

    launch()

    if args.no_health:
        log('已跳过健康检查')
        return 0

    log('等待 40 秒让渲染器启动 ...')
    time.sleep(40)

    if not alive():
        log('[FAIL] 进程没起来，回滚')
        rollback()
        return 1

    new_log = read_since(web_log, off_web) + read_since(main_log, off_main)
    hits = [p.decode() for p in ERROR_PATTERNS if p in new_log]
    if hits:
        log(f'[FAIL] 渲染器报错：{hits}')
        for line in new_log[-800:].decode('utf-8', errors='replace').splitlines()[-6:]:
            log('   ' + line)
        rollback()
        return 1

    log('=== SUCCESS：无渲染器错误，补丁已生效 ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
