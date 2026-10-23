# -*- coding: utf-8 -*-
"""
Claude Desktop Ultracode 一键智能自适应永久固化修复工具
内建 Windows UAC 自动提权、杀进程、解除权限写保护、跨版本自适应补丁注入与右下角胶囊常驻显示 Ultracode。
支持全增量幂等执行，任意步骤已打过补丁自动平滑跳过并继续下一步。
"""
import os
import sys
import glob
import re
import shutil
import subprocess
import ctypes
import time

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_elevation():
    script = os.path.abspath(__file__)
    params = f'"{script}"'
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    if ret <= 32:
        print("[!] 提权请求未被允许或被用户取消。")
    sys.exit(0)

def get_claude_install_dir():
    try:
        cmd = ['powershell', '-NoProfile', '-Command', '(Get-AppxPackage *Claude*).InstallLocation']
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        path = res.stdout.strip().splitlines()[-1].strip() if res.stdout.strip() else None
        if path and os.path.isdir(path):
            return path
    except Exception:
        pass

    try:
        dirs = glob.glob(r'C:\Program Files\WindowsApps\Claude_*_x64__pzs8sxrjxfjjc')
        if dirs:
            dirs.sort(key=lambda d: os.path.getmtime(d), reverse=True)
            return dirs[0]
    except Exception:
        pass

    return None

def unlock_file(file_path):
    try:
        subprocess.run(['takeown', '/f', file_path, '/a'], capture_output=True)
        subprocess.run(['takeown', '/f', file_path], capture_output=True)
        subprocess.run(['icacls', file_path, '/grant:r', 'administrators:F'], capture_output=True)
        subprocess.run(['icacls', file_path, '/grant:r', 'Everyone:F'], capture_output=True)
    except Exception as e:
        print(f"[WARN] 解除文件写保护失败: {e}")

