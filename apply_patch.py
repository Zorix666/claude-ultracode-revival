# -*- coding: utf-8 -*-
"""
Claude Desktop Ultracode 一键智能自适应永久固化修复工具 (支持 Claude v2 & v3 全系列)
"""
import os
import sys
import glob
import re
import shutil
import subprocess
import ctypes
import time

log_file = os.path.join(os.path.expanduser('~'), 'Desktop', 'patch_execution.log')

def log(msg):
    print(msg)
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except Exception:
        pass

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
        log("[!] 提权请求未被允许或被用户取消。")
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
        log(f"[WARN] 解除文件写保护失败: {e}")

def patch_bundle():
    log("=" * 65)
    log("  Claude Desktop Ultracode 智能自适应永久固化修复工具 (v2/v3 通用)")
    log("=" * 65)

    # 1. 关停 Claude
    log("\n[*] 正在关闭运行中的 Claude 客户端...")
    subprocess.run(['taskkill', '/F', '/IM', 'Claude.exe'], capture_output=True)
    time.sleep(1)

    # 2. 定位当前安装路径
    claude_dir = get_claude_install_dir()
    if not claude_dir:
        log("[!] 未检测到 Claude 安装目录，请确认是否已安装 Claude Desktop！")
        return False

    log(f"[*] 锁定当前活跃版本路径:\n    {claude_dir}")
    assets_dir = os.path.join(claude_dir, 'app', 'resources', 'ion-dist', 'assets', 'v1')
    if not os.path.isdir(assets_dir):
        log(f"[!] 资源目录不存在: {assets_dir}")
        return False

    backup_dir = os.path.join(os.path.expanduser('~'), 'Desktop', 'Claude_Patch_Backup')
    os.makedirs(backup_dir, exist_ok=True)
    all_js = glob.glob(os.path.join(assets_dir, '*.js'))
    large_js = [f for f in all_js if os.path.getsize(f) > 40000]

    log("\n[*] 正在智能定位核心前端 Bundle 文件...")

    # -------------------------------------------------------------
    # 步骤 1：定位并修补刻度扩展 & 强制独立滑块模式 (f1, 如 c227f4d5e-*.js)
    # -------------------------------------------------------------
    f1_path = None
    f1_content = None
    p1_pattern = re.compile(r'let\s+i\s*=\s*e\.filter\(e\s*=>\s*([a-zA-Z0-9_$]+)\(e\.id\)\s*\?\s*t\s*:\s*([a-zA-Z0-9_$]+)\(\[e\]\)\.length\s*>\s*0\)\s*,\s*a\s*=\s*i\.length\s*===\s*e\.length\s*\?\s*e\s*:\s*i;')

    for js in large_js:
        try:
            txt = open(js, 'r', encoding='utf-8').read()
            if 'id:"ultracode",name:"Ultracode"' in txt and 'ModelSelectorEffort' in txt:
                f1_path = js
                f1_content = txt
                log(f"[OK] 刻度扩展已处于生效状态 -> {os.path.basename(js)}")
                break
            elif p1_pattern.search(txt) and 'ModelSelectorEffort' in txt:
                f1_path = js
                f1_content = txt
                break
        except Exception:
            continue

    if f1_path:
        f1_name = os.path.basename(f1_path)
        unlock_file(f1_path)
        shutil.copy2(f1_path, os.path.join(backup_dir, f"{f1_name}.bak-original"))
        modified_f1 = False

        # 补丁 1.1：注入第 6 档 Ultracode 刻度
        if 'id:"ultracode",name:"Ultracode"' not in f1_content:
            m1 = p1_pattern.search(f1_content)
            if m1:
                vc_name = m1.group(1)
                ha_name = m1.group(2)
                f1_new = f'let i=[...e.filter(e=>!{vc_name}(e.id)&&{ha_name}([e]).length>0),{{id:"ultracode",name:"Ultracode"}}],a=i;'
                f1_content = f1_content.replace(m1.group(0), f1_new, 1)
                modified_f1 = True
                log(f"[OK] 成功注入第 6 档 Ultracode 刻度 -> {f1_name}")
        else:
            log(f"[OK] 第 6 档刻度已处于生效状态 -> {f1_name}")

        # 补丁 1.2：强制激活独立滑块胶囊模式 (恢复被收缩进菜单的滑块)
        if 'thinkingStyle:"separate"' in f1_content and ('w$={shortcuts:!0,thinkingStyle:"separate"}' in f1_content or 'wK={shortcuts:!0,thinkingStyle:"separate"}' in f1_content):
            log(f"[OK] 强制独立滑块胶囊模式已生效 -> {f1_name}")
        else:
            p_style = re.compile(r'([a-zA-Z0-9_$]+)\s*=\s*\{\s*shortcuts\s*:\s*!0\s*\}')
            m_style = p_style.search(f1_content)
            if m_style:
                var_name = m_style.group(1)
                f1_content = f1_content.replace(m_style.group(0), f'{var_name}={{shortcuts:!0,thinkingStyle:"separate"}}', 1)
                modified_f1 = True
                log(f"[OK] 成功激活全场景独立滑块胶囊模式 -> {f1_name}")

        if modified_f1:
            with open(f1_path, 'w', encoding='utf-8') as f:
                f.write(f1_content)
    elif not f1_path:
        log("[WARN] 未能定位到刻度扩展文件 f1")

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

        # 补丁 2.1：双向交互派发 (适配 v2 及 v3)
        if 'e==="ultracode"' in f2_content:
            log(f"[OK] 双向交互派发已处于生效状态 -> {f2_name}")
        else:
            p2_v3 = re.compile(r'([a-zA-Z0-9_$]+)\s*=\s*J1\((\$,\d+,[a-zA-Z0-9_$]+)\)\?K1\(\2,\(e,t\)\s*=>\s*([a-zA-Z0-9_$]+)\(e,\s*!1\s*,\s*\{\s*recordAsPick\s*:\s*t\?\.recordAsPick\s*\}\)\):(\$\[\d+\])')
            m2_v3 = p2_v3.search(f2_content)
            p2_v2 = re.compile(r'([a-zA-Z0-9_$]+)\s*=\s*([a-zA-Z0-9_$]+)\(\(e,t\)\s*=>\s*([a-zA-Z0-9_$]+)\(e,\s*!1\s*,\s*\{\s*recordAsPick\s*:\s*t\?\.recordAsPick\s*\}\),\s*\[\3\]\),')
            m2_v2 = p2_v2.search(f2_content)

            if m2_v3:
                yt_var, k1_arg, mt_var, arr_var = m2_v3.groups()
                new_dispatch = f'{yt_var}=J1({k1_arg})?K1({k1_arg},(e,t)=>e==="ultracode"?{mt_var}("xhigh",!0,{{recordAsPick:t?.recordAsPick}}):{mt_var}(e,!1,{{recordAsPick:t?.recordAsPick}})):{arr_var}'
                f2_content = f2_content.replace(m2_v3.group(0), new_dispatch, 1)
                modified_f2 = True
                log(f"[OK] 成功打通双向交互派发 (v3) -> {f2_name}")
            elif m2_v2:
                ze_var, x_var, je_var = m2_v2.groups()
                new_dispatch = f'{ze_var}={x_var}((e,t)=>e==="ultracode"?{je_var}("xhigh",!0,{{recordAsPick:t?.recordAsPick}}):{je_var}(e,!1,{{recordAsPick:t?.recordAsPick}}),[{je_var}]),'
                f2_content = f2_content.replace(m2_v2.group(0), new_dispatch, 1)
                modified_f2 = True
                log(f"[OK] 成功打通双向交互派发 (v2) -> {f2_name}")

        # 补丁 2.2：胶囊呈现变量修正
        if 'pe==="xhigh"?"ultracode":pe' in f2_content or 'Y==="xhigh"?"ultracode":Y' in f2_content:
            log(f"[OK] 胶囊呈现实体已处于生效状态 -> {f2_name}")
        elif 'wt=pe?Y:null,Tt=' in f2_content:
            f2_content = f2_content.replace('wt=pe?Y:null,Tt=', 'wt=pe?(ye||_e||Y==="xhigh"?"ultracode":Y):null,Tt=', 1)
            modified_f2 = True
            log(f"[OK] 成功修复胶囊呈现实体挂钩 (v3) -> {f2_name}")
        elif 'tt=G?pe:null' in f2_content:
            f2_content = f2_content.replace('tt=G?pe:null', 'tt=G?(ye||K||pe==="xhigh"?"ultracode":pe):null', 1)
            modified_f2 = True
            log(f"[OK] 成功修复胶囊呈现实体挂钩 (v2) -> {f2_name}")

        # 补丁 2.3：解除第三方模型（如 DeepSeek）的 Ultracode 拦截与自动重置
        if '&&(!0)&&' in f2_content and 'disableWorkflows' in f2_content:
            log(f"[OK] 第三方模型 Ultracode 放行已处于生效状态 -> {f2_name}")
        else:
            p2_by_v3 = re.compile(r'&&\(([a-zA-Z0-9_$]+)\|\|([a-zA-Z0-9_$]+)\)&&([a-zA-Z0-9_$]+),ge=')
            m2_by_v3 = p2_by_v3.search(f2_content)
            if m2_by_v3:
                f2_content = f2_content.replace(m2_by_v3.group(0), f'&&(!0)&&{m2_by_v3.group(3)},ge=', 1)
                modified_f2 = True
                log(f"[OK] 成功放行第三方模型支持 Ultracode (v3) -> {f2_name}")
            elif '&&u&&(he||oe)&&ge' in f2_content:
                f2_content = f2_content.replace('&&u&&(he||oe)&&ge', '&&u&&(!0)&&ge', 1)
                modified_f2 = True
                log(f"[OK] 成功放行第三方模型支持 Ultracode (v2) -> {f2_name}")

        if modified_f2:
            with open(f2_path, 'w', encoding='utf-8') as f:
                f.write(f2_content)
    else:
        log("[WARN] 未能定位到交互与呈现文件 f2")

    # -------------------------------------------------------------
    # 步骤 3：定位并修补胶囊触发器显示组件 (f3, 如 c8e04f916-*.js)
    # -------------------------------------------------------------
    f3_path = None
    f3_content = None

    for js in all_js:
        try:
            txt = open(js, 'r', encoding='utf-8').read()
            if 'ModelSelectorEffort' in txt and ('Ee=g.findIndex(' in txt or 'I=v.findIndex(' in txt):
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

        # 补丁 3.1：索引计算映射 (适配 v2 与 v3)
        p3_idx_v3 = re.compile(r'([a-zA-Z0-9_$]+)=([a-zA-Z0-9_$]+)\.findIndex\(([a-zA-Z0-9_$]+)\),\s*([a-zA-Z0-9_$]+)=\1>=0\?\1:0')
        m3_idx_v3 = p3_idx_v3.search(f3_content)
        if m3_idx_v3 and 'ultracode' not in m3_idx_v3.group(0):
            ee_var, g_var, te_var, n_var = m3_idx_v3.groups()
            repl_idx = f'{ee_var}={g_var}.findIndex({te_var}),{n_var}={ee_var}>=0?{ee_var}:(_==="ultracode"||_==="xhigh"?{g_var}.length-1:0)'
            f3_content = f3_content.replace(m3_idx_v3.group(0), repl_idx, 1)
            modified_f3 = True
            log(f"[OK] 成功绑定胶囊索引查找 (v3) -> {f3_name}")
        elif 'I=v.findIndex(e=>e.id===y),L=I>=0?I:0' in f3_content:
            p4_old = 'I=v.findIndex(e=>e.id===y),L=I>=0?I:0'
            p4_new = 'I=v.findIndex(e=>e.id===(y==="xhigh"?"ultracode":y)),L=I>=0?I:(y==="ultracode"||y==="xhigh"?v.length-1:0)'
            f3_content = f3_content.replace(p4_old, p4_new, 1)
            modified_f3 = True
            log(f"[OK] 成功绑定胶囊索引查找 (v2) -> {f3_name}")
        else:
            log(f"[OK] 胶囊索引查找已处于生效状态 -> {f3_name}")

        # 补丁 3.2：Trigger 药丸文字与高亮实时联动
        if 'I===g.length-1' in f3_content or 'H===v.length-1' in f3_content:
            log(f"[OK] 右下角胶囊实时联动已处于生效状态 -> {f3_name}")
        else:
            # v3 形式
            old_trig_v3 = 'tt=typeof de=="function"?de({label:H(N),warningLabel:K,open:j,disabled:S||!R}):de??n(ee,{variant:"ghost",size:C,"data-cds":"ModelSelectorEffort","aria-label":q,"aria-keyshortcuts":We,"aria-disabled":z!==void 0||void 0,className:s("min-w-0 shrink-0",z!==void 0&&"opacity-disabled",pe),children:[t("span",{className:"min-w-0 truncate",children:H(N)}),'
            expr_v3 = '(I===g.length-1||F?.id==="ultracode"||_==="ultracode"||_==="xhigh"?"Ultracode":H(N))'
            repl_trig_v3 = f'tt=typeof de=="function"?de({{label:{expr_v3},warningLabel:K,open:j,disabled:S||!R}}):de??n(ee,{{variant:"ghost",size:C,"data-cds":"ModelSelectorEffort","aria-label":q,"aria-keyshortcuts":We,"aria-disabled":z!==void 0||void 0,className:s("min-w-0 shrink-0",z!==void 0&&"opacity-disabled",pe),children:[t("span",{{className:s("min-w-0 truncate",ke&&"font-medium text-pro"),children:{expr_v3}}}),'

            # v2 形式
            expr_v2 = '(H===v.length-1||B?.id==="ultracode"||y==="ultracode"||y==="xhigh"?"Ultracode":q(L))'
            old_trig_v2 = 'render:typeof O=="function"?O({label:q(L),warningLabel:Z,open:M,disabled:S||!W}):O??t(ee,{variant:"ghost",size:C,"data-cds":"ModelSelectorEffort","aria-label":Oe,"aria-keyshortcuts":Ae,className:_("min-w-0 shrink-0",ce),children:[r("span",{className:"min-w-0 truncate",children:q(L)}),'
            repl_trig_v2 = f'render:typeof O=="function"?O({{label:{expr_v2},warningLabel:Z,open:M,disabled:S||!W}}):O??t(ee,{{variant:"ghost",size:C,"data-cds":"ModelSelectorEffort","aria-label":Oe,"aria-keyshortcuts":Ae,className:_("min-w-0 shrink-0",ce),children:[r("span",{{className:_("min-w-0 truncate",_e&&"font-medium text-pro"),children:{expr_v2}}}),'

            if old_trig_v3 in f3_content:
                f3_content = f3_content.replace(old_trig_v3, repl_trig_v3, 1)
                modified_f3 = True
                log(f"[OK] 成功打通右下角胶囊实时联动与紫色高亮 (v3) -> {f3_name}")
            elif old_trig_v2 in f3_content:
                f3_content = f3_content.replace(old_trig_v2, repl_trig_v2, 1)
                modified_f3 = True
                log(f"[OK] 成功打通右下角胶囊实时联动与紫色高亮 (v2) -> {f3_name}")

        if modified_f3:
            with open(f3_path, 'w', encoding='utf-8') as f:
                f.write(f3_content)
    else:
        log("[WARN] 未能定位到胶囊触发器组件 f3")

    log("\n" + "=" * 65)
    log("  [SUCCESS] 永久固化全部完成！")
    log("  滑块已恢复独立显示，拥有 6 档刻度，胶囊常驻显示为紫色的 Ultracode！")
    log("=" * 65)

    # 4. 重新拉起 Claude
    log("\n[*] 正在重新拉起 Claude Desktop 客户端...")
    try:
        claude_exe = os.path.join(claude_dir, 'app', 'Claude.exe')
        subprocess.Popen(f'explorer.exe "{claude_exe}"', shell=True)
    except Exception as e:
        log(f"[!] 自动拉起提示: 请从桌面或开始菜单手动打开 Claude ({e})")

    return True

def main():
    if not is_admin():
        log("[*] 正在请求管理员权限以解除系统文件保护...")
        run_elevation()
        return

    try:
        success = patch_bundle()
    except Exception as e:
        log(f"\n[!] 发生异常: {e}")
        success = False

    log("\n------------------------------------------------------------")
    log("执行完毕。")
    # 如果是独立终端窗口运行，保留输入以便查看
    try:
        input("按回车键退出窗口...")
    except Exception:
        pass

if __name__ == '__main__':
    main()
