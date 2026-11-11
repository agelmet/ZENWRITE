#!/bin/bash
# ZenWrite build — cloud container paths
set -e
cd /home/claude/zw
A=/home/claude/ac/.advon
python3 src/build.py
NODE_PATH=$(npm root -g) node og.js
ADVON_TOOLS=/home/claude/tools python3 $A/privacy/privacy_fix.py apply site >/dev/null
python3 $A/favicon.py make $PWD/site assets/img/zenwrite-logo.svg --tile "#F6F2EA" | tail -1
python3 src/post.py site
python3 $A/seo_live.py fix $PWD/site zenwrite.gr | tail -3
python3 $A/ai_seo.py fix $PWD/site zenwrite.gr | tail -3