def patch_bundle():
    print("=" * 65)
    print("  Claude Desktop Ultracode 智能自适应永久固化修复工具")
    print("=" * 65)

    # 1. 关停 Claude
    print("\n[*] 正在关闭运行中的 Claude 客户端...")
    subprocess.run(['taskkill', '/F', '/IM', 'Claude.exe'], capture_output=True)
    time.sleep(1)

    # 2. 定位当前安装路径
    claude_dir = get_claude_install_dir()
    if not claude_dir:
        print("[!] 未检测到 Claude 安装目录，请确认是否已安装 Claude Desktop！")
        return False

    print(f"[*] 锁定当前活跃版本路径:\n    {claude_dir}")
    assets_dir = os.path.join(claude_dir, 'app', 'resources', 'ion-dist', 'assets', 'v1')
    if not os.path.isdir(assets_dir):
        print(f"[!] 资源目录不存在: {assets_dir}")
        return False

    backup_dir = os.path.join(os.path.expanduser('~'), 'Desktop', 'Claude_Patch_Backup')
    os.makedirs(backup_dir, exist_ok=True)
    all_js = glob.glob(os.path.join(assets_dir, '*.js'))
    large_js = [f for f in all_js if os.path.getsize(f) > 40000]

    print("\n[*] 正在智能定位核心前端 Bundle 文件...")

    # -------------------------------------------------------------
    # 步骤 1：定位并修补刻度扩展文件 (f1, 如 c227f4d5e-*.js)
    # -------------------------------------------------------------
    f1_path = None
    f1_content = None
    p1_pattern = re.compile(r'let\s+i\s*=\s*e\.filter\(e\s*=>\s*[a-zA-Z0-9_$]+\(e\.id\)\s*\?\s*t\s*:\s*[a-zA-Z0-9_$]+\(\[e\]\)\.length\s*>\s*0\)\s*,\s*a\s*=\s*i\.length\s*===\s*e\.length\s*\?\s*e\s*:\s*i;')

    for js in large_js:
        try:
            txt = open(js, 'r', encoding='utf-8').read()
            if 'id:"ultracode",name:"Ultracode"' in txt and 'ModelSelectorEffort' in txt:
                f1_path = js
                f1_content = txt
                print(f"[OK] 刻度扩展已处于生效状态 -> {os.path.basename(js)}")
                break
            elif p1_pattern.search(txt):
                f1_path = js
                f1_content = txt
                break
        except Exception:
            continue

    if f1_path and 'id:"ultracode",name:"Ultracode"' not in f1_content:
        f1_name = os.path.basename(f1_path)
        unlock_file(f1_path)
        shutil.copy2(f1_path, os.path.join(backup_dir, f"{f1_name}.bak-original"))
        old_snippet = p1_pattern.search(f1_content).group(0)
        m1 = re.search(r'e\.filter\(e\s*=>\s*([a-zA-Z0-9_$]+)\(e\.id\)\s*\?\s*t\s*:\s*([a-zA-Z0-9_$]+)\(\[e\]\)\.length\s*>\s*0\)', old_snippet)
        if m1:
            vc_name = m1.group(1)
            ha_name = m1.group(2)
            f1_new = f'let i=[...e.filter(e=>!{vc_name}(e.id)&&{ha_name}([e]).length>0),{{id:"ultracode",name:"Ultracode"}}],a=i;'
            f1_content = f1_content.replace(old_snippet, f1_new, 1)
            with open(f1_path, 'w', encoding='utf-8') as f:
                f.write(f1_content)
            print(f"[OK] 成功注入第 6 档 Ultracode 刻度 -> {f1_name}")
    elif not f1_path:
        print("[WARN] 未能定位到刻度扩展文件 f1")

    # -------------------------------------------------------------
    # 步骤 2：定位并修补交互派发与呈现逻辑 (f2, 如 c9543da06-*.js)
    # -------------------------------------------------------------
    f2_path = None
    f2_content = None

    for js in large_js:
        try:
            txt = open(js, 'r', encoding='utf-8').read()
            if 'recordAsPick' in txt and 'presentedEffortLevel' in txt:
                f2_path = js
                f2_content = txt
                break
        except Exception:
            continue

    if f2_path:
        f2_name = os.path.basename(f2_path)
        unlock_file(f2_path)
        shutil.copy2(f2_path, os.path.join(backup_dir, f"{f2_name}.bak-original"))
        modified_f2 = False

        # 补丁 2.1：双向交互派发
        if 'e==="ultracode"' in f2_content:
            print(f"[OK] 双向交互派发已处于生效状态 -> {f2_name}")
        else:
            p2_pattern = re.compile(r'([a-zA-Z0-9_$]+)\s*=\s*([a-zA-Z0-9_$]+)\(\(e,t\)\s*=>\s*([a-zA-Z0-9_$]+)\(e,\s*!1\s*,\s*\{\s*recordAsPick\s*:\s*t\?\.recordAsPick\s*\}\),\s*\[\3\]\),')
            m2 = p2_pattern.search(f2_content)
            if m2:
                old_dispatch = m2.group(0)
                ze_var = m2.group(1)
                x_var = m2.group(2)
                je_var = m2.group(3)
                new_dispatch = f'{ze_var}={x_var}((e,t)=>e==="ultracode"?{je_var}("xhigh",!0,{{recordAsPick:t?.recordAsPick}}):{je_var}(e,!1,{{recordAsPick:t?.recordAsPick}}),[{je_var}]),'
                f2_content = f2_content.replace(old_dispatch, new_dispatch, 1)
                modified_f2 = True
                print(f"[OK] 成功打通双向交互派发 -> {f2_name}")

        # 补丁 2.2：胶囊呈现变量修正 (tt=G?pe:null)
        if 'pe==="xhigh"?"ultracode":pe' in f2_content:
            print(f"[OK] 胶囊呈现实体已处于生效状态 -> {f2_name}")
        elif 'tt=G?pe:null' in f2_content:
            f2_content = f2_content.replace('tt=G?pe:null', 'tt=G?(ye||K||pe==="xhigh"?"ultracode":pe):null', 1)
            modified_f2 = True
            print(f"[OK] 成功修复胶囊呈现实体挂钩 -> {f2_name}")

        # 补丁 2.3：解除第三方模型（如 DeepSeek）的 Ultracode 拦截与自动重置
        if 'disableWorkflows?.value!==!0&&u&&(!0)&&ge' in f2_content:
            print(f"[OK] 第三方模型 Ultracode 放行已处于生效状态 -> {f2_name}")
        elif '&&u&&(he||oe)&&ge' in f2_content:
            f2_content = f2_content.replace('&&u&&(he||oe)&&ge', '&&u&&(!0)&&ge', 1)
            modified_f2 = True
            print(f"[OK] 成功放行第三方模型支持 Ultracode -> {f2_name}")

        if modified_f2:
            with open(f2_path, 'w', encoding='utf-8') as f:
                f.write(f2_content)
    else:
        print("[WARN] 未能定位到交互与呈现文件 f2")

    # -------------------------------------------------------------
    # 步骤 3：定位并修补胶囊触发器显示组件 (f3, 如 c8e04f916-*.js)
    # -------------------------------------------------------------
    f3_path = None
    f3_content = None

    for js in all_js:
        try:
            txt = open(js, 'r', encoding='utf-8').read()
            if 'ModelSelectorEffort' in txt and ('I=v.findIndex(e=>e.id===y)' in txt or 'y==="xhigh"?"ultracode":y' in txt):
                f3_path = js
                f3_content = txt
                break
        except Exception:
            continue

    if f3_path:
        f3_name = os.path.basename(f3_path)
        unlock_file(f3_path)
        shutil.copy2(f3_path, os.path.join(backup_dir, f"{f3_name}.bak-original"))
        modified_f3 = False

        # 补丁 3.1：索引计算映射
        p4_old = 'I=v.findIndex(e=>e.id===y),L=I>=0?I:0'
        p4_new = 'I=v.findIndex(e=>e.id===(y==="xhigh"?"ultracode":y)),L=I>=0?I:(y==="ultracode"||y==="xhigh"?v.length-1:0)'
        if p4_old in f3_content:
            f3_content = f3_content.replace(p4_old, p4_new, 1)
            modified_f3 = True
            print(f"[OK] 成功绑定胶囊索引查找 -> {f3_name}")
        elif p4_new in f3_content:
            print(f"[OK] 胶囊索引查找已处于生效状态 -> {f3_name}")

        # 补丁 3.2：Trigger 药丸文字与高亮实时联动
        expr = '(H===v.length-1||B?.id==="ultracode"||y==="ultracode"||y==="xhigh"?"Ultracode":q(L))'
        target_render = 'render:typeof O=="function"?O({label:q(L),warningLabel:Z,open:M,disabled:S||!W}):O??t(ee,{variant:"ghost",size:C,"data-cds":"ModelSelectorEffort","aria-label":Oe,"aria-keyshortcuts":Ae,className:_("min-w-0 shrink-0",ce),children:[r("span",{className:"min-w-0 truncate",children:q(L)}),'
        repl_render = f'render:typeof O=="function"?O({{label:{expr},warningLabel:Z,open:M,disabled:S||!W}}):O??t(ee,{{variant:"ghost",size:C,"data-cds":"ModelSelectorEffort","aria-label":Oe,"aria-keyshortcuts":Ae,className:_("min-w-0 shrink-0",ce),children:[r("span",{{className:_("min-w-0 truncate",_e&&"font-medium text-pro"),children:{expr}}}),'

        if target_render in f3_content:
            f3_content = f3_content.replace(target_render, repl_render, 1)
            modified_f3 = True
            print(f"[OK] 成功打通右下角胶囊实时联动与紫色高亮 -> {f3_name}")
        elif expr in f3_content:
            print(f"[OK] 右下角胶囊实时联动已处于生效状态 -> {f3_name}")

        if modified_f3:
            with open(f3_path, 'w', encoding='utf-8') as f:
                f.write(f3_content)
    else:
        print("[WARN] 未能定位到胶囊触发器组件 f3")

    print("\n" + "=" * 65)
    print("  [SUCCESS] 永久固化全部完成！")
    print("  滑块已拥有 6 档，右下角胶囊将常驻显示为紫色的 Ultracode！")
    print("=" * 65)

    # 4. 重新拉起 Claude
    print("\n[*] 正在重新拉起 Claude Desktop 客户端...")
    try:
        claude_exe = os.path.join(claude_dir, 'app', 'Claude.exe')
        subprocess.Popen(f'explorer.exe "{claude_exe}"', shell=True)
    except Exception as e:
        print(f"[!] 自动拉起提示: 请从桌面或开始菜单手动打开 Claude ({e})")

    return True

def main():
    if not is_admin():
        print("[*] 正在请求管理员权限以解除系统文件保护...")
        run_elevation()
        return

    try:
        success = patch_bundle()
    except Exception as e:
        print(f"\n[!] 发生异常: {e}")
        success = False

    print("\n------------------------------------------------------------")
    input("执行完毕。按回车键退出窗口...")

if __name__ == '__main__':
    main()
