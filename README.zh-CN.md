# claude-ultracode-revival

把 Claude Desktop 努力程度滑块上被隐藏的第六档 **Ultracode** 还原回来的补丁，以及它为什么会消失的分析。

[English](README.md) · [简体中文](README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)](#使用方式)
[![Claude Desktop](https://img.shields.io/badge/claude%20desktop-2.31226-black)](#兼容性)

---

## 这是什么

较新的 Claude Desktop 里存在一个叫 `ultracode` 的第六档努力程度。渲染组件、样式、以及它背后的工作流行为，在 app bundle 里都是完整的——但滑块上永远不显示这一档；而且只要你碰一下滑块，它在这个会话里就彻底没了。

本仓库做两件事：

- 说明导致这个现象的四条独立代码路径（见[根因分析](#根因分析)）。
- 提供两种还原方式：一种持久修改 app bundle，一种用 DevTools 热补丁、不动磁盘上任何文件。

## 打补丁前请先读这一段

这是非官方补丁，与 Anthropic 无关，也未获得其认可或支持。

- **它会修改 `C:\Program Files\WindowsApps` 下的文件。** 这是受保护目录。`patch_ultracode.bat` 会夺取其中一个文件的所有权并授予较宽的 ACL，这个改动在补丁完成后依然存在。
- **客户端更新会覆盖它。** 任何一次 Claude Desktop 更新都会替换 bundle。更新后重跑脚本即可，脚本会识别出已打过补丁的文件并直接退出，不会重复修改。
- **补丁按压缩后代码的精确子串匹配。** 新版本会重命名标识符。匹配不到时脚本会打印 `pattern not found` 后退出，不会写入——不会留下一个半残的文件。
- **保留脚本放在你桌面的备份**（`c593f7513-DQShcHgn.js.bak-original`）。回滚靠它，或者直接重装。
- **Ultracode 实际效果取决于你的后端。** 客户端无论如何都会下发这条指令，但最终同时开出多少子代理由网关和模型决定，第三方端点差异很大。见[Ultracode 是真的吗](#ultracode-是真的吗)。

## 现象

同一个 bug 的三种表现：

1. Claude Code CLI 里 `/effort` 显示 `Ultracode on (Tab to toggle) · dynamic workflows on every task`；Claude Desktop 的胶囊里只有五个点，没有第六个。
2. 记得曾经见过它的人反馈说，拖动一次滑块之后就永久消失了。
3. 在输入框里敲 `/effort ultracode` 也没用——胶囊只会退化成 `Extra` 或 `High`，滑块停在第 4 或第 5 格。

## 根因分析

四个独立的问题，按叠加顺序排列。

### 1. 滑块事件处理里把标志位写死成关闭

在交互 bundle 中：

```js
be = h(e => {
  let { level: t, ultracode: n, silent: r = !1 } = e;
  let l = t === void 0 ? { ultracode: n } : { effortLevel: t, ultracode: n };
  // ...
});
// 点击 / 拖动普通档位时的调用：
Ye = h((e, t) => Ke(e, !1, { recordAsPick: t?.recordAsPick }), [Ke]);
```

传给 `Ke` 的第二个参数就是字面量 `false`。所以任何一次对 1~5 档的点击或拖动，都会发出 `{ ultracode: false }`，把当前会话的标志位清掉。这就是为什么看起来是「手一碰滑块它就消失」，也是为什么外部配置重写（比如别处把 `"ultracode": true` 抹掉）会像是触发原因。

### 2. 模型目录里只有五档

滑块的档位来自本地缓存的模型目录（`published.json`），不是写死的常量：

```js
function ip(e, t) {
  let i = e.filter(e => ri(e.id) ? t : Fn([e]).length > 0);
  return n.set(t, a), a;
}
```

`ri(id)` 的实现是 `id === "ultracode"`。官方下发的目录对所有模型都只列了 `[low, medium, high, xhigh, max]`，所以过滤后的数组长度恒为 5，第六档在渲染之前就被滤掉了。

### 3. 前端其实已经写好了第六档

来自 `c8e04f916-CUEn4KMP.js`：

```js
let V = Math.min(L ?? z?.index ?? I, _.length - 1),
    H = _[V],
    ge = H?.id === te; // te === "ultracode"

re({ label: K(V), accent: ge, index: V });
```

`accent` 就是那个激活后变成紫色 `font-medium text-pro` 字体、并点亮 overlay（`qf({ lit: e.atMax })`）的开关。官方更新日志也直接写了：*"Added Ultracode to the effort slider, which selects the highest effort level and turns on dynamic workflows."* 只差目录里那一项。

### 4. 为什么标签显示成 `Extra` 或 `High`

`ultracode` 对应的底层 effort 级别是 `xhigh`，而 `xhigh` 的展示文案就是 `Extra`。如果模型能力表里没有声明这一档，还会被钳制函数（`zV`）进一步降级显示为 `High`。这只影响显示的标签，底层发出去的值是生效的。

## Ultracode 是真的吗

在客户端这一侧，是真的。进入 Ultracode 状态时，客户端会往 prompt 里注入工作流指令，要求模型把每个实质性任务拆成并行子任务，并绕过常规的子代理并发上限。后端支持 tool use 的话，客户端确实会同时发出大量子代理请求。

至于这有多有用，取决于后端。走第三方网关时，并行是真的，但拆解质量就是你那个模型对这条指令的理解。本仓库对效果不做判断。

## 补丁内容

目标文件：

```
%PROGRAMFILES%\WindowsApps\Claude_<version>\app\resources\ion-dist\assets\v1\c593f7513-DQShcHgn.js
```

**补丁 1 —— 把第六档加回过滤后的选项列表：**

```diff
- let i=e.filter(e=>ri(e.id)?t:Fn([e]).length>0),a=i.length===e.length?e:i;
+ let i=[...e.filter(e=>!ri(e.id)&&Fn([e]).length>0),{id:"ultracode",name:"Ultracode"}],a=i;
```

**补丁 2 —— 选中第六档时置位，而不是清零：**

```diff
- Ye=h((e,t)=>Ke(e,!1,{recordAsPick:t?.recordAsPick}),[Ke]),
+ Ye=h((e,t)=>ri(e)?Ke(ti,!0,{recordAsPick:t?.recordAsPick}):Ke(e,!1,{recordAsPick:t?.recordAsPick}),[Ke]),
```

两处替换各应用一次，按上述顺序，由 `apply_patch.py` 执行。

## 使用方式

### 方案 A：持久补丁

环境要求：Windows 10/11、从 Microsoft Store 安装的 Claude Desktop（MSIX，所以位于 `WindowsApps` 下）、`PATH` 中有 Python 3、管理员权限。

```bash
git clone https://github.com/Zorix666/claude-ultracode-revival.git
cd claude-ultracode-revival
```

右键 `patch_ultracode.bat` → **以管理员身份运行**。脚本会：

1. 通过 UAC 提权。
2. 结束正在运行的 `Claude.exe`。
3. 在 `WindowsApps` 下定位 bundle。
4. 夺取该文件的所有权并授予写权限（`takeown` / `icacls`）。
5. 把原始文件备份到你桌面，命名为 `c593f7513-DQShcHgn.js.bak-original`。
6. 执行 `apply_patch.py`。
7. 重新拉起 Claude。

打开右下角的努力程度胶囊，应该有六个点了。拖到最右端即 Ultracode；1~5 档双向拖动都正常。

### 方案 B：DevTools 热补丁

不改任何文件、不需要管理员权限，刷新后失效。

1. 在配置里设 `allowDevTools: true`，用 `Ctrl + Alt + I` 打开 DevTools。
2. 切到 **Console**，输入 `allow pasting` 回车。
3. 在界面上点一次努力程度胶囊，让弹窗组件挂载。
4. 粘贴并执行 [`hotpatch_console.js`](hotpatch_console.js)。
5. 再打开胶囊，六个点。

脚本从 `[data-cds="ModelSelectorEffort"]` 出发沿 React fiber 向上找，定位第一个 `memoizedProps.options` 是数组的祖先，然后把 `ultracode` 这一项追加进去。

需要说明的是：它只扩展了选项数组，**没有**打补丁 2。所以第六个点会显示出来，但选中它时走的仍是未修补的处理函数，依旧会发出 `{ ultracode: false }`。请把方案 B 当作「验证根因 + 看 UI」的手段，而不是可用的开关。要真正生效还是得用方案 A。

## 配置检查

如果第六档仍然会被重置，bundle 之外还有两处值得看：

`~/.claude/settings.json` —— 保留开关和一个合理的默认值：

```json
{
  "ultracode": true,
  "effortLevel": "high"
}
```

`%LOCALAPPDATA%\Claude-3p\configLibrary\<config-id>.json` —— 第三方网关版本：

- 删掉 `maxEffort: "high"`，它会把模型的档位表裁成 `[low, medium, high]`。
- 把 `defaultModelEffort` 设为 `"high"` 或 `"xhigh"`。

## 兼容性

基于 Claude Desktop **2.31226** 编写。bundle 文件名里带构建哈希，两处补丁又都是压缩代码的子串匹配，所以更新后大概率失效。失效时脚本会拒绝写入，而不是写出一份半成品 bundle。

如果你的版本已经匹配不上，欢迎开 issue 附上构建号和上下文代码——通常只有变量名会变。

## 回滚

以管理员身份把桌面的 `c593f7513-DQShcHgn.js.bak-original` 覆盖回目标文件，或者重装/修复应用。客户端更新本身也会覆盖 bundle。

之前对该文件的 owner 和 ACL 改动在回滚后仍然保留。想完全还原安装目录原状可以执行 `icacls "<path>" /reset`。

## 仓库结构

```
apply_patch.py            # 执行两处子串替换，附带备份逻辑
patch_ultracode.bat       # 提权、定位文件、接管权限、重启
hotpatch_console.js       # DevTools 用，不改磁盘
```

## 许可证

[MIT](LICENSE)
