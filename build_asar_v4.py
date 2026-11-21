# -*- coding: utf-8 -*-
"""
Builder for Claude Desktop **4.23118.x Electron standalone** (non-MSIX).

Unlike the 5.x / 6.x MSIX builds, this one installs under
`%LOCALAPPDATA%\\Programs\\Claude` and lays out resources differently:

    <root>\\resources\\ion-dist.asar     <-- no `app\\` level
    <root>\\claude.exe

What it does
  1. Turns 5 effort stops into 6. The 6th stop uses the id **"ultracode"**,
     which this build already knows natively (see `shared-33`'s `pT()` and
     `shared-7`'s `t.id==="ultracode"` accent branch) — using "ultra" here
     means hand-patching three extra places for no gain.
  2. Forces `thinkingStyle:"separate"`, which is what pulls the effort slider
     OUT of the model menu and renders it as its own pill. `"inline"` gives
     you a list, not a slider.
  3. Always renders the bottom Effort pill; paints it pure violet via
     `var(--cds-text-pro)` with **zero** shadow / border / background.
  4. Widens the panel to 260px and removes the standalone Ultracode toggle row.

Usage
    # inspect every anchor without writing anything
    python build_asar_v4.py --dry-run \
        --asar "%LOCALAPPDATA%\\Programs\\Claude\\resources\\ion-dist.asar.bak" \
        --exe  "%LOCALAPPDATA%\\Programs\\Claude\\claude.exe.bak"

    # build
    python build_asar_v4.py \
        --asar "%LOCALAPPDATA%\\Programs\\Claude\\resources\\ion-dist.asar.bak" \
        --exe  "%LOCALAPPDATA%\\Programs\\Claude\\claude.exe.bak" \
        --out  build/v4

Input MUST be the pristine (unpatched) pair. Feeding an already-patched file
fails every anchor check on purpose — no half-patched bundle is ever produced.
"""
import os
import sys
import json
import argparse
import hashlib
import struct
import subprocess

VERSION = "4.23118.x (Electron standalone)"

