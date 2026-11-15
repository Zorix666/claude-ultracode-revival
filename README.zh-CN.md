# Claude Desktop: Ultracode 档位永久固化与滑块复活器

> **攻破 Claude Desktop 架构重写、折叠菜单收缩、事件分发覆盖、模型元数据过滤、底层降级与 Windows MSIX 自动升级重置的跨版本 AST 自适应永久固化引擎**  
> *[English Documentation](README.md) · 简体中文文档*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D6)](#快速开始)
[![Claude Desktop](https://img.shields.io/badge/Claude%20Desktop-v2.x%20~%20v5.x-black)](#兼容性与验证矩阵)
[![Release](https://img.shields.io/badge/Release-v2.0.0-purple.svg)](https://github.com/Zorix666/claude-ultracode-revival/releases)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#)

---

## 架构演进与链路全景

```mermaid
flowchart TD
    subgraph UI ["前端呈现层 (Frontend Presentation)"]
        Pill["右下角常驻胶囊 (Trigger Pill)"]
        Slider["Effort 滑块 (6 档刻度 / 紫色 Pro 质感)"]
        Menu["Claude 3.x 折叠二级菜单 (已击碎恢复)"]
    end

    subgraph Logic ["前端业务逻辑 (Bundle Core)"]
        ThinkingStyle["布局策略 (thinkingStyle: separate)"]
        ScaleFilter["刻度过滤链 (ip / Fn)"]
        Dispatch["事件派发 (Ye / Ke / mt)"]
        ModelGate["第三方模型门禁 (he || oe / me || K)"]
        PresLevel["呈现变量挂钩 (presentedEffortLevel)"]
    end

    subgraph State ["状态与网关 (Runtime State)"]
        Session["活跃会话状态 (local_*.json)"]
        ThirdParty["第三方网关 / 本地代理 (DeepSeek / OpenAI)"]
        Official["Anthropic 官方协议"]
    end

    ThinkingStyle -- "击碎二级菜单，强制独立胶囊" --> Slider
    ScaleFilter -- "注入第 6 档 Ultracode" --> Slider
    Slider -- "双向派发 xhigh / ultracode" --> Dispatch
    ModelGate -- "解除非官方模型门禁，免除静默重置" --> ThirdParty
    Dispatch -- "持久化 ultracode: true" --> Session
    Session -- "挂钩 presentedEffortLevel" --> PresLevel
    PresLevel -- "触发器动态联动，紫色 Pro 高亮" --> Pill
```

---

## 核心痛点与现象复现

在 Windows 平台使用 Claude Desktop（尤其配合第三方网关如 DeepSeek、或跨版本使用 Claude Code）时，官方前端存在以下深层缺陷：

1. **Claude 3.x（3.6556.2+）官方干掉滑块，收缩为折叠二级菜单**：
   - 官方在 Claude 3.x 更新中重构了底栏策略（`thinkingStyle`），默认未指定 `separate`，导致 Effort 滑块被收进 ModelSelector 作为一个横向折叠列表（Dropdown Submenu），原汁原味的滑块胶囊直接消失。
2. **终端 CLI 与 UI 档位断层**：
   - Claude Code 终端原生支持 `/effort ultracode` 高阶推理；但桌面端 UI 原生仅开放 5 个档位（`low` ~ `max`），缺失官方最高档第 6 档 `Ultracode`。
3. **第三方模型（DeepSeek 等）静默剥夺重置**：
   - 当会话接入 DeepSeek 等第三方模型时，由于元数据中缺少官方 `xhigh`，系统门禁 `_e = (he || oe)` 会判定不支持，并在会话监听中主动触发静默重置（`Ce({ultracode: false})`），将用户好不容易拉上的 Ultracode 瞬间抹平。
4. **胶囊触发器（Trigger Pill）死锁显示为 High**：
   - 在底栏渲染层，右下角胶囊写死了 `label: q(L)`，无论滑块如何拖拽，胶囊永远定格为 `High`，浮窗与底栏严重脱节。
5. **MSIX 自动静默更新覆盖**：
   - WindowsApps 商店服务会在后台无声无息推送大版本安装，旧目录被废弃，所有传统手工修改全数归零失效。

---

## 底层原理与关键修复链

本工具通过对 Electron 渲染源 Bundle 与 React 内部状态的精准逆向，一次性闭环解决所有 5 重卡点：

### 1. 强制激活全场景独立滑块模式（击碎 3.x 折叠菜单）
- **根因**：组件配置函数 `A$(e, t, n)` 在判断底栏 `chin` / `row` 时返回了无 `thinkingStyle` 的配置 `w$`，导致 `ModelSelector` 将 Effort 当做子菜单渲染。
- **修复**：将配置强制提升为 `{ shortcuts: !0, thinkingStyle: "separate" }`，促使 Effort 永远以独立的滑块浮窗（`EffortControl`）展示在底栏。

### 2. 刻度链注入第 6 档 Ultracode
- **根因**：模型选项过滤器 `e.filter(...)` 依据 `ri(e.id)` 拦截，但元数据未下发 `ultracode`，刻度被截断为 5 档。
- **修复**：在过滤链末端自动补齐 `{id: "ultracode", name: "Ultracode"}`，滑块拥有完整的第 6 档刻度，且继承官方专有的 `font-medium text-pro` 紫色高亮与网格动态滤镜。

### 3. 解除第三方模型门禁拦截（支持 DeepSeek 等）
- **根因**：门禁条件 `_e = G && ... && (he || oe) && ge`（或 3.x 中的 `me || K`）要求模型必须原生带 `xhigh`，非官方模型一律判定为不支持并静默重置。
- **修复**：将门禁逻辑改写为全面放行 `(!0)`，DeepSeek、OpenAI 等所有 3p 接入模型均能稳定锁定并持久化 Ultracode。

### 4. 双向交互派发与呈现挂钩
- **根因**：滑块选择时事件处理器默认将 `ultracode` 标记写死为 `false`；状态挂钩只读 `pe`。
- **修复**：在用户选定 `ultracode` 时向上派发 `{ effortLevel: "xhigh", ultracode: true }`，并将呈现变量 `wt` / `tt` 挂钩至会话激活状态。

### 5. 胶囊 Trigger 实时联动与紫色高亮
- **根因**：底层渲染容器调用 `renderTrigger({label})` 时写死传入未联动的外部状态。
- **修复**：将 label 升级为状态感知表达式：
  ```javascript
  label: (I === g.length - 1 || F?.id === "ultracode" || _ === "ultracode" || _ === "xhigh" ? "Ultracode" : H(N))
  ```
  并为 Trigger 药丸外层容器挂载 `font-medium text-pro`，选定 Ultracode 时底栏胶囊常驻显示为**高贵的紫色 Ultracode**。

---

## 全架构 AST 替换规范 (v2.x & v3.x)

| 目标层 | 目标文件特征 | 原版逻辑 (Old) | 注入逻辑 (Patched) |
| :--- | :--- | :--- | :--- |
| **滑块恢复** | `c227f4d5e-*.js` | `w$={shortcuts:!0}` | `w$={shortcuts:!0,thinkingStyle:"separate"}` |
| **第 6 档刻度** | `c227f4d5e-*.js` | `let i=e.filter(...)` | `let i=[...e.filter(...),{id:"ultracode",name:"Ultracode"}],a=i;` |
| **双向交互派发** | `c9543da06-*.js` | `(e,t)=>mt(e,!1,{...})` | `(e,t)=>e==="ultracode"?mt("xhigh",!0,{...}):mt(e,!1,{...})` |
| **第三方模型放行** | `c9543da06-*.js` | `&&(me\|\|K)&&` / `&&(he\|\|oe)&&` | `&&(!0)&&` |
| **呈现变量挂钩** | `c9543da06-*.js` | `wt=pe?Y:null` / `tt=G?pe:null` | `wt=pe?(ye\|\|_e\|\|Y==="xhigh"?"ultracode":Y):null` |
| **胶囊实时联动** | `c8e04f916-*.js` | `label:H(N)` / `label:q(L)` | `label:(I===g.length-1\|\|...?"Ultracode":H(N))` |

---

## Claude 5.x（asar 形态）

从 5.x 起，前端不再是解包的 `ion-dist/assets/v1/` 目录，而是单个 **`ion-dist.asar`**。
改单个 `.js` 文件这条路走不通，5.x 走另一条流水线：解包 → 替换字节串 → 重打包 → 同步 `claude.exe` 里内嵌的哈希。

```bash
# 1. 指向安装目录里的【原件】（未打补丁的那份）
python build_asar.py --asar "<install>\app\resources\ion-dist.asar" ^
                     --exe  "<install>\app\claude.exe"

# 2. 安装（自动提权，40 秒健康检查，失败自动回滚）
python install_asar.py
```

构建器对每个补丁点做唯一性断言，并对每个改过的模块跑 `node --check`，
任何一个不通过就**一个字节都不写**。

| 目标 | 模块 | 改动 |
| :--- | :--- | :--- |
| 滑块模式 | `shared-8` | `thinkingStyle:"inline"/"submenu"` → `"separate"` |
| 第 6 档 | `shared-36` / `shared-222` | 追加 `{id:"ultra",name:"Ultracode"}` |
| 档位白名单 | `shared-4`、`shared-192`、`shared-0`、`cd4f82e77`、`c325ea79a` | 加 `"ultra"`（**共 5 处，漏一处就会拖到末档弹回 Extra**） |
| 状态钳制 | `cc2521586`、`shared-33` | 放行 `ultra`，关卡后不被重置 |
| 底栏药丸 | `c82492f2c`、`cc43287c9` | 恒渲染独立 Effort 胶囊，掐掉与模型名合体 |
| 面板 | `c8e04f916` | `w-[220px]` → `w-[260px]`，accent 判定改认 `ultra` |

### 配色

胶囊和面板标题必须解析到**同一个 CSS 变量**：

```js
color: "var(--cds-text-pro)"   // .text-pro → violet-600 #5437B8（浅色）/ violet-300（深色）
```

写死十六进制、或改用 `--cds-violet-450`（`#785EE8`），底栏会明显比面板标题亮。
本项目**刻意不加任何光晕、边框、底色** —— 带发光的版本试过，已被否决。

### asar 重打包的三条铁律

写错任何一条都会白屏，而且报错信息完全指不到真正的原因：

1. **`offset` 必须是字符串**。C++ 侧用 `FindString("offset")` 取值，写成整数会返回 `nullptr`，
   所有文件瞬间变成 `ENOENT`，连 `index.html` 都读不到。
2. **Pickle 头四字段**：`f0=4`、`f1=4+f2`、`f2=4+padded_json_len`、`f3=json_len`，数据区从 `8+f1` 开始。
3. **`integrity` 要成对更新**：`integrity.hash` 和 `integrity.blocks`（按 `blockSize` 分块）缺一不可。

另外，header 的 sha256 是内嵌在 `claude.exe` 里的，重打包后不同步替换，客户端会静默秒退。

---

## 快速开始

本工具采用纯 Python + Windows 原生 API 编写，内置 Windows UAC 管理员自动提权、自动探测当前最新活跃版本、解除 ACL 保护、幂等注入与自动重启。

### 方式一：下载 Release 运行（推荐）

1. 前往 [Releases 页面](https://github.com/Zorix666/claude-ultracode-revival/releases) 下载最新版本的 `claude-ultracode-revival.zip`；
2. 解压后，双击运行 **`patch_ultracode.bat`**；
3. 弹出 UAC 提权提示时点击“是”，脚本将在 1 秒内完成自适应固化并自动重新打开 Claude。

### 方式二：克隆源码运行

```bash
git clone https://github.com/Zorix666/claude-ultracode-revival.git
cd claude-ultracode-revival
python apply_patch.py
```

---

## 兼容性与验证矩阵

- [x] **Claude Desktop 5.11492.5.0**（asar 形态，走 `build_asar.py` / `install_asar.py`）
- [x] **Claude Desktop v3.6556.2+**（Claude 3.x，完美恢复被折叠的滑块）
- [x] **Claude Desktop v2.42304+**（经典版本，完美固化 6 档）
- [x] **Claude Desktop v2.31226+**
- [x] **第三方网关兼容**：DeepSeek 全系列、OpenAI 协议中继、Claude 官方 Direct API
- [x] **系统环境**：Windows 11 / Windows 10 (x64)

其它版本会在第一个不匹配的目标串处**直接失败** —— 这是刻意的。
重新定位补丁点是十分钟的活；悄悄产出一个只打了一半的包不是。

## 已知坑（都是真金白银踩出来的）

| 现象 | 原因 |
| :--- | :--- |
| 日志显示成功，界面毫无变化 | 多版本目录并存，补丁装进了一个没在运行的目录。安装路径必须从**正在运行的进程**反查，不能按目录 mtime 取最新。 |
| 打完客户端起不来，或起来后会话列表全空 | 用 `explorer.exe <dir>\app\claude.exe` 拉起，绕过了 MSIX 包身份。要走 `explorer.exe shell:AppsFolder\Claude_pzs8sxrjxfjjc!Claude`。 |
| 白屏，所有资源报 `ENOENT` | asar 的 `offset` 写成了整数，没有写成字符串。 |
| 装完立刻退出 | 只改了 `integrity.hash`，没重算 `integrity.blocks`。 |
| 重启后补丁自动变回旧版 | 开机守卫任务在重装它记着的旧构建。**改构建目录时，目标 hash 必须一起改**。 |

---

## 开源许可证 (License)

本项目基于 [MIT License](LICENSE) 许可协议开源。
