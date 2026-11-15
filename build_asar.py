# -*- coding: utf-8 -*-
"""
Claude Desktop 5.x 补丁构建器（asar 形态）

5.x 把前端打进单个 `ion-dist.asar`（2.x/3.x 是解包目录），所以不能直接改 .js 文件，
必须解包 → 改字符串 → 按 Chromium Pickle 规则重打包 → 同步 exe 内嵌的 header 哈希。

本脚本面向 Claude 5.11492.5.0，做完这些事：
  1. 6 档 effort（low/medium/high/xhigh/max/ultra）
  2. thinkingStyle 强制 separate —— 把滑块从模型菜单里摘出来独立渲染
  3. 底栏 Effort 胶囊独立，不与模型名合体，去掉模型菜单里的二级子菜单
  4. ultra 档在状态中枢放行，关卡后不再被重置回 High
  5. 胶囊 / 面板标题用原生 `.text-pro` 着色（纯紫文字，无光晕）

用法：
    python build_asar.py --asar  <原始 ion-dist.asar> ^
                         --exe   <原始 claude.exe>     ^
                         [--out  build/v5]

输出：
    <out>/ion-dist.asar   已打补丁
    <out>/claude.exe      内嵌 header 哈希已同步

注意：必须用**未打过补丁**的原件作为输入。已经改过的文件会在 assert 处失败。
"""
import os
import sys
import json
import argparse
import hashlib
import struct
import subprocess

VERSION = "5.11492.5.0"

