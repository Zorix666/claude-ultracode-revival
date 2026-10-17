import os
import sys
import shutil
import glob

def find_target_file():
    # 优先匹配 WindowsApps 下的 Claude
    pattern = r'C:\Program Files\WindowsApps\Claude_*\app\resources\ion-dist\assets\v1\c593f7513-DQShcHgn.js'
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    
    # 备选路径：用户本地安装路径或自定义路径
    fallback = r'C:\Program Files\WindowsApps\Claude_2.31226.1.0_x64__pzs8sxrjxfjjc\app\resources\ion-dist\assets\v1\c593f7513-DQShcHgn.js'
    if os.path.exists(fallback):
        return fallback
    return None

def main():
    print("=" * 60)
    print(" Claude Desktop Ultracode 6-Stop Effort Slider Patcher")
    print("=" * 60)

    target_file = find_target_file()
    if not target_file or not os.path.exists(target_file):
        print(f"[ERROR] 目标 Bundle 文件未找到！请确认是否安装了 Claude Desktop。")
        sys.exit(1)

    print(f"[INFO] 目标文件: {target_file}")
    
    # 备份到用户桌面，避开 WindowsApps 目录下的权限问题
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    backup_file = os.path.join(desktop, "c593f7513-DQShcHgn.js.bak-original")

    if not os.path.exists(backup_file):
        try:
            shutil.copy2(target_file, backup_file)
            print(f"[OK] 已成功备份原始文件至桌面: {backup_file}")
        except Exception as e:
            print(f"[WARN] 备份失败: {e}，继续尝试打补丁...")
    else:
        print(f"[INFO] 原始备份已存在: {backup_file}")

    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 核心补丁 1：刻度过滤函数扩展第 6 项
    patch1_old = 'let i=e.filter(e=>ri(e.id)?t:Fn([e]).length>0),a=i.length===e.length?e:i;'
    patch1_new = 'let i=[...e.filter(e=>!ri(e.id)&&Fn([e]).length>0),{id:"ultracode",name:"Ultracode"}],a=i;'

    # 核心补丁 2：双向交互事件派发联动
    patch2_old = 'Ye=h((e,t)=>Ke(e,!1,{recordAsPick:t?.recordAsPick}),[Ke]),'
    patch2_new = 'Ye=h((e,t)=>ri(e)?Ke(ti,!0,{recordAsPick:t?.recordAsPick}):Ke(e,!1,{recordAsPick:t?.recordAsPick}),[Ke]),'

    if patch1_new in content and patch2_new in content:
        print("[SUCCESS] 目标文件已打过补丁，6 档 Ultracode 滑块已生效！无需重复修改。")
        return

    if patch1_old not in content or patch2_old not in content:
        print("[ERROR] 未能在目标文件内匹配到特征代码！")
        print("可能原因：您的 Claude 客户端版本较新，代码混淆变量名已发生变更。")
        sys.exit(1)

    content = content.replace(patch1_old, patch1_new, 1)
    content = content.replace(patch2_old, patch2_new, 1)

    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("[SUCCESS] 补丁注入成功！")
    print("滑块已永久开启第 6 档 Ultracode，且已打通双向拖动交互！")

if __name__ == '__main__':
    main()
