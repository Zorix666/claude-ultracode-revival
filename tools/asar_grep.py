"""在整个 asar 内逐个文件统计关键词出现次数。

用法: python asar_grep.py <asar> <keyword> [maxhits]
"""
import sys, struct, json

p = sys.argv[1]
kw = sys.argv[2].encode('utf-8')
maxhits = int(sys.argv[3]) if len(sys.argv) > 3 else 30

d = open(p, 'rb').read()
hs = struct.unpack('<I', d[12:16])[0]
header = json.loads(d[16:16 + hs].decode('utf-8'))
base = 8 + struct.unpack('<I', d[4:8])[0]

out = []


def walk(node, path):
    if 'files' in node:
        for k, v in node['files'].items():
            walk(v, (path + '/' + k) if path else k)
    elif 'size' in node and 'offset' in node:
        off = base + int(node['offset'])
        size = int(node['size'])
        if size > 40 * 1024 * 1024:
            return
        blob = d[off:off + size]
        c = blob.count(kw)
        if c:
            out.append((c, path, size))


walk(header, '')
out.sort(reverse=True)
for c, path, size in out[:maxhits]:
    print('%5d  %8d  %s' % (c, size, path))
print('files_with_hits', len(out))