# ---------------------------------------------------------------------------
# 补丁表
#
# 每一项是 (文件名前缀, [(旧串, 新串), ...])。
# 所有旧串都必须在上游原版里**唯一出现**，否则脚本直接 assert 失败，
# 不会产出半成品包 —— 这是换版本时最省事的保护。
# ---------------------------------------------------------------------------
PATCHES = [
    # ---- 主输入栏 / 新会话环境栏：掐灭模型名尾巴拼接、强制独立 Effort 胶囊 ----
    ('cc43287c9', [
        # 模型药丸尾巴不再拼 effort
        # 源码里这里写的是字面的 `·` 六个字符（不是 UTF-8 中点），
        # 所以 bytes 里要用 `\\u00B7` 精确匹配
        (b's=(o?[{field:"fastMode",word:e.fastLabel},{field:"effort",word:e.thinkingLabel},'
         b'{field:null,word:e.toggleLabel&&`\\u00B7 ${e.toggleLabel}`}]:[]).filter(oAe)',
         b's=(o?[{field:"fastMode",word:e.fastLabel}]:[]).filter(oAe)'),

        # 恒渲染 Effort 胶囊；renderTrigger 外层 span 只在 Ultracode 时挂 .text-pro
        (b'effort:n.effortOptionCount>0?b(kS.Effort,{...n.effort,tooltip:Ce,shortcut:Te,'
         b'renderTrigger:e=>{let{label:n,toggleLabel:r}=e;return b(Y,{variant:"ghost",'
         b'className:R5(t),"data-testid":"environment-row-effort",children:b(z5,'
         b'{overridden:G("effort"),label:r?p.formatMessage(KV.levelWithUltracode,'
         b'{level:n,ultracode:r}):n})})}}):null',
         b'effort:b(kS.Effort,{...n.effort,tooltip:Ce,shortcut:Te,renderTrigger:e=>{'
         b'let{label:n,toggleLabel:r}=e,isU=n==="Ultracode"||r==="Ultracode"||n==="ultra";'
         b'return b(Y,{variant:"ghost",className:R5(t),"data-testid":"environment-row-effort",'
         b'children:b("span",{className:isU?"text-pro":void 0,children:b(z5,'
         b'{overridden:G("effort"),label:r?p.formatMessage(KV.levelWithUltracode,'
         b'{level:n,ultracode:r}):n})})})}})'),

        # bar 布局下不再降级成药丸合体
        (b'let e=r.field==="effort"&&(!t.effort?.options.length||d==="bar")?"model":r.field;',
         b'let e=r.field==="effort"&&!t.effort?.options.length?"model":r.field;'),
    ]),

    # ---- 底栏装配：强制 separate、清掉独立开关、overlay 恒用 OE ----
    ('c82492f2c', [
        (b'function wE(e,t,n){switch(e){case"chin":case"row":return n?t?SE:xE:t?bE:yE;'
         b'case"rail":return t?vE:_E;case"composer":return t?vE:gE}}',
         b'function wE(e,t,n){switch(e){case"chin":case"row":return t?vE:_E;'
         b'case"rail":return t?vE:_E;case"composer":return t?vE:gE}}'),
        (b'fe=n,pe=z?v?v.on?kE:AE:void 0:Ns(Y?.thinking?.effort_options?.at(-1)?.id)?OE:void 0',
         b'fe=void 0,pe=OE'),
        (b'n.effortOptionCount>0?b(Gl.Effort,{...n.effort}):null',
         b'b(Gl.Effort,{...n.effort})'),
        (b'effortInModelMenu:tt', b'effortInModelMenu:!1'),
        (b'effortOptionCount:vt', b'effortOptionCount:vt||6'),
    ]),

    # ---- Effort 面板：260px、标题跟随本地下标、accent 判定认 ultra ----
    ('c8e04f916', [
        (b'p("w-[220px]",D)', b'p("w-[260px]",D)'),
        (b'p("isolate flex w-[220px] select-none flex-col gap-lg",D)',
         b'p("isolate flex w-[260px] select-none flex-col gap-lg",D)'),
        (b'className:"flex w-[220px] select-none flex-col gap-xs"',
         b'className:"flex w-[260px] select-none flex-col gap-xs"'),

        # 末档判定：上游只认 "ultracode"，补丁注入的 id 是 "ultra"
        (b'Ne=z?.id==="ultracode"||N!==null',
         b'Ne=z?.id==="ultra"||z?.id==="ultracode"||N!==null'),

        # 胶囊文字跟随本地下标 R（面板标题用的就是它），不再用后端 catalog 的 F
        # 自定义 renderTrigger 与内部触发器都用这一个对象，改一处两边同步
        (b'label:G(F),warningLabel:Y,toggleLabel:N,open:A,disabled:S||!B',
         b'label:G(R),warningLabel:Y,toggleLabel:N,open:A,disabled:S||!B'),
    ]),

    # ---- 模型选择器：兜底注入第 6 档、胶囊 fallback 着色 ----
    ('shared-36-', [
        (b'function SE(e){return e?.thinking?.effort_options??[]}',
         b'function SE(e){let a=e?.thinking?.effort_options??[];'
         b'return a.some(e=>e.id=="ultra")?a:a.concat({id:"ultra",name:"Ultracode"})}'),
        # 胶囊 fallback：只有 ultra 才上 .text-pro
        (b'y=f&&"text-pro"',
         b'y=(i==="ultra"||i==="ultracode"||f||x==="Ultracode")&&"font-medium text-pro"'),
        # 彻底抹杀模型菜单里的 Effort 二级子菜单与药丸合体
        (b'K=c?.thinkingStyle==="separate"?[]:SE(G)', b'K=[]'),
        (b'I=C?.thinkingStyle==="separate"', b'I=!0'),
        (b'q=o?.thinkingStyle==="separate"', b'q=!0'),
    ]),

    # ---- 模型菜单：二级子菜单恒不渲染 ----
    ('shared-8-', [
        (b'u?{overflowStyle:"inline",thinkingStyle:"inline",overflowSearch:X,...e.renderConfig}:'
         b'{overflowStyle:"submenu",thinkingStyle:"submenu",overflowSearch:X,'
         b'...e.renderConfig,overflowRowPresentation:X?h_:void 0}',
         b'{overflowStyle:"submenu",thinkingStyle:"separate",overflowSearch:X,...e.renderConfig}'),
        (b'xt?null:e.config?.thinkingStyle==="separate"?'
         b'j?.models.find(e=>e.id===Oe.model)?.thinking?.effort_options?.length??0:0',
         b'xt?null:(j?.models.find(e=>e.id===Oe.model)?.thinking?.effort_options?.length||6)'),
        (b'(!u||_)&&b(tg,{currentModel:U,conversationUuid:t,surface:_',
         b'!1&&b(tg,{currentModel:U,conversationUuid:t,surface:_'),
    ]),

    # ---- 状态中枢：放行 ultra，关卡后不再被钳制回 High ----
    ('cc2521586', [
        (b'B=e=>{let n=b(e,_,v);return z.length>0&&!z.includes(n)?t&&z.includes(t)?t:z[0]:n}',
         b'B=e=>{let n=b(e,_,v);return(n==="ultra"||n==="ultracode")?n:'
         b'z.length>0&&!z.includes(n)?t&&z.includes(t)?t:z[0]:n}'),
        (b'function y(e){return u(e)?d:_.safeParse(e).data??null}',
         b'function y(e){return(e==="ultra"||e==="ultracode")?e:u(e)?d:_.safeParse(e).data??null}'),
    ]),

    # ---- 会话标记函数放行 ultra ----
    ('shared-33-', [
        (b'function sb(e){return e===ob}',
         b'function sb(e){return e===ob||e==="ultra"}'),
    ]),

    # ---- 全局 catalog 注入第 6 档 ----
    ('shared-222-', [
        (b'effortOptionsFor:e=>v(e)?.effort_options??[]',
         b'effortOptionsFor:e=>{let a=v(e)?.effort_options??[];'
         b'return a.some(e=>e.id=="ultra")?a:a.concat({id:"ultra",name:"Ultracode"})}'),
    ]),

    # ---- 国际化词条 ----
    ('c74045701', [
        (b'max:{defaultMessage:"Max",id:"vWw9vwL+Z/"}',
         b'max:{defaultMessage:"Max",id:"vWw9vwL+Z/"},'
         b'ultra:{defaultMessage:"Ultracode",id:"ultra_label"}'),
    ]),

    # ---- 选档回调：ultra 且标记 ultracode ----
    ('cd07e0b93', [
        (b'mn=J2($,189,ln,Xe)?K2($,189,ln,Xe,(e,t)=>ln(e,Xe(),{recordAsPick:t?.recordAsPick})):$[191]',
         b'mn=J2($,189,ln,Xe)?K2($,189,ln,Xe,(e,t)=>ln(e,e==="ultra",t??{})):$[191]'),
        (b'if(t&&!U)return r;', b'if((t||e==="ultra")&&!U)return r;'),
    ]),
]

