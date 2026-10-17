# Claude Desktop Ultracode 复活补丁 ⚡

> **揭秘 Claude Desktop 的 Ultracode「神秘消失」之谜：前端源码逆向、MSIX 静默升级陷阱、右下角胶囊常驻显示与永久 6 档 Effort 滑块跨版本自适应修复指南。**  
> *[English Documentation](README.md) · 简体中文文档*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](#一键安装与使用)
[![Claude Desktop](https://img.shields.io/badge/Claude%20Desktop-2.31226%20~%202.42304+-black?logo=anthropic)](#跨版本自适应原理)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#)

---

## 🧐 现象与离奇谜团

在使用 Claude Desktop（尤其是通过 3p 自定义网关接入 DeepSeek 等第三方模型）配合 Claude Code 开发时，许多开发者都遭遇过以下诡异现象：

1. **终端明明有，桌面端只有 5 档**：
   - 在终端 Claude Code 运行 `/effort` 时，右侧清清楚楚显示：`Ultracode on (Tab to toggle) · dynamic workflows on every task`；
   - 但在 Claude Desktop 桌面端右下角打开 Effort 胶囊时，滑条从 Faster 到 Smarter **只有 5 个圆点**，根本找不到第 6 档 Ultracode。
2. **曾经出现过，拖一下滑块永久蒸发**：
   - 开发者此前确实体验过 Ultracode，但某次手欠**在界面上拖动了一下滑条**，Ultracode 瞬间蒸发，再也选不回来；
   - 哪怕在输入框强行敲 `/effort ultracode`，胶囊也只退化显示 `Extra` 或 `High`，滑块始终停在第 4 或第 5 格。
3. **右下角胶囊死活显示 High，不显示 Ultracode**：
   - 即便选上了第 6 格，右下角常驻胶囊（Trigger Pill）依然顽固显示 `High`，无法直观确认当前是否真的运行在 Ultracode 模式。
4. **关机重启后，补丁莫名其妙又消失了**：
   - 明明手动打好了补丁，重启电脑后再打开 Claude，滑块居然又变回了 5 档。
5. **双击修复脚本，黑框打开一秒就闪退**：
   - 双击 `.bat` 批处理文件没有任何反应，或者黑框闪一下直接消失，连系统提权窗口都看不到。

---

## 🔍 源码级深度破案：六大底层根因深度剖析

通过对 Claude Desktop 前端资源 Bundle（Rollup 打包）与 WindowsApps 底层文件架构的全面逆向反编译，彻底摸清了整个因果闭环：

### 1. 致命陷阱：交互派发的「强制清空门控」（消失的罪魁祸首）
在前端交互处理代码（如 `c593f7513-*.js` / `c9543da06-*.js`）中：
```javascript
be = h(e => {
  let { level: t, ultracode: n, silent: r = !1 } = e;
  let l = t === void 0 ? { ultracode: n } : { effortLevel: t, ultracode: n };
  // ...
});
// 用户点击/拖动普通滑块时的调用：
Ye = h((e, t) => Ke(e, !1, { recordAsPick: t?.recordAsPick }), [Ke]);
```
**关键破绽**：`Ye` 传给 `Ke` 的第二个参数被官方直接硬编码写死为 **`!1` (`false`)**！  
这意味着：**只要你在桌面端点击或拖动过 1~5 档中的任意一档，前端就会强行发送 `{ultracode: false}`，将当前会话的 Ultracode 彻底注销冲刷！**  
结合外部配置重写（例如其他模型或扩展改写了 `settings.json`，把 `"ultracode": true` 抹掉），直接造成了“神秘消失”的假象。

### 2. 模型静态目录（`published.json`）刻度缺失
桌面端 Effort 滑条上的刻度不是写死的，而是读取官方下发并本地缓存的模型目录：
```javascript
function ip(e, t) {
  let i = e.filter(e => ri(e.id) ? t : Fn([e]).length > 0);
  return n.set(t, a), a;
}
```
其中 `ri(e.id)` 的底层定义正是 `e.id === "ultracode"`。  
检查官方下发的 `published.json` 发现，所有模型的原始刻度表一律只有 5 档：`[low, medium, high, xhigh, max]`，**静态目录里压根没有 `ultracode` 这一项**，导致过滤后数组长度恒为 5。

### 3. 前端早已完全做好 Ultracode 第 6 格 UI（被雪藏）
检查滑块渲染组件（`c8e04f916-*.js`）：
```javascript
let V = Math.min(L ?? z?.index ?? I, _.length - 1),
    H = _[V],
    ge = H?.id === te; // te === "ultracode"

re({ label: K(V), accent: ge, index: V });
// accent: ge 激活专属紫色高亮加粗字体："font-medium text-pro"
// overlay 激活点亮发光动画：qf({ lit: e.atMax })
```
官方在前端组件中**已经把第 6 格 Ultracode 的渲染、紫色 Pro 字体高亮、点亮发光动画全部写完了**！官方更新日志中也明确写道：
> *"Added Ultracode to the effort slider, which selects the highest effort level and turns on dynamic workflows"*

仅因模型目录缺失第 6 项，这一特性在桌面端被无情雪藏。

### 4. 为什么右下角胶囊常驻显示 High 而不是 Ultracode？（呈现层传递截断）
即使滑条拖到了第 6 格，底下的常驻胶囊（Trigger Pill）依然显示 `High`：
- **底层原因**：外层组件派发给胶囊的呈现变量 `presentedEffortLevel`（源码中的 `tt`）被写成了 `tt = G ? pe : null`，它只传递了经过 `zV` 钳制后的数值档位（`"xhigh"` -> 钳制为 `"high"`），完全丢弃了当前会话的 `ultracode: true` 标记；
- **渲染组件盲区**：胶囊渲染组件（`c8e04f916-*.js`）在执行 `I = v.findIndex(e => e.id === y)` 时，拿到的 `y` 是 `"high"`，无法命中新增的 `"ultracode"`，从而退化选中第 3 档（High）；
- **解决方案**：在注入补丁中将 `presentedEffortLevel` 动态挂钩为 `ultracode`，并在胶囊组件中打通索引查找映射，**彻底实现右下角胶囊常驻显示 `Ultracode`**！

### 5. 关机重启为何再次失效？（Windows 微软应用商店 MSIX 静默升级陷阱）
很多开发者发现辛苦改好的代码在电脑关机重启后又被打回原形。  
**真相只有一个**：Claude Desktop 是通过微软商店（MSIX/AppX）托管分发的打包应用。  
Windows 在关机或开机时，经常会在后台**静默将应用覆盖升级到全新版本**（例如从 `Claude_2.31226.1.0` 跃升至 `Claude_2.42304.0.0`）！  
- 升级后旧版目录被直接销毁，新目录全是微软商店刚解包的未改动官方 JS；
- 前端打包构建的 Content Hash 全部重置（例如刻度文件由 `c593f7513-*.js` 变成 `c227f4d5e-*.js`，交互文件由 `c593f7513` 拆分到 `c9543da06-*.js`）；
- 若脚本写死固定文件路径，版本一更新就会因找不到文件而失效。
- **本工具对策**：采用自适应动态正则扫描与动态版本嗅探，不论商店如何升级，均可在 0.1 秒内自动寻轨并重新注入。

### 6. 双击批处理为什么闪退？（Windows cmd.exe 编码错位陷阱）
若批处理文件以 UTF-8 编码保存，Windows 原生 `cmd.exe` 在解析中文字符和嵌套括号时会发生字节错位，把 `echo` 识别成 `cho`，把提权识别成非法命令，导致脚本报错秒退，连 UAC 授权弹窗都无法触发。必须使用纯正 GBK 编码并直接调用 Python 内置 Windows Shell API 原生提权。

---

## ⚡ Ultracode 到底是不是噱头？真的会分出超多子 Agent 吗？

**答：是的，绝对真实！这是 Ultracode 的灵魂所在。**

1. **机制实锤**：当会话进入 Ultracode 状态时，系统会向 Prompt 注入底层协议指令，强制开启 `Workflow` 工具链。
2. **绕开并发上限**：指令明确要求模型：**每个实质性任务都必须主动拆解为子任务并行处理，并且直接绕开常规模式下的 Subagent 并发上限限制**！
3. **在 3p / DeepSeek 接入下的表现**：只要网关与后端支持 Tool Use，Claude 就会并发触发大量子代理同时发起推理请求，在客户端形成壮观的多子代理协同作业流水线。

---

## 🚀 解决方案与一键使用指南

本仓库提供了**全自动跨版本自适应注入工具**：
- 自动通过 PowerShell `Get-AppxPackage` 获取当前最新安装的 Claude 目录；
- 自动在大体积 Bundle（>40KB）中定位特征代码，不受文件名哈希变更影响；
- 原生调起 Windows 蓝色 UAC 提权，解除系统写保护；
- **智能防污染备份**：所有原始 JS 文件自动备份至桌面的 `Claude_Patch_Backup` 独立文件夹，绝不产生散落桌面的“白纸”无格式文件；
- 注入完成后安全拉起 Claude Desktop。

### 步骤 1：克隆或下载本仓库
```bash
git clone https://github.com/<your-username>/claude-ultracode-revival.git
cd claude-ultracode-revival
```

### 步骤 2：一键执行固化
直接双击 **[`patch_ultracode.bat`](patch_ultracode.bat)** 或在终端运行：
```bash
python apply_patch.py
```
在弹出的系统 UAC 提示窗口点击【是】。

脚本将在 0.1 秒内自动完成：
1. 关停 Claude 运行进程；
2. 自动定位当前最新活跃版本路径（如 `Claude_2.42304.0.0`）；
3. 解除 WindowsApps 系统写保护；
4. 备份原文件至桌面 `Claude_Patch_Backup` 目录；
5. 精准注入 4 大核心补丁（刻度、交互、呈现、胶囊常驻显示）；
6. 安全重新拉起 Claude Desktop。

打开 Claude，可以看到：
- **右下角常驻胶囊直观显示为 `Ultracode`**；
- 点击胶囊，弹出的滑块拥有**完整的 6 档发光圆点**，拖动自由，最右端为专属紫色发光 Pro 样式！

---

## 🛠️ 4 大核心补丁闭环原理 (Diff)

### 补丁 1：扩展第 6 格刻度（自适应定位，如 `c227f4d5e-*.js`）
```diff
- let i=e.filter(e=>vc(e.id)?t:Ha([e]).length>0),a=i.length===e.length?e:i;
+ let i=[...e.filter(e=>!vc(e.id)&&Ha([e]).length>0),{id:"ultracode",name:"Ultracode"}],a=i;
```

### 补丁 2：双向交互派发联动（支持自由拖动，如 `c9543da06-*.js`）
```diff
- Ze=x((e,t)=>Je(e,!1,{recordAsPick:t?.recordAsPick}),[Je]),
+ Ze=x((e,t)=>e==="ultracode"?Je("xhigh",!0,{recordAsPick:t?.recordAsPick}):Je(e,!1,{recordAsPick:t?.recordAsPick}),[Je]),
```

### 补丁 3：修复胶囊呈现变量挂钩（呈现层打通，如 `c9543da06-*.js`）
```diff
- tt=G?pe:null
+ tt=G?(ye||K||pe==="xhigh"?"ultracode":pe):null
```

### 补丁 4：绑定右下角胶囊常驻显示（组件层映射，如 `c8e04f916-*.js`）
```diff
- I=v.findIndex(e=>e.id===y),L=I>=0?I:0
+ I=v.findIndex(e=>e.id===(y==="xhigh"?"ultracode":y)),L=I>=0?I:(y==="ultracode"||y==="xhigh"?v.length-1:0)
```

---

## 🛡️ 配置文件防御性推荐

为了保证状态彻底稳定，建议检查以下两处配置：

1. **`~/.claude/settings.json`**：
   在顶层配置中保留开关：
   ```json
   {
     "ultracode": true,
     "effortLevel": "high"
   }
   ```
2. **`%LOCALAPPDATA%\Claude-3p\configLibrary\<config-id>.json`**（3p 网关用户）：
   - 检查并删除 `maxEffort: "high"`，避免该参数将模型选项强制裁成 3 档（`[low, medium, high]`）；
   - 将 `defaultModelEffort` 设为 `"high"` 或 `"xhigh"`。

---

## 📄 License
[MIT License](LICENSE) © 2026
