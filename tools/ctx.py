"""按关键词打印 bundle 上下文片段。

用法: python ctx.py <file> <keyword> [width] [maxhits]
"""
import sys

p = sys.argv[1]
kw = sys.argv[2]
w = int(sys.argv[3]) if len(sys.argv) > 3 else 400
maxhits = int(sys.argv[4]) if len(sys.argv) > 4 else 20

s = open(p, encoding='utf-8', errors='replace').read()
i = 0
n = 0
while n < maxhits:
    j = s.find(kw, i)
    if j < 0:
        break
    n += 1
    print('=== hit %d at %d' % (n, j))
    print(s[max(0, j - w): j + w].replace('\n', ' '))
    print()
    i = j + len(kw)
print('total_shown', n)