# 档位白名单散落在 5 个模块里，漏一处就会出现「拖到末档弹回 Extra」
ENUM_PATCHES = [
    (b'new Set(["low","medium","high","xhigh","max"])',
     b'new Set(["low","medium","high","xhigh","max","ultra"])'),
    (b'["low","medium","high","xhigh","max"]',
     b'["low","medium","high","xhigh","max","ultra"]'),
]
ENUM_TARGETS = ['shared-4-', 'shared-192-', 'shared-0-', 'cd4f82e77', 'c325ea79a']


# ---------------------------------------------------------------------------
# asar 读写
# ---------------------------------------------------------------------------
def load_asar(path):
    raw = open(path, 'rb').read()
    header_size = struct.unpack('<I', raw[12:16])[0]
    header = json.loads(raw[16:16 + header_size].decode('utf-8'))
    base = 8 + struct.unpack('<I', raw[4:8])[0]
    if base < 16 + header_size:
        raise ValueError("bad asar header geometry")
    return raw, header, base, header_size


def walk_leaves(header):
    leaves = []

    def walk(node, path):
        if 'files' in node:
            for k, v in node['files'].items():
                walk(v, (path + '/' + k) if path else k)
        elif 'size' in node and 'offset' in node:
            leaves.append((int(node['offset']), int(node['size']), path, node))

    walk(header, '')
    leaves.sort()
    return leaves


def repack(raw, header, base, replacements):
    """按 Chromium Pickle 规则重打包。

    三个必须守住的点（写错任何一个都会白屏，且报错信息毫无指向性）：
      1. offset 必须写**字符串** —— C++ 侧用 FindString("offset") 取，写 int 会返回 nullptr
      2. 头部四字段：f0=4, f1=4+f2, f2=4+padded_json_len, f3=json_len
      3. 每个文件的 integrity.hash 与 integrity.blocks 要一起更新
    """
    chunks = []
    pos = 0
    for off, size, path, node in walk_leaves(header):
        blob = raw[base + off: base + off + size]
        if path in replacements:
            blob = replacements[path]
            node['integrity']['hash'] = hashlib.sha256(blob).hexdigest()
            if 'blocks' in node['integrity']:
                bs = int(node['integrity'].get('blockSize') or 4194304)
                node['integrity']['blocks'] = [
                    hashlib.sha256(blob[i:i + bs]).hexdigest()
                    for i in range(0, len(blob), bs)
                ]
        node['offset'] = str(pos)
        node['size'] = len(blob)
        chunks.append(blob)
        pos += len(blob)

    hjson = json.dumps(header, separators=(',', ':')).encode('utf-8')
    pad = (4 - len(hjson) % 4) % 4
    hjson_padded = hjson + b'\0' * pad

    f3 = len(hjson)
    f2 = 4 + len(hjson_padded)
    f1 = 4 + f2

    out = bytearray()
    out += struct.pack('<I', 4)
    out += struct.pack('<I', f1)
    out += struct.pack('<I', f2)
    out += struct.pack('<I', f3)
    out += hjson_padded
    if len(out) != 8 + f1:
        raise AssertionError('pickle header length mismatch')
    for c in chunks:
        out += c
    return bytes(out), hashlib.sha256(hjson).hexdigest()


