#!/usr/bin/env bash
# Claude の環境設定の Setup script に貼り付けて使用する。
# プラグインを /opt/claude-plugins/pstack-claude に展開する。環境設定の環境変数に
# CLAUDE_CODE_PLUGIN_DIRS=/opt/claude-plugins を書くと、セッションがプラグインとして読み込む。
# 環境設定の環境変数はこのスクリプトに渡らないため、取得する版は下の値を書き換えて指定する。
set -euo pipefail

PSTACK_CLAUDE_REF="${PSTACK_CLAUDE_REF:-v0.15.21}"
PLUGINS_DIR="${PLUGINS_DIR:-/opt/claude-plugins}"

download_dir="$(mktemp -d)"
trap 'rm -rf -- "$download_dir"' EXIT
curl --fail --show-error --silent --location --retry 3 --connect-timeout 15 --max-time 120 \
    "https://codeload.github.com/hasegama/pstack-claude/tar.gz/${PSTACK_CLAUDE_REF}" \
    --output "$download_dir/plugin.tar.gz"
tar -xzf "$download_dir/plugin.tar.gz" -C "$download_dir" --strip-components=1
mkdir -p "$PLUGINS_DIR"
rm -rf -- "$PLUGINS_DIR/pstack-claude"
mv "$download_dir/plugins/pstack-claude" "$PLUGINS_DIR/pstack-claude"
echo "[pstack] ${PSTACK_CLAUDE_REF} を ${PLUGINS_DIR}/pstack-claude に展開しました。"
