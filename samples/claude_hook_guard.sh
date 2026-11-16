#!/bin/bash
input=$(cat)
echo "fired" >> "$CLAUDE_PROJECT_DIR/hook.log"
if echo "$input" | grep -q 'danger-test'; then
  echo "danger-test가 들어간 명령은 이 프로젝트에서 막혀 있습니다" >&2
  exit 2
fi
exit 0
