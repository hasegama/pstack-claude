#!/usr/bin/env bash
# Claude の環境設定の Setup script に貼り付けて使用する。
# PSTACK_CLAUDE_REF に配布リポジトリのコミット SHA またはリリースタグを指定できる。
# WORKSPACE_ROOT を省略した場合は CLAUDE_PROJECT_DIR または現在の Git ルートを使う。
set -euo pipefail

PSTACK_CLAUDE_REF="${PSTACK_CLAUDE_REF:-v0.2.0}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-}}"
if [ -z "$WORKSPACE_ROOT" ]; then
    WORKSPACE_ROOT="$(git rev-parse --show-toplevel)" || {
        echo 'WORKSPACE_ROOT に対象リポジトリの絶対パスを指定してください。' >&2
        exit 1
    }
fi
WORKSPACE_ROOT="$(cd -- "$WORKSPACE_ROOT" && pwd)"
for command in python3 git curl tar; do
    command -v "$command" >/dev/null || { echo "必要なコマンドがありません: $command" >&2; exit 1; }
done
case "$PSTACK_CLAUDE_REF" in
    ''|*[!a-zA-Z0-9._-]*) echo 'PSTACK_CLAUDE_REF はコミット SHA またはタグ名を指定してください。' >&2; exit 1 ;;
esac

download_dir="$(mktemp -d)"
trap 'rm -rf -- "$download_dir"' EXIT
curl --fail --show-error --silent --location --retry 3 --connect-timeout 15 --max-time 120 \
    "https://codeload.github.com/hasegama/pstack-claude/tar.gz/${PSTACK_CLAUDE_REF}" \
    --output "$download_dir/plugin.tar.gz"
tar -xzf "$download_dir/plugin.tar.gz" -C "$download_dir" --strip-components=1
python3 "$download_dir/scripts/install.py" --project "$WORKSPACE_ROOT"
python3 "$download_dir/scripts/install_shared.py" --project "$WORKSPACE_ROOT" --target claude --source "$download_dir/plugins/pstack-claude" --templates
python3 "$download_dir/scripts/project_start.py" --project "$WORKSPACE_ROOT"
echo "[pstack] 配布物 ${PSTACK_CLAUDE_REF} の導入を確認しました。"
