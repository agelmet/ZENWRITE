#!/usr/bin/env python3
"""Copy favicon.py's icon block from index.html into every sub-page (favicon.py only links root pages)."""
import os, re, sys
root = sys.argv[1]
idx = open(f'{root}/index.html').read()
m = re.search(r'<!-- advon-icons.*?<!-- /advon-icons -->', idx, re.S)
blk = m.group(0)
n = 0
for dp, _, fs in os.walk(root):
    for f in fs:
        if not f.endswith('.html'): continue
        p = os.path.join(dp, f); rel = os.path.relpath(p, root)
        depth = rel.count('/')
        if depth == 0: continue
        pre = '../' * depth
        b = re.sub(r'href="(?!https?:|/)', f'href="{pre}', blk)
        s = open(p).read()
        s = re.sub(r'<!-- advon-icons.*?<!-- /advon-icons -->\n?', '', s, flags=re.S)
        s = s.replace('</title>', '</title>\n' + b, 1)
        open(p, 'w').write(s); n += 1
# privacy page: meta description
pp=f'{root}/privacy.html'
s=open(pp).read()
if 'name="description"' not in s:
    s=s.replace('</title>','</title>\n<meta name="description" content="Πολιτική απορρήτου & cookies της ZenWrite: ποια στοιχεία χρησιμοποιούνται, για ποιον σκοπό και ποια είναι τα δικαιώματά σας. Privacy & cookies policy in English.">',1)
    open(pp,'w').write(s)
print('icons →', n, 'sub-pages')