# ---------------------------------------------------------------------------
# (module prefix, [(old, new, expected_count), ...])
# ---------------------------------------------------------------------------
PATCHES = [
    # ============ shared-8: schema source + model-menu submenu -> separate ============
    ('shared-8-', [
        # The one authoritative stop list: Wb = a(Vb) is the zod enum, and Yb()
        # filters candidates through Wb.safeParse. Extend Vb and the whole chain
        # (Gb / Yb / Xb) accepts the 6th stop with no further edits.
        (b'var Vb=["low","medium","high","xhigh","max"],Hb="high",',
         b'var Vb=["low","medium","high","xhigh","max","ultracode"],Hb="high",', 1),
        # Kill the submenu; "separate" is the only value that yields a slider.
        (b'u?{overflowStyle:"inline",thinkingStyle:"inline",overflowSearch:le}:'
         b'{overflowStyle:"submenu",thinkingStyle:"submenu",overflowSearch:le,'
         b'overflowRowPresentation:le?Lm:void 0}',
         b'{overflowStyle:"submenu",thinkingStyle:"separate",overflowSearch:le}', 1),
        # In separate mode the stop count must not collapse to 0, or the pill is culled.
        (b'xt?null:e.config?.thinkingStyle==="separate"?'
         b'O?.models.find(e=>e.id===Te.model)?.thinking?.effort_options?.length??0:0',
         b'xt?null:(O?.models.find(e=>e.id===Te.model)?.thinking?.effort_options?.length||6)', 1),
        # Never render the "Effort >" row inside the model menu.
        (b'(!u||v)&&g(Eg,{currentModel:U,conversationUuid:t,surface:v,effortOverride:y,',
         b'!1&&g(Eg,{currentModel:U,conversationUuid:t,surface:v,effortOverride:y,', 1),
    ]),

    # ============ shared-7: inject 6th stop + force separate ============
    ('shared-7-', [
        # When the ultracode flag is on, the backend itself ships stop names like
        # "Extra · Ultracode" (the i18n template "{level} · {ultracode}").
        # Strip that suffix first, otherwise the bottom pill keeps the tail and the
        # 6th stop still reads "Extra". This bites even after toggleLabel is nulled,
        # because the value comes from the option *name*, not from the toggle.
        (b'function GV(e){return e?.thinking?.effort_options??[]}',
         b'function GV(e){let a=(e?.thinking?.effort_options??[]).map(o=>'
         b'({...o,name:(o.name||"").replace(/\\s*\\u00B7\\s*Ultracode$/,"")}));'
         b'return a.some(e=>e.id==="ultracode")?a:a.concat({id:"ultracode",name:"Ultracode"})}', 1),
        (b're=c?.thinkingStyle==="separate"?[]:GV(ne)',
         b're=[]', 1),
        (b'I=C?.thinkingStyle==="separate"',
         b'I=!0', 1),
        (b'U=o?.thinkingStyle==="separate"',
         b'U=!0', 1),
        (b'v=f&&"text-pro",',
         b'v=(f||c?.id==="ultracode")&&"text-pro",', 1),
        # `f` is what the trigger later receives as `toggleLabel`, and its value
        # is `a?.checked ? a.label : null` — non-null whenever the *session's*
        # ultracode flag is on, no matter which stop is selected. That is how
        # "High · Ultracode" reached the bottom pill even after the option-name
        # suffix was stripped. Pin it to null and scrub the name suffix too, so
        # a stale flag can never resurrect the tail.
        (b'd=c?.name??"",f=a?.checked?a.label:null,',
         b'd=(c?.name??"").replace(/\\s*\\u00B7\\s*Ultracode$/,""),f=null,', 1),
    ]),

    # ============ c227f4d5e: which surface config each placement gets ============
    ('c227f4d5e', [
        # HR = {shortcuts:!0}  -> no thinkingStyle -> submenu -> LIST
        # zR = {shortcuts:!0, thinkingStyle:"separate"} -> SLIDER
        # chin/row is the environment row under the composer: force the slider.
        (b'case"chin":case"row":return n?t?GR:WR:t?UR:HR;',
         b'case"chin":case"row":return t?VR:BR;', 1),
        (b'tR=["low","medium","high","xhigh","max"]',
         b'tR=["low","medium","high","xhigh","max","ultracode"]', 1),
        # Slider glow. Official code:
        #   fe = F ? (v ? (v.on ? ez : tz) : void 0)
        #            : (last stop is ultracode ? $R : void 0)
        # ez = always lit, tz = never lit, $R = lit only at the last stop (atMax).
        # We force `separate`, so F is always true and the glow follows the
        # ultracode toggle instead of the chosen stop: once that flag has ever
        # been true, the track glows at Max/High too. Pin it to $R.
        (b'fe=F?v?v.on?ez:tz:void 0:uf(ue?.thinking?.effort_options?.at(-1)?.id)?$R:void 0',
         b'fe=$R', 1),
    ]),

    # ============ cc43287c9: environment row / bottom pill ============
    ('cc43287c9', [
        # Stop appending effort to the model pill tail.
        (b's=(o?[{field:"fastMode",word:e.fastLabel},{field:"effort",word:e.thinkingLabel},'
         b'{field:null,word:e.toggleLabel&&`\\u00B7 ${e.toggleLabel}`}]:[]).filter(lCe)',
         b's=(o?[{field:"fastMode",word:e.fastLabel}]:[]).filter(lCe)', 1),
        # Always render the Effort pill; pure violet text, nothing else.
        (b'effort:n.effortOptionCount>0?p(sy.Effort,{...n.effort,tooltip:Ce,shortcut:Te,'
         b'renderTrigger:e=>{let{label:n,toggleLabel:r}=e;return p(he,{variant:"ghost",'
         b'className:G5(t),"data-testid":"environment-row-effort",children:p(q5,'
         b'{overridden:K("effort"),label:r?m.formatMessage(fB.levelWithUltracode,'
         b'{level:n,ultracode:r}):n})})}}):null',
         b'effort:p(sy.Effort,{...n.effort,tooltip:Ce,shortcut:Te,renderTrigger:e=>{'
         b'let{label:n,toggleLabel:r}=e,isU=n==="Ultracode"||r==="Ultracode"||n==="ultracode"'
         b'||n.includes("Ultracode");'
         b'return p(he,{variant:"ghost",className:G5(t),"data-testid":"environment-row-effort",'
         b'children:isU?p("span",{className:"font-medium text-pro",'
         b'style:{color:"var(--cds-text-pro)"},children:"Ultracode"}):p(q5,'
         b'{overridden:K("effort"),label:r?m.formatMessage(fB.levelWithUltracode,'
         b'{level:n,ultracode:r}):n})})}})', 1),
        # The bare `reportEffortOptionCount:!1` appears twice; only the main
        # environment row must flip. Anchor on its neighbours.
        (b'finalFocus:G??a,reportEffortOptionCount:!1,environmentModelId:be.modelId',
         b'finalFocus:G??a,reportEffortOptionCount:!0,environmentModelId:be.modelId', 1),
        # Fallback label path (used when the trigger is not a function): never
        # format the "level · Ultracode" template, just show the stop.
        (b'label:r?m.formatMessage(fB.levelWithUltracode,{level:n,ultracode:r}):n',
         b'label:n', 1),
    ]),

    # ============ c3f9f1667: the environment-row pill's label producer ============
    # cc43287c9 imports this module's pe() (aliased `WV`) to compute the effort
    # text on the environment row. Upstream, when the ultracode flag is on and
    # the layout is `separate`, it deliberately swaps the stop name for
    # formatMessage(levelWithUltracode, {level, ultracode}) — i.e.
    # "Max · Ultracode". `separate` is forced here, so that branch always runs.
    # Our 6th stop is a real stop, so the label is simply the current one.
    ('c3f9f1667', [
        (b'function pe(e,t){if(!e)return null;'
         b'let n=e.options.find(t=>t.id===e.level)?.label??null,{ultracode:r}=e;'
         b'return r?.on?r.separate?n===null?null:t.formatMessage(O.levelWithUltracode,'
         b'{level:n,ultracode:r.label}):r.label:n}',
         b'function pe(e,t){if(!e)return null;'
         b'let n=e.options.find(t=>t.id===e.level);'
         b'return n?.label??n?.name??null}', 1),
    ]),

    # ============ c9543da06: pin the ultracode flag to the chosen stop ============
    ('c9543da06', [
        # Official code passes Pe() — the *current* ultracode flag — as the second
        # argument on every pick, so once Ultracode has been turned on it stays on
        # forever: switching back to High/Max still yields "High · Ultracode", the
        # slider keeps glowing, and the panel title keeps its accent.
        # Upstream can do that because ultracode is a standalone toggle. We made it
        # the 6th stop, so the flag has to follow the stop itself.
        # Do NOT copy the 5.x form `At(e, e>"max", …)`: that string comparison is
        # also true for "xhigh" ('x' > 'm') and misreads Extra as ultracode.
        (b'(e,t)=>At(e,Pe(),{recordAsPick:t?.recordAsPick})',
         b'(e,t)=>At(e,e==="ultracode",{recordAsPick:t?.recordAsPick})', 1),
        # Picking a stop is not enough: the flag *itself* is read back when a
        # conversation is opened. It is `Ee = we && Se`, where `we` comes from a
        # per-conversation in-memory Map (`hc.get(J) ?? false`). Conversations
        # that once had ultracode on keep that `true` forever, so reopening them
        # shows the flag as on while the slider sits on High. `_e` is the
        # effective stop id (declared earlier in the same scope) — derive Ee
        # from it so the flag can only ever mean "the slider is on ultracode".
        (b'Ee=we&&Se,',
         b'Ee=_e==="ultracode",', 1),
        # Dt() builds fromLabel/toLabel for the switch-confirmation popover and
        # also appends " · Ultracode" in separate mode. With a real 6th stop,
        # the stop's own name is all we want.
        (b'return t?j.formatMessage(Pa.levelWithUltracode,{level:i,ultracode:r}):i',
         b'return i', 1),
    ]),

    # ============ c74045701: i18n ============
    ('c74045701', [
        (b'max:{defaultMessage:"Max",id:"kkjl2vQekD"}',
         b'max:{defaultMessage:"Max",id:"kkjl2vQekD"},'
         b'ultracode:{defaultMessage:"Ultracode",id:"ultracode_label"}', 1),
    ]),

    # ============ remaining stop whitelists ============
    ('shared-0-', [
        (b'HW=["low","medium","high","xhigh","max"]',
         b'HW=["low","medium","high","xhigh","max","ultracode"]', 1),
    ]),
    ('shared-196-', [
        (b'lJ=new Set(["low","medium","high","xhigh","max"])',
         b'lJ=new Set(["low","medium","high","xhigh","max","ultracode"])', 1),
    ]),
    ('shared-4-', [
        (b'dE=new Set(["low","medium","high","xhigh","max"])',
         b'dE=new Set(["low","medium","high","xhigh","max","ultracode"])', 1),
    ]),
    ('cd4f82e77', [
        (b'Rn=["low","medium","high","xhigh","max"]',
         b'Rn=["low","medium","high","xhigh","max","ultracode"]', 1),
    ]),
]

