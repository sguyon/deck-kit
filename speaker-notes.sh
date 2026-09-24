#!/bin/bash
# Extracts slide titles + speaker notes from deck.md into speaker-notes.md (read-only view for rehearsal).
cd "$(dirname "$0")"
python3 - <<'PY'
import re
s=open('deck.md').read()
body=s[s.index('\n---\n',4)+5:]
out=['# Speaker notes (generated from deck.md speaker notes — edit the deck, not this file)\n']
for sl in body.split('\n---\n'):
    t=re.search(r'^#{1,2} (.+)$',sl,re.M)
    n=re.search(r'<!-- Speaker notes:?\s*(.*?)-->',sl,re.S)
    if not t: continue
    out.append(f'## {t.group(1)}\n')
    out.append((n.group(1).strip() if n else '_(no notes)_')+'\n')
open('speaker-notes.md','w').write('\n'.join(out))
PY
echo "wrote speaker-notes.md"