def syntax_gate(path, blob, check_dir):
    os.makedirs(check_dir, exist_ok=True)
    tmp = os.path.join(check_dir, os.path.basename(path).replace('.js', '.mjs'))
    with open(tmp, 'wb') as f:
        f.write(blob)
    r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
    if r.returncode != 0:
        return (r.stderr or r.stdout or '')[:1500]
    return None


def main():
    ap = argparse.ArgumentParser(description=f'Build patched asar for Claude {VERSION}')
    ap.add_argument('--asar', required=True, help='原始 ion-dist.asar')
    ap.add_argument('--exe', required=True, help='原始 claude.exe')
    ap.add_argument('--out', default='build/v5', help='输出目录')
    ap.add_argument('--skip-syntax', action='store_true', help='跳过 node --check 门禁（不推荐）')
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out)
    check_dir = os.path.join(out_dir, 'check')
    os.makedirs(out_dir, exist_ok=True)

    raw, header, base, header_size = load_asar(args.asar)
    v1 = header['files']['assets']['files']['v1']['files']

    # 1) 应用补丁
    # strict=True：该对必须且只能出现一次
    # strict=False：候选对，命中哪对算哪对（档位白名单在不同模块里写法不一样，
    #               有的是 new Set([...])，有的是裸数组）
    todo = [(p, pairs, True) for p, pairs in PATCHES]
    todo += [(p, ENUM_PATCHES, False) for p in ENUM_TARGETS]

    replacements = {}
    for prefix, pairs, strict in todo:
        name = next((n for n in v1 if n.startswith(prefix)), None)
        if name is None:
            print(f'[SKIP] 找不到模块 {prefix} —— 可能上游又重构了，请重新定位')
            continue
        node = v1[name]
        off, size = int(node['offset']), int(node['size'])
        blob = raw[base + off: base + off + size]
        applied = 0
        for old, new in pairs:
            cnt = blob.count(old)
            if cnt > 1:
                print(f'[FAIL] {name}: 目标串出现 {cnt} 次（应为 1）\n       {old[:90]!r}')
                return 1
            if cnt == 0:
                if strict:
                    print(f'[FAIL] {name}: 目标串出现 0 次\n       {old[:90]!r}')
                    return 1
                continue
            blob = blob.replace(old, new, 1)
            applied += 1
        if applied == 0:
            print(f'[SKIP] {name}: 没有可命中的候选串')
            continue
        replacements['assets/v1/' + name] = blob
        print(f'[OK] {name}  {applied} 处  {size} -> {len(blob)} 字节')

    if not replacements:
        print('[FAIL] 一个补丁点都没命中，版本很可能不匹配')
        return 1

    # 2) 语法门禁
    if not args.skip_syntax:
        print('\n--- 语法门禁 (node --check) ---')
        bad = 0
        for path, blob in replacements.items():
            err = syntax_gate(path, blob, check_dir)
            if err:
                bad += 1
                print(f'  FAIL  {path}\n{err}')
            else:
                print(f'  PASS  {path}')
        if bad:
            print('\n!!! 语法门禁未通过，未打包 !!!')
            return 1

    # 3) 重打包
    print('\n--- 重打包 ---')
    new_asar, new_header_hash = repack(raw, header, base, replacements)
    out_asar = os.path.join(out_dir, 'ion-dist.asar')
    with open(out_asar, 'wb') as f:
        f.write(new_asar)
    print(f'[out] {out_asar}  ({len(new_asar)} 字节)')
    print(f'      新 header sha256 = {new_header_hash}')

    # 4) 同步 exe 内嵌的 header 哈希
    exe = open(args.exe, 'rb').read()
    old_header = raw[16:16 + header_size]
    old_hash = hashlib.sha256(old_header).hexdigest().encode('ascii')
    if old_hash not in exe:
        print('[FAIL] 原件 exe 里找不到原 header 哈希，asar/exe 不是同一版')
        return 1
    out_exe = os.path.join(out_dir, 'claude.exe')
    with open(out_exe, 'wb') as f:
        f.write(exe.replace(old_hash, new_header_hash.encode('ascii'), 1))
    print(f'[out] {out_exe}')

    print('\n>>> 构建完成，可以运行 install_asar.py 安装 <<<')
    return 0


if __name__ == '__main__':
    sys.exit(main())
