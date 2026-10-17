/**
 * Claude Desktop Ultracode DevTools 热补丁
 * 
 * 使用方式：
 * 1. 在 Claude Desktop 中按快捷键 Ctrl + Alt + I 打开开发者工具；
 * 2. 切换到 Console 标签页，输入 allow pasting 回车；
 * 3. 鼠标在 Claude 右下角点击一次 Effort 胶囊以挂载组件；
 * 4. 粘贴执行本代码，再次打开胶囊即可看到 6 档 Ultracode 滑块！
 */
(() => {
  const trigger = document.querySelector('[data-cds="ModelSelectorEffort"]');
  if (!trigger) {
    return console.warn("%c[WARN] 请先在右下角点击一次 Effort 胶囊让浮窗挂载，然后再运行此脚本！", "color: orange; font-weight: bold;");
  }
  const fiberKey = Object.keys(trigger).find(k => k.startsWith('__reactFiber$'));
  let node = fiberKey ? trigger[fiberKey] : null;
  let patched = false;
  while (node) {
    if (node.memoizedProps?.options && Array.isArray(node.memoizedProps.options)) {
      const opts = node.memoizedProps.options;
      if (!opts.some(o => o.id === 'ultracode')) {
        opts.push({ id: 'ultracode', name: 'Ultracode' });
        patched = true;
      }
      break;
    }
    node = node.return;
  }
  if (patched) {
    console.log("%c🎉 注入成功！滑条已扩展为 6 档！第 6 档正是 ULTRACORDE！", "color: #10b981; font-weight: bold; font-size: 14px;");
  } else {
    console.log("%c[INFO] 已经注入过或选项表中已有 Ultracode 项。", "color: #3b82f6; font-weight: bold;");
  }
})();
