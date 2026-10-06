#!/bin/bash
# Usage: tools/render_range.sh FIRST LAST  -> renders reels + cards for posts FIRST..LAST, 3 at a time
cd "$(dirname "$0")/.."
seq "$1" "$2" | xargs -P3 -I{} sh -c 'python3 render_reel.py tips/post-{}.json >/dev/null && python3 render_card.py tips/post-{}.json >/dev/null && echo "ok {}" || echo "FAIL {}"'