WIDTH_MODULE = 'c8e04f916'
WIDTH_PAIRS = [(b'w-[220px]', b'w-[260px]')]

# Panel-side fixes that must land after the toggle row is cut.
PANEL_PAIRS = [
    # The pill text must follow the *locally chosen* stop index R, not the
    # backend's effective index F. Under ultracode F still points at xhigh/max,
    # so the pill reads "Extra"/"Max" even when the 6th stop is selected.
    # R is the position the user actually dragged to, and it is the same source
    # the panel title uses (ft = G(R)) — so the two stay consistent.
    (b'pe({label:G(F),warningLabel:Y,',
     b'pe({label:G(R),warningLabel:Y,'),
    # Stop forwarding the toggle label to the custom trigger; otherwise
    # cc43287c9 formats it as "High · Ultracode".
    (b'toggleLabel:N,open:M,disabled:C||!B}',
     b'toggleLabel:null,open:M,disabled:C||!B}'),
    # Accent only when the selected stop really is the 6th one.
    (b'Ne=z?.id==="ultracode"||N!==null',
     b'Ne=z?.id==="ultracode"'),
    # Trigger fallback for when `pe` is not a function: label from the local
    # index R, and never paint violet from a leftover toggle flag.
    (b'className:c("min-w-0 truncate",N&&"text-pro"),children:G(F)',
     b'className:c("min-w-0 truncate",!1&&"text-pro"),children:G(R)'),
]

# The Ultracode toggle row lives in c8e04f916. Its slot index ($124) is stable
# across 5.x and 4.23.x, so anchor on the structure and cut to the trailing
# `,Et=` binding rather than trying to match the whole nested JSX.
TOGGLE_START = b'Tt=J4($,124,C,D,Ee,Te)?K4($,124,C,D,Ee,Te,D?t("div",{'
TOGGLE_END = b',Et='


def load_asar(path):
    with open(path, 'rb') as f:
        raw = f.read()
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


def cut_toggle_row(blob):
    start = blob.find(TOGGLE_START)
    if start < 0:
        return None, 'toggle-row start anchor not found'
    end = blob.find(TOGGLE_END, start)
    if end < 0:
        return None, 'toggle-row end anchor not found'
    return blob[:start] + b'Tt=null' + blob[end:], None


def repack(raw, header, base, replacements):
    """Repack per Chromium Pickle rules.

    Three invariants; break any one and the app white-screens with an error
    that points nowhere near the cause:
      1. offset must be written as a *string* (C++ reads it via FindString)
      2. f0=4, f1=4+f2, f2=4+padded_json_len, f3=json_len, data at 8+f1
      3. integrity.hash AND integrity.blocks must both be recomputed
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


def apply_patches(raw, v1, base):
    replacements = {}
    errors = []

    def get_blob(prefix):
        name = next((n for n in v1 if n.startswith(prefix)), None)
        if name is None:
            return None, None
        node = v1[name]
        off, size = int(node['offset']), int(node['size'])
        return name, raw[base + off: base + off + size]

    for prefix, pairs in PATCHES:
        name, blob = get_blob(prefix)
        if blob is None:
            errors.append(f'module not found: {prefix}')
            continue
        for old, new, want in pairs:
            cnt = blob.count(old)
            if cnt != want:
                errors.append(f'{name}: expected {want} match(es), got {cnt}\n    {old[:100]!r}')
                continue
            blob = blob.replace(old, new, want)
        replacements['assets/v1/' + name] = blob

    name, blob = get_blob(WIDTH_MODULE)
    if blob is None:
        errors.append(f'module not found: {WIDTH_MODULE}')
    else:
        for old, new in WIDTH_PAIRS:
            cnt = blob.count(old)
            if cnt == 0:
                errors.append(f'{name}: width anchor {old!r} missing')
                continue
            blob = blob.replace(old, new)
            print(f'  [width]  {name}: {cnt}x {old.decode()} -> {new.decode()}')
        blob2, err = cut_toggle_row(blob)
        if err:
            errors.append(f'{name}: {err}')
        else:
            blob = blob2
            print(f'  [toggle] {name}: Ultracode toggle row removed')
        for old, new in PANEL_PAIRS:
            cnt = blob.count(old)
            if cnt != 1:
                errors.append(f'{name}: panel anchor hit {cnt}x (want 1)\n    {old[:90]!r}')
                continue
            blob = blob.replace(old, new, 1)
        print(f'  [panel]  {name}: pill text and accent decoupled from the toggle')
        replacements['assets/v1/' + name] = blob

    return replacements, errors


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
    ap.add_argument('--asar', required=True, help='pristine ion-dist.asar')
    ap.add_argument('--exe', required=True, help='pristine claude.exe')
    ap.add_argument('--out', default='build/v4', help='output directory')
    ap.add_argument('--dry-run', action='store_true', help='validate anchors only')
    ap.add_argument('--skip-syntax', action='store_true', help='skip node --check (not advised)')
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out)
    raw, header, base, header_size = load_asar(args.asar)
    v1 = header['files']['assets']['files']['v1']['files']
    print(f'[in] {args.asar} ({len(raw)} bytes, {len(v1)} modules)')

    replacements, errors = apply_patches(raw, v1, base)
    if errors:
        print('\n!!! anchor validation FAILED !!!')
        for e in errors:
            print(' -', e)
        return 1
    print(f'\n[ok] {len(replacements)} modules patched')

    if args.dry_run:
        print('(dry run - nothing written)')
        return 0

    os.makedirs(out_dir, exist_ok=True)
    if not args.skip_syntax:
        print('\n--- syntax gate (node --check) ---')
        bad = 0
        for path, blob in replacements.items():
            err = syntax_gate(path, blob, os.path.join(out_dir, 'check'))
            if err:
                bad += 1
                print(f'  FAIL  {path}\n{err}')
            else:
                print(f'  PASS  {path}')
        if bad:
            print('\n!!! syntax gate failed - nothing written !!!')
            return 1

    print('\n--- repack ---')
    new_asar, new_hash = repack(raw, header, base, replacements)
    out_asar = os.path.join(out_dir, 'ion-dist.asar')
    with open(out_asar, 'wb') as f:
        f.write(new_asar)
    print(f'[out] {out_asar} ({len(new_asar)} bytes)')
    print(f'      header sha256 = {new_hash}')

    exe = open(args.exe, 'rb').read()
    old_hash = hashlib.sha256(raw[16:16 + header_size]).hexdigest().encode('ascii')
    if old_hash not in exe:
        print('[FAIL] original header sha256 not found in claude.exe - asar/exe mismatch')
        return 1
    out_exe = os.path.join(out_dir, 'claude.exe')
    with open(out_exe, 'wb') as f:
        f.write(exe.replace(old_hash, new_hash.encode('ascii'), 1))
    print(f'[out] {out_exe}')

    print('\n>>> build complete - run install_electron.py to install <<<')
    return 0


if __name__ == '__main__':
    sys.exit(main())
